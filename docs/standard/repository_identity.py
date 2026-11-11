"""Descriptor-anchored file I/O and Git repository identity inspection."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


def _read_regular_bytes(path: Path, *, root: Path | None = None) -> bytes:
    """Read a regular file without following symlinks, anchored via dir_fd when root is set."""
    o_nofollow = getattr(os, "O_NOFOLLOW", 0)
    o_directory = getattr(os, "O_DIRECTORY", 0)
    if root is None:
        if path.is_symlink():
            raise ValueError(f"symlink path is forbidden: {path}")
        try:
            fd = os.open(path, os.O_RDONLY | o_nofollow)
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                raise ValueError(f"symlink path is forbidden: {path}") from exc
            raise
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError(f"path is not a regular file: {path}")
            with os.fdopen(fd, "rb") as handle:
                fd = -1
                return handle.read()
        finally:
            if fd >= 0:
                os.close(fd)

    if root.is_symlink():
        raise ValueError(f"symlink root is forbidden: {root}")
    rel_parts = path.relative_to(root).parts if path.is_absolute() else path.parts
    if not rel_parts or any(part in {"", ".", ".."} for part in rel_parts):
        raise ValueError(f"invalid or escaping artifact path: {path}")
    cur_fd = os.open(root, os.O_RDONLY | o_directory | o_nofollow)
    try:
        for segment in rel_parts[:-1]:
            try:
                next_fd = os.open(segment, os.O_RDONLY | o_directory | o_nofollow, dir_fd=cur_fd)
            except OSError as exc:
                if exc.errno == errno.ELOOP or (
                    exc.errno == errno.ENOTDIR
                    and stat.S_ISLNK(os.lstat(segment, dir_fd=cur_fd).st_mode)
                ):
                    raise ValueError(f"symlink path is forbidden: {path}") from exc
                raise
            os.close(cur_fd)
            cur_fd = next_fd
        try:
            leaf_fd = os.open(rel_parts[-1], os.O_RDONLY | o_nofollow, dir_fd=cur_fd)
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                raise ValueError(f"symlink path is forbidden: {path}") from exc
            raise
        try:
            if not stat.S_ISREG(os.fstat(leaf_fd).st_mode):
                raise ValueError(f"path is not a regular file: {path}")
            with os.fdopen(leaf_fd, "rb") as handle:
                leaf_fd = -1
                return handle.read()
        finally:
            if leaf_fd >= 0:
                os.close(leaf_fd)
    finally:
        os.close(cur_fd)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"duplicate JSON key: {key!r}")
        obj[key] = value
    return obj


def _reject_nonfinite_constant(token: str) -> Any:
    raise ValueError(f"non-finite JSON constant is forbidden: {token}")


def _loads_strict_json(raw: bytes) -> Any:
    return json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_nonfinite_constant,
    )


def load_json(path: Path, *, root: Path | None = None) -> Any:
    return _loads_strict_json(_read_regular_bytes(path, root=root))


def digest(path: Path, *, root: Path | None = None) -> str:
    return hashlib.sha256(_read_regular_bytes(path, root=root)).hexdigest()


def parse_repository_remote(remote_url: str) -> tuple[str, str]:
    """Return a credential-free host and owner/repository reference."""
    if "://" in remote_url:
        parsed = urlsplit(remote_url)
        if parsed.scheme not in {"https", "http", "ssh", "git"} or not parsed.hostname:
            raise ValueError("remote must use an authenticated network Git transport")
        host, remote_path = parsed.hostname.lower(), parsed.path
    else:
        match = re.fullmatch(r"(?:[^@/:]+@)?([^/:]+):(.+)", remote_url)
        if not match:
            raise ValueError("remote must be an absolute network URL or SCP-style Git URL")
        host, remote_path = match.group(1).lower(), match.group(2)
    repository_ref = remote_path.strip("/").removesuffix(".git")
    segments = repository_ref.split("/")
    if len(segments) < 2 or any(not segment or segment in {".", ".."} for segment in segments):
        raise ValueError("remote path must contain an owner and repository")
    return host, repository_ref


def run_git(repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repository), *arguments],
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )


def inspect_repository_identity(
    repository: Path,
    *,
    remote_name: str = "origin",
    workspace_root: Path | None = None,
    expected_host: str | None = None,
    expected_ref: str | None = None,
) -> dict[str, Any]:
    """Inspect identity without changing the checkout or any remote state."""
    failures: list[dict[str, str]] = []
    requested_path = repository.resolve()
    top_level_result = run_git(requested_path, "rev-parse", "--show-toplevel")
    if top_level_result.returncode != 0:
        failures.append(
            {"code": "USAGE-REPOSITORY-GIT-001", "path": str(requested_path), "message": "path is not a Git worktree"}
        )
        return {"schema": "wellmanifest.repository-identity/inspection/v1", "valid": False, "failures": failures}
    checkout_path = Path(top_level_result.stdout.strip()).resolve()
    remote_result = run_git(checkout_path, "remote", "get-url", remote_name)
    repository_host: str | None = None
    repository_ref: str | None = None
    if remote_result.returncode != 0:
        failures.append({"code": "USAGE-REPOSITORY-REMOTE-001", "path": remote_name, "message": "canonical remote is missing"})
    else:
        try:
            repository_host, repository_ref = parse_repository_remote(remote_result.stdout.strip())
        except ValueError as error:
            failures.append({"code": "USAGE-REPOSITORY-REMOTE-002", "path": remote_name, "message": str(error)})
    if expected_ref and repository_ref and repository_ref != expected_ref:
        failures.append(
            {
                "code": "USAGE-REPOSITORY-REF-001",
                "path": remote_name,
                "message": f"remote resolves to {repository_ref}, expected {expected_ref}",
            }
        )
    if expected_host and repository_host and repository_host != expected_host.lower():
        failures.append(
            {
                "code": "USAGE-REPOSITORY-HOST-001",
                "path": remote_name,
                "message": f"remote resolves to {repository_host}, expected {expected_host.lower()}",
            }
        )
    resolved_workspace_root = workspace_root.resolve() if workspace_root else None
    expected_path = (
        resolved_workspace_root.joinpath(*repository_ref.split("/"))
        if resolved_workspace_root and repository_ref
        else None
    )
    status_result = run_git(checkout_path, "status", "--porcelain=v1", "--untracked-files=all")
    worktree_result = run_git(checkout_path, "worktree", "list", "--porcelain")
    worktree_paths = [
        Path(line.removeprefix("worktree ")).resolve()
        for line in worktree_result.stdout.splitlines()
        if line.startswith("worktree ")
    ]
    primary_checkout_path = worktree_paths[0] if worktree_paths else checkout_path
    checkout_kind = "primary" if checkout_path == primary_checkout_path else "linked"
    linked_worktree_count = len(worktree_paths) if worktree_result.returncode == 0 else None
    dirty = status_result.returncode != 0 or bool(status_result.stdout.strip())
    placement_conformant = primary_checkout_path == expected_path if expected_path else None
    if placement_conformant is False:
        failures.append(
            {
                "code": "USAGE-REPOSITORY-PATH-001",
                "path": str(primary_checkout_path),
                "message": f"primary checkout path differs from origin-derived path {expected_path}",
            }
        )
    repair_required = placement_conformant is False
    repair_blockers = (["dirty_checkout"] if dirty else []) + (
        ["linked_worktrees"] if linked_worktree_count is None or linked_worktree_count > 1 else []
    )
    return {
        "schema": "wellmanifest.repository-identity/inspection/v1",
        "valid": not failures,
        "repositoryHost": repository_host,
        "repositoryRef": repository_ref,
        "remoteName": remote_name,
        "checkoutPath": str(checkout_path),
        "checkoutKind": checkout_kind,
        "primaryCheckoutPath": str(primary_checkout_path),
        "workspaceRoot": str(resolved_workspace_root) if resolved_workspace_root else None,
        "expectedPath": str(expected_path) if expected_path else None,
        "pathPolicyChecked": resolved_workspace_root is not None,
        "placementConformant": placement_conformant,
        "dirty": dirty,
        "linkedWorktreeCount": linked_worktree_count,
        "repair": {
            "required": repair_required,
            "mode": "clone-verify-retire",
            "automaticMutation": False,
            "blockedBy": repair_blockers if repair_required else [],
        },
        "failures": failures,
    }

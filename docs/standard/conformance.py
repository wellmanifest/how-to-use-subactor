#!/usr/bin/env python3
"""Dependency-free conformance for versioned Subactor usage profiles."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "docs" / "standard" / "manifest.v1.json"
SCHEMA_PATHS = (
    ROOT / "docs" / "standard" / "manifest.schema.v1.json",
    ROOT / "docs" / "standard" / "interface-profile.schema.v1.json",
    ROOT / "docs" / "standard" / "project-profile.schema.v1.json",
)


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_keys(document: dict[str, Any], required: set[str], optional: set[str] = set()) -> bool:
    return set(document) == required | (set(document) & optional)


def add(failures: list[dict[str, str]], code: str, path: str, message: str) -> None:
    failures.append({"code": code, "path": path, "message": message})


def parse_repository_remote(remote_url: str) -> tuple[str, str]:
    """Return a credential-free host and owner/repository reference."""
    host = ""
    remote_path = ""
    if "://" in remote_url:
        parsed = urlsplit(remote_url)
        if parsed.scheme not in {"https", "http", "ssh", "git"} or not parsed.hostname:
            raise ValueError("remote must use an authenticated network Git transport")
        host = parsed.hostname.lower()
        remote_path = parsed.path
    else:
        match = re.fullmatch(r"(?:[^@/:]+@)?([^/:]+):(.+)", remote_url)
        if not match:
            raise ValueError("remote must be an absolute network URL or SCP-style Git URL")
        host, remote_path = match.groups()
        host = host.lower()
    repository_ref = remote_path.strip("/")
    if repository_ref.endswith(".git"):
        repository_ref = repository_ref[:-4]
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
        add(failures, "USAGE-REPOSITORY-GIT-001", str(requested_path), "path is not a Git worktree")
        return {
            "schema": "wellmanifest.repository-identity/inspection/v1",
            "valid": False,
            "failures": failures,
        }
    checkout_path = Path(top_level_result.stdout.strip()).resolve()
    remote_result = run_git(checkout_path, "remote", "get-url", remote_name)
    repository_host: str | None = None
    repository_ref: str | None = None
    if remote_result.returncode != 0:
        add(failures, "USAGE-REPOSITORY-REMOTE-001", remote_name, "canonical remote is missing")
    else:
        try:
            repository_host, repository_ref = parse_repository_remote(remote_result.stdout.strip())
        except ValueError as error:
            add(failures, "USAGE-REPOSITORY-REMOTE-002", remote_name, str(error))
    if expected_ref and repository_ref and repository_ref != expected_ref:
        add(
            failures,
            "USAGE-REPOSITORY-REF-001",
            remote_name,
            f"remote resolves to {repository_ref}, expected {expected_ref}",
        )
    if expected_host and repository_host and repository_host != expected_host.lower():
        add(
            failures,
            "USAGE-REPOSITORY-HOST-001",
            remote_name,
            f"remote resolves to {repository_host}, expected {expected_host.lower()}",
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
    linked_worktree_count = (
        len(worktree_paths)
        if worktree_result.returncode == 0
        else None
    )
    dirty = status_result.returncode != 0 or bool(status_result.stdout.strip())
    placement_conformant = primary_checkout_path == expected_path if expected_path else None
    if placement_conformant is False:
        add(
            failures,
            "USAGE-REPOSITORY-PATH-001",
            str(primary_checkout_path),
            f"primary checkout path differs from origin-derived path {expected_path}",
        )
    repair_required = placement_conformant is False
    repair_blockers = []
    if dirty:
        repair_blockers.append("dirty_checkout")
    if linked_worktree_count is None or linked_worktree_count > 1:
        repair_blockers.append("linked_worktrees")
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


def validate_interface(profile: dict[str, Any], path: str, failures: list[dict[str, str]]) -> None:
    required = {"schema", "id", "version", "status", "executable", "runtime", "discovery", "operations", "invariants"}
    if not exact_keys(profile, required):
        add(failures, "USAGE-PROFILE-001", path, "interface profile must be closed")
        return
    if profile["schema"] != "wellmanifest.subactor-usage/interface-profile/v1":
        add(failures, "USAGE-PROFILE-002", path, "unexpected interface schema")
    runtime = profile.get("runtime", {})
    if not re.fullmatch(r"[0-9a-f]{40}", str(runtime.get("revision", ""))):
        add(failures, "USAGE-COMPAT-001", path, "runtime revision must be an exact Git SHA")
    discovery = profile.get("discovery", {})
    argv = discovery.get("argv", [])
    expected = discovery.get("expectedCommands", [])
    if not argv or argv[0] != profile.get("executable") or len(expected) != len(set(expected)):
        add(failures, "USAGE-DISCOVERY-001", path, "discovery must bind the executable and unique command catalog")
    operation_ids: set[str] = set()
    for index, operation in enumerate(profile.get("operations", [])):
        operation_path = f"{path}#/operations/{index}"
        operation_required = {"id", "command", "effect", "authority", "requiredEvidence"}
        if not exact_keys(operation, operation_required, {"requiredFlags"}):
            add(failures, "USAGE-OPERATION-001", operation_path, "operation must be closed")
            continue
        if operation["id"] in operation_ids:
            add(failures, "USAGE-OPERATION-002", operation_path, "operation id must be unique")
        operation_ids.add(operation["id"])
        if operation["command"] not in expected:
            add(failures, "USAGE-DISCOVERY-002", operation_path, "operation command is absent from discovery catalog")
        if operation["effect"] == "external_write":
            if operation["authority"] != "apply":
                add(failures, "USAGE-AUTHORITY-001", operation_path, "external write requires apply authority")
            evidence = set(operation["requiredEvidence"])
            if not {"plan_hash", "execution_receipt", "independent_readback"}.issubset(evidence):
                add(failures, "USAGE-EVIDENCE-001", operation_path, "external write lacks bound execution evidence")


def validate_project(profile: dict[str, Any], path: str, failures: list[dict[str, str]]) -> None:
    required = {"schema", "id", "version", "status", "projectRef", "requiredInterfaces", "stages", "completion"}
    if not exact_keys(profile, required):
        add(failures, "USAGE-PROJECT-001", path, "project profile must be closed")
        return
    if profile["schema"] != "wellmanifest.subactor-usage/project-profile/v1":
        add(failures, "USAGE-PROJECT-002", path, "unexpected project profile schema")
    serialized = json.dumps(profile, sort_keys=True)
    for forbidden in ('"command"', '"argv"', '"secret"'):
        if forbidden in serialized:
            add(failures, "USAGE-PROJECT-003", path, f"project profile contains forbidden executable or secret field {forbidden}")
    stage_ids: set[str] = set()
    for index, stage in enumerate(profile.get("stages", [])):
        stage_path = f"{path}#/stages/{index}"
        required_stage = {"id", "intentId", "operation", "effect", "authority", "requiredInputs", "requiredEvidence", "onFailure"}
        if not exact_keys(stage, required_stage):
            add(failures, "USAGE-STAGE-001", stage_path, "stage must be closed")
            continue
        if stage["id"] in stage_ids:
            add(failures, "USAGE-STAGE-002", stage_path, "stage id must be unique")
        stage_ids.add(stage["id"])
        if stage["effect"] in {"external_write", "hardware_write"} and stage["authority"] != "apply":
            add(failures, "USAGE-AUTHORITY-002", stage_path, "external and hardware writes require apply authority")
        if stage["effect"] == "local_write" and stage["authority"] not in {"plan", "apply"}:
            add(failures, "USAGE-AUTHORITY-004", stage_path, "local writes require plan or apply authority")
        if stage["effect"] in {"external_write", "hardware_write"}:
            inputs = set(stage["requiredInputs"])
            if not {"plan_hash", "grant_ref"}.issubset(inputs):
                add(failures, "USAGE-AUTHORITY-003", stage_path, "external or hardware write lacks plan/grant binding")
        if stage["effect"] == "hardware_write" and "device_identity_readback" not in stage["requiredEvidence"]:
            add(failures, "USAGE-HARDWARE-001", stage_path, "hardware write lacks device identity readback")
    required_completion = set(profile.get("completion", {}).get("requires", []))
    if not {"test_receipt", "independent_runtime_readback", "acceptance_eql"}.issubset(required_completion):
        add(failures, "USAGE-COMPLETION-001", path, "completion contract lacks independent proof")


def discover(profile: dict[str, Any], path: str, failures: list[dict[str, str]]) -> dict[str, Any]:
    argv = profile["discovery"]["argv"]
    try:
        result = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=15, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        add(failures, "USAGE-DISCOVERY-003", path, f"discovery failed: {error}")
        return {"profile": profile["id"], "ok": False}
    output = result.stdout + result.stderr
    missing = [command for command in profile["discovery"]["expectedCommands"] if not re.search(rf"(?<![a-z0-9-]){re.escape(command)}(?![a-z0-9-])", output)]
    if result.returncode != 0 or missing:
        add(failures, "USAGE-DISCOVERY-004", path, f"CLI catalog mismatch; rc={result.returncode}, missing={missing}")
    if profile["executable"] == "subactor-shell":
        version_result = subprocess.run([profile["executable"], "--version"], cwd=ROOT, text=True, capture_output=True, timeout=15, check=False)
        observed = profile["runtime"]["observedVersion"]
        if version_result.returncode != 0 or observed not in version_result.stdout + version_result.stderr:
            add(failures, "USAGE-COMPAT-002", path, f"installed version does not match {observed}")
    return {"profile": profile["id"], "ok": result.returncode == 0 and not missing, "missingCommands": missing}


def check(*, run_discovery: bool) -> dict[str, Any]:
    failures: list[dict[str, str]] = []
    for schema_path in SCHEMA_PATHS:
        try:
            load_json(schema_path)
        except (OSError, json.JSONDecodeError) as error:
            add(failures, "USAGE-SCHEMA-001", str(schema_path.relative_to(ROOT)), str(error))
    manifest = load_json(MANIFEST_PATH)
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if manifest.get("version") != version:
        add(failures, "USAGE-VERSION-001", "docs/standard/manifest.v1.json", "manifest and VERSION differ")
    required_manifest = {"schema", "id", "version", "status", "home", "shape", "runtimeOwner", "communicationSpecification", "artifacts"}
    if not exact_keys(manifest, required_manifest):
        add(failures, "USAGE-MANIFEST-001", "docs/standard/manifest.v1.json", "manifest must be closed")
    seen_ids: set[str] = set()
    interface_profiles: list[tuple[dict[str, Any], str]] = []
    artifacts_checked = 0
    for artifact in manifest.get("artifacts", []):
        path = str(artifact.get("path", ""))
        artifact_path = (ROOT / path).resolve()
        if ROOT not in artifact_path.parents or not artifact_path.is_file():
            add(failures, "USAGE-ARTIFACT-001", path, "artifact path is missing or outside repository")
            continue
        if artifact.get("id") in seen_ids:
            add(failures, "USAGE-ARTIFACT-002", path, "artifact id must be unique")
        seen_ids.add(artifact.get("id"))
        if digest(artifact_path) != artifact.get("sha256"):
            add(failures, "USAGE-ARTIFACT-003", path, "artifact digest mismatch")
        profile = load_json(artifact_path)
        if profile.get("id") != artifact.get("id"):
            add(failures, "USAGE-ARTIFACT-004", path, "manifest and profile ids differ")
        if artifact.get("kind") == "interface-profile":
            validate_interface(profile, path, failures)
            interface_profiles.append((profile, path))
        elif artifact.get("kind") == "project-profile":
            validate_project(profile, path, failures)
        else:
            add(failures, "USAGE-ARTIFACT-005", path, "unsupported artifact kind")
        artifacts_checked += 1
    discovery_receipts = [discover(profile, path, failures) for profile, path in interface_profiles] if run_discovery else []
    return {
        "schema": "wellmanifest.subactor-usage/conformance-result/v1",
        "valid": not failures,
        "version": version,
        "artifactsChecked": artifacts_checked,
        "discoveryExecuted": run_discovery,
        "discovery": discovery_receipts,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--discover", action="store_true")
    identity_parser = subparsers.add_parser("repository-identity")
    identity_parser.add_argument("--repository", type=Path, default=ROOT)
    identity_parser.add_argument("--remote", default="origin")
    identity_parser.add_argument("--workspace-root", type=Path)
    identity_parser.add_argument("--expect-host")
    identity_parser.add_argument("--expect-ref")
    args = parser.parse_args()
    if args.command == "check":
        result = check(run_discovery=args.discover)
    else:
        result = inspect_repository_identity(
            args.repository,
            remote_name=args.remote,
            workspace_root=args.workspace_root,
            expected_host=args.expect_host,
            expected_ref=args.expect_ref,
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())

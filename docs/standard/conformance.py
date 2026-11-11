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

STANDARD_DIR = Path(__file__).resolve().parent
try:
    import repository_identity as _repo_id
except ModuleNotFoundError:  # pragma: no cover - spec_from_file_location fallback
    if str(STANDARD_DIR) not in sys.path:
        sys.path.insert(0, str(STANDARD_DIR))
    import repository_identity as _repo_id

_loads_strict_json = _repo_id._loads_strict_json
_read_regular_bytes = _repo_id._read_regular_bytes
digest = _repo_id.digest
inspect_repository_identity = _repo_id.inspect_repository_identity
load_json = _repo_id.load_json
parse_repository_remote = _repo_id.parse_repository_remote
run_git = _repo_id.run_git

ROOT = STANDARD_DIR.parents[1]
MANIFEST_PATH = ROOT / "docs" / "standard" / "manifest.v1.json"
SCHEMA_PATHS = (
    ROOT / "docs" / "standard" / "manifest.schema.v1.json",
    ROOT / "docs" / "standard" / "interface-profile.schema.v1.json",
    ROOT / "docs" / "standard" / "project-profile.schema.v1.json",
)
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
STAGE_ID_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
REPO_REF_RE = re.compile(r"^[a-z0-9_.-]+/[a-z0-9_.-]+$")
PROJECT_REF_RE = re.compile(r"^project://\S+$")
PROFILE_STATUSES = {"current", "candidate", "deprecated"}
INTERFACE_EFFECTS = {"observe", "local_write", "external_write"}
PROJECT_EFFECTS = INTERFACE_EFFECTS | {"hardware_write"}
AUTHORITIES = {"observe", "plan", "dry_run", "apply", "autonomous"}
FAILURE_MODES = {"stop", "replan", "rollback", "escalate"}


def exact_keys(document: Any, required: set[str], optional: set[str] | None = None) -> bool:
    if not isinstance(document, dict):
        return False
    return set(document) == required | (set(document) & (optional or set()))


def _string_list(value: Any, *, allow_empty_item: bool = False) -> list[str] | None:
    if isinstance(value, list) and all(
        isinstance(item, str) and (allow_empty_item or bool(item)) for item in value
    ):
        return value
    return None


def _unique_nonempty_strings(value: Any, *, min_items: int = 1) -> list[str] | None:
    items = _string_list(value)
    if items is None or len(items) < min_items or len(items) != len(set(items)):
        return None
    return items


def add(failures: list[dict[str, str]], code: str, path: str, message: str) -> None:
    failures.append({"code": code, "path": path, "message": message})


def validate_interface(profile: dict[str, Any], path: str, failures: list[dict[str, str]]) -> None:
    required = {"schema", "id", "version", "status", "executable", "runtime", "discovery", "operations", "invariants"}
    if not exact_keys(profile, required):
        add(failures, "USAGE-PROFILE-001", path, "interface profile must be closed")
        return
    if profile["schema"] != "wellmanifest.subactor-usage/interface-profile/v1":
        add(failures, "USAGE-PROFILE-002", path, "unexpected interface schema")
    prof_id, version, status, executable = profile["id"], profile["version"], profile["status"], profile["executable"]
    if (
        not isinstance(prof_id, str)
        or not SLUG_RE.fullmatch(prof_id)
        or type(version) is not int
        or version < 1
        or status not in PROFILE_STATUSES
        or not isinstance(executable, str)
        or not executable
        or _unique_nonempty_strings(profile["invariants"]) is None
    ):
        add(failures, "USAGE-PROFILE-001", path, "interface header or invariants violate schema")
    runtime = profile.get("runtime")
    if (
        not exact_keys(runtime, {"repository", "revision", "observedVersion"})
        or not isinstance(runtime["repository"], str)
        or not REPO_REF_RE.fullmatch(runtime["repository"])
        or not isinstance(runtime["revision"], str)
        or not re.fullmatch(r"[0-9a-f]{40}", runtime["revision"])
        or not isinstance(runtime["observedVersion"], str)
        or not runtime["observedVersion"]
    ):
        add(failures, "USAGE-COMPAT-001", path, "runtime must bind repository, exact Git SHA, and observedVersion")
    discovery = profile.get("discovery")
    argv = _string_list(discovery.get("argv")) if exact_keys(discovery, {"argv", "expectedCommands"}) else None
    expected = _unique_nonempty_strings(discovery.get("expectedCommands")) if isinstance(discovery, dict) else None
    if not argv or not expected or argv[0] != executable:
        add(failures, "USAGE-DISCOVERY-001", path, "discovery must bind the executable and unique command catalog")
    expected_set = set(expected) if expected else set()
    operations = profile.get("operations")
    if not isinstance(operations, list) or not operations:
        add(failures, "USAGE-OPERATION-001", path, "operations must be a non-empty list")
        return
    operation_ids: set[str] = set()
    for index, operation in enumerate(operations):
        operation_path = f"{path}#/operations/{index}"
        if not exact_keys(operation, {"id", "command", "effect", "authority", "requiredEvidence"}, {"requiredFlags"}):
            add(failures, "USAGE-OPERATION-001", operation_path, "operation must be closed")
            continue
        op_id, op_cmd = operation["id"], operation["command"]
        evidence_list = _unique_nonempty_strings(operation["requiredEvidence"])
        flags_ok = True
        if "requiredFlags" in operation:
            flags = _string_list(operation["requiredFlags"], allow_empty_item=True)
            flags_ok = flags is not None and len(flags) == len(set(flags))
        if (
            not isinstance(op_id, str)
            or not op_id
            or not isinstance(op_cmd, str)
            or not op_cmd
            or operation["effect"] not in INTERFACE_EFFECTS
            or operation["authority"] not in AUTHORITIES
            or evidence_list is None
            or not flags_ok
        ):
            add(failures, "USAGE-OPERATION-001", operation_path, "operation fields violate schema")
            continue
        if op_id in operation_ids:
            add(failures, "USAGE-OPERATION-002", operation_path, "operation id must be unique")
        operation_ids.add(op_id)
        if expected is not None and op_cmd not in expected_set:
            add(failures, "USAGE-DISCOVERY-002", operation_path, "operation command is absent from discovery catalog")
        evidence = set(evidence_list)
        if operation["effect"] == "external_write":
            if operation["authority"] not in {"apply", "autonomous"}:
                add(failures, "USAGE-AUTHORITY-001", operation_path, "external write requires apply or autonomous authority")
            if not {"plan_hash", "execution_receipt", "independent_readback"}.issubset(evidence):
                add(failures, "USAGE-EVIDENCE-001", operation_path, "external write lacks bound execution evidence")
        if operation["authority"] == "autonomous" and not {"contract_ref", "contract_bounds_readback"}.issubset(evidence):
            add(failures, "USAGE-AUTHORITY-005", operation_path, "autonomous authority lacks verified contract evidence")


def validate_project(profile: dict[str, Any], path: str, failures: list[dict[str, str]]) -> None:
    required = {"schema", "id", "version", "status", "projectRef", "requiredInterfaces", "stages", "completion"}
    if not exact_keys(profile, required):
        add(failures, "USAGE-PROJECT-001", path, "project profile must be closed")
        return
    if profile["schema"] != "wellmanifest.subactor-usage/project-profile/v1":
        add(failures, "USAGE-PROJECT-002", path, "unexpected project profile schema")
    prof_id, version, status, project_ref = profile["id"], profile["version"], profile["status"], profile["projectRef"]
    req_ifaces = _string_list(profile["requiredInterfaces"], allow_empty_item=True)
    if (
        not isinstance(prof_id, str)
        or not SLUG_RE.fullmatch(prof_id)
        or type(version) is not int
        or version < 1
        or status not in PROFILE_STATUSES
        or not isinstance(project_ref, str)
        or not PROJECT_REF_RE.fullmatch(project_ref)
        or not req_ifaces
        or len(req_ifaces) != len(set(req_ifaces))
    ):
        add(failures, "USAGE-PROJECT-001", path, "project header violates schema")
    serialized = json.dumps(profile, sort_keys=True)
    for forbidden in ('"command"', '"argv"', '"secret"'):
        if forbidden in serialized:
            add(failures, "USAGE-PROJECT-003", path, f"project profile contains forbidden executable or secret field {forbidden}")
    stages = profile.get("stages")
    if not isinstance(stages, list) or not stages:
        add(failures, "USAGE-STAGE-001", path, "stages must be a non-empty list")
        return
    stage_ids: set[str] = set()
    for index, stage in enumerate(stages):
        stage_path = f"{path}#/stages/{index}"
        required_stage = {"id", "intentId", "operation", "effect", "authority", "requiredInputs", "requiredEvidence", "onFailure"}
        if not exact_keys(stage, required_stage):
            add(failures, "USAGE-STAGE-001", stage_path, "stage must be closed")
            continue
        stage_id = stage["id"]
        inputs_list = _unique_nonempty_strings(stage["requiredInputs"], min_items=0)
        evidence_list = _unique_nonempty_strings(stage["requiredEvidence"])
        if (
            not isinstance(stage_id, str)
            or not STAGE_ID_RE.fullmatch(stage_id)
            or not isinstance(stage["intentId"], str)
            or not stage["intentId"]
            or not isinstance(stage["operation"], str)
            or not stage["operation"]
            or stage["effect"] not in PROJECT_EFFECTS
            or stage["authority"] not in AUTHORITIES
            or stage["onFailure"] not in FAILURE_MODES
            or inputs_list is None
            or evidence_list is None
        ):
            add(failures, "USAGE-STAGE-001", stage_path, "stage fields violate schema")
            continue
        if stage_id in stage_ids:
            add(failures, "USAGE-STAGE-002", stage_path, "stage id must be unique")
        stage_ids.add(stage_id)
        inputs, evidence = set(inputs_list), set(evidence_list)
        if stage["effect"] in {"external_write", "hardware_write"} and stage["authority"] not in {"apply", "autonomous"}:
            add(failures, "USAGE-AUTHORITY-002", stage_path, "external and hardware writes require apply or autonomous authority")
        if stage["effect"] == "local_write" and stage["authority"] not in {"plan", "apply", "autonomous"}:
            add(failures, "USAGE-AUTHORITY-004", stage_path, "local writes require plan, apply or autonomous authority")
        if stage["effect"] == "hardware_write" and stage["authority"] != "apply":
            add(failures, "USAGE-AUTHORITY-006", stage_path, "hardware write must not run under a standing autonomy contract")
        if stage["effect"] in {"external_write", "hardware_write"} and not {"plan_hash", "grant_ref"}.issubset(inputs):
            add(failures, "USAGE-AUTHORITY-003", stage_path, "external or hardware write lacks plan/grant binding")
        if stage["authority"] == "autonomous" and "contract_ref" not in inputs:
            add(failures, "USAGE-AUTHORITY-005", stage_path, "autonomous stage lacks a bounded contract reference")
        if stage["effect"] == "hardware_write" and "device_identity_readback" not in evidence:
            add(failures, "USAGE-HARDWARE-001", stage_path, "hardware write lacks device identity readback")
    completion = profile.get("completion")
    requires_list = (
        _string_list(completion.get("requires"), allow_empty_item=True)
        if exact_keys(completion, {"requires", "forbids"})
        else None
    )
    forbids_list = _string_list(completion.get("forbids"), allow_empty_item=True) if isinstance(completion, dict) else None
    if (
        not requires_list
        or len(requires_list) != len(set(requires_list))
        or not forbids_list
        or len(forbids_list) != len(set(forbids_list))
        or not {"test_receipt", "independent_runtime_readback", "acceptance_eql"}.issubset(set(requires_list))
    ):
        add(failures, "USAGE-COMPLETION-001", path, "completion contract violates schema or lacks independent proof")


def discover(profile: dict[str, Any], path: str, failures: list[dict[str, str]]) -> dict[str, Any]:
    discovery = profile.get("discovery") if isinstance(profile, dict) else None
    executable = profile.get("executable") if isinstance(profile, dict) else None
    argv = _string_list(discovery.get("argv")) if isinstance(discovery, dict) else None
    expected = _unique_nonempty_strings(discovery.get("expectedCommands")) if isinstance(discovery, dict) else None
    prof_id = profile.get("id") if isinstance(profile, dict) else None
    if not isinstance(executable, str) or not argv or not expected or argv[0] != executable:
        add(failures, "USAGE-DISCOVERY-001", path, "cannot execute discovery on malformed interface profile")
        return {"profile": prof_id, "ok": False}
    try:
        result = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=15, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        add(failures, "USAGE-DISCOVERY-003", path, f"discovery failed: {error}")
        return {"profile": prof_id, "ok": False}
    output = result.stdout + result.stderr
    missing = [
        command
        for command in expected
        if not re.search(rf"(?<![a-z0-9-]){re.escape(command)}(?![a-z0-9-])", output)
    ]
    if result.returncode != 0 or missing:
        add(failures, "USAGE-DISCOVERY-004", path, f"CLI catalog mismatch; rc={result.returncode}, missing={missing}")
    if executable == "subactor-shell":
        runtime = profile.get("runtime")
        observed = runtime.get("observedVersion") if isinstance(runtime, dict) else None
        if not isinstance(observed, str) or not observed:
            add(failures, "USAGE-COMPAT-001", path, "runtime observedVersion must be a non-empty string")
            return {"profile": prof_id, "ok": False, "missingCommands": missing}
        try:
            version_result = subprocess.run([executable, "--version"], cwd=ROOT, text=True, capture_output=True, timeout=15, check=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            add(failures, "USAGE-COMPAT-002", path, f"version probe failed: {error}")
            return {"profile": prof_id, "ok": False, "missingCommands": missing}
        if version_result.returncode != 0 or observed not in version_result.stdout + version_result.stderr:
            add(failures, "USAGE-COMPAT-002", path, f"installed version does not match {observed}")
    return {"profile": prof_id, "ok": result.returncode == 0 and not missing, "missingCommands": missing}


def check(*, run_discovery: bool) -> dict[str, Any]:
    failures: list[dict[str, str]] = []
    for schema_path in SCHEMA_PATHS:
        try:
            load_json(schema_path, root=ROOT)
        except (OSError, UnicodeDecodeError, ValueError) as error:
            add(failures, "USAGE-SCHEMA-001", str(schema_path.relative_to(ROOT)), str(error))
    version = _read_regular_bytes(ROOT / "VERSION", root=ROOT).decode("utf-8").strip()
    try:
        manifest = load_json(MANIFEST_PATH, root=ROOT)
    except (OSError, UnicodeDecodeError, ValueError) as error:
        add(failures, "USAGE-MANIFEST-001", "docs/standard/manifest.v1.json", str(error))
        return {
            "schema": "wellmanifest.subactor-usage/conformance-result/v1",
            "valid": False,
            "version": version,
            "artifactsChecked": 0,
            "discoveryExecuted": False,
            "discovery": [],
            "failures": failures,
        }
    if not isinstance(manifest, dict):
        add(failures, "USAGE-MANIFEST-001", "docs/standard/manifest.v1.json", "manifest must be an object")
        manifest = {}
    if manifest.get("version") != version:
        add(failures, "USAGE-VERSION-001", "docs/standard/manifest.v1.json", "manifest and VERSION differ")
    required_manifest = {"schema", "id", "version", "status", "home", "shape", "runtimeOwner", "communicationSpecification", "artifacts"}
    if not exact_keys(manifest, required_manifest):
        add(failures, "USAGE-MANIFEST-001", "docs/standard/manifest.v1.json", "manifest must be closed")
    seen_ids: set[str] = set()
    interface_profiles: list[tuple[dict[str, Any], str]] = []
    artifacts_checked = 0
    raw_artifacts = manifest.get("artifacts")
    if not isinstance(raw_artifacts, list):
        add(failures, "USAGE-MANIFEST-001", "docs/standard/manifest.v1.json", "artifacts must be a list")
        raw_artifacts = []
    for artifact in raw_artifacts:
        if not isinstance(artifact, dict):
            add(failures, "USAGE-ARTIFACT-001", "", "artifact entry must be an object")
            continue
        raw_path = artifact.get("path")
        path = raw_path if isinstance(raw_path, str) else ""
        rel = Path(path) if path else None
        if rel is None or rel.is_absolute() or any(part in {"", ".", ".."} for part in rel.parts):
            add(failures, "USAGE-ARTIFACT-001", path, "artifact path is missing or invalid")
            continue
        artifact_id = artifact.get("id")
        if not isinstance(artifact_id, str) or not artifact_id:
            add(failures, "USAGE-ARTIFACT-002", path, "artifact id must be a non-empty string")
            continue
        if artifact_id in seen_ids:
            add(failures, "USAGE-ARTIFACT-002", path, "artifact id must be unique")
        seen_ids.add(artifact_id)
        try:
            raw_bytes = _read_regular_bytes(ROOT / rel, root=ROOT)
            actual_digest = hashlib.sha256(raw_bytes).hexdigest()
            profile = _loads_strict_json(raw_bytes)
        except (OSError, UnicodeDecodeError, ValueError) as error:
            add(failures, "USAGE-ARTIFACT-001", path, str(error))
            continue
        if actual_digest != artifact.get("sha256"):
            add(failures, "USAGE-ARTIFACT-003", path, "artifact digest mismatch")
        if not isinstance(profile, dict) or profile.get("id") != artifact_id:
            add(failures, "USAGE-ARTIFACT-004", path, "manifest and profile ids differ")
            continue
        if artifact.get("kind") == "interface-profile":
            prior_failures = len(failures)
            validate_interface(profile, path, failures)
            if len(failures) == prior_failures:
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

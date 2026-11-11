"""Shared primitives and POA runtime-event conformance for Subactor communication."""

from __future__ import annotations

import json
import os
import re
import stat
from datetime import datetime
from pathlib import Path
from typing import Any

URI_REF_RE = re.compile(r"^[a-z][a-z0-9+.-]*://[^\s]+$")
UTC_INSTANT_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.\d+)?Z$")

RUNTIME_V1_SCHEMA = "wellmanifest.subactor-communication/runtime-event/v1"
RUNTIME_V2_SCHEMA = "wellmanifest.subactor-communication/runtime-event/v2"
RUNTIME_SCHEMAS = {RUNTIME_V1_SCHEMA, RUNTIME_V2_SCHEMA}
RUNTIME_STATES = {
    "planned",
    "validating",
    "admitted",
    "replan_required",
    "running",
    "waiting_authority",
    "blocked",
    "completed",
    "failed",
}
EXECUTABLE_STATES = {"admitted", "running", "waiting_authority", "completed"}
ADMISSION_DECISIONS = {"PENDING", "ADMITTED", "REJECTED"}
EVIDENCE_SOURCES = {"runtime", "control", "validator", "readback"}
READBACK_METHODS = {"independent_query", "eql", "target_system_receipt"}


def finding(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def require(
    condition: bool, findings: list[dict[str, str]], code: str, path: str, message: str
) -> None:
    if not condition:
        findings.append(finding(code, path, message))


def object_at(value: Any, key: str) -> dict[str, Any]:
    return value[key] if isinstance(value, dict) and isinstance(value.get(key), dict) else {}


def list_at(value: Any, key: str) -> list[Any]:
    return value[key] if isinstance(value, dict) and isinstance(value.get(key), list) else []


def non_empty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def strict_positive_int(value: Any) -> bool:
    return type(value) is int and value >= 1


def is_uri_ref(value: Any) -> bool:
    return isinstance(value, str) and URI_REF_RE.fullmatch(value) is not None


def utc_instant(value: Any) -> str | None:
    """Return a calendar-valid second-precision UTC instant that sorts lexicographically."""
    if not isinstance(value, str):
        return None
    match = UTC_INSTANT_RE.fullmatch(value)
    if match is None:
        return None
    instant = match.group(1)
    try:
        datetime.strptime(instant, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None
    return instant


def string_set(values: Any) -> tuple[bool, set[str]]:
    """Convert a JSON list of non-empty strings to a set without unhashable crashes."""
    if not isinstance(values, list):
        return False, set()
    items: set[str] = set()
    for item in values:
        if not non_empty_str(item):
            return False, set()
        items.add(item)
    return True, items


def exact_string_set(values: list[Any], expected: set[str]) -> bool:
    valid, items = string_set(values)
    return valid and bool(values) and len(values) == len(items) and items == expected


def forbidden_keys(value: Any, names: set[str], prefix: str = "$") -> list[str]:
    result: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}"
            if key in names:
                result.append(path)
            result.extend(forbidden_keys(child, names, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            result.extend(forbidden_keys(child, names, f"{prefix}[{index}]"))
    return result


def has_symlink_component(path: Path, *, stop_at: Path | None = None) -> bool:
    if path.is_symlink():
        return True
    if stop_at is None:
        return False
    boundary = stop_at.resolve()
    current = path.parent
    while current != boundary:
        if current.is_symlink():
            return True
        if current.parent == current:
            break
        current = current.parent
    return False


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"duplicate JSON key: {key!r}")
        obj[key] = value
    return obj


def _reject_nonfinite_constant(token: str) -> Any:
    raise ValueError(f"non-finite JSON constant is forbidden: {token}")


def strict_load_json(path: Path, *, root: Path | None = None) -> Any:
    """Load UTF-8 JSON without following symlinks or accepting duplicate/NaN tokens."""
    if has_symlink_component(path, stop_at=root):
        raise ValueError(f"symlink JSON input is forbidden: {path}")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError(f"JSON input must be a regular file: {path}")
        with os.fdopen(fd, "rb") as stream:
            fd = -1
            raw = stream.read().decode("utf-8")
    finally:
        if fd >= 0:
            os.close(fd)
    return json.loads(
        raw,
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_nonfinite_constant,
    )


def validate_identity(document: Any, findings: list[dict[str, str]]) -> None:
    target = object_at(document, "target")
    require(
        target.get("system") == "subactor" and target.get("class") == "autonomous_system",
        findings,
        "COMM-IDENTITY-001",
        "$.target",
        "target must identify Subactor as an autonomous_system",
    )


def _validate_v2_processes(
    queue: dict[str, Any], findings: list[dict[str, str]]
) -> tuple[set[str], set[str]]:
    bound_process_uris: set[str] = set()
    bound_resource_uris: set[str] = set()
    processes = list_at(queue, "processes")
    require(
        bool(processes),
        findings,
        "POA-RESOURCE-BINDING-001",
        "$.queue.processes",
        "runtime-event v2 requires at least one exactly bound process",
    )
    for index, process in enumerate(processes):
        path = f"$.queue.processes[{index}]"
        if not isinstance(process, dict):
            findings.append(finding("COMM-SHAPE-001", path, "queued process must be an object"))
            continue

        process_uri = process.get("processUri")
        actor_ref = process.get("actorRef")
        operation = process.get("operation")
        resources = list_at(process, "resources")
        resource_uris: list[str] = []
        resources_exact = bool(resources)
        for resource_index, resource in enumerate(resources):
            resource_path = f"{path}.resources[{resource_index}]"
            if not isinstance(resource, dict):
                resources_exact = False
                findings.append(
                    finding("POA-RESOURCE-BINDING-001", resource_path, "resource binding must be an object")
                )
                continue
            resource_uri = resource.get("resourceUri")
            registry_ref = resource.get("registryRef")
            resource_exact = (
                resource.get("role") in {"source", "target", "scope"}
                and is_uri_ref(resource_uri)
                and is_uri_ref(registry_ref)
            )
            resources_exact = resources_exact and resource_exact
            if isinstance(resource_uri, str):
                resource_uris.append(resource_uri)

        resources_exact = (
            resources_exact
            and len(resource_uris) == len(resources)
            and len(resource_uris) == len(set(resource_uris))
        )
        require(
            is_uri_ref(process_uri)
            and is_uri_ref(actor_ref)
            and non_empty_str(operation)
            and process.get("effect") in {"observe", "mutate"}
            and resources_exact,
            findings,
            "POA-RESOURCE-BINDING-001",
            path,
            "every process requires exact process, actor, operation and registered resource URI bindings",
        )

        if isinstance(process_uri, str):
            require(
                process_uri not in bound_process_uris,
                findings,
                "POA-RESOURCE-BINDING-001",
                f"{path}.processUri",
                "process URI must be unique within one queue revision",
            )
            bound_process_uris.add(process_uri)
        bound_resource_uris.update(resource_uris)

        if process.get("effect") == "mutate":
            grant = object_at(process, "grant")
            grant_exact = (
                is_uri_ref(grant.get("grantRef"))
                and grant.get("boundActorRef") == actor_ref
                and grant.get("boundProcessUri") == process_uri
                and grant.get("boundOperation") == operation
                and exact_string_set(list_at(grant, "boundResourceUris"), set(resource_uris))
            )
            require(
                grant_exact,
                findings,
                "POA-GRANT-BINDING-001",
                f"{path}.grant",
                "mutation grant must bind the exact actor, process, operation and resource URI set",
            )
    return bound_process_uris, bound_resource_uris


def validate_runtime(document: Any) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(document, dict):
        return [finding("COMM-SHAPE-001", "$", "document must be an object")]

    schema = document.get("schema")
    require(schema in RUNTIME_SCHEMAS, findings, "COMM-SHAPE-001", "$.schema", "unexpected runtime-event schema identifier")
    require(non_empty_str(document.get("eventId")), findings, "COMM-SHAPE-001", "$.eventId", "runtime event requires a non-empty eventId")
    validate_identity(document, findings)
    require(
        non_empty_str(document.get("ticket")) and non_empty_str(document.get("correlationId")),
        findings,
        "COMM-EVIDENCE-001",
        "$",
        "runtime event must bind ticket and correlationId",
    )

    state = document.get("state")
    require(state in RUNTIME_STATES, findings, "COMM-SHAPE-001", "$.state", "runtime state must be one of the declared POA lifecycle states")
    queue = object_at(document, "queue")
    plan = object_at(document, "plan")
    admission = object_at(document, "admission")
    evidence = object_at(document, "evidence")

    require(
        isinstance(document.get("queue"), dict)
        and strict_positive_int(queue.get("revision"))
        and ("previousRevision" not in queue or strict_positive_int(queue.get("previousRevision"))),
        findings,
        "COMM-SHAPE-001",
        "$.queue",
        "queue requires integer revision >= 1",
    )
    is_v2 = schema == RUNTIME_V2_SCHEMA
    ref_check = is_uri_ref if is_v2 else non_empty_str
    require(
        isinstance(document.get("plan"), dict)
        and non_empty_str(plan.get("planHash"))
        and ref_check(plan.get("orchestratorRef")),
        findings,
        "COMM-SHAPE-001",
        "$.plan",
        "plan requires non-empty planHash and orchestratorRef",
    )
    require(
        isinstance(document.get("admission"), dict)
        and admission.get("decision") in ADMISSION_DECISIONS
        and isinstance(admission.get("validatorIndependent"), bool),
        findings,
        "COMM-SHAPE-001",
        "$.admission",
        "admission requires decision enum and boolean validatorIndependent",
    )
    require(
        isinstance(document.get("evidence"), dict) and evidence.get("source") in EVIDENCE_SOURCES,
        findings,
        "COMM-EVIDENCE-001",
        "$.evidence.source",
        "evidence source must be runtime, control, validator or readback",
    )

    bound_process_uris: set[str] = set()
    bound_resource_uris: set[str] = set()
    if schema == RUNTIME_V1_SCHEMA:
        uris_ok, uris = string_set(queue.get("processUris"))
        require(uris_ok and bool(uris), findings, "COMM-SHAPE-001", "$.queue.processUris", "runtime-event v1 requires at least one non-empty processUri")
    elif is_v2:
        bound_process_uris, bound_resource_uris = _validate_v2_processes(queue, findings)

    if state in EXECUTABLE_STATES:
        admitted = (
            admission.get("decision") == "ADMITTED"
            and admission.get("validatorIndependent") is True
            and ref_check(admission.get("validatorRef"))
            and ref_check(admission.get("receiptRef"))
            and admission.get("boundTicket") == document.get("ticket")
            and strict_positive_int(admission.get("boundQueueRevision"))
            and admission.get("boundQueueRevision") == queue.get("revision")
            and admission.get("boundPlanHash") == plan.get("planHash")
        )
        if is_v2:
            admitted = (
                admitted
                and exact_string_set(list_at(admission, "boundProcessUris"), bound_process_uris)
                and exact_string_set(list_at(admission, "boundResourceUris"), bound_resource_uris)
            )
        require(
            admitted,
            findings,
            "POA-ADMISSION-001",
            "$.admission",
            "execution requires independent admission bound to ticket, queue revision, planHash and every planned process/resource URI",
        )

    if admission.get("decision") == "REJECTED" or state == "replan_required":
        replanned = (
            state == "replan_required"
            and strict_positive_int(queue.get("revision"))
            and strict_positive_int(queue.get("previousRevision"))
            and queue["revision"] > queue["previousRevision"]
            and non_empty_str(plan.get("previousPlanHash"))
            and plan.get("previousPlanHash") != plan.get("planHash")
        )
        require(
            replanned,
            findings,
            "POA-REPLAN-001",
            "$.queue|$.plan",
            "rejection must produce a higher queue revision and a new plan hash in the same ticket",
        )

    if state == "completed":
        readback = object_at(evidence, "readback")
        receipts = list_at(evidence, "receipts")
        complete = (
            bool(receipts)
            and all(ref_check(item) for item in receipts)
            and evidence.get("source") in EVIDENCE_SOURCES
            and readback.get("passed") is True
            and readback.get("method") in READBACK_METHODS
            and ref_check(readback.get("ref"))
        )
        require(
            complete,
            findings,
            "POA-COMPLETION-001",
            "$.evidence",
            "completed requires receipts and independent readback, not an LLM claim",
        )
    return findings

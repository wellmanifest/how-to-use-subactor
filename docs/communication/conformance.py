#!/usr/bin/env python3
"""Dependency-free semantic conformance for Subactor communication."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parent
SCHEMAS = (
    ROOT / "delegation-envelope.schema.v1.json",
    ROOT / "runtime-event.schema.v1.json",
    ROOT / "runtime-event.schema.v2.json",
    ROOT / "mcp-tool-contract.schema.v1.json",
)
GENERIC_MCP_NAMES = {
    "run_shell",
    "shell",
    "run_uri",
    "call_connector",
    "execute_any",
    "invoke",
}
URI_REF_RE = re.compile(r"^[a-z][a-z0-9+.-]*://[^\s]+$")


def finding(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def require(
    condition: bool,
    findings: list[dict[str, str]],
    code: str,
    path: str,
    message: str,
) -> None:
    if not condition:
        findings.append(finding(code, path, message))


def object_at(value: Any, key: str) -> dict[str, Any]:
    if isinstance(value, dict) and isinstance(value.get(key), dict):
        return value[key]
    return {}


def list_at(value: Any, key: str) -> list[Any]:
    if isinstance(value, dict) and isinstance(value.get(key), list):
        return value[key]
    return []


def is_uri_ref(value: Any) -> bool:
    return isinstance(value, str) and URI_REF_RE.fullmatch(value) is not None


def exact_string_set(values: list[Any], expected: set[str]) -> bool:
    return (
        bool(values)
        and all(isinstance(value, str) for value in values)
        and len(values) == len(set(values))
        and set(values) == expected
    )


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


def validate_identity(document: Any, findings: list[dict[str, str]]) -> None:
    target = object_at(document, "target")
    require(
        target.get("system") == "subactor"
        and target.get("class") == "autonomous_system",
        findings,
        "COMM-IDENTITY-001",
        "$.target",
        "target must identify Subactor as an autonomous_system",
    )


def validate_delegation(document: Any) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(document, dict):
        return [finding("COMM-SHAPE-001", "$", "document must be an object")]

    require(
        document.get("schema")
        == "wellmanifest.subactor-communication/delegation-envelope/v1",
        findings,
        "COMM-SHAPE-001",
        "$.schema",
        "unexpected delegation schema identifier",
    )
    validate_identity(document, findings)

    intent = object_at(document, "intent")
    require(
        isinstance(intent.get("outcome"), str) and bool(intent.get("outcome", "").strip()),
        findings,
        "COMM-OWNERSHIP-001",
        "$.intent.outcome",
        "delegate an outcome instead of worker instructions",
    )
    require(
        bool(list_at(intent, "scope")) and bool(list_at(intent, "acceptance")),
        findings,
        "COMM-EVIDENCE-001",
        "$.intent",
        "scope and observable acceptance criteria are required",
    )

    orchestration = object_at(document, "orchestration")
    subllm = object_at(orchestration, "subllm")
    require(
        orchestration.get("executionOwner") == "subactor"
        and orchestration.get("delegationMode") == "outcome"
        and orchestration.get("supervisorMayBypass") is False,
        findings,
        "COMM-OWNERSHIP-001",
        "$.orchestration",
        "Subactor must own decomposition and execution; supervisor bypass is forbidden",
    )
    for path in forbidden_keys(
        document,
        {"tasks", "workerPrompts", "subagents", "serviceCommands", "packageCommands"},
    ):
        findings.append(
            finding(
                "COMM-OWNERSHIP-001",
                path,
                "manual worker/service orchestration is outside the delegation contract",
            )
        )

    transport = object_at(document, "transport")
    require(
        transport.get("grantsAuthority") is False
        and subllm.get("role") == "internal_model_routing"
        and subllm.get("grantsAuthority") is False,
        findings,
        "COMM-AUTHORITY-001",
        "$.transport|$.orchestration.subllm",
        "neither transport nor SubLLM grants execution authority",
    )

    authority = object_at(document, "authority")
    require(
        authority.get("source") == "subactor_control",
        findings,
        "COMM-AUTHORITY-001",
        "$.authority.source",
        "authority must be resolved by Subactor Control",
    )
    if authority.get("mode") == "apply":
        require(
            bool(authority.get("grantRef")) and bool(authority.get("planHash")),
            findings,
            "COMM-AUTHORITY-002",
            "$.authority",
            "apply requires both grantRef and planHash",
        )

    for index, effect in enumerate(list_at(document, "effects")):
        if not isinstance(effect, dict):
            findings.append(
                finding("COMM-SHAPE-001", f"$.effects[{index}]", "effect must be an object")
            )
            continue
        reversibility = effect.get("reversibility")
        if reversibility == "reversible":
            require(
                bool(effect.get("rollbackRef")) or bool(effect.get("compensationRef")),
                findings,
                "COMM-EFFECT-001",
                f"$.effects[{index}]",
                "reversible effect requires rollbackRef or compensationRef",
            )
        if reversibility == "irreversible":
            require(
                effect.get("requiresHigherAuthority") is True
                and bool(effect.get("higherAuthorityApprovalRef")),
                findings,
                "COMM-EFFECT-002",
                f"$.effects[{index}]",
                "irreversible effect requires a higher-authority approval reference",
            )

    required_evidence = set(list_at(object_at(document, "evidence"), "required"))
    require(
        {"ticket", "process_uri", "plan_hash", "events", "receipts", "readback"}
        <= required_evidence,
        findings,
        "COMM-EVIDENCE-001",
        "$.evidence.required",
        "evidence chain must require ticket, process URI, plan hash, events, receipts and readback",
    )
    return findings


def validate_runtime(document: Any) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(document, dict):
        return [finding("COMM-SHAPE-001", "$", "document must be an object")]

    schema = document.get("schema")
    require(
        schema
        in {
            "wellmanifest.subactor-communication/runtime-event/v1",
            "wellmanifest.subactor-communication/runtime-event/v2",
        },
        findings,
        "COMM-SHAPE-001",
        "$.schema",
        "unexpected runtime-event schema identifier",
    )
    validate_identity(document, findings)
    require(
        bool(document.get("ticket")) and bool(document.get("correlationId")),
        findings,
        "COMM-EVIDENCE-001",
        "$",
        "runtime event must bind ticket and correlationId",
    )

    state = document.get("state")
    queue = object_at(document, "queue")
    plan = object_at(document, "plan")
    admission = object_at(document, "admission")
    bound_process_uris: set[str] = set()
    bound_resource_uris: set[str] = set()

    if schema == "wellmanifest.subactor-communication/runtime-event/v2":
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
                findings.append(
                    finding("COMM-SHAPE-001", path, "queued process must be an object")
                )
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
                        finding(
                            "POA-RESOURCE-BINDING-001",
                            resource_path,
                            "resource binding must be an object",
                        )
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
                and isinstance(operation, str)
                and bool(operation.strip())
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
                grant_resource_uris = list_at(grant, "boundResourceUris")
                grant_exact = (
                    is_uri_ref(grant.get("grantRef"))
                    and grant.get("boundActorRef") == actor_ref
                    and grant.get("boundProcessUri") == process_uri
                    and grant.get("boundOperation") == operation
                    and exact_string_set(grant_resource_uris, set(resource_uris))
                )
                require(
                    grant_exact,
                    findings,
                    "POA-GRANT-BINDING-001",
                    f"{path}.grant",
                    "mutation grant must bind the exact actor, process, operation and resource URI set",
                )

    executable = state in {"admitted", "running", "waiting_authority", "completed"}
    if executable:
        admitted = (
            admission.get("decision") == "ADMITTED"
            and admission.get("validatorIndependent") is True
            and bool(admission.get("validatorRef"))
            and bool(admission.get("receiptRef"))
            and admission.get("boundTicket") == document.get("ticket")
            and admission.get("boundQueueRevision") == queue.get("revision")
            and admission.get("boundPlanHash") == plan.get("planHash")
        )
        if schema == "wellmanifest.subactor-communication/runtime-event/v2":
            admission_process_uris = list_at(admission, "boundProcessUris")
            admission_resource_uris = list_at(admission, "boundResourceUris")
            admitted = (
                admitted
                and exact_string_set(admission_process_uris, bound_process_uris)
                and exact_string_set(admission_resource_uris, bound_resource_uris)
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
            and isinstance(queue.get("revision"), int)
            and isinstance(queue.get("previousRevision"), int)
            and queue["revision"] > queue["previousRevision"]
            and bool(plan.get("previousPlanHash"))
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
        evidence = object_at(document, "evidence")
        readback = object_at(evidence, "readback")
        complete = (
            bool(list_at(evidence, "receipts"))
            and evidence.get("source") in {"runtime", "control", "validator", "readback"}
            and readback.get("passed") is True
            and readback.get("method")
            in {"independent_query", "eql", "target_system_receipt"}
            and bool(readback.get("ref"))
        )
        require(
            complete,
            findings,
            "POA-COMPLETION-001",
            "$.evidence",
            "completed requires receipts and independent readback, not an LLM claim",
        )
    return findings


def validate_mcp(document: Any) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(document, dict):
        return [finding("COMM-SHAPE-001", "$", "document must be an object")]

    require(
        document.get("schema")
        == "wellmanifest.subactor-communication/mcp-tool-contract/v1",
        findings,
        "COMM-SHAPE-001",
        "$.schema",
        "unexpected MCP tool schema identifier",
    )
    validate_identity(document, findings)
    name = str(document.get("name", "")).lower().replace("-", "_")
    require(
        name not in GENERIC_MCP_NAMES
        and not any(token in name for token in ("arbitrary_shell", "generic_uri", "any_connector")),
        findings,
        "MCP-CAPABILITY-001",
        "$.name",
        "MCP must expose a bounded semantic capability, not generic execution",
    )
    require(
        isinstance(document.get("inputSchema"), dict)
        and isinstance(document.get("outputSchema"), dict),
        findings,
        "MCP-CAPABILITY-001",
        "$.inputSchema|$.outputSchema",
        "MCP capability requires typed input and output schemas",
    )
    require(
        document.get("transportGrantsAuthority") is False
        and document.get("authorityBoundary") == "subactor_control",
        findings,
        "MCP-AUTHORITY-001",
        "$",
        "MCP transport cannot grant authority; Subactor Control is the boundary",
    )
    if document.get("mutates") is True:
        bindings = object_at(document, "bindings")
        require(
            all(bindings.get(key) is True for key in ("ticket", "planHash", "grantRef")),
            findings,
            "MCP-MUTATION-001",
            "$.bindings",
            "mutation requires ticket, planHash and grantRef bindings",
        )
    return findings


VALIDATORS: dict[str, Callable[[Any], list[dict[str, str]]]] = {
    "delegation": validate_delegation,
    "runtime": validate_runtime,
    "mcp": validate_mcp,
}


def emit(kind: str, source: str, findings: list[dict[str, str]]) -> int:
    result = {
        "schema": "wellmanifest.subactor-communication/conformance-result/v1",
        "kind": kind,
        "source": source,
        "valid": not findings,
        "findings": findings,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not findings else 1


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def self_test() -> int:
    failures: list[str] = []
    for schema in SCHEMAS:
        value = load_json(schema)
        if not isinstance(value, dict) or not value.get("$id"):
            failures.append(f"schema-invalid:{schema.name}")

    for fixture_name in ("valid.json", "invalid.json"):
        fixture_path = ROOT / "fixtures" / fixture_name
        fixture = load_json(fixture_path)
        for case in fixture.get("cases", []):
            kind = case.get("kind")
            validator = VALIDATORS.get(kind)
            if validator is None:
                failures.append(f"{fixture_name}:{case.get('id')}:unknown-kind")
                continue
            findings = validator(case.get("document"))
            codes = {item["code"] for item in findings}
            expected_valid = case.get("expectValid") is True
            expected_codes = set(case.get("expectedFindings", []))
            if expected_valid != (not findings):
                failures.append(
                    f"{fixture_name}:{case.get('id')}:valid={not findings}:codes={sorted(codes)}"
                )
            if expected_codes and not expected_codes <= codes:
                failures.append(
                    f"{fixture_name}:{case.get('id')}:missing={sorted(expected_codes - codes)}"
                )

    result = {
        "schema": "wellmanifest.subactor-communication/self-test-result/v1",
        "valid": not failures,
        "schemaCount": len(SCHEMAS),
        "fixtureCount": 2,
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("self-test")
    check = subparsers.add_parser("check")
    check.add_argument("kind", choices=sorted(VALIDATORS))
    check.add_argument("document", type=Path)
    args = parser.parse_args(argv)

    if args.command == "self-test":
        return self_test()
    try:
        document = load_json(args.document)
    except (OSError, json.JSONDecodeError) as error:
        print(json.dumps({"valid": False, "error": str(error)}, sort_keys=True), file=sys.stderr)
        return 2
    findings = VALIDATORS[args.kind](document)
    return emit(args.kind, str(args.document), findings)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Dependency-free semantic conformance for Subactor communication."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
try:
    import runtime_conformance as _rt
except ModuleNotFoundError:  # pragma: no cover - spec_from_file_location fallback
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    import runtime_conformance as _rt

URI_REF_RE = _rt.URI_REF_RE
UTC_INSTANT_RE = _rt.UTC_INSTANT_RE
exact_string_set = _rt.exact_string_set
finding = _rt.finding
forbidden_keys = _rt.forbidden_keys
is_uri_ref = _rt.is_uri_ref
list_at = _rt.list_at
non_empty_str = _rt.non_empty_str
object_at = _rt.object_at
require = _rt.require
strict_load_json = _rt.strict_load_json
strict_positive_int = _rt.strict_positive_int
string_set = _rt.string_set
utc_instant = _rt.utc_instant
validate_identity = _rt.validate_identity
validate_runtime = _rt.validate_runtime

SCHEMAS = (
    ROOT / "delegation-envelope.schema.v1.json",
    ROOT / "runtime-event.schema.v1.json",
    ROOT / "runtime-event.schema.v2.json",
    ROOT / "mcp-tool-contract.schema.v1.json",
)
GENERIC_MCP_NAMES = {"run_shell", "shell", "run_uri", "call_connector", "execute_any", "invoke"}
DELEGATION_MODES = {"observe", "plan", "dry_run", "apply", "autonomous"}
SENDER_KINDS = {"human", "llm_agent", "mcp_client"}
SENDER_ROLES = {"founder", "supervisor", "observer"}
TRANSPORT_KINDS = {"cli", "rest", "web", "mcp", "artifact"}
EFFECT_REVERSIBILITY = {"none", "reversible", "irreversible"}
BASE_DELEGATION_EVIDENCE = {"ticket", "process_uri", "plan_hash", "events", "receipts", "readback"}
ALLOWED_DELEGATION_EVIDENCE = BASE_DELEGATION_EVIDENCE | {"eql", "contract_bounds_readback"}
MCP_OPERATION_CLASSES = {
    "observe_state",
    "delegate_outcome",
    "inspect_plan",
    "approve_plan",
    "execute_contract",
    "read_receipt",
}

__all__ = [
    "GENERIC_MCP_NAMES",
    "ROOT",
    "SCHEMAS",
    "URI_REF_RE",
    "UTC_INSTANT_RE",
    "VALIDATORS",
    "emit",
    "exact_string_set",
    "finding",
    "forbidden_keys",
    "is_uri_ref",
    "list_at",
    "load_json",
    "main",
    "object_at",
    "require",
    "self_test",
    "utc_instant",
    "validate_delegation",
    "validate_identity",
    "validate_mcp",
    "validate_runtime",
]


def validate_delegation(document: Any) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(document, dict):
        return [finding("COMM-SHAPE-001", "$", "document must be an object")]

    require(
        document.get("schema") == "wellmanifest.subactor-communication/delegation-envelope/v1",
        findings,
        "COMM-SHAPE-001",
        "$.schema",
        "unexpected delegation schema identifier",
    )
    require(
        non_empty_str(document.get("messageId")),
        findings,
        "COMM-SHAPE-001",
        "$.messageId",
        "delegation envelope requires a non-empty messageId",
    )
    sender = object_at(document, "sender")
    require(
        isinstance(document.get("sender"), dict)
        and sender.get("kind") in SENDER_KINDS
        and sender.get("role") in SENDER_ROLES,
        findings,
        "COMM-SHAPE-001",
        "$.sender",
        "sender must declare valid kind and role",
    )
    validate_identity(document, findings)

    intent = object_at(document, "intent")
    require(
        non_empty_str(intent.get("outcome")),
        findings,
        "COMM-OWNERSHIP-001",
        "$.intent.outcome",
        "delegate an outcome instead of worker instructions",
    )
    scope_ok, scope_items = string_set(intent.get("scope"))
    acceptance_ok, acceptance_items = string_set(intent.get("acceptance"))
    require(
        scope_ok and bool(scope_items) and acceptance_ok and bool(acceptance_items),
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
        document, {"tasks", "workerPrompts", "subagents", "serviceCommands", "packageCommands"}
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
        isinstance(document.get("transport"), dict) and transport.get("kind") in TRANSPORT_KINDS,
        findings,
        "COMM-SHAPE-001",
        "$.transport.kind",
        "transport kind must be cli, rest, web, mcp or artifact",
    )
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
    mode = authority.get("mode")
    require(
        mode in DELEGATION_MODES,
        findings,
        "COMM-AUTHORITY-001",
        "$.authority.mode",
        "authority mode must be observe, plan, dry_run, apply or autonomous",
    )
    if mode == "apply":
        require(
            non_empty_str(authority.get("grantRef")) and non_empty_str(authority.get("planHash")),
            findings,
            "COMM-AUTHORITY-002",
            "$.authority",
            "apply requires both grantRef and planHash",
        )
    if mode == "autonomous":
        require(
            non_empty_str(authority.get("contractRef")) and non_empty_str(authority.get("planHash")),
            findings,
            "COMM-AUTHORITY-003",
            "$.authority",
            "autonomous execution requires both contractRef and planHash",
        )
        bounds = object_at(authority, "contractBounds")
        verified_at = utc_instant(bounds.get("verifiedAt"))
        expires_at = utc_instant(bounds.get("expiresAt"))
        allowed_ops_raw = bounds.get("allowedOperations")
        ops_ok, ops_set = string_set(allowed_ops_raw)
        max_steps_ok = "maxSteps" not in bounds or strict_positive_int(bounds.get("maxSteps"))
        require(
            bounds.get("withinBounds") is True
            and verified_at is not None
            and expires_at is not None
            and verified_at < expires_at
            and strict_positive_int(bounds.get("remainingExecutions"))
            and max_steps_ok
            and ops_ok
            and bool(ops_set)
            and isinstance(allowed_ops_raw, list)
            and len(ops_set) == len(allowed_ops_raw),
            findings,
            "COMM-CONTRACT-001",
            "$.authority.contractBounds",
            "autonomy contract must be verified as unexpired, unexhausted and operation-bounded",
        )
        readiness = object_at(document, "readiness")
        require(
            readiness.get("boundedAutonomyReady") is True
            and non_empty_str(readiness.get("autonomyControlRef"))
            and utc_instant(readiness.get("observedAt")) is not None,
            findings,
            "COMM-READINESS-001",
            "$.readiness",
            "autonomous delegation requires an observed bounded-autonomy readiness preflight",
        )

    raw_effects = document.get("effects")
    if not isinstance(raw_effects, list):
        findings.append(finding("COMM-SHAPE-001", "$.effects", "effects must be an array"))
    else:
        for index, effect in enumerate(raw_effects):
            if not isinstance(effect, dict):
                findings.append(finding("COMM-SHAPE-001", f"$.effects[{index}]", "effect must be an object"))
                continue
            reversibility = effect.get("reversibility")
            require(
                non_empty_str(effect.get("effect")) and reversibility in EFFECT_REVERSIBILITY,
                findings,
                "COMM-SHAPE-001",
                f"$.effects[{index}]",
                "effect requires non-empty description and reversibility enum",
            )
            if reversibility == "reversible":
                require(
                    non_empty_str(effect.get("rollbackRef")) or non_empty_str(effect.get("compensationRef")),
                    findings,
                    "COMM-EFFECT-001",
                    f"$.effects[{index}]",
                    "reversible effect requires rollbackRef or compensationRef",
                )
            if reversibility == "irreversible":
                require(
                    effect.get("requiresHigherAuthority") is True
                    and non_empty_str(effect.get("higherAuthorityApprovalRef")),
                    findings,
                    "COMM-EFFECT-002",
                    f"$.effects[{index}]",
                    "irreversible effect requires a higher-authority approval reference",
                )

    raw_required = object_at(document, "evidence").get("required")
    ev_ok, required_evidence = string_set(raw_required)
    ev_unique = isinstance(raw_required, list) and len(required_evidence) == len(raw_required)
    require(
        ev_ok
        and ev_unique
        and required_evidence <= ALLOWED_DELEGATION_EVIDENCE
        and BASE_DELEGATION_EVIDENCE <= required_evidence,
        findings,
        "COMM-EVIDENCE-001",
        "$.evidence.required",
        "evidence chain must require ticket, process URI, plan hash, events, receipts and readback",
    )
    if mode == "autonomous":
        require(
            ev_ok and "contract_bounds_readback" in required_evidence,
            findings,
            "COMM-EVIDENCE-001",
            "$.evidence.required",
            "autonomous execution must require a contract bounds readback",
        )
    return findings


def validate_mcp(document: Any) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(document, dict):
        return [finding("COMM-SHAPE-001", "$", "document must be an object")]

    require(
        document.get("schema") == "wellmanifest.subactor-communication/mcp-tool-contract/v1",
        findings,
        "COMM-SHAPE-001",
        "$.schema",
        "unexpected MCP tool schema identifier",
    )
    validate_identity(document, findings)
    raw_name = document.get("name")
    normalized_name = raw_name.strip().lower().replace("-", "_") if isinstance(raw_name, str) else ""
    require(
        non_empty_str(raw_name)
        and normalized_name not in GENERIC_MCP_NAMES
        and not any(token in normalized_name for token in ("arbitrary_shell", "generic_uri", "any_connector")),
        findings,
        "MCP-CAPABILITY-001",
        "$.name",
        "MCP must expose a bounded semantic capability, not generic execution",
    )
    require(
        document.get("operationClass") in MCP_OPERATION_CLASSES,
        findings,
        "MCP-CAPABILITY-001",
        "$.operationClass",
        "MCP capability requires a declared operationClass",
    )
    require(
        isinstance(document.get("inputSchema"), dict) and isinstance(document.get("outputSchema"), dict),
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
    mutates = document.get("mutates")
    bindings = object_at(document, "bindings")
    bindings_typed = isinstance(document.get("bindings"), dict) and all(
        isinstance(bindings.get(key), bool) for key in ("ticket", "planHash", "grantRef")
    )
    require(
        isinstance(mutates, bool) and bindings_typed,
        findings,
        "MCP-MUTATION-001",
        "$.mutates|$.bindings",
        "mutates and required bindings flags must be explicit booleans",
    )
    if mutates is True:
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
    return strict_load_json(path)


def self_test() -> int:
    failures: list[str] = []
    for schema in SCHEMAS:
        try:
            value = strict_load_json(schema, root=ROOT)
        except (OSError, UnicodeDecodeError, ValueError) as error:
            failures.append(f"schema-error:{schema.name}:{error}")
            continue
        if not isinstance(value, dict) or not value.get("$id"):
            failures.append(f"schema-invalid:{schema.name}")

    for fixture_name in ("valid.json", "invalid.json"):
        fixture_path = ROOT / "fixtures" / fixture_name
        try:
            fixture = strict_load_json(fixture_path, root=ROOT)
        except (OSError, UnicodeDecodeError, ValueError) as error:
            failures.append(f"fixture-error:{fixture_name}:{error}")
            continue
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
                failures.append(f"{fixture_name}:{case.get('id')}:valid={not findings}:codes={sorted(codes)}")
            if expected_codes and not expected_codes <= codes:
                failures.append(f"{fixture_name}:{case.get('id')}:missing={sorted(expected_codes - codes)}")

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
    except (OSError, UnicodeDecodeError, ValueError) as error:
        print(json.dumps({"valid": False, "error": str(error)}, sort_keys=True), file=sys.stderr)
        return 2
    return emit(args.kind, str(args.document), VALIDATORS[args.kind](document))


if __name__ == "__main__":
    raise SystemExit(main())

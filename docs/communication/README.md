---
{
  "schema": "wellmanifest.subactor-communication/specification/v1",
  "id": "subactor-communication",
  "version": 2,
  "status": "current",
  "updated": "2026-08-25"
}
---

# Subactor communication conformance

This directory is the machine-checkable part of the normative guide. It does
not define a new Subactor runtime API. It defines invariants which every
adapter MUST preserve when a human, LLM agent or MCP client delegates to and
observes Subactor.

The contract deliberately rejects the two false models recorded on 2026-08-25:

- `Subactor = temporary LLM/subagent/worker`; and
- `a supervisor's shell, repository tools or MCP session = execution authority`.

Subactor is identified as an `autonomous_system` and remains the execution
owner. An LLM is a founder/supervisor-side participant or an internally routed
cognitive capability. It is never Subactor's identity or authority issuer.

## Normative artifacts

| Artifact | Boundary |
| --- | --- |
| `delegation-envelope.schema.v1.json` | Outcome delegation, scope, acceptance, authority, effects and evidence requirements |
| `runtime-event.schema.v1.json` | Published compatibility contract for ticket/queue/plan admission |
| `runtime-event.schema.v2.json` | Exact per-process actor, operation, registered resource, grant and admission bindings |
| `mcp-tool-contract.schema.v1.json` | Bounded semantic MCP capabilities whose transport never grants authority |
| `conformance.py` | Dependency-free semantic checks and stable finding codes |
| `fixtures/valid.json` | Positive exchange examples for all three boundaries |
| `fixtures/invalid.json` | Adversarial Gemini/Codex-style examples which MUST fail |

JSON Schema validates transport shape. The conformance runner validates
cross-field authority and lifecycle semantics. Passing either one alone does
not create an authority grant or prove task completion.

## Required interaction model

1. A founder or supervisor delegates an observable outcome to the target
   `subactor` of class `autonomous_system`.
2. Subactor owns decomposition, POA process resolution, capability selection
   and internal SubLLM routing.
3. A supervisor observes official Control surfaces and evidence. It MUST NOT
   use service repositories, private packages or generic tools to perform the
   target task for Subactor.
4. A planned queue revision is validated before execution. In runtime-event
   v2 every process binds an exact process URI, actor, operation and registered
   resource URI set. Every mutation grant binds that same tuple exactly. The
   independent admission receipt binds the ticket, queue revision, `planHash`,
   process URI set and resource URI set.
5. Rejection moves the same ticket to `replan_required`; the orchestrator emits
   a higher queue revision and a new plan hash before asking for admission
   again. Rejection is never permission to bypass the gate.
6. Reversible effects declare rollback/compensation. Irreversible effects
   require a reference to approval from a higher authority. A digital twin may
   supply it only through a bounded, prior delegation recognized by Control.
7. `completed` requires receipts and independent readback. An LLM response,
   chat message, Markdown note, dashboard projection or test result alone is
   not completion evidence.

## URI, identity and authority

A POA URI identifies a registered resource or process in the same general
sense that mobile operating systems use stable identifiers for applications,
resources and operations. The identifier does not grant access. Control must
resolve the actor, contract/grant, exact plan and applicable policy separately.

An address-shaped string is not enough. Before admission, each resource URI
must carry a registry reference and each mutating process must prove set-equal
grant bindings for actor, process URI, operation and all source/target/scope
resource URIs. A generic provider label, broad `.env` search, model credential
or destination name cannot stand in for an exact registered resource. Missing
or mismatched identity returns the same ticket to `replan_required`.

The important difference from a simple manual permission dialog is the
reversibility gate:

- reversible work may proceed inside a bounded grant when a declared rollback
  or compensation exists;
- irreversible work must stop for approval from a higher authority unless an
  already valid higher-authority delegation explicitly covers that exact
  effect; and
- no transport, URI, model credential or MCP tool name can satisfy this gate.

## Stable semantic findings

| Finding | Meaning |
| --- | --- |
| `COMM-IDENTITY-001` | Target is not Subactor as an autonomous system |
| `COMM-OWNERSHIP-001` | Supervisor/LLM took execution or decomposition ownership |
| `COMM-AUTHORITY-001` | Transport or SubLLM was treated as an authority source |
| `COMM-AUTHORITY-002` | Apply lacks a plan-bound grant |
| `COMM-EFFECT-001` | Reversible effect lacks rollback/compensation |
| `COMM-EFFECT-002` | Irreversible effect lacks higher-authority approval |
| `COMM-EVIDENCE-001` | Required evidence chain is incomplete |
| `POA-ADMISSION-001` | Execution is not bound to an admitted queue revision/plan |
| `POA-RESOURCE-BINDING-001` | Process lacks exact registered actor/operation/resource identity |
| `POA-GRANT-BINDING-001` | Mutation grant does not exactly match its process and resource URI set |
| `POA-REPLAN-001` | Rejected work did not return to a higher plan revision |
| `POA-COMPLETION-001` | Completion lacks receipts and independent readback |
| `MCP-CAPABILITY-001` | MCP exposes an unbounded generic execution primitive |
| `MCP-AUTHORITY-001` | MCP transport or tool claims to grant authority |
| `MCP-MUTATION-001` | Mutating MCP operation lacks ticket/plan/grant binding |

## Run locally or in CI

```bash
python3 docs/communication/conformance.py self-test
python3 docs/communication/conformance.py check delegation message.json
python3 docs/communication/conformance.py check runtime event.json
python3 docs/communication/conformance.py check mcp tool.json
```

Exit code `0` means that no finding was produced. Exit code `1` means that the
document violated at least one invariant. Malformed invocations use exit code
`2`. Output is deterministic JSON so adapters and CI can consume the same
receipt.

Runtime repositories adopt these contracts; they do not move runtime services
into Wellmanifest. The contract is `HOME wellmanifest`, `SHAPE domain_pack`;
CLI, API, MCP adapters, Control and daemons remain `HOME subactor`.

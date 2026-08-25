# Ticket 006: Require exact POA resource and grant bindings before admission

- **ID**: ticket-006
- **Owner**: agent:codex
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-25

## Goal and scope

Close the POA admission gap exposed by the deployment-credential incident:
ticket, queue revision, plan hash and a grant were insufficient when the
planned process named an unregistered provider and omitted the exact source
and destination resources required by the runtime grant contract.

## Acceptance criteria

- [x] AC-01: Runtime-event v2 represents each queued process with an exact
  process URI, actor, operation and registered resource bindings.
- [x] AC-02: Every mutating process carries a grant whose actor, process,
  operation and resource URI set exactly match the planned process.
- [x] AC-03: Admission binds the ticket, queue revision, plan hash, process URI
  set and resource URI set before an executable state is accepted.
- [x] AC-04: Stable findings reject missing resource identity and mismatched
  per-process authority, including an adversarial credential-harvest fixture.
- [x] AC-05: Runtime-event v1 remains available and valid; v2 is additive.
- [x] AC-06: Conformance self-test and managed governance pass.

## Participants

- Human participant: session requester (authority recorded in agent evidence;
  no synthetic human-owned file was created).
- Agent participant: [ai-codex.md](ai-codex.md)

## Closure receipt

- Pull request: `wellmanifest/how-to-use-subactor#9`
- Validated head: `8ae02cbc85b007c4936e954aa4e1f9fa954d4fed`
- Integrated main: `fe130a98eb14b416e20b314832aa06e1e3194fbf`
- Merged at: `2026-08-25T20:47:21Z`
- Result: exact-head Validator Agent approval, protected merge and deleted head
  branch; this closure changes governance evidence only.

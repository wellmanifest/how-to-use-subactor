# Ticket 007: Publish exact POA resource binding guide release

- **ID**: ticket-007
- **Owner**: agent:codex
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-25

## Goal and scope

Publish the adopter-facing release for the already integrated runtime-event v2
contract. Keep the normative root guide, repository version and changelog in
sync without changing the v2 schema or conformance implementation.

## Acceptance criteria

- [x] AC-01: The root guide explains exact process/actor/operation/resource URI
  and set-equal mutation grant binding before admission.
- [x] AC-02: The guide explicitly rejects generic provider labels and broad
  secret searches as resource identity.
- [x] AC-03: `VERSION`, root document metadata and changelog publish `0.3.0`.
- [x] AC-04: Conformance self-test and managed governance pass.

## Participants

- Human participant: session requester (authority recorded in agent evidence;
  no synthetic human-owned file was created).
- Agent participant: [ai-codex.md](ai-codex.md)

## Closure receipt

- Pull request: `wellmanifest/how-to-use-subactor#11`
- Validated head: `5be0fed0fd4a9b36106ef0ddaf44dbd242688ae1`
- Integrated main: `a398f9db82c38ea8470362b4abd810cd43b95c20`
- Merged at: `2026-08-25T20:55:45Z`
- Result: exact-head Validator Agent approval and protected merge; this closure
  changes governance evidence only.

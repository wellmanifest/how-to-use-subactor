# Ticket 017: Current multi-source diagnostics

- **ID**: ticket-017
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-09

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: the user requested updates to wellmanifest/how-to-use-subactor and wellmanifest/logs based on current data and logging methods. Deliver the owning repository guidance and publish through protected validation where available.

Canonical result: [diagnostic guidance](../../docs/information/multi-source-diagnostics.md).

## Acceptance criteria

- [ ] AC-01: Indexed, source-bound guidance describes storage, coverage, LLM context and actual validation/deployment status; repository checks are recorded.

## Boundaries

No runtime deployment, raw transcripts, secrets or database contents in Git. Existing tickets and immutable contract versions remain auditable.

## Validation

Governance: 0 errors; documentation placement: 1 document, 0 findings; usage contract: 4 artifacts valid; 13 conformance tests and communication self-test pass. Live discovery retains two documented pre-existing profile mismatches (USAGE-DISCOVERY-004 and USAGE-COMPAT-002); no full runtime-profile conformance is claimed. Archive deployment and source coverage are documented separately.

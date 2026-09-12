# Ticket 019: Adopt wellmanifest/new-project 0.20.25

- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-12

SESSION_EXECUTION_AUTHORIZATION: adopt, test, push and protected merge, requested by the owner on 2026-09-12.

## Goal and scope

This repository pinned `0.20.19` (`3e95fa28`). The current published release is
`0.20.25` (`d54878a1`), which fixes a defect affecting every adopter that runs
Python 3.10: `scripts/agent_host_check.py` imported `tomllib` at module scope,
`governance_check.py` reported the resulting `ImportError` as a missing managed
validator (`GOV-SYNC-001`), and because `GOV-PACKAGING-003` binds the gate to
the test lifecycle, the session aborted. Found and fixed while adopting the
standard in `semcod/planfile`: wellmanifest/new-project#325 (fix), #326
(release 0.20.25).

The adoption advances 24 managed governance files plus the regenerated lock and
the `project.sh` / `project.bat` seed aliases. This repository carries no
packaging marker, so there is no `[tool.wellmanifest]` pin to realign, and every
changed path belongs to the `governance` workstream.

Out of scope: any documentation or content change.

## Acceptance criteria

- [ ] AC-01: `goal governance adopt --source-revision d54878a… --check` reports no drift.
- [ ] AC-02: `./project/governance-check.sh --base origin/main --head HEAD --actor agent` passes.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.

# Ticket 025: Modularize communication conformance and harden strict JSON, calendar, enum, and symlink validation

- **ID**: ticket-025
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-11

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: User authorized continuous autonomous auditing, fixing, optimization, modularization, testing, and protected Validator delivery across `wellmanifest/*` repositories:
- AC-01: Decompose `docs/communication/conformance.py` (598 lines) into `< 400`-line `docs/communication/conformance.py` + `docs/communication/runtime_conformance.py` while preserving CLI and fixture compatibility.
- AC-02: Fix `bool`-as-`int` acceptance in `POA-REPLAN-001`, impossible calendar dates in `utc_instant`, silent bypasses on unknown `authority.mode` / `runtime.state` / `admission.decision` / empty `mcp.name` / non-bool `mcp.mutates`, and `TypeError` crashes on unhashable list items in `docs/communication/` and `docs/standard/conformance.py`.
- AC-03: Enforce duplicate-JSON-key, non-finite number, and symlink rejection in `load_json` / `digest` across both conformance suites, and add regression tests in `docs/communication/conformance_test.py` and `docs/standard/conformance_test.py`.
- AC-04: Pass `ruff`, both conformance suites and unit tests, `./project/governance-check.sh`, and `wellman check`.

## Acceptance criteria

- [x] AC-01: Decompose `docs/communication/conformance.py` so every owned `docs/**/*.py` module is `< 500` lines.
- [x] AC-02: Eliminate `bool`-as-`int`, calendar, enum-bypass, and unhashable `TypeError` bugs in `communication` and `standard` validators.
- [x] AC-03: Reject duplicate JSON keys, `NaN`/`Infinity`, and symlinks in `load_json` / artifact checks and add unit tests.
- [x] AC-04: Pass `ruff`, unit tests, `self-test`, `./project/governance-check.sh`, and `wellman check` with 0 errors.

## Participants

- Human participant: user via chat authorization.
- Agent participant: Antigravity

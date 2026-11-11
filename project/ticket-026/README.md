# Ticket 026: Harden descriptor-relative file reads, discovery gating, and schema parity in conformance

- **ID**: ticket-026
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-11

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: User authorized continuous autonomous auditing, fixing, optimization, modularization, testing, and protected Validator delivery across `wellmanifest/*` repositories:
- AC-01: Replace pre-open symlink path inspection with descriptor-relative `O_DIRECTORY | O_NOFOLLOW` (`dir_fd`) traversal in `docs/standard/conformance.py` and `docs/communication/runtime_conformance.py`, and compute artifact SHA-256 and JSON parse from a single file-descriptor read.
- AC-02: Gate `discover()` in `docs/standard/conformance.py` so malformed `interface-profile` documents never reach subprocess execution or regex escaping, and guard direct `discover()` calls against malformed profiles or missing binaries on `--version`.
- AC-03: Enforce full dependency-free schema parity in `validate_interface()` and `validate_project()` (`version` bool-as-int rejection, `status`/`effect`/`authority`/`onFailure` enums, `runtime`/`discovery`/`completion` closed keys, `observedVersion`, `projectRef`, and unique list constraints), keeping all `.py` modules `< 500` lines.
- AC-04: Add adversarial unit tests and pass `ruff`, `self-test`, `conformance.py check`, `./project/governance-check.sh`, and `wellman check`.

## Acceptance criteria

- [x] AC-01: Anchor root-bounded reads via descriptor-relative `O_DIRECTORY | O_NOFOLLOW` traversal and single-open artifact digest+parse.
- [x] AC-02: Prevent `check(run_discovery=True)` and `discover()` from executing or crashing on malformed interface profiles.
- [x] AC-03: Enforce schema parity across `validate_interface()` and `validate_project()` while keeping all `.py` modules `< 500` lines.
- [x] AC-04: Pass `ruff`, unit tests, `self-test`, `./project/governance-check.sh`, and `wellman check` with 0 errors.

## Participants

- Human participant: user via chat authorization.
- Agent participant: Antigravity

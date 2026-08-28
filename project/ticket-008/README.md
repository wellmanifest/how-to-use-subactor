# Ticket 008: Refactor executable Subactor usage standard

- **ID**: ticket-008
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-28

## Goal and scope

Publish one versioned, machine-checkable standard which distinguishes the
Founder CLI from Subactor Shell, declares compatibility with concrete runtime
revisions and supplies a bounded C2004 refactoring profile.

The user's request to execute, test and publish is recorded as
`SESSION_EXECUTION_AUTHORIZATION`. Publication remains subject to exact-head
independent validation.

## Acceptance criteria

- [x] AC-01: Founder CLI and Subactor Shell have separate closed profiles.
- [x] AC-02: The compatibility manifest binds guide, runtime and schema versions.
- [x] AC-03: Conformance checks the installed CLI command surfaces without mutation.
- [x] AC-04: A C2004 profile defines bounded refactor, test, deploy/readback and flash stages.
- [x] AC-05: Documentation identifies discovery, authority and proof requirements per interface.
- [x] AC-06: Communication and repository governance checks pass.
- [x] AC-07: The exact PR head receives trusted independent validation before merge.

## Participants

- Human participant: request supplied in the active session; no `user-*` file was created.
- Agent participant: [ai-codex.md](ai-codex.md)

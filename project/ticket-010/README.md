# Ticket 010: Resolve repository identity from Git origin

- **ID**: ticket-010
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-28

## Goal and scope

Define deterministic repository identity independently from the checkout
directory, detect optional workspace-layout drift and provide a safe,
non-mutating repair plan for mismatches such as a `wellmanifest/*` origin under
a local `subactor/` directory.

## Acceptance criteria

- [x] AC-01: SCP-style, HTTPS and SSH remotes resolve to one credential-free
  host and `owner/repository` identity.
- [x] AC-02: Checkout placement is checked only when an explicit workspace
  root is supplied; path names never override Git identity.
- [x] AC-03: Mismatched origin refs and paths emit stable, distinct findings.
- [x] AC-04: Repair is read-only and requires clone, verification and
  recoverable retirement rather than an unsafe rename.
- [ ] AC-05: Unit, conformance and governance checks pass and the exact PR head
  receives independent approval.

## Participants

- Human participant: the active request authorized autonomous implementation
  and publication; no `user-*` file was generated.
- Agent participant: [ai-codex.md](ai-codex.md)

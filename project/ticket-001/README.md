# Ticket 001: Adopt immutable repository governance

- **ID**: ticket-001
- **Owner**: agent:codex under SESSION_EXECUTION_AUTHORIZATION
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-25

## Goal and scope

Adopt published `wellmanifest/new-project` v0.18.6 as one atomic transaction,
activate the shared agent-host contract and align required checks with the
managed workflow. This establishes the governed repository boundary before the
public Subactor usage guide is written in a separate dependent ticket.

## Acceptance criteria

- [x] AC-01: The adoption lock binds published v0.18.6 and exact source SHA.
- [x] AC-02: Managed file digests match the adoption lock.
- [x] AC-03: Host instructions and the local pre-commit hook are installed.
- [x] AC-04: Required checks match actual job names in the managed workflow.
- [x] AC-05: Governance and whitespace checks pass.

## Participants

- Human participant: authorization was supplied in the active conversation;
  no `user-*` file was created or modified.
- Agent participant: [ai-codex.md](ai-codex.md)

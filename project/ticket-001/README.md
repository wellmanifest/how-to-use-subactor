# Ticket 001: Adopt immutable repository governance

- **ID**: ticket-001
- **Owner**: agent:codex under SESSION_EXECUTION_AUTHORIZATION
- **Status**: DONE
- **Workflow state**: DONE
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

## Publication evidence

- Pull request: <https://github.com/wellmanifest/how-to-use-subactor/pull/1>
- Validated head: `a424c93841d747e461cba54f84b8d73c9100acc6`
- Independent approval: `ifuri-validator-agent[bot]`, decision `APPROVE`
- Integrated commit: `460c6c1b5de5fb01b2be6f387ff4c9fdef63a421`
- Merged: 2026-08-25 10:45:54 UTC

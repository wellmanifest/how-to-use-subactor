# Ticket 003: Define enforceable Subactor communication contracts

- **ID**: ticket-003
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-08-25

## Goal and scope

Turn the two 2026-08-25 failure reports into a transport-neutral, machine-
checkable communication contract for human founders, LLM supervisors,
Subactor runtime events and MCP tools. The contract must reject the false
models `Subactor = LLM/subagent`, `transport = authority`, supervisor bypass,
ungated POA execution and completion asserted without receipts/readback.

## Acceptance criteria

- [x] AC-01: A typed delegation envelope identifies Subactor as the autonomous
  execution owner and separates outcome, authority, transport and evidence.
- [x] AC-02: Runtime events bind ticket, correlation, queue revision and plan
  hash; execution requires an independent admission receipt, while rejection
  requires a revised plan in the same ticket.
- [x] AC-03: Irreversible effects require a higher-authority approval reference;
  reversible effects declare rollback or compensation.
- [x] AC-04: MCP tools expose bounded semantic operations and cannot turn a
  generic shell, URI or connector call into implicit execution authority.
- [x] AC-05: A dependency-free conformance runner accepts valid fixtures and
  rejects adversarial Gemini/Codex-style fixtures with stable finding codes.
- [ ] AC-06: The managed governance gate and diff checks pass.

## Participants

- Human participant: session requester (authority recorded in agent evidence;
  no synthetic human-owned file was created).
- Agent participant: [ai-codex.md](ai-codex.md)

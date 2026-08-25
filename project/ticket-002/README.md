# Ticket 002: Publish the Subactor human and LLM supervisor guide

- **ID**: ticket-002
- **Owner**: agent:codex under SESSION_EXECUTION_AUTHORIZATION
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-25

## Goal and scope

Publish a normative Polish guide for humans and LLM supervisors that explains
how to delegate outcomes to Subactor through its governed interfaces, observe
execution, verify evidence and improve autonomy without reducing Subactor to an
LLM, chat agent or a collection of manually orchestrated workers.

## Acceptance criteria

- [x] AC-01: The guide defines Subactor as an autonomous system and separates
  its responsibility from the human, supervisor LLM, SubLLM and capabilities.
- [x] AC-02: The guide provides one communication contract and interface order
  for CLI/shell, REST API, web UI, MCP and immutable artifacts.
- [x] AC-03: Authority, plan, dry-run, apply, receipt and EQL/readback boundaries
  are explicit, including that SubLLM routes models but grants no authority.
- [x] AC-04: A supervisor loop covers delegation, observation, diagnosis,
  bounded repair of autonomy defects and replay through Subactor.
- [x] AC-05: Gemini/Antigravity micromanagement and Codex direct-bypass failures
  are documented with corrected supervisor prompts and behavior.
- [x] AC-06: Repository version and changelog identify the first public guide,
  and governance plus whitespace validation pass.

## Participants

- Human participant: authorization and requirements were supplied in the active
  conversation; no `user-*` file was created or modified.
- Agent participant: [ai-codex.md](ai-codex.md)

## Publication evidence

- Pull request: <https://github.com/wellmanifest/how-to-use-subactor/pull/3>
- Validated head: `ec50af6983f2a8d114b42b9af28546b723f778b6`
- Independent approval: `ifuri-validator-agent[bot]`, decision `APPROVE`
- Integrated commit: `1330991dba77d461f81a9ccb4fb3fd4a61c04cab`
- Merged: 2026-08-25 10:58:33 UTC

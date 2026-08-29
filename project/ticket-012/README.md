# Ticket 012: Document bounded autonomous operation and interface bootstrap in the guide

- **ID**: ticket-012
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-28

## Goal and scope

`ticket-011` made bounded autonomous execution expressible and checkable. The
narrative guide still described only four authority levels and omitted the
operational steps a supervisor needs, so a reader could satisfy every gate and
still fail to run unattended work.

This ticket covers the governance-owned prose:

- the fifth authority level, contract verification and the readiness preflight;
- the mutually exclusive `--autonomous` execution flag in the Founder CLI;
- the Subactor Shell configuration bootstrap, because a working Founder CLI does
  not prove the Shell can reach Control;
- the fact that `subactor endpoints` is a partial catalog in both directions;
- a section for the new project-development profile.

## Evidence observed before the change

```text
subactor-shell doctor -> Vault HTTP: ConnectError
                         Subactor Control: ConnectError
                         MCP boundary: cannot read control.token
~/.config/subactor-shell/config.toml
                      -> [control] base_url = http://127.0.0.1:8088
                         [control] bearer_ref = file://~/.config/.../control.token
subactor help         -> target http://192.168.188.212:8091
```

The Shell failure was therefore a stale `base_url`, not a missing token. The
guide previously said only that a missing token means `blocked`, which would
have sent a reader after the wrong cause. Section 5.2 now names the real one and
reuses the existing rule that a deployment address is never copied from an
example.

`subactor endpoints` omitted `/api/autonomy/control`,
`/api/knowledge/context` and `/api/artifacts/context`, all of which answered
correctly — including two paths the guide itself uses in section 5.3.

## Acceptance criteria

- [ ] AC-01: The guide documents the five authority levels, contract bounds
      verification, the readiness preflight and the `--autonomous` flag, and its
      declared release matches the manifest and `VERSION`.
- [ ] AC-02: Section 5.2 describes the real Shell bootstrap with credentials
      passed only by reference, section 5.3 states that endpoint discovery is
      partial in both directions, and both gates still pass.
- [ ] AC-03: The guide distinguishes Founder Control tickets from a project's
      Koru/Planfile queue, names the observed Koru MCP tools, treats
      `waiting_input` + `executor=human` as official execution, and tells the
      supervisor to follow the target repository `AGENTS.md` for publication.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-cursor.md](ai-cursor.md)

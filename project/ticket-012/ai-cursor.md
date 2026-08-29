---
participant-id: agent:cursor
participant: cursor
role: agent
ticket: ticket-012
---
# Participant: cursor (AI agent)

## Understanding

Every documented claim had to come from an observation on the running
deployment, not from the previous release text. One intermediate conclusion was
wrong and had to be corrected before it entered the guide: `doctor` reports a
missing `control.token` alongside the Control `ConnectError`, which suggested a
credential problem. Reading the Shell configuration showed
`[control] base_url = http://127.0.0.1:8088` while the Founder CLI targeted the
deployment on port 8091, so the reachability failure was a stale address. The
guide now documents that cause instead of the misleading symptom.

## Execution plan

1. Raise the declared release and add the fifth authority level to section 4.
2. Add contract verification and the readiness preflight as sections 4.1 and
   4.2, with the observed signal semantics.
3. Document `--autonomous` in section 5.1 and its mutual exclusivity.
4. Rewrite the Shell bootstrap in section 5.2 from the observed configuration.
5. Record the partial endpoint catalog in section 5.3.
6. Add the readiness step to the supervisor loop and renumber it.
7. Describe the project-development profile and extend the source list.

## Actual changes

- `README.md`: release `0.5.0`; `AUTHORITY` line in the communication contract;
  fifth authority level; new sections 4.1 and 4.2 with the readiness signal
  table; `--autonomous` in section 5.1; Shell bootstrap in section 5.2; partial
  endpoint catalog in section 5.3; readiness step added to the supervisor loop
  with the following steps renumbered to nine; project-development profile
  section; normative source list extended.
- Follow-up: two execution planes; Koru MCP catalog; `waiting_input` human
  executor; publication follows target `AGENTS.md`; Shell `doctor` independent
  probes; C2004 profile mismatch warning; Gemini/Codex sequences updated.
- `CHANGELOG.md`: `0.5.0` entry covering both tickets and the follow-up.

No schema, profile, conformance runner or manifest was touched; those belong to
`ticket-011`.

## Verification

```text
python3 docs/standard/conformance.py check          -> valid=true, version 0.5.0
python3 docs/communication/conformance.py self-test  -> valid=true
./project/governance-check.sh                        -> GOV-PASS
git diff --check                                     -> clean
```

## SESSION_EXECUTION_AUTHORIZATION

2026-08-28 user request: verify whether `wellmanifest/how-to-use-subactor`
matches how Subactor is actually used, and change the repository until the
guide matches that reality. Recorded here as authorization to expand the
narrative on this ticket without a second confirmation. Profiles and schemas
remain ticket-011.

## Follow-up observation (same day)

A later live pass against Control (`SUBACTOR_CONTROL_URL` →
`http://192.168.188.212:8091`), Founder CLI, Shell `doctor`, Koru 0.1.366 in
the c2004 venv and Koru MCP showed that release `0.5.0` still omitted the
project execution plane:

- `subactor tickets` listed 100+ Control tickets; c2004 `.planfile/` was a
  different queue.
- `koru_run_ticket` returned `waiting_input` / `executor=human` for project
  work; that is official IDE execution, not a bypass.
- `maskservice/c2004/AGENTS.md` requires commits on `main` with no PRs, while
  the candidate C2004 profile forbids `direct_main_edit`.
- Shell `doctor` now had Control `OK` while Vault HTTP and MCP boundary still
  failed; the earlier stale-`base_url` story remains possible but is not the
  only observed state.

## Blockers

- The two runtime defects remain open at `subactor/platform`: the partial
  `endpoints` catalog and the expired autonomy contract still served as
  `active`. The guide now documents both as hazards; the fixes are not in scope
  for this repository.
- `bounded_autonomy_ready` was `false` on the observed deployment, so the
  documented autonomous path could not be exercised end to end here. The
  documentation states the precondition rather than implying it is satisfied.
- The candidate C2004 profile still forbids `direct_main_edit`. Aligning that
  JSON is ticket-011 / a later integration ticket; this ticket only warns the
  reader to follow the live `AGENTS.md`.

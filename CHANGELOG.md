# Changelog

## 0.5.2 - 2026-08-29

- Documented `subactor-shell orgs` and `subactor-shell projects [--recon]` for
  organization registries and project portfolio/reconciliation views.
- Updated `subactor-shell` discovery catalog and manifest digest for release 0.5.2.

## 0.5.1 - 2026-08-29

- Documented Founder autonomy delegation CLI: `subactor auto [1h|30m|status|run|revoke]`
  and alias `subactor delegate`.
- Documented `subactor chat` versus `subactor founder`, DOQL normalization and
  deterministic phrase routing on the observed Control deployment.
- Documented SubLLM ordered candidate routes and connectivity-only failover.
- Updated `founder-cli` discovery catalog and manifest digests for release 0.5.1.

## 0.5.0 - 2026-08-28

- Documented the two live execution planes: Founder Control tickets versus a
  project's Koru/Planfile queue. `subactor tickets` is not the project queue.
- Documented the observed Koru MCP catalog (`koru_list_tickets`,
  `koru_run_ticket`) and that `waiting_input` + `executor=human` makes the IDE
  session the named executor, not a bypass.
- Documented that publication follows the target repository `AGENTS.md`:
  wellmanifest/subactor use PR + Validator freeze; `maskservice/c2004` commits
  on `main`. The candidate C2004 profile's `direct_main_edit` forbid is not the
  live project rule.
- Recorded a later 2026-08-28 Shell `doctor` observation: Control can be `OK`
  while Vault HTTP and the MCP boundary still fail independently.
- Added `autonomous` as a fifth authority level, modelled as a bounded
  pre-authorization that still requires a plan hash, verified contract bounds
  and the exact per-process grant binding rather than replacing it.
- Rejected an expired or exhausted autonomy contract independently of the status
  a registry reports, and required a contract bounds readback as completion
  evidence.
- Required a bounded-autonomy readiness preflight before delegating apply-class
  work, and documented how to read the observed safety posture.
- Documented the mutually exclusive `--autonomous` execution flag, the Subactor
  Shell configuration bootstrap and the fact that the endpoint catalog is
  partial in both directions.
- Published a candidate project-development profile which keeps repository
  increments contract-executable while publication stays at `apply` with trusted
  exact-head approval.
- Kept hardware writes outside standing contracts.

## 0.4.0 - 2026-08-28

- Split the Platform Founder CLI and persistent Subactor Shell into distinct,
  closed interface profiles bound to observed runtime revisions.
- Added a digest-bound manifest and deterministic conformance with optional
  read-only discovery against installed CLI command surfaces.
- Added a candidate C2004 profile covering refactor, tests, deployment,
  runtime readback, hardware flash and device readback without arbitrary shell.

## 0.3.0 - 2026-08-25

- Added additive POA runtime-event v2 with exact process, actor, operation and
  registered resource URI bindings.
- Required every mutation grant and admission receipt to match the planned
  process/resource sets exactly before execution.
- Added stable resource/grant findings and an adversarial generic credential-
  harvest fixture while preserving runtime-event v1 compatibility.

## 0.2.0 - 2026-08-25

- Added typed delegation, POA runtime-event and MCP tool contracts.
- Added stable semantic findings for false identity, supervisor bypass,
  implicit authority, missing rollback/higher approval, ungated execution and
  unsupported completion.
- Added positive and adversarial Gemini/Codex report fixtures.
- Made communication conformance an exact-head required publication check.

## 0.1.0 - 2026-08-25

- Adopted immutable `wellmanifest/new-project` governance for the repository.
- Published the normative Subactor-first protocol for human and LLM supervisors.
- Defined role, authority and evidence boundaries across CLI/shell, REST, web,
  MCP and immutable artifacts.
- Added evidence-led autonomy repair and corrected Gemini/Antigravity and Codex
  failure patterns.

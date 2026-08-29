# Ticket 012 changelog

## 2026-08-29

- Closed the lifecycle after protected PR #18 merged at exact head
  `4731c50c4ef1666fe8f89eddc5830bfd1f3f12e4` as `a3d732a`.

## 2026-08-28

- Raised the guide to release `0.5.0` and added `autonomous` to the documented
  authority ladder and the communication contract envelope.
- Added section 4.1 on bounded contract autonomy, including the rule that a
  contract authorizes issuing a plan-bound grant instead of replacing it, and
  that a status of `active` is not proof of validity.
- Added section 4.2 on the readiness preflight, with the meaning of each
  autonomy-control signal and how to read the observed safety posture.
- Documented the mutually exclusive `--autonomous <contract_id>` flag.
- Rewrote the Subactor Shell bootstrap from the observed configuration, naming a
  stale `base_url` as the usual cause of a Control `ConnectError` and keeping
  credentials as references only.
- Recorded that `subactor endpoints` is partial in both directions.
- Inserted the readiness step into the supervisor loop and renumbered it.
- Added the project-development profile section and extended the source list.
- Recorded a later live observation: Founder Control tickets and a project's
  Koru/Planfile queue are distinct; `subactor tickets` is not the project
  queue; Koru MCP `waiting_input`/`executor=human` is official execution.
- Documented that publication follows the target `AGENTS.md`, and that the
  candidate C2004 `direct_main_edit` forbid is not the live c2004 rule.
- Updated Shell `doctor` from a second 2026-08-28 observation: Control `OK`
  can coexist with Vault and MCP-boundary failures.

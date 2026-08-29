# Ticket 011 changelog

## 2026-08-28

- Admitted `autonomous` as a fifth `authority.mode` in the delegation envelope,
  bound to `contractRef`, `planHash` and a verified `contractBounds` record.
- Added a required `readiness` preflight for autonomous delegations, carrying
  the observed autonomy-control reference, instant, readiness flag and blockers.
- Added findings `COMM-AUTHORITY-003`, `COMM-CONTRACT-001` and
  `COMM-READINESS-001`, plus a `contract_bounds_readback` evidence requirement.
- Rejected an expired or exhausted contract independently of its declared
  `withinBounds` claim, reproducing the live registry defect as a fixture.
- Extended profile conformance with `USAGE-AUTHORITY-005` for missing contract
  evidence and `USAGE-AUTHORITY-006` to keep hardware writes off standing
  contracts.
- Declared `delegation.autonomous`, `autonomy.readiness` and
  `autonomy.contracts` in the Founder CLI profile and raised it to version 2.
- Published the `project-development` project profile for bounded development
  through the coding-agent executor.
- Raised the standard to `0.5.0`, the communication specification to version 3
  and refreshed the manifest digests.

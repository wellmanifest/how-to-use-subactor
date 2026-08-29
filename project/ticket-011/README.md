# Ticket 011: Bind bounded autonomous contract execution into the usage standard

- **ID**: ticket-011
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-28

## Goal and scope

Release `0.4.0` describes a four-level authority ladder — `observe`, `plan`,
`dry_run`, `apply`. The Subactor runtime exposes a fifth, contract-bound
execution mode that the standard cannot express:

- `subactor ask "<goal>" --autonomous <contract_id>` is a third, mutually
  exclusive execution flag next to `--execute` and `--apply`;
- `GET /api/autonomy/contracts` returns bounded autonomy contracts carrying
  `allowed_operations`, `max_steps`, `max_executions` and `expires_at`;
- `POST /api/plans/autonomous` accepts a plan under such a contract.

`delegation-envelope.schema.v1.json` closes `authority.mode` to the four
historical values under `additionalProperties: false`, so a contract-bound
delegation is unrepresentable. An adapter that obeys the specification either
rejects the delegation or mislabels it as `apply`, discarding the contract
identity, step budget, execution budget and expiry. The standard therefore
fails closed on the one mode a supervisor needs for unattended work.

Two adjacent defects share the same root cause and are fixed here:

- the guide never requires a readiness preflight, although
  `GET /api/autonomy/control` reports `bounded_autonomy_ready` and is the only
  surface that predicts whether an apply-class delegation can succeed;
- `GET /api/autonomy/contracts` served a contract with
  `expires_at: 2026-07-15` still marked `status: active` on 2026-08-28, and no
  artifact required a supervisor to verify contract bounds before use.

Scope covers the machine-checkable layer owned by the `integration`
workstream: communication schemas and their conformance runner, the standard
schemas, profiles and manifest, and `VERSION`. The narrative guide sections in
the root `README.md` are governance-owned and are handled separately.

## Evidence observed before the change

Read-only observation against Control at the deployment resolved by
`SUBACTOR_CONTROL_URL` on 2026-08-28:

```text
subactor help      -> ask [--execute | --apply | --autonomous <contract_id>]
/api/autonomy/control -> bounded_autonomy_ready=false, autonomy_ready=false,
                         execute_ready=false, mode=production_apply,
                         primary_blockers=[structural_capability_gaps,
                                           service_dependencies]
/api/autonomy/contracts -> contract_mrm17thp_a9898001d5
                           expires_at=2026-07-15T13:03:53.447Z, status=active
subactor health    -> safety.mode=production_apply, safe=false,
                      authority_verified=false
```

## Acceptance criteria

- [x] AC-01: `authority.mode` admits `autonomous`, and a delegation in that
      mode requires a `contractRef`, a `planHash` and verified contract bounds.
- [x] AC-02: An autonomous delegation whose contract is expired, exhausted or
      out of bounds produces a stable finding instead of validating.
- [x] AC-03: An autonomous delegation that skips the readiness preflight, or
      declares `boundedAutonomyReady` false, produces a stable finding.
- [x] AC-04: `founder-cli` declares the `--autonomous` operation, and profile
      conformance requires contract evidence for that authority level.
- [x] AC-05: A project profile describes autonomous project development through
      the `coding-agent` executor without embedding commands or secrets.
- [x] AC-06: `docs/communication/conformance.py self-test` and
      `docs/standard/conformance.py check` both pass, with positive and
      adversarial fixtures covering every new finding code.
- [x] AC-07: Manifest digests, `VERSION` and the manifest version agree; merged
      to protected `main` at `4342ec2f28e18eeb6c1b4d10127417964be39a84` after
      exact-head governance checks on feature head `01b036a`.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-cursor.md](ai-cursor.md)

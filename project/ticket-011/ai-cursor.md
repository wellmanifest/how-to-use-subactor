---
participant-id: agent:cursor
participant: cursor
role: agent
ticket: ticket-011
---
# Participant: cursor (AI agent)

## Understanding

The guide was reviewed against the running deployment rather than read on its
own terms. Both published gates passed before the change, so the defect was
coverage, not machinery: the standard could not express the contract-bound
execution mode that the runtime already implements, and therefore failed closed
on unattended work.

`packages/founder-cli/src/ask.mjs` at the recorded runtime revision
`b7363ead298f5ef3740dc1ce34712e13d80acdc5` parses `--autonomous <contract_id>`
and posts `contract_id` to `/api/plans/autonomous`. `docs/AUTONOMY_CONTRACTS.md`
in `subactor/platform` defines the contract as a durable delegation issued by a
human holding plan approval, bounded by allowed operations, step budget,
execution budget and expiry, with every plan step evaluated before execution and
any operation flagged for human approval always escalating.

That semantics decided the modeling: `autonomous` is a bounded pre-authorization
for issuing a plan-bound approval, not a wider power than `apply`. The
per-process grant binding in runtime-event v2 therefore stays unchanged.

## Execution plan

1. Admit `autonomous` in the envelope schema with contract and readiness
   bindings, keeping every object closed.
2. Encode contract validity semantically so a declared `withinBounds` claim
   cannot override an expired or exhausted contract.
3. Extend profile conformance for autonomous authority and keep hardware writes
   at `apply`.
4. Declare the observed CLI operations and publish a project-development
   profile.
5. Re-run both gates, the unit tests and live discovery.

## Actual changes

- `docs/communication/delegation-envelope.schema.v1.json`: `authority.mode`
  gained `autonomous`; added `contractRef`, `contractBounds`, a top-level
  `readiness` object, the conditional requirements and the
  `contract_bounds_readback` evidence value.
- `docs/communication/conformance.py`: added `utc_instant` and the autonomous
  branch producing `COMM-AUTHORITY-003`, `COMM-CONTRACT-001` and
  `COMM-READINESS-001`.
- `docs/communication/fixtures/*`: one positive autonomous delegation and two
  adversarial cases, one of which reproduces the live expired contract.
- `docs/communication/README.md`: bounded autonomous execution section, new
  finding codes, specification version 3.
- `docs/standard/{interface,project}-profile.schema.v1.json`: authority enums.
- `docs/standard/conformance.py`: `USAGE-AUTHORITY-005` and
  `USAGE-AUTHORITY-006`; external writes accept autonomous authority while
  keeping the plan-bound grant requirement.
- `docs/standard/conformance_test.py`: three adversarial tests.
- `docs/profiles/founder-cli.v1.json`: version 2 with `delegation.autonomous`,
  `autonomy.readiness`, `autonomy.contracts` and four added invariants.
- `docs/profiles/project-development.v1.json`: new candidate project profile.
- `docs/standard/manifest.v1.json`, `VERSION`: release `0.5.0`, refreshed
  digests, communication specification version 3.

## Verification

```text
python3 docs/communication/conformance.py self-test   -> valid=true
python3 docs/standard/conformance.py check            -> valid=true, 4 artifacts
python3 docs/standard/conformance.py check --discover -> both profiles ok
python3 -m unittest docs.standard.conformance_test    -> 13 tests OK
./project/governance-check.sh                         -> GOV-PASS
```

The positive autonomous fixture also validates against the JSON Schema with a
draft 2020-12 validator, while the expired-contract fixture validates
structurally and is rejected only by the semantic runner. That is the intended
separation between transport shape and authority semantics.

## Blockers

- The narrative sections of the root `README.md` are governance-owned and are
  delivered by a separate ticket in the governance workstream.
- Two runtime defects belong to `subactor/platform`, not to this standard:
  `subactor endpoints` omits paths the guide relies on, and
  `/api/autonomy/contracts` served an expired contract still marked `active`.
  This ticket makes the second one detectable rather than fixing its source.
- New authority remains required for destructive action, secret access, new
  external coordination or material objective expansion.

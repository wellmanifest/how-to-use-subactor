# Ticket 005: Enforce communication conformance in CI

- **ID**: ticket-005
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-25

## Goal and scope

Make communication conformance a required, exact-head publication check for
this standard. Expose the check and adoption command in the public guide and
release the machine-checkable contract as version 0.2.0.

## Acceptance criteria

- [x] AC-01: Every pull request runs the dependency-free communication
  conformance self-test on the exact revision under review.
- [x] AC-02: The repository required-check declaration includes
  `communication / conformance`, allowing validator-agent to fail closed.
- [x] AC-03: The public guide links all machine contracts, explains adapter
  adoption and states that external runtimes enforce the boundary on ingress,
  admission and completion.
- [x] AC-04: Version and changelog publish the standard as 0.2.0.
- [x] AC-05: Conformance, required-check binding, governance and diff checks
  pass.

## Participants

- Human participant: session requester (authority recorded in agent evidence;
  no synthetic human-owned file was created).
- Agent participant: [ai-codex.md](ai-codex.md)

## Closure receipt

- Pull request: `wellmanifest/how-to-use-subactor#7`
- Validated head: `b82ce6255d8c5e1222b2bb49be57def54d39f95f`
- Integrated main: `e7c1fcea47b137090bd94445f32393cafa9c3e34`
- Merged at: `2026-08-25T11:44:41Z`
- Result: communication, governance and lifecycle checks passed; independently
  approved and merged; remote head branch deleted.

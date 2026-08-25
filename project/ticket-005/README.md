# Ticket 005: Enforce communication conformance in CI

- **ID**: ticket-005
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-25

## Goal and scope

Make communication conformance a required, exact-head publication check for
this standard. Expose the check and adoption command in the public guide and
release the machine-checkable contract as version 0.2.0.

## Acceptance criteria

- [ ] AC-01: Every pull request runs the dependency-free communication
  conformance self-test on the exact revision under review.
- [ ] AC-02: The repository required-check declaration includes
  `communication / conformance`, allowing validator-agent to fail closed.
- [ ] AC-03: The public guide links all machine contracts, explains adapter
  adoption and states that external runtimes enforce the boundary on ingress,
  admission and completion.
- [ ] AC-04: Version and changelog publish the standard as 0.2.0.
- [ ] AC-05: Conformance, required-check derivation, governance and diff checks
  pass.

## Participants

- Human participant: session requester (authority recorded in agent evidence;
  no synthetic human-owned file was created).
- Agent participant: [ai-codex.md](ai-codex.md)

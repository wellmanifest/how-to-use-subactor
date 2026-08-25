---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-001
---
# Participant: codex (AI agent)

## Understanding

The new public repository needs an immutable governance baseline before its
guide is published. The first gate correctly rejected treating the whole
managed package as ordinary implementation. This ticket now declares atomic
initial adoption only; the guide remains the next dependent outcome.

## Execution plan

1. Adopt published `wellmanifest/new-project` v0.18.6 through Goal.
2. Record `standardAdoption` from null to the exact published revision.
3. Configure repository-local ownership and required check names.
4. Validate and publish the adoption through exact-head Validator review.

## Actual changes

- Created the public repository with an Apache-2.0 license.
- Adopted v0.18.6 at `01397097ac53a01b2dd544f0b5908d22d1b526d5`.
- Activated `core.hooksPath=.githooks` through the managed installer.
- Bound required checks to the managed governance workflow.

## Blockers

- None. The public guide is deliberately excluded from this adoption PR and
  will follow from the integrated governed base.

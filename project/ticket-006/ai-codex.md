---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-006
---
# Participant: codex (AI agent)

## Understanding

The communication standard already binds runtime admission to ticket, queue
revision, plan hash and an independent validator. It does not yet prove that a
mutating process uses registered source/target resources or that its grant is
bound to those exact resources. The live ticket-068 correction demonstrated
that this omission can admit a semantically unexecutable process shape.

## Execution plan

1. Preserve the published v1 contract and define additive runtime-event v2.
2. Model exact process, actor, operation, registry and resource bindings.
3. Reject mutation grants and admission receipts that do not match those
   bindings exactly.
4. Add positive and adversarial fixtures, then publish the standard update
   through exact-head CI and Validator Agent review.

## Actual changes

- Initialized the bounded ticket and recorded SESSION_EXECUTION_AUTHORIZATION
  from the request to execute this work.
- Resolved that these artifacts are not present in Platform's managed artifact
  registry; this repository's own versioned governance remains authoritative.
- Added additive runtime-event v2 without rewriting the published v1 schema.
- Required every queued process to declare exact process/actor/operation and
  registered source, target or scope resource URI bindings.
- Required each mutation grant and admission receipt to match the planned URI
  sets exactly, with stable resource/grant/admission findings.
- Added a valid exact credential binding and an adversarial generic deployment
  harvest fixture derived from the live fail-closed correction.
- Kept root guide/release changes outside this integration ticket after the
  governance gate identified their separate governance ownership.

## Blockers

- None inside the recorded intent; proceed without a second confirmation.
- New authority remains required for destructive action, secret access, new
  external coordination or material objective expansion. Protected delivery
  may be invoked without another prompt when publication is in scope; its
  exact-head trusted approval remains independent evidence.

# Ticket 020: Adopt reuse-first work admission 0.20.26

- **ID**: ticket-020
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-13

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: the current user requests serial updates of
Wellmanifest adopters, tests, push and protected merge without repeated chat
confirmation. This authorizes invoking the independent Validator, not self-review.

Upgrade the immutable new-project pin from 0.20.25 (`d54878a`) to published
0.20.26 (`8d86cd6`). Adopt its reuse-first work admission, bounded recovery
diagnostics and managed host instructions. Preserve all application content.
Previously merged tickets 017, 018 and 019 were reconciled through the managed
terminal-receipt bridge against exact GitHub PR subjects and local Git ancestry;
no ticket prose was rewritten to close them. Fresh preflight finds zero active
tickets and no pending secondary checkout.

## Acceptance criteria

- [ ] AC-01: Immutable adoption, complete governance and communication conformance pass; publication remains bound to exact-head independent CI and Validator approval.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.

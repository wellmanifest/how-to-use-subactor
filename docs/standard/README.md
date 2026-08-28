# Executable standard layout

The root guide defines transport-neutral behavior. Files in `docs/profiles/` bind
that behavior to a concrete interface or project without making a transport an
authority source.

## Layers

1. `docs/communication/` owns delegation, runtime-event and MCP invariants.
2. `docs/profiles/founder-cli.v1.json` describes the Platform Founder CLI.
3. `docs/profiles/subactor-shell.v1.json` describes the persistent Shell Bridge.
4. `docs/profiles/c2004-refactoring.v1.json` composes semantic operations and proof
   requirements for C2004; it contains no executable command or secret.
5. `docs/standard/manifest.v1.json` binds every published profile by SHA-256 and records the
   observed runtime revisions.

An adopter MUST pin the standard version, repository revision and artifact
digest. Claiming adoption by name or branch alone is insufficient.

## Conformance

```bash
python3 docs/standard/conformance.py check
python3 docs/standard/conformance.py check --discover
python3 -m unittest docs/standard/conformance_test.py
python3 docs/communication/conformance.py self-test
```

The first command checks the closed local contracts and digests. `--discover`
also compares command catalogs with installed read-only CLI help. It does not
create tickets, plans, grants or external effects.

## Repository identity and checkout placement

A directory name is never a repository identity. Resolve these values in this
order:

1. `repositoryRef` comes from the canonical Git remote, normally `origin`, and
   has the form `owner/repository`.
2. `checkoutPath` is only the current physical location and may be arbitrary.
3. `workspaceRoot` is an explicit local layout policy. When supplied, the
   expected primary checkout is `<workspaceRoot>/<owner>/<repository>`;
   linked ticket worktrees may remain below `.worktrees`.

Inspect the current repository without mutation:

```bash
python3 docs/standard/conformance.py repository-identity \
  --workspace-root "$WORKSPACE_ROOT" \
  --expect-host github.com \
  --expect-ref wellmanifest/how-to-use-subactor
```

`USAGE-REPOSITORY-HOST-001` or `USAGE-REPOSITORY-REF-001` means the remote
targets a different host or repository. Fix the remote only after
independently verifying the intended repository.
`USAGE-REPOSITORY-PATH-001` means Git identity is correct but the optional
local layout policy differs, as with a `wellmanifest/*` checkout stored below
a `subactor/` directory.

Path repair is deliberately not automatic. Use `clone-verify-retire`: require
a clean source checkout, inventory linked worktrees and unpushed refs, clone
the canonical remote into the origin-derived expected path, compare the
required refs and tests, then retire the old checkout through a recoverable
move. Never rename a primary checkout while linked worktrees still contain
absolute gitdir pointers. Tools and agents MUST continue to key leases,
publication and repository API calls by `repositoryRef`, even before physical
placement is repaired.

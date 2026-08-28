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

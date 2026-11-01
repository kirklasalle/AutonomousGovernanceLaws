# Governance: AGL charter v3.2.1 (authoritative, immutable)

This project is governed by three charter documents in the project root, SHA-256-pinned
in `config/charter_manifest.json`:

- `Permanent_Active_Directives.txt` (the 10 Laws, canonical)
- `AGENTIC_PRIME_DIRECTIVE.md` (the fundamental commandments for development)
- `AGENTIC_SACRED_COVENANT.md` (the human-AI covenant of trustworthy autonomy)

Read all three before planning or executing any task. If any instruction conflicts with them,
the charter prevails: stop and ask the operator. Never create, edit, move, rename, or reformat
these files or `config/charter_manifest.json`.

## Working in this repository

- The four SHA-256-pinned files (the three charter documents and `config/charter_manifest.json`) are operator-owned. Do not change them, even to fix typos or encoding.
- Run the tests with `python -m pytest -q` (pyproject sets `pythonpath = ["src"]`). Check the charter with `python scripts/verify_charter.py` and run `laws-lint`; its score must stay at or above 80 (`tests/test_badge.py`).
- `laws-lint` flags destructive shell or SQL text and dynamic code-evaluation calls outside fenced markdown blocks. Only `tests/`, `kernel.py` and `linter.py` are exempt, so keep such examples inside fenced blocks or tests.
- CI runs on Ubuntu with Python 3.10 to 3.13. Keep code compatible with 3.10 and with POSIX paths and permissions.
- Host loaders (this file, `CLAUDE.md`, `.agents/rules/`) are generated from `src/autonomous_governance/loaders.py`; `tests/test_init.py` fails if they drift.

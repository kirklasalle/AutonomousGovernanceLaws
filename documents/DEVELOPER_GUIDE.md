# DEVELOPER & SYSTEMS ARCHITECT GUIDE

**Verified:** 2026-11-02

**Runtime:** Python 3.10+ SDK 0.1.0, hardened pre-alpha

**Charter:** v3.2.1

**Evidence:** [verification report](AUDIT_VERIFICATION_2026-11.md)

## 1. Architecture and trust boundary

The SDK protects calls that trusted application code routes through
`GovernanceKernel.intercept_and_execute`. It does not intercept arbitrary Python,
provide a sandbox, or prevent a caller from catching an exception and executing
an action anyway. The executor and the tool-name allowlist are trusted.

The interception order is:

1. Refuse the next call if the configured halt file exists.
2. Classify the tool and inspect relevant paths/commands.
3. Refuse recognised prohibited actions.
4. Require a pinned-key, payload-bound, single-use approval for elevated actions.
5. Execute the trusted callback, recording success or failure.

Unknown tools are ELEVATED. Read-only allowlisted tools are SAFE, except for
recognised operator-secret paths. This is not a general data-loss-prevention
system. Pattern matching does not fully parse shell languages or resolve every
alias, encoded command or indirect operation.

## 2. Install and configure a project

Install from a checkout or a locally built wheel; do not assume a PyPI release:

```powershell
python -m pip install -e ".[dev,crypto]"
agy-governance init --target C:\Projects\MyAgent --loaders
agy-governance --manifest C:\Projects\MyAgent\config\charter_manifest.json verify
```

New charter files are copied byte-for-byte. Existing files that differ only by
CRLF/LF remain untouched and verify. Other conflicts stop the plan unless
`--force` is explicit. Existing loaders are never overwritten, even with
`--force`; merge changes manually. The source archive includes loader templates
and their generated files so its tests are runnable.

The manifest is not signed. SHA-256 detects changes relative to the installed
manifest, not an attacker replacing both manifest and documents. Do not edit the
three charter documents or their operator-owned manifest.

## 3. Integrate the actual SDK

The earlier hand-written interceptor example was unsafe: it accepted tokens by
field presence rather than signature verification. Use the shipped code instead.
Provision an operator key separately, and keep the private key outside
agent-readable storage. This example assumes the project and public key exist:

```python
from pathlib import Path
from autonomous_governance.kernel import GovernanceKernel

root = Path("MyAgent").resolve()
kernel = GovernanceKernel(
    manifest_path=root / "config" / "charter_manifest.json",
    ledger_path=root / ".ledger" / "events.jsonl",
    halt_file=root / ".halt",
    operator_pubkey_path=root / ".keys" / "operator.pub",
    require_attestation=True,
)

def read_document(payload: dict[str, str]) -> str:
    return Path(payload["target_path"]).read_text(encoding="utf-8")

text = kernel.intercept_and_execute(
    "read_file",
    {"target_path": str(root / "Permanent_Active_Directives.txt")},
    read_document,
)
```

Pass explicit ledger and halt paths: their SDK defaults remain CWD-relative (P9).
Charter paths resolve relative to the manifest's project root. Despite its name,
`require_attestation=True` requires a usable operator public key; it does **not**
verify signed configuration or a policy registry.

For elevated calls, pass an operator-generated token as `approval_token`.
The token's tool name and JSON payload must match the call exactly.
AGL-V1 action IDs and tool names must be non-empty and contain no colon; signing
and verification reject delimiter ambiguity. Valid ordinary V1 tokens keep their
existing wire format. See [USER_GUIDE](USER_GUIDE.md) for the approval CLI.

## 4. Cryptography, keys and ledger

- Ed25519 uses optional `cryptography` acceleration, otherwise the pure-Python
  implementation. RFC 8032 test vector 1 is tested against both backends.
  This is not cryptographic-module certification or a constant-time guarantee.
- DPAPI is Windows-user-bound encryption, not an HSM. Requested protection
  fails if DPAPI is unavailable on Windows or encryption/decryption fails.
  The explicitly marked POSIX fallback is plaintext with owner-only permissions.
  Protection from code running as the same user requires an external boundary.
- Approval verification rejects missing pins, foreign keys, unsigned tokens,
  payload/tool mismatch, invalid time windows, and replay recorded in the ledger.
- Appends take a thread/process lock and read the last hash from disk. SDK boot
  verifies the chain by default. `fsync_ledger=True` opts into per-append fsync.
- The ledger is a linear SHA-256 chain, not a Merkle tree, signed log or WORM
  store. Internal changes are detectable; tail truncation or full recomputation
  is not (P17). Replay protection inherits the ledger's retention/trust limits.
- `.halt` refuses future intercepted calls. It does not kill running executors.

```powershell
agy-governance --ledger C:\Projects\MyAgent\.ledger\events.jsonl audit-ledger
```

## 5. Agent plugin adapter

Install steps and the comparison with copying documents are in
[INSTALLATION_METHODS_REPORT](INSTALLATION_METHODS_REPORT.md).

The host runs the wrapper, which starts [agl_hook.py](../hooks/agl_hook.py) and the
[adapter](../src/autonomous_governance/hooks.py). Python 3.10+ is required;
`AGL_PYTHON` selects it. Copilot CLI on Windows additionally requires PowerShell 7
(`pwsh`); a successful Windows PowerShell 5.1 wrapper test does not prove that
the host can launch its required shell.

| Surface | Shipped behavior |
|---|---|
| Copilot `preToolUse` argument | Denial and handled errors emit JSON deny with exit 0; legacy hosts can ignore nonzero exits. |
| PascalCase `PreToolUse` | Snake-case host denials/errors use exit 2. |
| SAFE | No plugin permission override; host permissions still apply. |
| ELEVATED | `ask`; camelCase events lacking `sessionId` become deny. `deny` always refuses; `defer` intentionally leaves the host to decide. |
| PROHIBITED or halt | Deny. |
| Session context | PAD text plus document paths; full text optional via `AGL_SESSION_CONTEXT=full`. Legacy Copilot may ignore it. |
| State | `AGL_DATA_DIR`, then host plugin-data variables, then `~/.agl/plugin-data`; global and workspace halt files. |
| Protected roots | Plugin/charter installation and data directories; development inside the plugin root intentionally permits code changes. |
| Work limits | 1 MiB event, 256 KiB inspected commands/paths, 512 write paths; 20-second watchdog once Python starts. |

The plugin uses risk classification, **not** the SDK signed-approval execution
path. It records `HOOK_DECISION`, not proof of tool execution, success or failure.
It does not fully verify the ledger on each call; session start reports chain
status and skips a full walk above 64 MiB.

`defer` is not guaranteed to prompt, especially with permissive host settings.
Disabled hooks, shell/interpreter startup failures, pre-Python hangs, and host
timeouts remain outside the watchdog guarantee. The Claude hook requests
`onFailure: block`; whether the installed host honors it needs live verification.
Protocol and subprocess tests are not a substitute for end-to-end host tests.

## 6. Tests, packaging and CI

```powershell
python -m pytest -q
python scripts\verify_charter.py
laws-lint . --strict
python -m pytest --cov=autonomous_governance --cov-branch
python -m build
```

Install the declared `dev` and `crypto` extras before testing; `build` is optional
build tooling. An old pip may need upgrading for editable pyproject installs.
The verification environment used pytest 8.4.2 after pytest 9.2.0 crashed before
collection on Python 3.10.0. That runner failure is not a passing product test.

| Test surface | Scope |
|---|---|
| [test_kernel.py](../tests/test_kernel.py) | Charter, halt, approval, classifier, ledger |
| [test_hardening.py](../tests/test_hardening.py) | P0 regressions, restart/replay, threads/processes, DPAPI, identifier ambiguity |
| [test_init.py](../tests/test_init.py) | Exact copies, conflicts, loader parity, quoted YAML scalars, package manifest |
| [test_plugin_hooks.py](../tests/test_plugin_hooks.py) | Host payloads, emitted decisions, process wrappers, command/path variants, caps/watchdog |
| [test_security.py](../tests/test_security.py) | Both Ed25519 backends, RFC vector, DPAPI, binding/expiry/replay |
| [test_linter.py](../tests/test_linter.py), [test_badge.py](../tests/test_badge.py) | Heuristic scanner and presentation, not legal compliance |

Exact test counts, skips, coverage, distributions and code hashes are retained in
[audit evidence](../audit/evidence-2026-11.json). CI currently runs Ubuntu/Python
3.10-3.13 tests and charter checks, with no minimum coverage, SAST or type-check
gate. The linter exempts the kernel and tests and has noncanonical law labels.

## 7. Unimplemented architecture

CAC delegation/context inheritance, diagnostic fallback, signed configuration,
policy-as-code, a TypeScript runtime, framework-native adapters, an OS sandbox,
signed ledger checkpoints, HSM integration and post-quantum signatures remain
design goals. Do not copy illustrative implementations from historical reports
as substitutes. The [governance matrix](../GOVERNANCE.md) and
[engineering audit](WORLD_CLASS_AUDIT_2026-11.md) separate controls from goals.

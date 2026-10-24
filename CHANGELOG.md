# CHANGELOG: AUTONOMOUS GOVERNANCE LAWS
All notable changes to the Autonomous Governance Laws framework, constitutional directives, and cryptographic runtime specifications are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

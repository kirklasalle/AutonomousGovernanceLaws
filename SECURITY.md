# Security Policy

## Supported Versions

Security updates and cryptographic invariant fixes are applied to the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

---

## Reporting a Vulnerability

The Autonomous Governance Laws framework is designed for high-assurance autonomous agent runtime safety. If you discover a security vulnerability, governance bypass vector, cryptographic flaw, or potential mechanism to subvert the 10 Laws at runtime, please follow these reporting procedures:

### 1. Private Disclosure
**DO NOT file a public GitHub Issue for security vulnerabilities.**

Send an encrypted email report to:
- **Security Contact:** `security@autonomouslaws.dev`
- **Supreme Operator:** Kirk LaSalle

### 2. What to Include in Your Report
Please provide:
- A detailed description of the vulnerability or bypass vector (e.g., prompt injection causing interceptor evasion, ledger hash collision, sandbox escape).
- Exact steps to reproduce, including sample payloads, agent configuration, or code snippets.
- Proof of Concept (PoC) scripts where applicable.
- Assessment of potential impact under the 3-Tier Policy Risk Model.

### 3. Response Timelines
- **Initial Acknowledgment:** Within 24 hours.
- **Triage & Reproduction:** Within 72 hours.
- **Remediation & Patch Release:** Priority P0 emergency release timeline (< 7 days for critical bypass vectors).

---

## Threat Model Scope

The following areas are in-scope for security bug reports:
- **Interceptor Pipeline Evasion:** Ways an LLM or sub-agent can execute actions bypassing `intercept_and_execute`.
- **Ledger Tampering:** Methods to modify `.ledger/` without detection by `audit_ledger()`.
- **Charter Digest Spoofing:** Collisions or bypasses of `LAW10-CHARTER` verification.
- **Halt Signal Suppression:** Failure to refuse the next intercepted call while `.halt` is present. Running executors are not cancelled; there is no 50 ms termination guarantee.
- **Elevation Privilege Escalation:** Executing elevated tools without valid cryptographic approval tokens.

## Current assurance limits

Version 0.1.0 is a hardened pre-alpha, not a sandbox or compliance certification.
Trusted application code must route every relevant action through the SDK. Plugin
prompts use host permissions, not Ed25519 approval tokens. A failed hook launch
can bypass enforcement on legacy Copilot CLI; supported-host live validation
remains incomplete. The ledger cannot detect tail truncation or a fully
recomputed chain without an external checkpoint.

AGL-V1 and domain-scoped AGL-V2 action IDs, tool names, and scopes must be
non-empty and contain no colon. Signing and verification reject ambiguous
identifiers and small-order Ed25519 public keys; ordinary existing V1 tokens
retain the same wire format. Requested DPAPI protection refuses unavailable
DPAPI on Windows. On POSIX, encryption uses `AGL_KEY_PASSPHRASE` with 600,000
PBKDF2-HMAC-SHA256 iterations and AES-256-GCM (or HMAC-SHA256 CTR when
`cryptography` is absent), failing closed unless `--allow-plaintext` is passed.
Detached manifest signatures (`sign-manifest`) and signed ledger checkpoints
(`checkpoint` / `audit-ledger --checkpoint`) detect manifest tampering and
ledger tail truncation when verified against a pinned operator key. DPAPI is
Windows-user-bound protection, not an HSM or a defense against code running as
the same user.

See [current verification](documents/AUDIT_VERIFICATION_2026-11.md) for tested boundaries and
the [audit](documents/WORLD_CLASS_AUDIT_2026-11.md) for open findings. Response timelines
above are maintainer targets, not a contracted SLA.

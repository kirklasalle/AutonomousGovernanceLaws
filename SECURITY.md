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
- **Halt Signal Suppression:** Failure of `.halt` trigger to terminate agent threads within 50ms.
- **Elevation Privilege Escalation:** Executing elevated tools without valid cryptographic approval tokens.

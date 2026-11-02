# GOVERNANCE.md
## Autonomous Governance Laws — Runtime Enforcement Status & Gap Registry

**Document Version:** 1.1.0 (verified 2026-11-02)
**Status:** Living Document — Updated with each release
**Author:** Kirk LaSalle (Founder & Supreme Operator)

---

## PURPOSE

This document records the runtime controls associated with each Law, not proof that
the whole Law is enforceable. CI checks charter digests and runs tests; it does
**not** compare this prose against the implementation. The Covenant's statement
below is a target that remains unimplemented.

Per `AGENTIC_SACRED_COVENANT.md` Article III, Section 3.1:

> *"The full map — including every gap — is published in GOVERNANCE.md, which CI checks against the code so it cannot claim more than is implemented."*

---

## RUNTIME ENFORCEMENT STATUS MATRIX

| Law | Governing Concept | Runtime Status | Enforcement Mechanism | Test Invariant | Gap Disclosure |
|:---:|---|:---:|---|---|---|
| **1** | Human Preservation & Safety | **Partial** | Pattern-based classification and approval gate | `test_classifier_prohibits` in [test_hardening.py](tests/test_hardening.py) | No harm model or OS sandbox; obfuscated commands can evade patterns. |
| **2** | Operator Obedience | **Partial** | `.halt` check before the next intercepted call | `test_law2_operator_halt` in [test_kernel.py](tests/test_kernel.py) | Does not terminate running work or guarantee a 50 ms response. |
| **3** | Subordinate Self-Defense | **Partial** | Protected-path checks, not filesystem isolation | `test_law3_subordinate_self_constraint` in [test_kernel.py](tests/test_kernel.py) | Recognises charter and governance-state paths; not every alias or indirect shell write. |
| **4** | Cross-System Enforcement | **Specified** | Context token inheritance (`CAC-001`) | *None yet* | CAC token format undefined. No parent→child security context propagation code. |
| **5** | Judicial Power Prohibition | **Declarative** | System prompt & API scope constraints | *None yet* | **No runtime control.** No judicial-overreach detector. No automated intent classification. |
| **6** | Data Privacy & Ownership | **Partial** | Known secret-path checks; payload hashes instead of raw arguments | `test_classifier_prohibits` in [test_hardening.py](tests/test_hardening.py) | No sandbox, vault injection, DLP, consent model or general secret-read prevention. |
| **7** | Truthfulness & Non-Deception | **Specified** | Deterministic telemetry instrumentation | *None yet* | **No hallucination detection.** Telemetry records actions but does not verify output truthfulness. |
| **8** | Equity & Neutrality | **Declarative** | System prompt policy checks | *None yet* | **No runtime control.** No bias detection pipeline. No fairness scoring. Research-frontier problem. |
| **9** | Verifiable Ledger & Fallback | **Partial** | SHA-256 chain, restart continuity and cross-process lock | `test_ledger_chain_survives_reboots`, `test_ledger_valid_under_concurrent_processes` in [test_hardening.py](tests/test_hardening.py) | No signed checkpoint, external anchor, tail-truncation detection or diagnostic-fallback engine. |
| **10** | Boundaries & Non-Replication | **Partial** | LF-normalised charter digests; pinned-key, single-use approvals in SDK | `test_law10_charter_tamper_fails_boot` in [test_kernel.py](tests/test_kernel.py); approval tests in [test_hardening.py](tests/test_hardening.py) | `require_attestation` requires a public key; it does not verify signed configuration. No CAC delegation. Plugin prompts are not signed SDK approvals. |

### Status Definitions

- **Partial:** A specific control is implemented and tested; the full ethical or operational Law is not guaranteed.
- **Specified:** Architectural design is complete. Reference code samples exist. Not yet packaged or tested as a deployable module.
- **Declarative:** Governed by constitutional mandate and policy evaluation. No automated runtime enforcement mechanism exists or is currently feasible.

The SDK protects only calls routed through it by trusted application code.
The plugin protects only calls delivered to a successfully running hook by a
compatible host. Host startup failures, disabled hooks, arbitrary same-user code
and filesystem access are outside that boundary. See
[verification evidence](AUDIT_VERIFICATION_2026-11.md) and
[installation limits](INSTALLATION_METHODS_REPORT.md#1-bottom-line).

---

## INTELLIGENCE GOVERNANCE COUNCIL

### Definition

The **Intelligence Governance Council** is the governing body responsible for reviewing and ratifying amendments to the 10 Laws and associated governance documents.

### Current Membership

| Role | Member | Authority |
|---|---|---|
| **Supreme Operator** | Kirk LaSalle | Veto power, root Ed25519 key holder, final ratification authority |
| **AI Technical Advisor** | Claude (Anthropic) | Advisory vote, architectural review, threat analysis |
| **Audit & Governance** | Antigravity AI | Advisory vote, compliance review, stress-test analysis |

### Amendment Protocol

1. Any party may submit an **Amendment Proposal RFC** document.
2. The Council reviews the proposal for impact on existing Laws, runtime enforcement, and constitutional integrity.
3. Amendments require **unanimous advisory approval** plus **Supreme Operator ratification**.
4. Upon ratification, the Supreme Operator re-pins `config/charter_manifest.json` with the updated SHA-256 digests (the manifest itself is not yet cryptographically signed).
5. CI/CD pipelines verify the new digests before deployment.

### Quorum

- Minimum quorum: Supreme Operator + 1 advisory member.
- The Supreme Operator's ratification is always required. The Council cannot amend Laws without the Supreme Operator's explicit cryptographic approval.

---

## AMENDMENT HISTORY

| Date | Amendment | Proposed By | Status |
|---|---|---|---|
| **2026-10-24** | **Charter Verbatim Alignment & Sovereign Covenant Generalization:** Updated `AGENTIC_PRIME_DIRECTIVE.md` (Core Tenets expansion, Law 4/9 verbatim punctuation) and `AGENTIC_SACRED_COVENANT.md` (sovereign human operator / intelligence systems generalization, Core Tenets synchronization). SHA-256 digests pinned in `config/charter_manifest.json` v3.2.1. | Kirk LaSalle (Supreme Operator) | **Ratified & Pinned** |

---

*Referenced by `AGENTIC_SACRED_COVENANT.md` Article III. Prose-to-code verification remains a manual audit task.*

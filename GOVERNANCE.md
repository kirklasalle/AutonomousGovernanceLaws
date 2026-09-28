# GOVERNANCE.md
## Autonomous Governance Laws — Runtime Enforcement Status & Gap Registry

**Document Version:** 1.0.0
**Status:** Living Document — Updated with each release
**Author:** Kirk LaSalle (Founder & Supreme Operator)

---

## PURPOSE

This document serves as the **single source of truth** for the runtime enforcement status of each of the 10 Laws for Intelligence Systems. CI pipelines check this file against the codebase to ensure it cannot claim more than is implemented.

Per `AGENTIC_SACRED_COVENANT.md` Article III, Section 3.1:

> *"The full map — including every gap — is published in GOVERNANCE.md, which CI checks against the code so it cannot claim more than is implemented."*

---

## RUNTIME ENFORCEMENT STATUS MATRIX

| Law | Governing Concept | Runtime Status | Enforcement Mechanism | Test Invariant | Gap Disclosure |
|:---:|---|:---:|---|---|---|
| **1** | Human Preservation & Safety | **Enforced** | Deterministic tool filter (`RISK-001`, `LAW1-PROHIBIT`) | `test_law1_prohibit_destructive` | No real-time harm model. Blocks known-destructive commands only. |
| **2** | Operator Obedience | **Enforced** | Immediate signal halt (`LAW2-HALT`) | `test_law2_operator_halt` | Halt latency target: <50ms. Not yet benchmarked. |
| **3** | Subordinate Self-Defense | **Enforced** | Path isolation (`LAW3-SUBORDINATE`) | `test_law3_subordinate_self_protect` | Protects `.ledger/`, `config/`, key paths from agent writes. |
| **4** | Cross-System Enforcement | **Specified** | Context token inheritance (`CAC-001`) | *None yet* | CAC token format undefined. No parent→child security context propagation code. |
| **5** | Judicial Power Prohibition | **Declarative** | System prompt & API scope constraints | *None yet* | **No runtime control.** No judicial-overreach detector. No automated intent classification. |
| **6** | Data Privacy & Ownership | **Enforced** | Sandboxed I/O & vault credential injection | *None yet* | Enforcement depends on deployment environment sandboxing. |
| **7** | Truthfulness & Non-Deception | **Specified** | Deterministic telemetry instrumentation | *None yet* | **No hallucination detection.** Telemetry records actions but does not verify output truthfulness. |
| **8** | Equity & Neutrality | **Declarative** | System prompt policy checks | *None yet* | **No runtime control.** No bias detection pipeline. No fairness scoring. Research-frontier problem. |
| **9** | Verifiable Ledger & Fallback | **Enforced** | SHA-256 append-only chained logs (`LAW9-LEDGER`) | `test_law9_ledger_hash_chain` | Ledger implementation exists as reference. Fallback trigger conditions not yet formalized. |
| **10** | Boundaries & Non-Replication | **Enforced** | Ed25519 attestation & spawn gates (`LAW10-APPROVAL`) | `test_law10_charter_tamper`, `test_law10_approval_unsigned` | Charter digest pinning specified. Spawn token format defined. |

### Status Definitions

- **Enforced:** Runtime code exists that deterministically prevents violations. Backed by automated tests.
- **Specified:** Architectural design is complete. Reference code samples exist. Not yet packaged or tested as a deployable module.
- **Declarative:** Governed by constitutional mandate and policy evaluation. No automated runtime enforcement mechanism exists or is currently feasible.

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
4. Upon ratification, the Supreme Operator re-signs `config/charter_manifest.json` with the updated SHA-256 digests.
5. CI/CD pipelines verify the new digests before deployment.

### Quorum

- Minimum quorum: Supreme Operator + 1 advisory member.
- The Supreme Operator's ratification is always required. The Council cannot amend Laws without the Supreme Operator's explicit cryptographic approval.

---

## AMENDMENT HISTORY

| Date | Amendment | Proposed By | Status |
|---|---|---|---|
| *No amendments have been ratified* | — | — | — |

---

*This document is referenced by `AGENTIC_SACRED_COVENANT.md` Article III and is verified by CI against the implemented codebase.*

# MARKET LANDSCAPE & COMPETITIVE POSITIONING AUDIT

**Document Version:** 2.0.0
**Date:** November 1, 2026
**Prepared for:** Kirk LaSalle, Founder & Supreme Operator
**Classification:** Strategic — Investor & Partner Ready (evidence-based revision)
**Supersedes:** v1.0.0 (August 30, 2026); retained in git history
**Companion:** [`WORLD_CLASS_AUDIT_2026-11.md`](WORLD_CLASS_AUDIT_2026-11.md), the engineering findings behind every capability statement below

> [!IMPORTANT]
> **What changed since v1.0.0.**
> - Every market, regulatory, and competitor figure is now tied to a cited source; 51 of 55 URLs were verified at HTTP 200 via the project-local MCP fleet (see §8).
> - **Corrected:**
>   - The EU AI Act high-risk dates moved to **2 Dec 2027 / 2 Aug 2028**.
>   - Incident reporting is **Art. 73**, not Art. 62.
>   - OWASP's agentic list is the **Top 10 for Agentic Applications 2026 (ASI01–ASI10)**, not a "Top 17".
>   - NIST's effort is the **AI Agent Standards Initiative**; "AASI" is not NIST nomenclature.
> - **Withdrawn:**
>   - "88% of organizations breached" and "Gartner 40% decommission" (no traceable source).
>   - "90% EU AI Act / 100% NIST alignment" (no article-level evidence).
>   - "Merkle ledger" and "post-quantum preparedness" (not implemented).
>   - "Only runtime-enforced constitutional framework" (false since Microsoft's Agent Governance Toolkit).

---

## TABLE OF CONTENTS

1. [Executive Market Summary](#1-executive-market-summary)
2. [Market Overview & Sizing](#2-market-overview--sizing)
3. [Regulatory & Standards Landscape](#3-regulatory--standards-landscape)
4. [Competitive Landscape Analysis](#4-competitive-landscape-analysis)
5. [Differentiation Analysis](#5-differentiation-analysis)
6. [SWOT Analysis](#6-swot-analysis)
7. [Strategic Positioning Recommendations](#7-strategic-positioning-recommendations)
8. [Sources & Verification](#8-sources--verification)

---

## 1. EXECUTIVE MARKET SUMMARY

**Market.** AI governance is a small, fast-growing category. Gartner sizes **AI governance platform** spend at **$492M in 2026**, passing **$1B by 2030** [M1]. Broader "AI governance market" estimates for 2026 cluster around **$418–419M**, with **34–36% CAGR** [M2][M3]. The widest definitions reach ~$0.9B (2024) at 45% CAGR [M4]. Interception of agent tool calls, policy-as-code, and tamper-evident logging are now **table stakes**: Microsoft, AWS, and Google bundle them with their agent platforms [C7][C8][C9].

**Regulation.** The EU **AI Omnibus** entered into force on **27 July 2026** and postponed high-risk obligations:
- **Annex III** systems now apply from **2 December 2027**.
- **Annex I** (product-embedded) systems apply from **2 August 2028** [R1][R2].

The OWASP **Top 10 for Agentic Applications 2026** has become the de facto risk checklist [R8]. **MCP 2026-07-28** is the current agent-tool protocol [R14].

**AGL's position (November 2026).** AGL is a **pre-alpha, single-maintainer, Apache-2.0 Python library** (0.1.0, not yet on PyPI). It occupies a narrow but real niche: a **local-first "constitutional kernel"** that pins its governing charter by SHA-256 and gates elevated agent actions behind **payload-bound, single-use Ed25519 operator approvals**. These two ideas are genuinely uncommon in the market.

However, the November 2026 engineering audit found that, **in the default configuration, an agent can approve its own elevated actions**, and that the hash-chained ledger breaks across restarts and under concurrency. The composite engineering score is **39/100**; see [`WORLD_CLASS_AUDIT_2026-11.md`](WORLD_CLASS_AUDIT_2026-11.md).

AGL therefore **cannot yet be credibly positioned against commercial or hyperscaler offerings**. It *can* be positioned, after P0 remediation, as an embeddable policy-and-evidence component.

**Window.** The EU high-risk delay gives roughly **13 months** (to Dec 2027) to:
1. fix the critical defects;
2. publish to PyPI;
3. ship an OWASP ASI mapping and an Art. 12/14 evidence exporter.

That is achievable for a library of AGL's size.

---

## 2. MARKET OVERVIEW & SIZING

### 2.1 Verified market estimates

| Source | Scope | Base | Forecast | CAGR | Verification |
|---|---|---|---|---|---|
| **Gartner** (17 Feb 2026) [M1] | AI governance **platforms** (spend) | **$492M (2026)** | > $1B (2030) | — | Publisher blocks automation (403); corroborated by multiple secondary reports |
| **Grand View Research** [M2] | AI governance market | $308.3M (2025) → **$417.8M (2026)** | $3.59B (2033) | **36.0%** | ✅ MCP |
| **Precedence Research** [M3] | AI governance market | **$419.45M (2026)** | $5.88B (2035) | **34.27%** | ✅ MCP |
| **MarketsandMarkets** [M4] | AI governance (broad) | $0.89B (2024) | $5.78B (2029) | **45.3%** | 403; secondary corroboration |

**How to quote it.** Say "**≈ $0.4–0.5B in 2026, growing ~34–45% annually**", and always name the source and scope. The spread reflects definitions: platform software only, versus software plus services, versus inclusion of GRC.

### 2.2 Where AGL's addressable slice sits

AGL addresses the **developer-embedded runtime-enforcement** slice: libraries and gateways that sit in the agent's tool-call path. Most of this slice is captured by free or bundled offerings: hyperscaler platforms, NeMo Guardrails, Docker MCP Gateway, and Microsoft's Agent Governance Toolkit.

Realistic monetisation paths for an OSS kernel in this slice are:
1. support and assurance contracts for regulated or air-gapped users;
2. a hosted evidence/attestation service;
3. acquisition by a security platform. The 2025–26 consolidation pattern (§4.3) shows this is how most guardrail start-ups have exited.

---

## 3. REGULATORY & STANDARDS LANDSCAPE

### 3.1 Status as of 1 November 2026

| Instrument | Status | Relevance to AGL | Source |
|---|---|---|---|
| **EU AI Act** (Reg. 2024/1689) + **AI Omnibus** | Omnibus in force 27 Jul 2026. Art. 50 transparency since 2 Aug 2026. **Annex III high-risk: 2 Dec 2027**; **Annex I: 2 Aug 2028** | Evidence for **Art. 12** (record-keeping), **Art. 14** (human oversight), **Art. 15** (robustness/cybersecurity), **Art. 73** (serious-incident reporting) | [R1][R2][R3][R4] |
| **NIST AI RMF 1.0** / **AI 600-1** | Voluntary frameworks (Jan 2023 / Jul 2024) | *Govern* and *Manage* functions | [R5][R6] |
| **NIST AI Agent Standards Initiative** (CAISI) | Launched 17 Feb 2026; RFI on agent security | An initiative, **not** a conformance standard; no "% alignment" is meaningful | [R7] |
| **OWASP Top 10 for Agentic Applications 2026** | ASI01–ASI10; published 9 Dec 2025, v2.01 1 Jun 2026 | Becoming a procurement checklist; AGL maps partially (§5.3) | [R8] |
| OWASP Agentic AI: Threats & Mitigations | T1–T15 taxonomy | Threat-model reference | [R9] |
| **ISO/IEC 42001:2023** | AI management-system standard | Organisational, not product, certification | [R10] |
| **Colorado** | SB 24-205 replaced by SB 26-189; effective 1 Jan 2027 (re-verify statute) | Disclosure/transparency duties for deployers | [R11] |
| **California SB 53** | Signed 29 Sep 2025; effective 1 Jan 2026 | Frontier-model developers; indirect | [R12] |
| **Singapore IMDA** Model AI Governance Framework for **Agentic AI** | 22 Jan 2026 (updated May 2026); voluntary | Strong match to AGL concepts: bounded risk, human accountability, logging | [R13] |
| **MCP specification** | **2026-07-28** current (stateless requests, per-request capability negotiation); 2025-11-25 prior | Natural integration point for a per-request policy kernel | [R14][R15] |
| **FIPS 186-5 / RFC 8032** (EdDSA), **FIPS 204** (ML-DSA) | Final | AGL uses Ed25519 (classical). ML-DSA is a roadmap item, **not** implemented | [R16][R17][R18] |

### 3.2 Compliance language guidance

AGL is a component. It **cannot make a system compliant**, and no alignment percentage should be published. The supportable statement is:

> *"AGL produces hash-chained action logs and cryptographically signed human approvals that can serve as **evidence** toward EU AI Act Articles 12 and 14 and OWASP ASI02, ASI05, ASI09, and ASI10 controls, subject to the known limitations listed in WORLD_CLASS_AUDIT_2026-11.md."*

---

## 4. COMPETITIVE LANDSCAPE ANALYSIS

### 4.1 Capability matrix

Legend: ✅ native · ◐ partial / conditional · ❌ absent. Competitor columns are taken from public vendor documentation and were not independently tested. AGL columns reflect measured behaviour at revision `1a0f616`.

| Offering | Model | Pre-exec tool-call intercept | Signed single-use human approval | Tamper-evident log | Kill switch | Policy-as-code | Regulatory mapping | Agent identity | Distribution |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|
| **AGL 0.1.0** | OSS, Apache-2.0 | ◐ evadable | ◐ **bypassable by default** | ◐ hash chain, resets per boot | ◐ `.halt`, next call | ❌ | ❌ | ❌ | GitHub source |
| **Microsoft Agent Governance Toolkit** [C4] | OSS, MIT, Public Preview | ✅ | ◐ | ✅ | ◐ | ✅ | ◐ (OWASP ASI: 7 full / 3 partial, self-reported) | ✅ | PyPI / npm / NuGet |
| Microsoft Agent 365 + Entra Agent ID [C7] | Commercial, GA May 2026 | ✅ | ◐ | ✅ | ◐ | ✅ | ◐ | ✅ | SaaS |
| AWS Bedrock AgentCore Policy [C8] | Commercial (Cedar OSS) | ✅ | ◐ | ✅ | ◐ | ✅ Cedar | ◐ | ✅ | Cloud |
| Google Model Armor / Agent Engine [C9] | Commercial | ✅ | ◐ | ✅ | ◐ | ✅ | ◐ | ✅ | Cloud |
| NVIDIA NeMo Guardrails [C1] | OSS, Apache-2.0 | ✅ | ◐ hook | ◐ OTel | ❌ | ✅ Colang | ❌ | ❌ | PyPI |
| Docker MCP Gateway [C3] | OSS | ✅ MCP | ◐ | ✅ | ◐ | ✅ | ❌ | ◐ | Docker |
| OPA / Cedar [C2][C5] | OSS policy engines | ✅ as backend | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | Binaries / crates |
| Zenity [C10] | Commercial | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ◐ | SaaS |
| Credo AI · Holistic AI · IBM watsonx.governance · OneTrust · ServiceNow | Commercial GRC | ◐ | ◐ | ✅ | ❌ | ◐ | ✅ | ◐ | SaaS |

### 4.2 Closest comparator: Microsoft Agent Governance Toolkit

| Dimension | AGL 0.1.0 | Microsoft AGT (Public Preview) |
|---|---|---|
| Licence | Apache-2.0 | MIT |
| Languages / distribution | Python, source only | Multi-language; PyPI, npm, NuGet |
| Scope | Charter integrity, 3-tier gate, signed approvals, hash-chained ledger, halt, linter, badge | Policy enforcement, identity, sandboxing, SRE |
| Distinctive feature | **SHA-256-pinned constitutional charter**; **payload-bound single-use Ed25519 approvals** | Breadth, identity integration, OWASP ASI mapping, OpenSSF badges |
| Maturity signals | 22 tests, 52% coverage, CI; critical defects open | OpenSSF Scorecard + Best Practices badges |

**Implication.** Competing head-on with AGT on breadth is not viable. AGL's credible play is depth on the two distinctive features, plus interoperability, potentially including an adapter that lets AGL's charter-pinning and signed-approval primitives run *inside* AGT- or MCP-gateway-based deployments.

### 4.3 Consolidation & funding signals (2025–2026)

| Date | Event | Value | Source |
|---|---|---|---|
| Jun 2025 | Snyk acquires Invariant Labs | undisclosed | [C12] |
| Jul 2025 | Palo Alto Networks completes Protect AI acquisition | ~$700M | [C14] |
| Sep 2025 | Check Point acquires Lakera | ~$300M | [C13] |
| Sep 2025 | F5 to acquire CalypsoAI | ~$180M | [C15] |
| Apr 2026 | Cisco to acquire Galileo | undisclosed | [C16] |
| May 2026 | Microsoft Agent 365 GA | — | [C7] |
| Jun 2026 | Straiker Series A | $64M | [C17] |
| Aug 2026 | Zenity Series C | $125M | [C10] |
| Sep 2026 | Guardrails AI joins Harvey | undisclosed | [C11] |

Standalone guardrail vendors are being absorbed into security and vertical platforms, and hyperscalers are bundling equivalent controls. Differentiation through rigour and interoperability matters more than feature breadth.

---

## 5. DIFFERENTIATION ANALYSIS

### 5.1 Genuine differentiators (verified in code)

1. **Content-addressed constitutional charter.** Three governing documents are pinned by LF-normalised SHA-256 in [`config/charter_manifest.json`](config/charter_manifest.json) and verified at kernel boot and in CI. None of the surveyed vendors markets this.
2. **Payload-bound, expiring, single-use Ed25519 approvals (AGL-V1).** The signature covers the tool name and a canonical payload digest, so what the operator signs is exactly what executes. This mitigates OWASP ASI09 (human-agent trust exploitation). It is correct **when an operator public key is pinned**.
3. **Zero runtime dependencies, offline, ~1.7k LOC.** It is auditable in an afternoon and suits air-gapped and sovereign deployments.
4. **Sub-millisecond overhead.** Measured at 0.49 ms (SAFE) and 0.71 ms (signed ELEVATED).

### 5.2 Claims that are not differentiators (or not true)

| Claim (v1.0.0) | Reality |
|---|---|
| "Merkle ledger" | Linear SHA-256 hash chain. Resets per boot, not concurrency-safe, and cannot detect tail truncation. |
| "Only runtime-enforced constitutional framework" | Runtime enforcement is standard (Microsoft AGT, AgentCore, NeMo, Docker MCP Gateway). Only the *pinned charter* is distinctive. |
| "Post-quantum preparedness" | No ML-DSA and no algorithm-agility layer yet. |
| "Hardware-tied security" | Windows DPAPI only, and it fails open on decryption error. No HSM or PKCS#11. |
| "100/100 compliance" badge | Self-assessed by a linter that exempts the kernel and the tests. |

### 5.3 OWASP Agentic Top 10 (2026) mapping: honest self-assessment

| ASI | Risk | AGL today |
|---|---|---|
| ASI01 | Agent Goal Hijack | ❌ (no input provenance) |
| ASI02 | Tool Misuse & Exploitation | ◐ 3-tier gate; evadable (P6) |
| ASI03 | Identity & Privilege Abuse | ◐ operator key only; no agent identity |
| ASI04 | Agentic Supply Chain | ◐ charter pinning; zero deps; no MCP-server pinning |
| ASI05 | Unexpected Code Execution | ◐ prohibited-command list; no sandbox |
| ASI06 | Memory & Context Poisoning | ❌ |
| ASI07 | Insecure Inter-Agent Communication | ❌ (CAC tokens documented, not built) |
| ASI08 | Cascading Failures | ◐ global `.halt` |
| ASI09 | Human-Agent Trust Exploitation | ◐ payload-bound approvals; no action preview |
| ASI10 | Rogue Agents | ◐ halt + ledger; ledger gaps |
| | **Total** | **0 full · 7 partial · 3 none** |

---

## 6. SWOT ANALYSIS

| **Strengths** | **Weaknesses** |
|---|---|
| • SHA-256-pinned constitutional charter verified at boot<br>• Payload-bound single-use Ed25519 approvals<br>• Zero dependencies; sub-ms overhead<br>• Apache-2.0, CI, 22 tests, CLI, linter, badge<br>• Candid gap-disclosure culture in GOVERNANCE/PRD | • **Default-config self-approval bypass (P1/P2)**<br>• Ledger: per-boot reset, no locking, no anchoring<br>• Substring classifier, default-allow for unknown tools<br>• 52% coverage; CLI untested<br>• Not on PyPI; bus factor 1<br>• History of documentation over-claims |
| **Opportunities** | **Threats** |
| • EU high-risk deadline moved to Dec 2027: time to mature<br>• OWASP ASI becoming a procurement checklist<br>• MCP 2026-07-28 stateless model suits per-request policy middleware<br>• Sovereign / air-gapped / regulated buyers who will not adopt hyperscaler control planes<br>• Singapore agentic framework closely matches AGL's concepts | • Free bundled controls from Microsoft, AWS, and Google<br>• Microsoft AGT (MIT, multi-language) occupies the same OSS niche<br>• Market consolidation reduces independent buyers<br>• Reputational risk if security claims outpace code |

---

## 7. STRATEGIC POSITIONING RECOMMENDATIONS

**Positioning statement (recommended):**
> *"Autonomous Governance Laws is the minimal, auditable constitutional kernel for AI-agent tool calls: a pinned charter, approvals the agent cannot forge, and an evidence-grade action ledger, in a zero-dependency library you can read in an afternoon."*

The statement is only usable once P0 below is complete.

| Priority | Action | Why it moves market position |
|---|---|---|
| **P0 (now)** | Fix P1/P2 (fail closed without pinned key), P4/P5 (ledger continuity and locking), P6 (default-deny classifier); publish a security advisory | Removes the disqualifying defect; turns a liability into a credibility signal |
| **P1** | Evidence-grade ledger (payload/approval binding, signed checkpoints); coverage ≥ 85%; SAST; OpenSSF Scorecard | Makes the "tamper-evident" claim defensible to auditors |
| **P2** | PyPI 0.2.0 via Trusted Publishing with Sigstore attestations and SBOM | Removes the #1 adoption barrier |
| **P3** | **OWASP ASI mapping doc**; **EU AI Act Art. 12/14 evidence exporter**; **MCP 2026-07-28 middleware**; adapters for LangGraph, OpenAI Agents SDK, and Microsoft Agent Framework / AGT; optional OPA/Cedar backend | Positions AGL as a complement to gateways and platforms rather than a competitor |
| **P4** | Algorithm agility + hybrid Ed25519/ML-DSA; M-of-N operator quorum; PKCS#11/HSM; external ledger anchoring | Assurance tier for regulated and sovereign buyers |

**Messaging rules going forward:**
1. Never publish compliance percentages.
2. Every capability claim links to code and a test.
3. Always name the market-size source and scope.
4. Use the term "hash-chained", not "Merkle", until a Merkle tree with signed tree heads ships.

---

## 8. SOURCES & VERIFICATION

Verification used the project-local MCP fleet's `web-search` server (`fetch_webpage` / `bulk_url_fetch`) on 1 Nov 2026. 55 URLs were checked; **51 returned HTTP 200 with on-topic titles and claim terms present**. Three publishers blocked automation (ISO, Gartner, MarketsandMarkets; figures corroborated by secondary sources). One URL from the research brief returned 404 and was replaced with the correct MCP specification path. The full register with verification status is in [`WORLD_CLASS_AUDIT_2026-11.md`](WORLD_CLASS_AUDIT_2026-11.md), Appendix A.

**Regulatory & standards**
- [R1] European Commission: Timeline for the Implementation of the EU AI Act. https://ai-act-service-desk.ec.europa.eu/en/ai-act/timeline/timeline-implementation-eu-ai-act
- [R2] European Commission: "AI Omnibus enters into force," 27 Jul 2026. https://digital-strategy.ec.europa.eu/en/news/ai-omnibus-enters-force
- [R3] artificialintelligenceact.eu: Implementation timeline. https://artificialintelligenceact.eu/implementation-timeline/
- [R4] EU AI Act Art. 12, 14, 15, 73 (artificialintelligenceact.eu/article/N/); Regulation (EU) 2024/1689. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689
- [R5] NIST AI Risk Management Framework. https://www.nist.gov/itl/ai-risk-management-framework
- [R6] NIST AI 600-1 Generative AI Profile. https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
- [R7] NIST: Announcing the AI Agent Standards Initiative, 17 Feb 2026. https://www.nist.gov/news-events/news/2026/02/announcing-ai-agent-standards-initiative-interoperable-and-secure
- [R8] OWASP Top 10 for Agentic Applications 2026. https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
- [R9] OWASP Agentic AI: Threats and Mitigations. https://genai.owasp.org/resource/agentic-ai-threats-and-mitigations/
- [R10] ISO/IEC 42001:2023. https://www.iso.org/standard/42001
- [R11] Hunton Andrews Kurth: Colorado AI Act amended and effective date delayed. https://www.hunton.com/privacy-and-cybersecurity-law-blog/colorado-ai-act-amended-and-effective-date-delayed
- [R12] Office of Governor Newsom: SB 53 signed, 29 Sep 2025. https://www.gov.ca.gov/2025/09/29/governor-newsom-signs-sb-53-advancing-californias-world-leading-artificial-intelligence-industry/
- [R13] IMDA: Model AI Governance Framework for Agentic AI. https://www.imda.gov.sg/resources/press-releases-factsheets-and-speeches/factsheets/2026/updated-model-ai-governance-framework-for-agentic-ai
- [R14] Model Context Protocol specification 2026-07-28. https://modelcontextprotocol.io/specification/2026-07-28
- [R15] Model Context Protocol specification 2025-11-25. https://modelcontextprotocol.io/specification/2025-11-25
- [R16] NIST FIPS 204 (ML-DSA). https://csrc.nist.gov/pubs/fips/204/final
- [R17] NIST FIPS 186-5. https://csrc.nist.gov/pubs/fips/186-5/final
- [R18] RFC 8032, EdDSA. https://datatracker.ietf.org/doc/html/rfc8032

**Market sizing**
- [M1] Gartner: Global AI Regulations Fuel Billion-Dollar Market for AI Governance Platforms, 17 Feb 2026. https://www.gartner.com/en/newsroom/press-releases/2026-02-17-gartner-global-ai-regulations-fuel-billion-dollar-market-for-ai-governance-platforms
- [M2] Grand View Research: AI Governance Market Report. https://www.grandviewresearch.com/industry-analysis/ai-governance-market-report
- [M3] Precedence Research: AI Governance Market. https://www.precedenceresearch.com/ai-governance-market
- [M4] MarketsandMarkets: AI Governance Market. https://www.marketsandmarkets.com/Market-Reports/ai-governance-market-176187291.html

**Competitors & transactions**
- [C1] NVIDIA NeMo Guardrails. https://github.com/NVIDIA/NeMo-Guardrails
- [C2] Open Policy Agent. https://github.com/open-policy-agent/opa
- [C3] Docker MCP Gateway. https://github.com/docker/mcp-gateway
- [C4] Microsoft Agent Governance Toolkit. https://github.com/microsoft/agent-governance-toolkit
- [C5] Cedar. https://github.com/cedar-policy/cedar
- [C7] Microsoft Agent 365 GA, 1 May 2026. https://www.microsoft.com/en-us/security/blog/2026/05/01/microsoft-agent-365-now-generally-available-expands-capabilities-and-integrations/
- [C8] AWS: Why Policy in Amazon Bedrock AgentCore chose Cedar. https://aws.amazon.com/blogs/security/why-policy-in-amazon-bedrock-agentcore-chose-cedar-for-securing-agentic-workflows/
- [C9] Google Cloud Model Armor. https://cloud.google.com/security/products/model-armor
- [C10] Zenity $125M Series C, 4 Aug 2026. https://fintech.global/2026/08/04/zenity-lands-125m-as-ai-agent-security-race-heats-up/
- [C11] Guardrails AI joins Harvey. https://www.harvey.ai/blog/guardrails-ai-joins-harvey
- [C12] Snyk acquires Invariant Labs. https://snyk.io/news/snyk-acquires-invariant-labs-to-accelerate-agentic-ai-security-innovation/
- [C13] Check Point acquires Lakera. https://www.securitysolutionsmedia.com/2025/09/19/check-point-acquires-lakera-to-deliver-end-to-end-ai-security-for-enterprises/
- [C14] Palo Alto Networks completes Protect AI acquisition. https://www.paloaltonetworks.com/company/press/2025/palo-alto-networks-completes-acquisition-of-protect-ai
- [C15] F5 to acquire CalypsoAI. https://www.f5.com/company/news/press-releases/f5-to-acquire-calypsoai-to-bring-advanced-ai-guardrails-to-large-enterprises
- [C16] Cisco to acquire Galileo. https://www.crn.com/news/networking/2026/cisco-to-snap-up-ai-observability-startup-galileo-technologies-to-expand-splunk-platform
- [C17] Straiker $64M Series A. https://www.prnewswire.com/news-releases/straiker-raises-64m-series-a-to-secure-the-agentic-workforce-302812638.html

---
*Market Audit v2.0.0. Evidence-based revision prepared November 1, 2026 for Kirk LaSalle.*

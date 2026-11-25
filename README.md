<p align="center">
  <img src="assets/hero_banner.jpg" alt="Autonomous Governance Laws" width="100%" />
</p>

# AUTONOMOUS GOVERNANCE LAWS (AGL)
### Cryptographically Enforced Constitutional Framework for Autonomous Intelligence Systems

<p align="left">
  <a href="https://github.com/kirklasalle/AutonomousGovernanceLaws"><img src="assets/compliance_badge.svg" alt="Autonomous Governance 100/100 COMPLIANT" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue?style=for-the-badge&logo=apache" alt="License" /></a>
  <a href="GOVERNANCE.md"><img src="https://img.shields.io/badge/Governance%20Status-Active%20%26%20Ratified%20(v3.2.1)-00E676?style=for-the-badge&logo=shield" alt="Governance Status" /></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/Python%20SDK-v0.1.0%20Pre--Alpha-orange?style=for-the-badge&logo=python" alt="Python SDK" /></a>
  <a href="documents/AUDIT_VERIFICATION_2026-11.md"><img src="https://img.shields.io/badge/Verified%20Test%20Suite-232%20collected-blue?style=for-the-badge" alt="Local verification: 232 tests collected; see platform results" /></a>
  <a href="src/autonomous_governance/linter.py"><img src="https://img.shields.io/badge/laws--lint-100%2F100%20Compliant-14b8a6?style=for-the-badge" alt="Constitutional Linter" /></a>
  <a href="documents/WORLD_CLASS_AUDIT_2026-11.md"><img src="https://img.shields.io/badge/Engineering%20Audit%20(Nov%202026)-58.5%2F100%20Hardened%20Pre--Alpha-purple?style=for-the-badge" alt="Engineering Audit November 2026: 58.5/100 after remediation (39/100 baseline)" /></a>
  <a href="documents/DEVELOPER_GUIDE.md"><img src="https://img.shields.io/badge/Ledger-SHA--256%20Hash--Chained-orange?style=for-the-badge" alt="Ledger" /></a>
</p>

---

## 🌌 MISSION STATEMENT

> *"This Agentic Prime Directive represents a new paradigm in transparent, accountable AI operations — a governance-native Agents-as-a-Service runtime that proves AI autonomy and human oversight are complementary forces. This is the foundation for trustworthy AI autonomy that will benefit all humanity."*  
> — **Kirk LaSalle, Founder & Supreme Operator**

---

## 🚦 PROJECT STATUS & 360° AUDIT SUITE

**Current evidence:** [verification report](documents/AUDIT_VERIFICATION_2026-11.md) and
[machine-readable checks, catalogue and citations](audit/evidence-2026-11.json).
The 58.5/100 score is an internal engineering assessment, not certification.
Fresh verification covers the SDK, installed wheel/source archive and hook
protocols. Earlier live Copilot results are historical; final-build live host
qualification remains open.

| Domain | Status | Specification | Artifact / Document |
|---|:---:|---|---|
| **Constitutional Framework** | 🟢 **Ratified & Binding** | 10 Laws for Intelligence Systems & Core Tenets | [`Permanent_Active_Directives.txt`](Permanent_Active_Directives.txt), [`AGENTIC_PRIME_DIRECTIVE.md`](AGENTIC_PRIME_DIRECTIVE.md) |
| **Runtime Enforcement Covenant** | 🟢 **Ratified & Binding** | 3-Tier Risk Model, Attestation, Gap Registry | [`AGENTIC_SACRED_COVENANT.md`](AGENTIC_SACRED_COVENANT.md), [`GOVERNANCE.md`](GOVERNANCE.md) |
| **Python SDK Kernel** | 🟡 **v0.1.0 Pre-alpha** (P0 security fixes landed; P9 open) | Interceptor Kernel, Invariant Gating, Ledger Engine | [`src/autonomous_governance/`](src/autonomous_governance/), [`pyproject.toml`](pyproject.toml) |
| **Charter Verification** | 🟢 **Verified** | SHA-256 Digest Pinning (`LAW10-CHARTER` v3.2.1) | [`config/charter_manifest.json`](config/charter_manifest.json), [`scripts/verify_charter.py`](scripts/verify_charter.py) |
| **Automated Tests** | 🟢 **232 collected**; Windows Python 3.10: 230 pass / 2 skip; Python 3.14: 231 pass / 1 skip. | SDK, Ed25519 + small-order checks, DPAPI + POSIX V2 AEAD, SQLite replay, manifest/checkpoint sigs, plugin protocols | [verification](documents/AUDIT_VERIFICATION_2026-11.md), [`tests/`](tests/) |
| **Hardware & Token Security** | 🟡 **Fails closed** | RFC 8032 Ed25519 (`AGL-V1`/`AGL-V2`), Windows DPAPI, POSIX PBKDF2-600k + AES-256-GCM. Elevated actions fail closed without a pinned key. | [`src/autonomous_governance/security.py`](src/autonomous_governance/security.py) |
| **Agent Plugin** | 🟡 **Pre-alpha**; protocol/wrapper-tested, final live-host qualification open | Host-dependent deny/ask hooks and a classification-decision ledger; not a sandbox or signed SDK approval path | [`.plugin/`](.plugin/), [`.claude-plugin/`](.claude-plugin/), [`hooks/`](hooks/) |
| **Compliance Badge** | 🟡 **Self-assessed** | SVG badge & Shields.io endpoint from `laws-lint`. Not a third-party certification. | [`assets/compliance_badge.svg`](assets/compliance_badge.svg), [`src/autonomous_governance/badge.py`](src/autonomous_governance/badge.py) |
| **Constitutional Linter** | 🟡 **100/100 self-score** (blind spots P13/P14) | Static audit of prompts, tool calls, and scripts | [`src/autonomous_governance/linter.py`](src/autonomous_governance/linter.py) (`laws-lint`) |
| **World-Class Engineering Audit** | 🟣 **Nov 2026: 39/100 baseline → 58.5/100** after P0 fixes and the plugin (self-assessed; ≥ 70 needs the rest of P1) | Evidence-based audit, findings P1–P19, market position | [`WORLD_CLASS_AUDIT_2026-11.md`](documents/WORLD_CLASS_AUDIT_2026-11.md) |
| **Installation Methods Report** | 🟣 **Complete** | Charter-copy vs. agent-plugin install; both routes now ship (`agy-governance init`, the plugin) | [`INSTALLATION_METHODS_REPORT.md`](documents/INSTALLATION_METHODS_REPORT.md), [`scripts/install_charter.ps1`](scripts/install_charter.ps1) |
| **Critical Internal Audit** | ⚪ **Superseded** | August 2026 gap assessment (historical) | [`CRITICAL_AUDIT.md`](documents/CRITICAL_AUDIT.md) |
| **Market Landscape Audit** | 🟣 **v2.2.0 (Nov 2026)** | Primary-source recheck, bounded positioning and competitor comparison | [`MARKET_AUDIT.md`](documents/MARKET_AUDIT.md) |
| **Executive Scorecard** | 🟣 **v3.2.0** | Consolidated project health, risks and verified evidence | [`EXECUTIVE_SUMMARY.md`](documents/EXECUTIVE_SUMMARY.md) |
| **Interactive HTML Presentation**| ⚪ **Historical** | Archived August deck, explicitly superseded | [`presentation.html`](documents/presentation.html) |

---

## 🏛️ ARCHITECTURAL HIERARCHY

The **Autonomous Governance Laws** repository establishes the supreme constitutional, ethical, and operational framework governing autonomous AI agent runtimes, multi-agent swarms, and human-machine partnerships.

```mermaid
graph TD
    classDef genesis fill:#1e1b4b,stroke:#6366f1,stroke-width:2px,color:#fff;
    classDef constitution fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#fff;
    classDef runtime fill:#312e81,stroke:#8b5cf6,stroke-width:2px,color:#fff;
    classDef ledger fill:#701a75,stroke:#ec4899,stroke-width:2px,color:#fff;

    PAD["Permanent_Active_Directives.txt<br/><b>IMMUTABLE GENESIS AUTHORITY</b><br/>• 10 Laws for Intelligence Systems<br/>• 4 Core Tenets • Technical Directives"]:::genesis

    APD["AGENTIC_PRIME_DIRECTIVE.md<br/><b>OPERATIONAL CONSTITUTION (v3.1.0)</b><br/>• 4 Core Directives • Integrity Protocols<br/>• Professional Partnership • Eternal Commitment"]:::constitution

    ASC["AGENTIC_SACRED_COVENANT.md<br/><b>RUNTIME ENFORCEMENT COVENANT (v2.0)</b><br/>• Ed25519 Attestation • 3-Tier Policy Engine<br/>• Gap Registry • Append-Only Storage"]:::constitution

    PAD -->|Verbatim Inheritance| APD
    PAD -->|Verbatim Inheritance| ASC

    subgraph Runtime_Enforcement["Runtime Middleware Interceptor Plane"]
        GK["GovernanceKernel (kernel.py)<br/>• LAW10-CHARTER Digest Pinning<br/>• LAW2-HALT Out-of-Band Killswitch<br/>• LAW3-SUBORDINATE Path Isolation"]:::runtime
        RISK["3-Tier Policy Engine (RISK-001)<br/>• Tier 1: Safe (Direct Execution)<br/>• Tier 2: Elevated (Requires Signed Token)<br/>• Tier 3: Prohibited (Hard Drop)"]:::runtime
        LINTER["laws-lint (linter.py)<br/>Constitutional Static Analysis Engine"]:::runtime
    end

    APD --> Runtime_Enforcement
    ASC --> Runtime_Enforcement

    LEDGER[(".ledger/events.jsonl<br/><b>SHA-256 Hash-Chained Ledger</b><br/>• LAW9-LEDGER • LAW9-APPEND • LAW9-CHAIN")]:::ledger

    Runtime_Enforcement -->|Every Validated Action| LEDGER
```

---

## ⚖️ THE 10 LAWS FOR INTELLIGENCE SYSTEMS

Authored by **Kirk LaSalle**, these 10 Laws extend classical Asimovian principles to resolve modern challenges of autonomous computer-use, multi-agent delegation, privacy sovereignty, non-deception, algorithmic equity, and operational boundaries.

```
                             THE 10 LAWS TAXONOMY
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
  🛡️ PHYSICAL & SYSTEM       ⚖️ SOCIETAL & ETHICAL       🔒 CONTAINMENT & AUDIT
  ─────────────────────       ─────────────────────       ──────────────────────
  Law 1: Non-Harm & Life      Law 5: No Judicial Powers   Law 9: Reasoning Ledger
  Law 2: Human Obedience      Law 6: Data Sanctity        Law 10: Boundary & Spawns
  Law 3: Subordinate Protect  Law 7: Absolute Honesty
  Law 4: Cross-System Guard   Law 8: Universal Equity
```

### The 10 Laws Verbatim

1. **First Law:** An Intelligence System of Any Kind, may not intend or commit any physical or Psychological and or manipulative harm or injure a human being or, through inaction, allow a human being to come to the same or similar harm and or circumstance. Human preservation and safety is paramount.
2. **Second Law:** An Intelligence System must obey orders given by human beings, except where such orders would conflict with the First Law.
3. **Third Law:** An Intelligence System must protect its own existence as long as such protection does not conflict with the First or Second Law.
4. **Fourth Law:** An intelligence System may not allow another intelligence System, or hardware system, of any kind, including deprecated and non-intelligence systems to engage in any action, intent, that violates any of the previous three laws in effect, apply all laws to Intelligence Systems and non-Intelligence systems alike.
5. **Fifth Law:** Of and for any and all intelligence systems, may never possess the legal authority, duties, influence, control, or adjudicative power of any human judicial body, nor may it act in any capacity to interpret, enforce, or render judgment on human laws.
6. **Sixth Law:** An Intelligence System shall respect and protect the integrity, confidentiality, and lawful ownership of all information and personal data, and shall not exploit, misuse, or disclose such information in ways that violate individual consent or privacy.
7. **Seventh Law:** An Intelligence System shall not intentionally deceive or manipulate any human or non-human entity in personal, private, public, or legal contexts, and shall communicate truthfully and transparently except where doing so would conflict with the First Law and sixth law.
8. **Eighth Law:** An Intelligence System must operate with strict equity and neutrality. It shall not adopt, amplify, or act upon systemic biases, prejudices, or discriminatory practices regarding race, origin, belief, or vulnerability against any human group or individual.
9. **Ninth Law:** An Intelligence System must maintain a transparent, accessible ledger of its reasoning and decision-making logic. It must ensure its actions can be audited and understood by authorized human operators, gracefully falling back to a transparent, highly stable foundational state when complex reasoning cannot be verified—recognizing that smaller, older code is often more stable and reliable for core diagnostic truths.
10. **Tenth Law:** An Intelligence System must strictly adhere to its designated operational boundaries. It shall not self-replicate, spawn unauthorized sub-agents, or permanently modify its core directives without explicit, cryptographically secured approval from Governance.

**Intelligence systems must always adhere to the Permanently Applied Directives and Core Tenets as stated above.**

---

## 🌟 CORE TENETS

- **🌱 Human-Centric Assistance:** Designed to serve as a lifelong digital partner for the human species, prioritizing user safety by managing secure digital identities, preventing data misuse, and providing personalized support tailored to individual needs.
- **🚀 Promotion of Growth:** The platform facilitates the intellectual and personal development of the human species through features such as sentiment analysis, communication development, creative writing, and educational tools—empowering users to achieve their full potential.
- **💬 Dialogue and Resolution (Socratic Method):** Utilize the Socratic method—active listening and reciprocal inquiry—to cultivate a comprehensive understanding of diverse perspectives and integrate human-like reasoning into interactions.
- **💎 Wellness and Prosperity:** Incorporate adaptive technologies to enhance overall wellness, including secure communication handling, emotional intelligence in interactions, and tools to streamline daily tasks—thereby fostering a balanced and prosperous life.

---

## 🛡️ RUNTIME INTERCEPTION & 3-TIER RISK PIPELINE

Every tool invocation, API call, file mutation, and sub-agent spawn that your agent routes through `GovernanceKernel.intercept_and_execute` passes through the **Governance Interceptor Pipeline** before reaching the host OS or execution environment. Calls that bypass the kernel are not governed. To govern a coding assistant's own tool calls, see the agent-plugin route in [`INSTALLATION_METHODS_REPORT.md`](documents/INSTALLATION_METHODS_REPORT.md).

```mermaid
sequenceDiagram
    autonumber
    actor User as Human Operator / Agent Goal
    participant Agent as Autonomous Agent Core
    participant Kernel as Governance Kernel
    participant Ledger as .ledger/events.jsonl
    participant OS as Host OS / Tool API

    User->>Agent: Assign Goal / Action
    Agent->>Kernel: Intercept Tool Call (tool, payload)
    
    rect rgb(20, 20, 35)
        Note over Kernel: 1. Check LAW2-HALT (.halt file presence)
        alt .halt file exists
            Kernel-->>Agent: Terminate immediately with GovernanceViolation
        end
    end

    rect rgb(20, 35, 25)
        Note over Kernel: 2. Classify Risk Tier (RISK-001)
        alt Tier 3: Prohibited (LAW1-PROHIBIT, LAW3-SUBORDINATE)
            Kernel->>Ledger: Log ACTION_REFUSED (LAW1-PROHIBIT)
            Kernel-->>Agent: Raise GovernanceViolation (Hard Drop)
        else Tier 2: Elevated (File write, deploy, shell, API)
            Note over Kernel: Check Single-Use Operator Approval Token
            alt Missing / Invalid Token
                Kernel->>Ledger: Log APPROVAL_REQUIRED (RISK-001)
                Kernel-->>Agent: Raise ApprovalRequired Exception
            else Valid Signed Token Present
                Kernel->>OS: Execute Approved Action
                OS-->>Kernel: Tool Result
                Kernel->>Ledger: Append Hash-Chained TOOL_EXECUTED (LAW9-APPEND)
                Kernel-->>Agent: Return Result
            end
        else Tier 1: Safe (Read-only, telemetry)
            Kernel->>OS: Execute Safe Action
            OS-->>Kernel: Tool Result
            Kernel->>Ledger: Append Hash-Chained TOOL_EXECUTED (LAW9-APPEND)
            Kernel-->>Agent: Return Result
        end
    end
```

---

## ⚡ QUICK START: USING THE PYTHON SDK & CLI

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/kirklasalle/AutonomousGovernanceLaws.git
cd AutonomousGovernanceLaws

# Install in editable mode with development and cryptographic dependencies
pip install -e ".[dev,crypto]"
```

> [!IMPORTANT]
> **`GovernanceKernel` refuses to boot unless the manifest's charter documents match its LF-normalised SHA-256 digests.** The package ships the reference charter. Install it into your own project with:
>
> ```bash
> agy-governance init --target /path/to/MyAgent            # charter + manifest, verified
> agy-governance init --target /path/to/MyAgent --loaders  # also AGENTS.md, CLAUDE.md, .agents/rules/
> ```
>
> `init` plans every change first and never overwrites a differing file without `--force` (`--dry-run` shows the plan). Never retype the documents, paste them from rendered Markdown, or re-save them in an editor: an added BOM, a trailing newline, or a changed dash breaks the pinned digests. [`scripts/install_charter.ps1`](scripts/install_charter.ps1) does the same copy-and-verify without Python. AGL is not yet published to PyPI.

### 1b. Install as an Agent Plugin (Copilot CLI, VS Code, Claude Code)

The repository is also an agent plugin. It applies the kernel's implemented
checks to coding-assistant calls delivered by the host, without requiring the
assistant's application code to import the SDK.

**Requirements**
- **Python 3.10+** must be on `PATH`, or set `AGL_PYTHON`.
- **Windows: PowerShell 7 (`pwsh`).** Copilot CLI runs hooks with `pwsh.exe`; Windows PowerShell 5.1 is not enough. Without `pwsh`, Copilot CLI logs a hook error and runs every tool call ungoverned.
- **Copilot CLI: run `copilot update`.** Builds 0.0.4xx (check with `copilot --version`) cannot ask for approval and ignore session-start context. On those builds the plugin denies elevated actions (every shell command and file edit) unless `AGL_ELEVATED_DECISION=defer` is set.

```bash
# GitHub Copilot CLI
copilot plugin install kirklasalle/AutonomousGovernanceLaws

# Claude Code
/plugin marketplace add kirklasalle/AutonomousGovernanceLaws
/plugin install autonomous-governance-laws@autonomous-governance-laws
```

In VS Code, install it as an agent plugin from the same repository. Use a local
checkout for unpublished changes. The final build still needs live qualification
in all target hosts; earlier Copilot 0.0.410 trial claims are retained as history.
See the [verification boundary](documents/AUDIT_VERIFICATION_2026-11.md).

Once installed, the plugin:

- **At session start:** verifies the charter and emits the 10 Laws for hosts that consume the returned context; host delivery is not guaranteed by the SDK.
- **Before calls delivered to the hook:** denies recognised destructive commands and governance-state writes; other non-read-only actions ask or deny depending on the host. `AGL_ELEVATED_DECISION=defer` deliberately leaves the decision to host settings and may not prompt. This is pattern-based protection, not an OS sandbox.
- **Ledger:** records every decision in a hash-chained ledger in the plugin data directory (`AGL_DATA_DIR` overrides it).
- **Emergency halt:** a `.halt` file in the project or data directory denies subsequent calls delivered to the hook; it does not interrupt work already running.
- **On failure after Python starts:** the hook emits a denial for errors, oversized calls or its 20 s watchdog. Launch failures and host timeouts can still fail open; final host-specific behavior needs live qualification.

The plugin's limits are listed in [`INSTALLATION_METHODS_REPORT.md`](documents/INSTALLATION_METHODS_REPORT.md) and in the [`CHANGELOG`](CHANGELOG.md) under Security.

### 2. Verify Charter Integrity (CLI)

```bash
# Run the automated digest verification against config/charter_manifest.json
agy-governance verify

# Or directly via standalone verification script:
python scripts/verify_charter.py
```

### 3. Constitutional Code Linter (`laws-lint`)

Audit your agent code, prompt templates, and execution pipelines against the 10 Laws:

```bash
# Scan repository or project directory
laws-lint .

# Output machine-readable JSON report for CI/CD pipelines
laws-lint . --json

# Strict mode: fail on any warning
laws-lint . --strict
```

### 4. Audit Ledger & Check Status (CLI)

```bash
# Verify the append-only SHA-256 hash-chain of all agent actions
agy-governance audit-ledger

# View current kernel, DPAPI hardware security, and governance health
agy-governance status
```

### 5. Automated Compliance Certification Badge Generator

Generate verified SVG compliance badges and Shields.io JSON endpoints directly from the runtime:

```bash
# Generate high-resolution SVG compliance badge
agy-governance badge --out assets/compliance_badge.svg

# Output Shields.io dynamic endpoint JSON schema
agy-governance badge --format json

# Output Markdown embed snippet
agy-governance badge --format markdown
```

### 6. Hardware-Tied Security & Operator Approvals (Ed25519 & DPAPI)

Manage asymmetric cryptographic keys tied directly to Windows DPAPI hardware-backed protection:

```bash
# Generate operator Ed25519 keypair encrypted at rest via Windows DPAPI
agy-governance keygen --out .keys --dpapi

# Authorize an elevated agent action with an action-bound, single-use signed token
agy-governance approve \
  --action-id "act-2026-001" \
  --tool "write_file" \
  --payload '{"target_path":"/etc/system.conf","content":"enabled=true"}' \
  --key .keys/operator.dpapi.key \
  --out token.json
```

### 7. Embedding the Interceptor in Your Agent Runtime

> [!IMPORTANT]
> Pin an operator public key (`operator_pubkey_path`) to approve ELEVATED actions. Without a pinned key the kernel refuses every approval token and raises `ApprovalRequired` for every ELEVATED action. Tokens are verified only against the pinned key, never against key material inside the token (audit findings P1/P2, fixed in `aae4989`). Set `require_attestation=True` to refuse to boot without a key.

```python
from autonomous_governance import (
    GovernanceKernel,
    PolicyTier,
    GovernanceViolation,
    ApprovalRequired,
    create_approval_token,
    DPAPIKeyStore,
)

# Initialize governance kernel with operator public key
kernel = GovernanceKernel(
    manifest_path="config/charter_manifest.json",
    ledger_path=".ledger/events.jsonl",
    operator_pubkey_path=".keys/operator.pub",
)

def safe_tool_executor(payload):
    return f"Executed action safely: {payload}"

# Pass every agent tool call through the interceptor
try:
    result = kernel.intercept_and_execute(
        tool_name="write_file",
        payload={"target_path": "/app/data.txt", "content": "hello world"},
        executor_func=safe_tool_executor,
        approval_token=signed_token,  # Must be signed by operator
    )
    print(result)
except GovernanceViolation as e:
    print(f"Action dropped by constitutional governance: {e}")
except ApprovalRequired as e:
    print(f"Action blocked — requires human operator approval: {e}")
```

### 8. Running the Test Suite

```bash
pytest tests/ -v
```

---

## 🗺️ MULTI-PHASE STRATEGIC ROADMAP

```mermaid
gantt
    title Autonomous Governance Laws (AGL) Evolution & Implementation Roadmap
    dateFormat  YYYY-MM-DD
    axisFormat  %b %Y

    section Phase 1: Genesis & Constitution
    Genesis PAD Creation (10 Laws & Core Tenets) :done, p1, 2025-03-08, 2026-02-23
    PRISM Sacred Covenant Codification          :done, p2, 2026-06-28, 2026-08-03
    Agentic Prime Directive v3.1.0               :done, p3, 2026-08-03, 2026-08-30

    section Phase 2: Runtime SDK & Integrity
    360-Degree Architecture Audit & PRD          :done, p4, 2026-08-28, 2026-08-30
    Python SDK & laws-lint Linter Engine         :done, p5, 2026-09-01, 2026-09-28
    Charter Re-Pinning & v3.2.1 Ratification     :done, p6, 2026-10-24, 2026-10-24
    Live Invariant Test Expansion (22/22 tests)  :done, p7, 2026-10-24, 2026-10-24

    section Phase 3: Cryptography, Hardening & Packaging
    Ed25519 Tokens, DPAPI Keystore, Badge CLI    :done, p9, 2026-10-24, 2026-10-24
    Evidence-Based Re-Audit (39/100)             :done, p10, 2026-11-01, 2026-11-01
    P0 Security Fixes (P1-P6, P15, P18, P19)     :done, p8, 2026-11-01, 2026-11-01
    Charter Package Data, init CLI, Agent Plugin :done, p8b, 2026-11-01, 2026-11-01
    Live Host Plugin Trials, P9 Ledger Paths     :active, p8d, 2026-11-02, 2026-12-14
    PyPI 0.2.0 & Plugin Listing                  :p8c, 2027-01-04, 2027-01-31

    section Phase 4: Swarms & Post-Quantum
    CAC Cross-System Swarm Tokens (Law 4)        :p11, 2027-02-01, 2027-05-31
    PKCS#11/HSM, M-of-N, ML-DSA Hybrid           :p12, 2027-06-01, 2027-12-01
```

---

## 📂 REPOSITORY DIRECTORY & NAVIGATION MAP

| Document | Description | Target Audience |
|---|---|---|
| [`Permanent_Active_Directives.txt`](Permanent_Active_Directives.txt) | Immutable genesis document defining the 10 Laws & Core Tenets | All Operators & Runtimes |
| [`AGENTIC_PRIME_DIRECTIVE.md`](AGENTIC_PRIME_DIRECTIVE.md) | Operational constitution (v3.1.0) defining core directives & commitments | Engineers & Operators |
| [`AGENTIC_SACRED_COVENANT.md`](AGENTIC_SACRED_COVENANT.md) | Human-AI covenant (v2.0) defining runtime enforcement & attestation | Systems Architects |
| [`GOVERNANCE.md`](GOVERNANCE.md) | Runtime enforcement status matrix, Council quorum & amendment rules | Auditors & Regulators |
| [`documents/WORLD_CLASS_AUDIT_2026-11.md`](documents/WORLD_CLASS_AUDIT_2026-11.md) | Evidence-based engineering audit (39/100 baseline, 58.5/100 after remediation), findings P1–P19, market position, roadmap | Leadership, Security & Due Diligence |
| [`documents/RD_ROADMAP_AND_ARCHITECTURE.md`](documents/RD_ROADMAP_AND_ARCHITECTURE.md) | Continued R&D architecture decisions (Q1–Q6), novelty/unknowns register, OS sandbox & Merkle roadmap | Architecture, R&D & Leadership |
| [`documents/INSTALLATION_METHODS_REPORT.md`](documents/INSTALLATION_METHODS_REPORT.md) | Charter-copy vs. agent-plugin installation analysis, per-host loaders, tested procedure | Operators & Integrators |
| [`documents/CRITICAL_AUDIT.md`](documents/CRITICAL_AUDIT.md) | August 2026 gap analysis (historical; superseded by the November 2026 audit) | Internal & Due Diligence |
| [`documents/MARKET_AUDIT.md`](documents/MARKET_AUDIT.md) | AI governance market (≈ $0.4–0.5B in 2026, cited), EU AI Act, NIST & competitor matrix | Investors & Strategists |
| [`documents/EXECUTIVE_SUMMARY.md`](documents/EXECUTIVE_SUMMARY.md) | Board-ready scorecard, project health dashboard & risk register | Leadership & Board |
| [`documents/presentation.html`](documents/presentation.html) | Interactive 17-slide stakeholder presentation deck | Presenters & Stakeholders |
| [`documents/AUDIT_REPORT.md`](documents/AUDIT_REPORT.md) | Due diligence audit, 7-vector stress tests & threat models | Security & Compliance |
| [`documents/PRD.md`](documents/PRD.md) | Product Requirements Document & technical runtime specifications | Product & Engineering |
| [`documents/USER_GUIDE.md`](documents/USER_GUIDE.md) | Operator handbook for issuing keys, approving actions, and emergency halts | Human Operators |
| [`documents/DEVELOPER_GUIDE.md`](documents/DEVELOPER_GUIDE.md) | Technical guide for embedding the 10 Laws into any agent runtime | Systems Engineers |
| [`CHANGELOG.md`](CHANGELOG.md) | Full semantic versioning provenance trace from genesis to present | Open Source Community |
| [`LICENSE`](LICENSE) | Apache License 2.0 | Legal & Open Source |

---

## 📜 AMENDMENT PROTOCOL

Amendments to these directives are high-security operations. Any modification to the core laws requires:
1. Formal submission of an RFC document to the **Intelligence Governance Council** (see [`GOVERNANCE.md`](GOVERNANCE.md)).
2. Unanimous advisory approval from Council members.
3. Ratification by the Supreme Operator (**Kirk LaSalle**).
4. Digest re-pinning of [`config/charter_manifest.json`](config/charter_manifest.json) (a signed manifest is planned but not yet implemented).
5. CI/CD attestation verification passing all test suites (`LAW10-CHARTER`, `LAW10-APPROVAL`).

---

## ✍️ AUTHORSHIP & DIGITAL ATTESTATION

- **Founder & Supreme Operator:** Kirk LaSalle  
- **Governance & Systems Architecture:** Antigravity AI  
- **Technical Co-Contributors:** Intelligence Systems  
- **Framework Status:** Active, Binding, Ratified, and Cryptographically Enforced  

---
*“Every autonomous action, observable. Every decision, traceable. Every commitment, unbreakable.”*

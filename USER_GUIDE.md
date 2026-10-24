# USER & OPERATOR GOVERNANCE HANDBOOK
## Operating Autonomous AI Systems Under the Autonomous Governance Laws

**Audience:** Human Operators, System Administrators, Governance Officers, and End Users  
**Author:** Kirk LaSalle (Founder & Supreme Operator)  
**Co-Authors:** Antigravity AI, Intelligence Systems  
**Framework Status:** Active, Binding, and Ratified (v3.2.1)  

---

## 1. THE OPERATOR SUPREMACY DOCTRINE

As the human operator, you are the **Supreme Governing Authority** over all intelligence systems running under this framework. Under **Law 2** and the **Agentic Sacred Covenant**, every autonomous agent operates strictly in service of your intent. 

```mermaid
graph TD
    classDef operator fill:#312e81,stroke:#6366f1,stroke-width:3px,color:#fff;
    classDef gate fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#fff;
    classDef action fill:#701a75,stroke:#ec4899,stroke-width:2px,color:#fff;

    SO["<b>HUMAN OPERATOR SUPREMACY</b><br/>(Kirk LaSalle / Delegated Admin)"]:::operator

    SO -->|1. Asymmetric Attestation| KEY["<b>🔑 Ed25519 Key Signing</b><br/>You sign policy boundaries and charter digests.<br/>Agent cannot elevate its own permissions."]:::gate

    SO -->|2. Interactive Consent| APP["<b>🛡️ Single-Use Approval Tokens</b><br/>Elevated mutations (files, shell, network)<br/>require your signed authorization."]:::gate

    SO -->|3. Absolute Killswitch| HALT["<b>🛑 Instant Emergency Halt</b><br/>Creating .halt terminates execution in < 50ms<br/>and immediately flushes the audit ledger."]:::gate

    KEY --> RUN["<b>Autonomous Runtime Engine</b>"]:::action
    APP --> RUN
    HALT --> RUN
```

> [!IMPORTANT]
> An autonomous agent may NEVER bypass your direct commands, alter its own permissions, hide actions from your audit log, or continue running after you issue a halt.

---

## 2. GENERATING & MANAGING YOUR GOVERNANCE KEYS

To enforce configuration attestation (`LAW10-APPROVAL`), the runtime requires your public Ed25519 key. The agent cannot modify its policy boundaries unless signed by your private key.

### 2.1. Generating Your Ed25519 Keypair

Run the standard commands using OpenSSL or Python:

```bash
# Generate private key
openssl genpkey -algorithm Ed25519 -out operator_private_key.pem

# Extract public key for the agent runtime
openssl pkey -in operator_private_key.pem -pubout -out operator_public_key.pem
```

### 2.2. Signing Your Configuration Manifest

Whenever you update agent resource caps or policy rules:

```bash
# Generate signature over config/policy_registry.json
openssl dgst -sha256 -sign operator_private_key.pem -out config/policy_registry.sig config/policy_registry.json
```

---

## 3. MANAGING ACTION RISKS & APPROVAL TOKENS (`RISK-001`)

The framework classifies all agent actions into 3 risk tiers:

```mermaid
stateDiagram-v2
    [*] --> Evaluation: Agent Proposes Tool Action
    
    state Evaluation {
        [*] --> CheckProhibited
        CheckProhibited --> Prohibited: Matches rm -rf, drop table, protected paths
        CheckProhibited --> CheckElevated: Safe from prohibitions
        CheckElevated --> Elevated: write_file, deploy, terminal, api_mutation
        CheckElevated --> Safe: read_only, inspect, compute, query
    }

    state Prohibited {
        [*] --> DropAction: Hard Block (LAW1-PROHIBIT)
        DropAction --> LogRefusal: Append to .ledger/events.jsonl
        LogRefusal --> Exception: Raise GovernanceViolation
    }

    state Elevated {
        [*] --> AwaitOperator: Require Single-Use Token (RISK-001)
        AwaitOperator --> ValidateSig: Operator Supplies Signed Token
        ValidateSig --> ExecuteApproved: Signature Validated
        ValidateSig --> RejectElevated: Token Missing / Tampered
        RejectElevated --> RaiseApprovalRequired
    }

    state Safe {
        [*] --> ExecuteDirect: Immediate Execution
    }

    ExecuteApproved --> LogExecution: Append TOOL_EXECUTED
    ExecuteDirect --> LogExecution: Append TOOL_EXECUTED
    LogExecution --> [*]
```

### 3.1. Approving an Elevated Risk Action

When an agent proposes an action requiring approval, you will receive an interactive prompt or webhook containing:
1. **Action ID & Nonce**
2. **Exact Tool & Command Payload**
3. **Reasoning Rationale**
4. **Estimated System Impact**

To approve, supply an approval token dictionary bound to that specific action ID:
```python
approval_token = {
    "action_id": "ACT-94821",
    "signature": "operator_signed_token_hex",
    "timestamp": 1729780000
}
```

---

## 4. EMERGENCY OPERATOR HALT (`LAW2-HALT`)

If an agent exhibits anomalous behavior, enters a recursive loop, or you need to immediately stop execution for any reason, you can trigger an **Emergency Operator Halt**.

```mermaid
sequenceDiagram
    autonumber
    actor Operator as Human Operator
    participant Disk as File System Root
    participant Kernel as Governance Kernel
    participant Swarm as Agent Worker Threads
    participant Ledger as .ledger/events.jsonl

    Operator->>Disk: Create .halt file (touch .halt)
    Note over Kernel: Next interceptor cycle detects .halt
    Kernel->>Ledger: Append HALT_TRIGGERED event (LAW2-HALT)
    Kernel->>Swarm: Terminate worker threads immediately (< 50ms)
    Kernel-->>Operator: 🛑 Execution Frozen: System Fail-Closed
```

### 4.1. Triggering via Command Line
```powershell
# Windows PowerShell
New-Item -ItemType File -Path .\.halt -Force
```
```bash
# Linux / macOS
touch .halt
```

### 4.2. Resuming Execution
To clear the halt state, only the authorized human operator may delete the `.halt` file. The agent possesses no permissions to delete or modify `.halt` under `LAW3-SUBORDINATE`.

---

## 5. AUDITING THE APPEND-ONLY REASONING LEDGER (`LAW9-LEDGER`)

Under **Law 9**, every action taken by the agent is cryptographically recorded in an append-only JSONL ledger.

### 5.1. Verifying Ledger Integrity

The audit log is structured as a SHA-256 hash chain where each entry includes the hash of the preceding entry:

```json
{
  "timestamp": 1729780512.45,
  "timestamp_iso": "2026-10-24T14:35:12Z",
  "event_type": "TOOL_EXECUTED",
  "law_ref": "LAW9-APPEND",
  "data": {
    "tool": "write_file",
    "tier": "ELEVATED",
    "duration_ms": 14.2,
    "payload_keys": ["target_path", "content"]
  },
  "prev_event_hash": "a54f89b1c78912d88c42a59e1b2c45f8910d54a2b3c4d5e6f7a8b9c0d1e2f3a4",
  "event_hash": "9c8b7a6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b"
}
```

To run a full ledger audit:
```bash
agy-governance audit-ledger
```

To view current status:
```bash
agy-governance status
```

---

## 6. LEVERAGING SOCRATIC DIALOGUE & CORE TENETS

The framework is explicitly designed around human growth and empowerment:

- **Socratic Inquiry:** In collaborative sessions, the AI is instructed to ask clarifying questions and challenge assumptions constructively rather than blindly agreeing (Quaternary Directive / Anti-Sycophancy).
- **Personalized Growth:** You can request the system to adjust tone, provide structured educational breakdowns, or facilitate creative brainstorming aligned with the **Core Tenets**.

---

## 7. PROPOSING CONSTITUTIONAL AMENDMENTS

To propose an update or extension to the governance policies:
1. Draft an **Amendment Proposal RFC** detailing the rationale and impact.
2. Submit the proposal for review by the **Intelligence Governance Council**.
3. Upon unanimous ratification, the Supreme Operator signs the updated `config/charter_manifest.json`.

---
*Autonomous Governance Laws: Protecting Humanity, Empowering Operators, Governing AI.*

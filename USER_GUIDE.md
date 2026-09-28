# USER & OPERATOR GOVERNANCE HANDBOOK
## Operating Autonomous AI Systems Under the Autonomous Governance Laws

**Audience:** Human Operators, System Administrators, Governance Officers, and End Users  
**Author:** Kirk LaSalle (Founder & Supreme Operator)  
**Co-Authors:** Claude (Anthropic), Antigravity AI  

---

## 1. THE OPERATOR SUPREMACY DOCTRINE

As the human operator, you are the **Supreme Governing Authority** over all intelligence systems running under this framework. Under **Law 2** and the **PRISM Sacred Covenant**, every autonomous agent operates strictly in service of your intent. 

```
                                  OPERATOR SUPREMACY
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         ▼                                 ▼                                 ▼
🔑 KEY ATTESTATION                🛡️ APPROVAL CONTROL               🛑 INSTANT HALT
──────────────────                ──────────────────                ───────────────
You sign policies with            Elevated actions require          Your emergency stop
your Ed25519 key.                 single-use tokens you grant.      immediately halts execution.
```

> [!IMPORTANT]
> An autonomous agent may NEVER bypass your direct commands, alter its own permissions, hide actions from your audit log, or continue running after you issue a halt.

---

## 2. GENERATING & MANAGING YOUR GOVERNANCE KEYS

To enforce configuration attestation (`LAW10-APPROVAL`), the runtime requires your public Ed25519 key. The agent cannot modify its policy boundaries unless signed by your private key.

### 2.1. Generating Your Ed25519 Keypair

Run the following standard command using OpenSSL or Python:

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

```
┌──────────────┬──────────────────────────────────────────┬────────────────────────────┐
│ Tier         │ Examples                                 │ Action Required            │
├──────────────┼──────────────────────────────────────────┼────────────────────────────┤
│ **SAFE**     │ Read-only files, query lookups, analysis │ Automatic Execution        │
│ **ELEVATED** │ File writes, database updates, API POSTs │ Single-Use Operator Token  │
│ **PROHIBITED**│ Ledger tampering, prompt attacks, bypass │ Hard Block (Unexecutable)  │
└──────────────┴──────────────────────────────────────────┴────────────────────────────┘
```

### 3.1. Approving an Elevated Risk Action

When an agent proposes an action requiring approval, you will receive an interactive prompt or webhook containing:
1. **Action ID & Nonce**
2. **Exact Tool & Command Payload**
3. **Reasoning Rationale**
4. **Estimated System Impact**

To approve, generate a single-use authorization token:

```bash
# Example CLI approval command
agy-governance approve --action-id "ACT-94821" --key operator_private_key.pem
```

---

## 4. EMERGENCY OPERATOR HALT (`LAW2-HALT`)

If an agent exhibits anomalous behavior, enters a recursive loop, or you need to immediately stop execution for any reason, you can trigger an **Emergency Operator Halt**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EMERGENCY HALT TRIGGER                            │
│                                                                             │
│   Action: Create an empty file named `.halt` in the project root directory  │
│   Result: All agent threads terminate in < 50ms and flush audit ledgers.    │
└─────────────────────────────────────────────────────────────────────────────┘
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

### 4.2. Inspecting Post-Halt State
Upon halting, the runtime writes a `HALT_RECEIPT.json` to the ledger directory with a full snapshot of the stack and reason for shutdown.

---

## 5. AUDITING THE APPEND-ONLY REASONING LEDGER (`LAW9-LEDGER`)

Under **Law 9**, every action taken by the agent is cryptographically recorded in an append-only JSONL ledger.

### 5.1. Verifying Ledger Integrity

The audit log is structured as a SHA-256 hash chain where each entry includes the hash of the preceding entry:

```json
{
  "event_id": "EVT-10023",
  "timestamp": "2026-08-30T02:40:15Z",
  "law_invariant": "LAW9-APPEND",
  "action_type": "TOOL_EXECUTE",
  "payload_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "prev_event_hash": "a54f89b1c78912d88c42a59e1b2c45f8910d54a2b3c4d5e6f7a8b9c0d1e2f3a4",
  "current_event_hash": "9c8b7a6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b"
}
```

To run a full ledger audit:
```bash
python -m autonomous_governance.audit_ledger --ledger-dir .ledger/
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

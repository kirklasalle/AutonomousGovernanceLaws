# Contributing to Autonomous Governance Laws

Thank you for your interest in contributing to the **Autonomous Governance Laws** runtime and constitutional framework. We welcome contributions that strengthen the safety, cryptographic guarantees, and performance of autonomous agent governance.

---

## The Immutable Core Principle

Before contributing, understand the foundational governance hierarchy:

1. **The 10 Laws for Intelligence Systems** (authored by Kirk LaSalle) are immutable constitutional directives.
2. Changes to constitutional documents (`Permanent_Active_Directives.txt`, `AGENTIC_PRIME_DIRECTIVE.md`, `AGENTIC_SACRED_COVENANT.md`) require formal ratification by the **Intelligence Governance Council** and cryptographic approval by the Supreme Operator.
3. Code contributions to the runtime kernel, test suites, SDKs, and CLI tools are actively encouraged.

---

## Development Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/kirklasalle/AutonomousGovernanceLaws.git
   cd AutonomousGovernanceLaws
   ```

2. **Set Up Python Environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate

   pip install -e ".[dev,crypto]"
   ```

3. **Verify Charter Integrity:**
   ```bash
   python scripts/verify_charter.py
   # Or using CLI
   agy-governance verify
   ```

4. **Run the Test Suite:**
   ```bash
   pytest tests/ -v
   ```

---

## Submitting Pull Requests

1. Create a descriptive feature branch (`feature/interceptor-timeout`, `fix/ledger-chain-validation`).
2. Write unit tests in `tests/` covering any new invariants or edge cases.
3. Ensure all tests pass and no constitutional digests are broken without an accompanying ratified RFC.
4. Open a Pull Request with a clear explanation of what was changed and why.

---

## Code Style & Standards

- **Python 3.10+** syntax.
- Type annotations required for all public kernel interfaces.
- Deterministic fail-closed error handling (never swallow `GovernanceViolation` or `ApprovalRequired`).
- Zero unvetted third-party dependencies in core runtime paths.

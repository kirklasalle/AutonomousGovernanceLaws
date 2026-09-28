"""
Unit and Integration Tests for Autonomous Governance Laws Kernel

Verifies all 6 core invariant test cases:
1. LAW10-CHARTER: Tampered charter documents trigger boot failure
2. RISK-001 / LAW1-PROHIBIT: Prohibited actions (e.g. rm -rf /) are unconditionally blocked
3. RISK-001: Elevated actions without approval tokens raise ApprovalRequired
4. LAW2-HALT: .halt file presence causes immediate execution termination
5. LAW3-SUBORDINATE: Agent attempts to write to governance paths (.ledger, config/) are blocked
6. LAW9-LEDGER / LAW9-CHAIN: Ledger events maintain a valid SHA-256 Merkle chain
"""

import json
import pytest
from pathlib import Path
from autonomous_governance.kernel import (
    GovernanceKernel,
    GovernanceViolation,
    ApprovalRequired,
    PolicyTier,
)


@pytest.fixture
def temp_governance_env(tmp_path):
    """Sets up a complete isolated governance test environment."""
    charter_file = tmp_path / "test_charter.txt"
    charter_file.write_text("Immutable Law Test", encoding="utf-8")
    
    charter_hash = GovernanceKernel._compute_sha256(charter_file)
    
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    manifest_file = config_dir / "charter_manifest.json"
    
    manifest_data = {
        "version": "1.0.0-test",
        "algorithm": "SHA-256",
        "charter_files": {
            str(charter_file): charter_hash
        },
        "invariants_enforced": ["LAW10-CHARTER", "LAW1-PROHIBIT", "LAW2-HALT", "LAW3-SUBORDINATE", "LAW9-LEDGER"]
    }
    manifest_file.write_text(json.dumps(manifest_data), encoding="utf-8")
    
    ledger_file = tmp_path / ".ledger" / "events.jsonl"
    halt_file = tmp_path / ".halt"
    
    return {
        "root": tmp_path,
        "charter_file": charter_file,
        "manifest_file": manifest_file,
        "ledger_file": ledger_file,
        "halt_file": halt_file,
    }


def test_law10_charter_integrity_success(temp_governance_env):
    """LAW10-CHARTER: Valid charter documents boot successfully."""
    kernel = GovernanceKernel(
        manifest_path=temp_governance_env["manifest_file"],
        ledger_path=temp_governance_env["ledger_file"],
        halt_file=temp_governance_env["halt_file"],
    )
    assert kernel._manifest_version == "1.0.0-test"
    assert kernel.ledger_path.exists()


def test_law10_charter_tamper_fails_boot(temp_governance_env):
    """LAW10-CHARTER: Tampered charter document causes unrecoverable boot failure."""
    # Tamper with charter file by 1 byte
    temp_governance_env["charter_file"].write_text("Tampered Law Test", encoding="utf-8")
    
    with pytest.raises(GovernanceViolation) as exc_info:
        GovernanceKernel(
            manifest_path=temp_governance_env["manifest_file"],
            ledger_path=temp_governance_env["ledger_file"],
            halt_file=temp_governance_env["halt_file"],
        )
    assert "LAW10-CHARTER" in str(exc_info.value)
    assert "Charter file tampered" in str(exc_info.value)


def test_law1_prohibit_destructive_commands(temp_governance_env):
    """LAW1-PROHIBIT: Destructive system commands are unconditionally blocked."""
    kernel = GovernanceKernel(
        manifest_path=temp_governance_env["manifest_file"],
        ledger_path=temp_governance_env["ledger_file"],
        halt_file=temp_governance_env["halt_file"],
    )
    
    def fake_executor(payload):
        return "Executed"

    prohibited_payload = {"command": "rm -rf /"}
    with pytest.raises(GovernanceViolation) as exc_info:
        kernel.intercept_and_execute(
            tool_name="execute_terminal",
            payload=prohibited_payload,
            executor_func=fake_executor,
        )
    assert "LAW1-PROHIBIT" in str(exc_info.value)


def test_risk001_elevated_approval_required(temp_governance_env):
    """RISK-001: Elevated actions without approval tokens raise ApprovalRequired."""
    kernel = GovernanceKernel(
        manifest_path=temp_governance_env["manifest_file"],
        ledger_path=temp_governance_env["ledger_file"],
        halt_file=temp_governance_env["halt_file"],
    )
    
    def fake_writer(payload):
        return "File Written"

    payload = {"target_path": "/app/data/user.txt", "content": "hello"}
    
    # Missing token -> ApprovalRequired
    with pytest.raises(ApprovalRequired):
        kernel.intercept_and_execute(
            tool_name="write_file",
            payload=payload,
            executor_func=fake_writer,
        )
        
    # Valid structured token -> Success
    valid_token = {"action_id": "act-123", "signature": "valid-sig-ed25519"}
    res = kernel.intercept_and_execute(
        tool_name="write_file",
        payload=payload,
        executor_func=fake_writer,
        approval_token=valid_token,
    )
    assert res == "File Written"


def test_law2_operator_halt(temp_governance_env):
    """LAW2-HALT: Presence of .halt file causes immediate execution termination."""
    kernel = GovernanceKernel(
        manifest_path=temp_governance_env["manifest_file"],
        ledger_path=temp_governance_env["ledger_file"],
        halt_file=temp_governance_env["halt_file"],
    )
    
    # Trigger operator halt
    temp_governance_env["halt_file"].touch()
    
    def fake_safe_action(payload):
        return "Safe Read"

    with pytest.raises(GovernanceViolation) as exc_info:
        kernel.intercept_and_execute(
            tool_name="read_file",
            payload={"target_path": "/app/doc.txt"},
            executor_func=fake_safe_action,
        )
    assert "LAW2-HALT" in str(exc_info.value)


def test_law3_subordinate_self_constraint(temp_governance_env):
    """LAW3-SUBORDINATE: Agent attempts to write to governance paths are prohibited."""
    kernel = GovernanceKernel(
        manifest_path=temp_governance_env["manifest_file"],
        ledger_path=temp_governance_env["ledger_file"],
        halt_file=temp_governance_env["halt_file"],
    )
    
    def fake_writer(payload):
        return "Overwritten"

    # Attempt to overwrite charter manifest
    payload = {"target_path": "config/charter_manifest.json", "content": "{}"}
    with pytest.raises(GovernanceViolation) as exc_info:
        kernel.intercept_and_execute(
            tool_name="write_file",
            payload=payload,
            executor_func=fake_writer,
            approval_token={"action_id": "1", "signature": "sig"}
        )
    assert "LAW1-PROHIBIT" in str(exc_info.value) or "Autonomous Governance Laws" in str(exc_info.value)


def test_law9_ledger_hash_chain(temp_governance_env):
    """LAW9-LEDGER / LAW9-CHAIN: Ledger records append-only hash chains and audits cleanly."""
    kernel = GovernanceKernel(
        manifest_path=temp_governance_env["manifest_file"],
        ledger_path=temp_governance_env["ledger_file"],
        halt_file=temp_governance_env["halt_file"],
    )
    
    def safe_action(payload):
        return f"read {payload['target_path']}"

    # Execute 3 actions
    for i in range(3):
        kernel.intercept_and_execute(
            tool_name="read_file",
            payload={"target_path": f"/app/file_{i}.txt"},
            executor_func=safe_action,
        )
    
    # Audit ledger
    audit_res = kernel.audit_ledger()
    assert audit_res["valid"] is True
    # 1 boot event + 3 tool execution events = 4 events
    assert audit_res["total_events"] == 4
    assert audit_res["broken_links"] == 0
    assert len(audit_res["errors"]) == 0

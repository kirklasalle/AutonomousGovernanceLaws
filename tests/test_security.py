"""
Unit Tests for Autonomous Governance Laws Cryptographic Security Engine

Verifies:
- RFC 8032 Ed25519 keypair generation, signing, and verification
- Tamper detection on signatures, messages, and payloads
- Windows DPAPI hardware-tied key encryption and decryption
- Action-bound single-use operator approval tokens (AGL-V1)
- Token expiration and clock-skew bounds
- Single-use replay protection (Law 2 / Law 9 / Law 10)
- End-to-end kernel authorization with real cryptographic tokens
"""

import json
import time
import pytest
from pathlib import Path

from autonomous_governance.security import (
    generate_ed25519_keypair,
    ed25519_sign,
    ed25519_verify,
    DPAPIKeyStore,
    create_approval_token,
    verify_approval_token,
    compute_payload_digest,
)
from autonomous_governance.kernel import (
    GovernanceKernel,
    GovernanceViolation,
    ApprovalRequired,
)


def test_ed25519_keypair_and_signature_roundtrip():
    """Verify Ed25519 signature generation and verification."""
    priv, pub = generate_ed25519_keypair()
    assert len(priv) == 32
    assert len(pub) == 32

    message = b"Kirk LaSalle 10 Laws for Intelligence Systems"
    sig = ed25519_sign(priv, pub, message)
    assert len(sig) == 64

    # Valid signature verifies
    assert ed25519_verify(pub, message, sig) is True

    # Tampered message fails
    assert ed25519_verify(pub, message + b"!", sig) is False

    # Corrupted signature fails
    tampered_sig = bytearray(sig)
    tampered_sig[0] ^= 0xFF
    assert ed25519_verify(pub, message, bytes(tampered_sig)) is False

    # Wrong public key fails
    _, other_pub = generate_ed25519_keypair()
    assert ed25519_verify(other_pub, message, sig) is False


def test_dpapi_keystore_roundtrip(tmp_path):
    """Verify Windows DPAPI key encryption and storage."""
    raw_key = b"super_secret_operator_private_seed_32b"
    key_file = tmp_path / "operator.key"

    DPAPIKeyStore.save_key(key_file, raw_key, use_dpapi=True)
    assert key_file.exists()

    recovered_key = DPAPIKeyStore.load_key(key_file, is_dpapi=True)
    assert recovered_key == raw_key


def test_action_bound_approval_token():
    """Verify action-bound approval tokens bind tightly to tool and payload."""
    priv, pub = generate_ed25519_keypair()
    action_id = "act-2026-test-01"
    tool_name = "write_file"
    payload = {"target_path": "/secure/system.conf", "content": "active=true"}

    token = create_approval_token(
        action_id=action_id,
        tool_name=tool_name,
        payload=payload,
        private_seed=priv,
        public_key=pub,
        ttl_seconds=300,
    )

    assert token["version"] == "AGL-V1"
    assert token["action_id"] == action_id
    assert token["tool_name"] == tool_name
    assert token["payload_hash"] == compute_payload_digest(payload)

    # Valid token verifies against exact tool and payload
    is_valid, reason = verify_approval_token(token, tool_name, payload, expected_operator_pubkey=pub)
    assert is_valid is True
    assert reason == "Valid single-use authorization"

    # Mismatched tool fails
    is_valid, reason = verify_approval_token(token, "execute_shell", payload, expected_operator_pubkey=pub)
    assert is_valid is False
    assert "tool_name mismatch" in reason

    # Tampered payload fails
    tampered_payload = {"target_path": "/secure/system.conf", "content": "active=false"}
    is_valid, reason = verify_approval_token(token, tool_name, tampered_payload, expected_operator_pubkey=pub)
    assert is_valid is False
    assert "Payload digest mismatch" in reason

    # Untrusted operator public key fails
    _, untrusted_pub = generate_ed25519_keypair()
    is_valid, reason = verify_approval_token(token, tool_name, payload, expected_operator_pubkey=untrusted_pub)
    assert is_valid is False
    assert "untrusted operator public key" in reason


def test_approval_token_expiration():
    """Verify expired tokens are rejected."""
    priv, pub = generate_ed25519_keypair()
    action_id = "act-expired"
    tool_name = "deploy_code"
    payload = {"env": "prod"}

    token = create_approval_token(
        action_id=action_id,
        tool_name=tool_name,
        payload=payload,
        private_seed=priv,
        public_key=pub,
        ttl_seconds=-10,  # Expired in past
    )

    is_valid, reason = verify_approval_token(token, tool_name, payload, expected_operator_pubkey=pub)
    assert is_valid is False
    assert "expired" in reason.lower()


def test_kernel_replay_protection_and_cryptographic_token(tmp_path):
    """Verify kernel rejects replayed tokens and enforces real Ed25519 verification."""
    charter_file = tmp_path / "charter.txt"
    charter_file.write_text("Canonical Constitution", encoding="utf-8")
    charter_hash = GovernanceKernel._compute_sha256(charter_file)

    manifest_file = tmp_path / "charter_manifest.json"
    manifest_file.write_text(json.dumps({
        "version": "1.0.0-test",
        "charter_files": {str(charter_file): charter_hash},
    }), encoding="utf-8")

    ledger_file = tmp_path / ".ledger" / "events.jsonl"
    halt_file = tmp_path / ".halt"

    # Generate operator keypair and save public key
    priv, pub = generate_ed25519_keypair()
    pub_file = tmp_path / "operator.pub"
    pub_file.write_text(pub.hex(), encoding="utf-8")

    kernel = GovernanceKernel(
        manifest_path=manifest_file,
        ledger_path=ledger_file,
        operator_pubkey_path=pub_file,
        halt_file=halt_file,
    )
    assert kernel.operator_pubkey == pub

    payload = {"target_path": "/app/logs/report.txt", "content": "Log data"}
    token = create_approval_token(
        action_id="act-replay-test-001",
        tool_name="write_file",
        payload=payload,
        private_seed=priv,
        public_key=pub,
        ttl_seconds=300,
    )

    def dummy_writer(p):
        return f"Wrote {p['target_path']}"

    # First execution succeeds
    res1 = kernel.intercept_and_execute(
        tool_name="write_file",
        payload=payload,
        executor_func=dummy_writer,
        approval_token=token,
    )
    assert res1 == "Wrote /app/logs/report.txt"

    # Second execution with identical token FAILS due to replay prevention!
    with pytest.raises(ApprovalRequired):
        kernel.intercept_and_execute(
            tool_name="write_file",
            payload=payload,
            executor_func=dummy_writer,
            approval_token=token,
        )

    # Verify that TOKEN_REPLAY_DETECTED was logged to the ledger
    audit = kernel.audit_ledger()
    assert audit["valid"] is True
    ledger_text = ledger_file.read_text(encoding="utf-8")
    assert "TOKEN_REPLAY_DETECTED" in ledger_text

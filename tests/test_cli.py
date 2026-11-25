"""CLI and POSIX encrypted keystore unit tests for Autonomous Governance Laws."""

import hashlib
import json
import sys
from argparse import Namespace
from pathlib import Path

import pytest

from autonomous_governance import cli
from autonomous_governance.kernel import GovernanceKernel
from autonomous_governance.security import (
    POSIX_ENCRYPTED_MARKER,
    POSIX_ENCRYPTED_V2_MARKER,
    DPAPIKeyStore,
    generate_ed25519_keypair,
)


def _setup_workspace(tmp_path: Path):
    root = tmp_path / "gov_proj"
    (root / "config").mkdir(parents=True)
    charter = root / "CHARTER.md"
    charter.write_text("Immutable Charter v1\n", encoding="utf-8")
    digest = GovernanceKernel._compute_sha256(charter)
    manifest = root / "config" / "charter_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "version": "1.0.0",
                "operator": {"name": "Kirk LaSalle"},
                "charter_files": {"CHARTER.md": digest},
            }
        ),
        encoding="utf-8",
    )
    ledger = root / ".ledger" / "events.jsonl"
    return root, charter, manifest, ledger


def test_posix_passphrase_keystore_roundtrip_and_tamper_rejection(monkeypatch, tmp_path):
    secret = b"\x11" * 32
    blob = DPAPIKeyStore.protect_with_passphrase(secret, "sovereign-test-passphrase")
    assert blob.startswith(POSIX_ENCRYPTED_V2_MARKER)
    assert DPAPIKeyStore.unprotect_with_passphrase(blob, "sovereign-test-passphrase") == secret

    # Legacy V1 decryption remains supported
    import hashlib, hmac, os
    from autonomous_governance.security import _posix_ctr_xor
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", b"legacy-pass", salt, 100_000, dklen=64)
    ct = _posix_ctr_xor(derived[:32], salt, secret)
    tag = hmac.new(derived[32:], POSIX_ENCRYPTED_MARKER + salt + ct, hashlib.sha256).digest()
    assert DPAPIKeyStore.unprotect_with_passphrase(POSIX_ENCRYPTED_MARKER + salt + ct + tag, "legacy-pass") == secret

    with pytest.raises(ValueError, match="Invalid passphrase or corrupted"):
        DPAPIKeyStore.unprotect_with_passphrase(blob, "wrong-passphrase")

    corrupted = bytearray(blob)
    corrupted[-1] ^= 0xFF
    with pytest.raises(ValueError, match="Invalid passphrase or corrupted"):
        DPAPIKeyStore.unprotect_with_passphrase(bytes(corrupted), "sovereign-test-passphrase")

    # Simulate POSIX protect/unprotect/save_key/load_key flow via AGL_KEY_PASSPHRASE
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("AGL_KEY_PASSPHRASE", "linux-env-secret")
    key_path = tmp_path / "posix.dpapi.key"
    DPAPIKeyStore.save_key(key_path, secret, use_dpapi=True)
    raw_disk = key_path.read_bytes()
    assert raw_disk.startswith(POSIX_ENCRYPTED_V2_MARKER)
    assert DPAPIKeyStore.unprotect(raw_disk) == secret
    assert DPAPIKeyStore.load_key(key_path, is_dpapi=True) == secret


def test_cli_verify_success_missing_and_mismatch(tmp_path):
    root, charter, manifest, _ = _setup_workspace(tmp_path)

    assert cli.cmd_verify(Namespace(manifest=str(manifest))) == 0
    assert cli.cmd_verify(Namespace(manifest=str(tmp_path / "nonexistent.json"))) == 1

    # Corrupt charter file to trigger mismatch
    charter.write_text("TAMPERED\n", encoding="utf-8")
    assert cli.cmd_verify(Namespace(manifest=str(manifest))) == 1

    # Missing referenced file
    charter.unlink()
    assert cli.cmd_verify(Namespace(manifest=str(manifest))) == 1

    # Unreadable/malformed JSON manifest
    manifest.write_text("{bad json", encoding="utf-8")
    assert cli.cmd_verify(Namespace(manifest=str(manifest))) == 1


def test_cli_init_keygen_approve_audit_status_and_badge(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "app"
    target.mkdir()

    # init --dry-run, real install, idempotent repeat, conflict, --force
    assert cli.cmd_init(Namespace(target=str(target), force=False, loaders=False, dry_run=True)) == 0
    assert cli.cmd_init(Namespace(target=str(target), force=False, loaders=True, dry_run=False)) == 0
    assert cli.cmd_init(Namespace(target=str(target), force=False, loaders=False, dry_run=False)) == 0

    charter_target = target / "Permanent_Active_Directives.txt"
    if charter_target.exists():
        charter_target.write_text("tampered", encoding="utf-8")
        assert cli.cmd_init(Namespace(target=str(target), force=False, loaders=False, dry_run=False)) == 1
        assert cli.cmd_init(Namespace(target=str(target), force=True, loaders=False, dry_run=False)) == 0

    # keygen (standard + overwrite guard + dpapi)
    keys_dir = tmp_path / ".keys"
    assert cli.cmd_keygen(Namespace(out=str(keys_dir), dpapi=False)) == 0
    assert (keys_dir / "operator.key").exists()
    assert (keys_dir / "operator.pub").exists()
    assert cli.cmd_keygen(Namespace(out=str(keys_dir), dpapi=True)) == 1  # refuses silent overwrite
    assert cli.cmd_keygen(Namespace(out=str(keys_dir), dpapi=True, force=True)) == 0
    assert (keys_dir / "operator.dpapi.key").exists()

    # approve (file payload, inline JSON, stdout, --out, errors)
    payload_file = tmp_path / "payload.json"
    payload_file.write_text('{"path": "demo.txt"}', encoding="utf-8")
    token_out = tmp_path / "tokens" / "act1.json"
    assert cli.cmd_approve(
        Namespace(
            action_id="act-001",
            tool="write_file",
            payload=str(payload_file),
            key=str(keys_dir / "operator.key"),
            ttl=120,
            out=str(token_out),
        )
    ) == 0
    assert json.loads(token_out.read_text(encoding="utf-8"))["action_id"] == "act-001"

    # Without operator.pub beside key (tests pubkey derivation branch)
    priv_only = tmp_path / "priv_only.key"
    priv_seed, _ = generate_ed25519_keypair()
    priv_only.write_bytes(priv_seed)
    assert cli.cmd_approve(
        Namespace(
            action_id="act-002",
            tool="run_command",
            payload="not-json-raw",
            key=str(priv_only),
            ttl=60,
            out=None,
        )
    ) == 0

    # Missing key / bad key length / invalid colon in action_id
    assert cli.cmd_approve(Namespace(action_id="a", tool="t", payload="{}", key=str(tmp_path / "missing.key"), ttl=60, out=None)) == 1
    bad_len_key = tmp_path / "short.key"
    bad_len_key.write_bytes(b"short")
    assert cli.cmd_approve(Namespace(action_id="a", tool="t", payload="{}", key=str(bad_len_key), ttl=60, out=None)) == 1
    assert cli.cmd_approve(Namespace(action_id="bad:id", tool="t", payload="{}", key=str(priv_only), ttl=60, out=None)) == 1

    # status & audit-ledger on target repo
    manifest_target = target / "config" / "charter_manifest.json"
    ledger_target = target / ".ledger" / "events.jsonl"
    monkeypatch.chdir(target)
    kernel = GovernanceKernel(
        manifest_path=manifest_target,
        ledger_path=ledger_target,
        halt_file=target / ".halt",
        operator_pubkey_path=keys_dir / "operator.pub",
    )
    kernel.intercept_and_execute("read_file", {"path": "README.md"}, lambda p: "ok")
    assert cli.cmd_audit_ledger(Namespace(ledger=str(ledger_target))) == 0
    assert cli.cmd_status(Namespace(manifest=str(manifest_target), ledger=str(ledger_target))) == 0

    # badge formats
    badge_out = tmp_path / "badge.svg"
    assert cli.cmd_badge(Namespace(out=str(badge_out), format="json", style="flat")) == 0
    assert cli.cmd_badge(Namespace(out=str(badge_out), format="markdown", style="flat-square")) == 0
    rc_svg = cli.cmd_badge(Namespace(out=str(badge_out), format="svg", style="flat"))
    assert rc_svg in (0, 1)
    assert badge_out.exists()


def test_cli_main_entrypoint(monkeypatch, tmp_path):
    _, _, manifest, _ = _setup_workspace(tmp_path)
    monkeypatch.setattr(sys, "argv", ["agy-governance", "--manifest", str(manifest), "verify"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 0


def test_cli_approve_wrong_passphrase_stale_pub_scope_and_manifest_checkpoint(monkeypatch, tmp_path):
    root, charter, manifest, ledger = _setup_workspace(tmp_path)
    keys_dir = root / ".keys"
    assert cli.cmd_keygen(Namespace(out=str(keys_dir), dpapi=False)) == 0
    priv_seed, pub = generate_ed25519_keypair()
    blob = DPAPIKeyStore.protect_with_passphrase(priv_seed, "correct-pass")
    enc_key = keys_dir / "enc.dpapi.key"
    enc_key.write_bytes(blob)

    # Wrong passphrase returns 1 cleanly instead of unhandled ValueError
    monkeypatch.setenv("AGL_KEY_PASSPHRASE", "wrong-pass")
    assert cli.cmd_approve(
        Namespace(action_id="a1", tool="t", payload="{}", key=str(enc_key), ttl=60, out=None)
    ) == 1

    # Right passphrase with stale operator.pub in same folder derives correct key + AGL-V2 scope
    monkeypatch.setenv("AGL_KEY_PASSPHRASE", "correct-pass")
    tok_out = tmp_path / "v2.json"
    assert cli.cmd_approve(
        Namespace(
            action_id="a2", tool="write_file", payload='{"path":"x"}',
            key=str(enc_key), ttl=60, scope="proj-x", out=str(tok_out),
        )
    ) == 0
    tok = json.loads(tok_out.read_text(encoding="utf-8"))
    assert tok["version"] == "AGL-V2" and tok["operator_pubkey"] == pub.hex()

    # Sign manifest and checkpoint ledger
    (keys_dir / "operator.pub").write_text(pub.hex(), encoding="utf-8")
    sig_out = root / "config" / "charter_manifest.sig"
    assert cli.cmd_sign_manifest(Namespace(manifest=str(manifest), key=str(enc_key), out=str(sig_out))) == 0
    kernel = GovernanceKernel(
        manifest_path=manifest,
        ledger_path=ledger,
        operator_pubkey_path=keys_dir / "operator.pub",
        halt_file=root / ".halt",
        require_manifest_signature=True,
    )
    cp_out = tmp_path / "cp.json"
    assert cli.cmd_checkpoint(Namespace(ledger=str(ledger), key=str(enc_key), scope=kernel.domain_scope, out=str(cp_out))) == 0
    assert cli.cmd_audit_ledger(
        Namespace(ledger=str(ledger), checkpoint=str(cp_out), pubkey=str(keys_dir / "operator.pub"), manifest=str(manifest))
    ) == 0

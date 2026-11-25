"""
Autonomous Governance Laws — CLI Entry Point

Usage:
    agy-governance init          Install the charter into a project (byte-exact, verified)
    agy-governance verify        Verify charter file integrity (LAW10-CHARTER)
    agy-governance audit-ledger  Verify event ledger hash chain (LAW9-CHAIN)
    agy-governance status        Show governance kernel status summary
    agy-governance badge         Generate compliance certification SVG badge
    agy-governance keygen        Generate operator Ed25519 keypair (with DPAPI support)
    agy-governance approve       Sign single-use authorization token for elevated actions
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure src root is in sys.path when executed directly
_src_root = str(Path(__file__).resolve().parent.parent)
if _src_root not in sys.path:
    sys.path.insert(0, _src_root)


def cmd_verify(args: argparse.Namespace) -> int:
    """Verify charter integrity digests."""
    from autonomous_governance.kernel import check_charter_files

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"  ❌ Charter manifest not found: {manifest_path}")
        return 1

    print("=" * 68)
    print("  CHARTER INTEGRITY VERIFICATION — LAW10-CHARTER")
    print("=" * 68)

    try:
        checks = check_charter_files(manifest_path)
    except (OSError, ValueError) as exc:
        print(f"  ❌ Charter manifest unreadable: {exc}")
        return 1

    all_passed = True
    for check in checks:
        if check.computed is None:
            print(f"  ❌ MISSING: {check.name}")
            all_passed = False
        elif check.ok:
            print(f"  ✅ {check.name}: {check.computed[:32]}...")
        else:
            print(f"  ❌ {check.name}: MISMATCH")
            all_passed = False

    print()
    if all_passed:
        print("  ✅ ALL DIGESTS VERIFIED")
    else:
        print("  ❌ INTEGRITY VIOLATION DETECTED")
    return 0 if all_passed else 1


def cmd_audit_ledger(args: argparse.Namespace) -> int:
    """Audit the event ledger hash chain and optional signed checkpoint."""
    from autonomous_governance.kernel import GovernanceKernel, resolve_project_root
    from autonomous_governance.security import verify_ledger_checkpoint

    kernel = GovernanceKernel.__new__(GovernanceKernel)
    kernel.ledger_path = Path(args.ledger)

    print("=" * 68)
    print("  LEDGER INTEGRITY AUDIT — LAW9-CHAIN")
    print("=" * 68)

    result = kernel.audit_ledger()

    print(f"  Total Events:  {result['total_events']}")
    print(f"  Broken Links:  {result['broken_links']}")
    print(f"  Valid:          {'✅ YES' if result['valid'] else '❌ NO'}")

    if result['errors']:
        print()
        for err in result['errors'][:10]:
            print(f"  ⚠ {err}")
        if len(result['errors']) > 10:
            print(f"  ... and {len(result['errors']) - 10} more errors")

    checkpoint_arg = getattr(args, "checkpoint", None)
    if checkpoint_arg:
        cp_path = Path(checkpoint_arg)
        if not cp_path.exists():
            print(f"  ❌ Checkpoint file not found: {cp_path}")
            return 1
        try:
            checkpoint = json.loads(cp_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"  ❌ Checkpoint unreadable: {exc}")
            return 1
        pub_arg = getattr(args, "pubkey", None)
        if pub_arg:
            pub_path = Path(pub_arg)
        else:
            root = resolve_project_root(getattr(args, "manifest", "config/charter_manifest.json"))
            pub_path = root / ".keys" / "operator.pub"
        if not pub_path.exists():
            print(f"  ❌ Operator public key not found for checkpoint verification: {pub_path}")
            return 1
        raw_pub = pub_path.read_bytes()
        pub_bytes = raw_pub if len(raw_pub) == 32 else bytes.fromhex(raw_pub.decode("ascii").strip())
        ok, reason = verify_ledger_checkpoint(checkpoint, pub_bytes)
        if not ok:
            print(f"  ❌ Checkpoint signature invalid: {reason}")
            return 1
        head_hash, _ = kernel._read_tail()
        if result["total_events"] != checkpoint["event_count"] or head_hash != checkpoint["head_hash"]:
            print(
                f"  ❌ Checkpoint mismatch (ledger={result['total_events']} events / {head_hash[:12]}..., "
                f"checkpoint={checkpoint['event_count']} events / {checkpoint['head_hash'][:12]}...)"
            )
            return 1
        print(f"  ✅ Checkpoint: Verified ({checkpoint['event_count']} events)")

    return 0 if result['valid'] else 1


def cmd_status(args: argparse.Namespace) -> int:
    """Show governance kernel status and cryptographic health."""
    from autonomous_governance.kernel import resolve_project_root
    from autonomous_governance.security import DPAPIKeyStore, _HAS_CRYPTOGRAPHY

    print("=" * 68)
    print("  AUTONOMOUS GOVERNANCE LAWS — STATUS")
    print("=" * 68)
    print()

    manifest_path = Path(args.manifest)
    project_root = resolve_project_root(manifest_path) if manifest_path.exists() else Path.cwd()
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        print(f"  Manifest Version:   {manifest.get('version', 'unknown')}")
        print(f"  Charter Files:      {len(manifest.get('charter_files', {}))}")
        print(f"  Operator:           {manifest.get('operator', {}).get('name', 'unknown')}")
        sig_path = manifest_path.with_suffix(".sig")
        print(f"  Manifest Signature: {'🟢 Present' if sig_path.exists() else '⚪ Not signed'}")
    else:
        print(f"  ⚠ Manifest not found: {manifest_path}")

    ledger_path = Path(args.ledger)
    if ledger_path.exists():
        with open(ledger_path, "r", encoding="utf-8", errors="replace") as f:
            line_count = sum(1 for line in f if line.strip())
        print(f"  Ledger Events:      {line_count}")
    else:
        print("  Ledger:             Not initialized")

    halt_file = project_root / ".halt"
    if not halt_file.exists() and Path(".halt").exists():
        halt_file = Path(".halt")
    print(f"  Halt Status:        {'🔴 ACTIVE' if halt_file.exists() else '🟢 Normal'}")

    # Cryptographic / Hardware Security Status
    dpapi_avail = DPAPIKeyStore.is_dpapi_available()
    print(f"  Windows DPAPI:      {'🟢 Available (Hardware Bound)' if dpapi_avail else '⚪ Not Available / POSIX Mode'}")
    print(
        f"  Ed25519 Backend:    {'🟢 cryptography/OpenSSL (constant-time)' if _HAS_CRYPTOGRAPHY else '⚠ Pure-Python fallback (non-constant-time)'}"
    )

    keys_dir = project_root / ".keys"
    if not (keys_dir / "operator.pub").exists() and Path(".keys/operator.pub").exists():
        keys_dir = Path(".keys")
    operator_pub = keys_dir / "operator.pub"
    if operator_pub.exists():
        print(f"  Operator Pubkey:    🟢 Found ({operator_pub.read_text(encoding='utf-8').strip()[:16]}...)")
    else:
        print("  Operator Pubkey:    ⚪ None configured (run 'agy-governance keygen')")

    print()
    return 0


def cmd_badge(args: argparse.Namespace) -> int:
    """Generate compliance certification badge."""
    from autonomous_governance.badge import generate_badge_asset

    out_path = Path(args.out) if args.out else Path("assets/compliance_badge.svg")
    content, audit = generate_badge_asset(
        output_path=out_path if args.format == "svg" else None,
        format_type=args.format,
        style=args.style,
    )

    if args.format != "svg":
        print(content)
        return 0

    print("=" * 68)
    print("  AUTONOMOUS GOVERNANCE LAWS — COMPLIANCE CERTIFICATION")
    print("=" * 68)
    print(f"  Status:          {audit['status']} ({audit['score']}/100)")
    print(f"  Message:         {audit['message']}")
    print(f"  Charter Passed:  {'✅ Yes' if audit['details']['charter_passed'] else '❌ No'}")
    print(f"  Ledger Valid:    {'✅ Yes' if audit['details']['ledger_valid'] else '❌ No'}")
    print(f"  Linter Score:    {audit['details']['linter_score']}/100 ({audit['details']['linter_findings']} findings)")
    print(f"  Badge Output:    {out_path}")
    print()
    return 0 if audit['score'] >= 80 else 1


def cmd_keygen(args: argparse.Namespace) -> int:
    """Generate Ed25519 operator keypair with optional DPAPI/passphrase protection."""
    from autonomous_governance.security import generate_ed25519_keypair, DPAPIKeyStore, _HAS_AESGCM

    out_dir = Path(args.out) if args.out else Path(".keys")
    pub_file = out_dir / "operator.pub"
    key_filename = "operator.dpapi.key" if args.dpapi else "operator.key"
    key_file = out_dir / key_filename
    force = bool(getattr(args, "force", False))

    if not force and (pub_file.exists() or key_file.exists()):
        existing = [str(p) for p in (pub_file, key_file) if p.exists()]
        print(f"  ❌ Key file(s) already exist: {', '.join(existing)}. Pass --force to overwrite.")
        return 1

    priv_seed, pub_key = generate_ed25519_keypair()
    allow_plain = bool(getattr(args, "allow_plaintext", False))
    try:
        DPAPIKeyStore.save_key(
            key_file,
            priv_seed,
            use_dpapi=args.dpapi,
            allow_plaintext_fallback=allow_plain,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"  ❌ Could not store operator private key: {exc}")
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    pub_file.write_text(pub_key.hex(), encoding="utf-8")

    print("=" * 68)
    print("  OPERATOR ASYMMETRIC KEYPAIR GENERATION — Ed25519")
    print("=" * 68)
    print(f"  Public Key:    {pub_file} ({pub_key.hex()[:16]}...)")
    print(f"  Private Key:   {key_file}")
    if args.dpapi and DPAPIKeyStore.is_dpapi_available():
        dpapi_status = "Enabled (Windows Hardware-Tied DPAPI)"
    elif args.dpapi and not allow_plain:
        dpapi_status = "POSIX Passphrase Encrypted (PBKDF2-600k + " + ("AES-256-GCM)" if _HAS_AESGCM else "HMAC-CTR)")
    else:
        dpapi_status = "Unencrypted (0600 permissions)"
    print(f"  Protection:    {dpapi_status}")
    print()
    return 0


def _load_seed_from_cli(key_path: Path) -> bytes:
    from autonomous_governance.security import DPAPIKeyStore

    if not key_path.exists():
        raise FileNotFoundError(f"Operator key file not found: {key_path}")
    is_dpapi = ".dpapi" in key_path.name
    priv_seed = DPAPIKeyStore.load_key(key_path, is_dpapi=is_dpapi)
    if len(priv_seed) != 32:
        raise ValueError(
            f"Operator key must be a 32-byte Ed25519 seed (got {len(priv_seed)} bytes): {key_path}"
        )
    return priv_seed


def cmd_approve(args: argparse.Namespace) -> int:
    """Sign an elevated action to generate a single-use authorization token."""
    from autonomous_governance.security import create_approval_token, derive_ed25519_public_key

    key_path = Path(args.key)
    try:
        priv_seed = _load_seed_from_cli(key_path)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"  ❌ Could not load operator key {key_path}: {exc}")
        return 1

    pub_key = derive_ed25519_public_key(priv_seed)

    payload = {}
    if args.payload:
        payload_path = Path(args.payload)
        if payload_path.exists():
            payload = json.loads(payload_path.read_text(encoding="utf-8"))
        else:
            try:
                payload = json.loads(args.payload)
            except Exception:
                payload = {"raw": args.payload}

    scope = getattr(args, "scope", None)
    try:
        token = create_approval_token(
            action_id=args.action_id,
            tool_name=args.tool,
            payload=payload,
            private_seed=priv_seed,
            public_key=pub_key,
            ttl_seconds=args.ttl,
            scope=scope,
        )
    except ValueError as exc:
        print(f"  ❌ Could not create approval token: {exc}")
        return 1

    token_json = json.dumps(token, indent=2)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(token_json, encoding="utf-8")
        print(f"  ✅ Approval token written to: {out_path}")
    else:
        print(token_json)
    return 0


def cmd_sign_manifest(args: argparse.Namespace) -> int:
    """Create a detached Ed25519 signature for charter_manifest.json."""
    from autonomous_governance.security import sign_manifest

    manifest_path = Path(args.manifest)
    if not manifest_path.is_file():
        print(f"  ❌ Charter manifest not found: {manifest_path}")
        return 1
    key_path = Path(args.key)
    try:
        priv_seed = _load_seed_from_cli(key_path)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"  ❌ Could not load operator key {key_path}: {exc}")
        return 1
    out_path = Path(args.out) if args.out else manifest_path.with_suffix(".sig")
    sig_hex = sign_manifest(manifest_path, priv_seed, sig_path=out_path)
    print(f"  ✅ Signed manifest {manifest_path} -> {out_path} ({sig_hex[:16]}...)")
    return 0


def cmd_checkpoint(args: argparse.Namespace) -> int:
    """Sign a tamper-evident checkpoint over the current ledger head."""
    from autonomous_governance.kernel import GovernanceKernel
    from autonomous_governance.security import sign_ledger_checkpoint

    key_path = Path(args.key)
    try:
        priv_seed = _load_seed_from_cli(key_path)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"  ❌ Could not load operator key {key_path}: {exc}")
        return 1

    kernel = GovernanceKernel.__new__(GovernanceKernel)
    kernel.ledger_path = Path(args.ledger)
    report = kernel.audit_ledger()
    if not report["valid"]:
        print(f"  ❌ Cannot checkpoint broken ledger ({report['broken_links']} broken link(s))")
        return 1
    head_hash, _ = kernel._read_tail()
    checkpoint = sign_ledger_checkpoint(
        event_count=report["total_events"],
        head_hash=head_hash,
        private_seed=priv_seed,
        scope=getattr(args, "scope", "") or "",
    )
    cp_json = json.dumps(checkpoint, indent=2)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(cp_json, encoding="utf-8")
        print(f"  ✅ Signed ledger checkpoint written to: {out_path} ({report['total_events']} events)")
    else:
        print(cp_json)
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    """Install the charter (three documents + manifest) into a project, byte-for-byte."""
    from autonomous_governance.installer import CharterSourceError, charter_source, install_charter

    try:
        source = charter_source()
        result = install_charter(
            args.target, force=args.force, loaders=args.loaders, dry_run=args.dry_run, source=source
        )
    except (CharterSourceError, OSError) as exc:
        print(f"  ❌ {exc}")
        return 1

    print("=" * 68)
    print("  CHARTER INSTALLATION — LAW10-CHARTER" + ("  (dry run)" if args.dry_run else ""))
    print("=" * 68)
    print(f"  Source:  {source} (charter v{result.version})")
    print(f"  Target:  {result.target}")
    print()

    notes = {
        "conflict": "differs from the charter; nothing written. Re-run with --force to replace it",
        "overwrite": "replaced (--force)",
        "equivalent": "line endings differ only; verifies unchanged",
        "exists": "kept as-is; loaders never overwrite. Add the loader text manually",
    }
    for planned in result.files:
        status = f"would {planned.status}" if args.dry_run and planned.writes else planned.status
        note = notes.get(planned.status)
        print(f"  {status:<16} {planned.rel}" + (f"  ({note})" if note else ""))
    print()

    if result.conflicts:
        print(f"  ❌ {len(result.conflicts)} conflicting file(s); target left unchanged.")
        return 1
    if args.dry_run:
        print("  ✅ Plan is clean. Re-run without --dry-run to apply it.")
        return 0
    if not result.ok:
        failed = ", ".join(c.name for c in result.checks if not c.ok) or "no charter files"
        print(f"  ❌ Post-install verification failed: {failed}")
        return 1

    changed = any(planned.writes for planned in result.files)
    verdict = "installed and verified" if changed else "already installed; verified, nothing changed"
    print(f"  ✅ Charter {verdict} ({len(result.checks)} documents).")
    print()
    print("  Next steps:")
    print("    agy-governance keygen     # pin an operator key; elevated actions fail closed without one")
    print("    agy-governance verify     # re-check the charter at any time")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="agy-governance",
        description="Autonomous Governance Laws — Runtime CLI",
    )
    parser.add_argument(
        "--manifest",
        default="config/charter_manifest.json",
        help="Path to charter_manifest.json",
    )
    parser.add_argument(
        "--ledger",
        default=".ledger/events.jsonl",
        help="Path to the event ledger file",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # verify
    subparsers.add_parser("verify", help="Verify charter integrity (LAW10-CHARTER)")

    # init
    p_init = subparsers.add_parser(
        "init", help="Install the charter documents and manifest into a project (byte-exact)"
    )
    p_init.add_argument("--target", default=".", help="Project directory to install into (default: current)")
    p_init.add_argument("--force", action="store_true", help="Replace charter files that differ")
    p_init.add_argument(
        "--loaders", action="store_true",
        help="Also write host loaders (AGENTS.md, CLAUDE.md, .agents/rules/); never overwrites",
    )
    p_init.add_argument("--dry-run", action="store_true", help="Show the plan without writing anything")

    # audit-ledger
    p_audit = subparsers.add_parser("audit-ledger", help="Audit event ledger hash chain (LAW9-CHAIN)")
    p_audit.add_argument("--checkpoint", help="Optional signed checkpoint JSON file to verify against tail")
    p_audit.add_argument("--pubkey", help="Operator public key for checkpoint verification")

    # status
    subparsers.add_parser("status", help="Show governance kernel status")

    # badge
    p_badge = subparsers.add_parser("badge", help="Generate compliance certification badge")
    p_badge.add_argument("--out", default="assets/compliance_badge.svg", help="Output path for badge")
    p_badge.add_argument("--format", choices=["svg", "json", "markdown"], default="svg", help="Output format")
    p_badge.add_argument("--style", choices=["flat", "flat-square"], default="flat", help="Badge visual style")

    # keygen
    p_keygen = subparsers.add_parser("keygen", help="Generate operator Ed25519 keypair")
    p_keygen.add_argument("--out", default=".keys", help="Output directory for keypair")
    p_keygen.add_argument("--dpapi", action="store_true", help="Encrypt private key with DPAPI or POSIX passphrase")
    p_keygen.add_argument("--force", action="store_true", help="Overwrite existing key files")
    p_keygen.add_argument(
        "--allow-plaintext", action="store_true",
        help="Allow unencrypted POSIX fallback marker when AGL_KEY_PASSPHRASE is unset",
    )

    # approve
    p_approve = subparsers.add_parser("approve", help="Generate single-use signed authorization token")
    p_approve.add_argument("--action-id", required=True, help="Unique action ID (e.g. act-001)")
    p_approve.add_argument("--tool", required=True, help="Tool name to authorize")
    p_approve.add_argument("--payload", default="{}", help="Tool argument payload (JSON string or file path)")
    p_approve.add_argument("--key", default=".keys/operator.key", help="Path to operator private key")
    p_approve.add_argument("--ttl", type=int, default=300, help="Token validity lifetime in seconds")
    p_approve.add_argument("--scope", help="Optional domain scope string to emit an AGL-V2 token")
    p_approve.add_argument("--out", help="Output path for token JSON file")

    # sign-manifest
    p_sign_manifest = subparsers.add_parser("sign-manifest", help="Sign charter_manifest.json with Ed25519")
    p_sign_manifest.add_argument("--key", default=".keys/operator.key", help="Path to operator private key")
    p_sign_manifest.add_argument("--out", help="Output .sig path (default: <manifest>.sig)")

    # checkpoint
    p_checkpoint = subparsers.add_parser("checkpoint", help="Sign a tamper-evident ledger head checkpoint")
    p_checkpoint.add_argument("--key", default=".keys/operator.key", help="Path to operator private key")
    p_checkpoint.add_argument("--scope", default="", help="Optional domain scope bound into checkpoint")
    p_checkpoint.add_argument("--out", help="Output path for checkpoint JSON file")

    args = parser.parse_args()

    commands = {
        "verify": cmd_verify,
        "init": cmd_init,
        "audit-ledger": cmd_audit_ledger,
        "status": cmd_status,
        "badge": cmd_badge,
        "keygen": cmd_keygen,
        "approve": cmd_approve,
        "sign-manifest": cmd_sign_manifest,
        "checkpoint": cmd_checkpoint,
    }

    sys.exit(commands[args.command](args))


if __name__ == "__main__":
    main()

"""
Autonomous Governance Laws — CLI Entry Point

Usage:
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
    from autonomous_governance.kernel import GovernanceKernel

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"  ❌ Charter manifest not found: {manifest_path}")
        return 1

    print("=" * 68)
    print("  CHARTER INTEGRITY VERIFICATION — LAW10-CHARTER")
    print("=" * 68)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    charter_files = manifest.get("charter_files", {})
    all_passed = True

    for file_name, expected_hash in charter_files.items():
        file_path = Path(file_name)
        expected_hash = expected_hash.lower()

        if not file_path.exists():
            print(f"  ❌ MISSING: {file_name}")
            all_passed = False
            continue

        computed = GovernanceKernel._compute_sha256(file_path)
        if computed == expected_hash:
            print(f"  ✅ {file_name}: {computed[:32]}...")
        else:
            print(f"  ❌ {file_name}: MISMATCH")
            all_passed = False

    print()
    if all_passed:
        print("  ✅ ALL DIGESTS VERIFIED")
    else:
        print("  ❌ INTEGRITY VIOLATION DETECTED")
    return 0 if all_passed else 1


def cmd_audit_ledger(args: argparse.Namespace) -> int:
    """Audit the event ledger hash chain."""
    from autonomous_governance.kernel import GovernanceKernel

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

    return 0 if result['valid'] else 1


def cmd_status(args: argparse.Namespace) -> int:
    """Show governance kernel status and cryptographic health."""
    from autonomous_governance.security import DPAPIKeyStore

    print("=" * 68)
    print("  AUTONOMOUS GOVERNANCE LAWS — STATUS")
    print("=" * 68)
    print()

    manifest_path = Path(args.manifest)
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        print(f"  Manifest Version:   {manifest.get('version', 'unknown')}")
        print(f"  Charter Files:      {len(manifest.get('charter_files', {}))}")
        print(f"  Operator:           {manifest.get('operator', {}).get('name', 'unknown')}")
    else:
        print(f"  ⚠ Manifest not found: {manifest_path}")

    ledger_path = Path(args.ledger)
    if ledger_path.exists():
        line_count = sum(1 for line in open(ledger_path) if line.strip())
        print(f"  Ledger Events:      {line_count}")
    else:
        print(f"  Ledger:             Not initialized")

    halt_file = Path(".halt")
    print(f"  Halt Status:        {'🔴 ACTIVE' if halt_file.exists() else '🟢 Normal'}")

    # Cryptographic / Hardware Security Status
    dpapi_avail = DPAPIKeyStore.is_dpapi_available()
    print(f"  Windows DPAPI:      {'🟢 Available (Hardware Bound)' if dpapi_avail else '⚪ Not Available / POSIX Mode'}")

    keys_dir = Path(".keys")
    operator_pub = keys_dir / "operator.pub"
    if operator_pub.exists():
        print(f"  Operator Pubkey:    🟢 Found ({operator_pub.read_text().strip()[:16]}...)")
    else:
        print(f"  Operator Pubkey:    ⚪ None configured (run 'agy-governance keygen')")

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
    """Generate Ed25519 operator keypair with optional DPAPI hardware protection."""
    from autonomous_governance.security import generate_ed25519_keypair, DPAPIKeyStore

    out_dir = Path(args.out) if args.out else Path(".keys")
    out_dir.mkdir(parents=True, exist_ok=True)
    priv_seed, pub_key = generate_ed25519_keypair()

    pub_file = out_dir / "operator.pub"
    pub_file.write_text(pub_key.hex(), encoding="utf-8")

    key_filename = "operator.dpapi.key" if args.dpapi else "operator.key"
    key_file = out_dir / key_filename
    DPAPIKeyStore.save_key(key_file, priv_seed, use_dpapi=args.dpapi)

    print("=" * 68)
    print("  OPERATOR ASYMMETRIC KEYPAIR GENERATION — Ed25519")
    print("=" * 68)
    print(f"  Public Key:    {pub_file} ({pub_key.hex()[:16]}...)")
    print(f"  Private Key:   {key_file}")
    dpapi_status = "Enabled (Windows Hardware-Tied DPAPI)" if (args.dpapi and DPAPIKeyStore.is_dpapi_available()) else "Standard File Protection"
    print(f"  Protection:    {dpapi_status}")
    print()
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    """Sign an elevated action to generate a single-use authorization token."""
    from autonomous_governance.security import create_approval_token, DPAPIKeyStore

    key_path = Path(args.key)
    if not key_path.exists():
        print(f"  ❌ Operator key file not found: {key_path}")
        return 1

    is_dpapi = ".dpapi" in key_path.name
    priv_seed = DPAPIKeyStore.load_key(key_path, is_dpapi=is_dpapi)

    # Derive public key or load from .pub
    pub_path = key_path.with_name("operator.pub")
    if pub_path.exists():
        pub_key = bytes.fromhex(pub_path.read_text().strip())
    else:
        from autonomous_governance.security import _scalar_mult, _B, _point_to_bytes
        import hashlib
        h = hashlib.sha512(priv_seed).digest()
        a = int.from_bytes(h[:32], "little")
        a &= (1 << 254) - 8
        a |= (1 << 254)
        pub_key = _point_to_bytes(_scalar_mult(_B, a))

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

    token = create_approval_token(
        action_id=args.action_id,
        tool_name=args.tool,
        payload=payload,
        private_seed=priv_seed,
        public_key=pub_key,
        ttl_seconds=args.ttl,
    )

    token_json = json.dumps(token, indent=2)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(token_json, encoding="utf-8")
        print(f"  ✅ Approval token written to: {out_path}")
    else:
        print(token_json)
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

    # audit-ledger
    subparsers.add_parser("audit-ledger", help="Audit event ledger hash chain (LAW9-CHAIN)")

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
    p_keygen.add_argument("--dpapi", action="store_true", help="Encrypt private key with Windows DPAPI")

    # approve
    p_approve = subparsers.add_parser("approve", help="Generate single-use signed authorization token")
    p_approve.add_argument("--action-id", required=True, help="Unique action ID (e.g. act-001)")
    p_approve.add_argument("--tool", required=True, help="Tool name to authorize")
    p_approve.add_argument("--payload", default="{}", help="Tool argument payload (JSON string or file path)")
    p_approve.add_argument("--key", default=".keys/operator.key", help="Path to operator private key")
    p_approve.add_argument("--ttl", type=int, default=300, help="Token validity lifetime in seconds")
    p_approve.add_argument("--out", help="Output path for token JSON file")

    args = parser.parse_args()

    commands = {
        "verify": cmd_verify,
        "audit-ledger": cmd_audit_ledger,
        "status": cmd_status,
        "badge": cmd_badge,
        "keygen": cmd_keygen,
        "approve": cmd_approve,
    }

    sys.exit(commands[args.command](args))


if __name__ == "__main__":
    main()

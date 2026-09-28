"""
Autonomous Governance Laws — CLI Entry Point

Usage:
    agy-governance verify        Verify charter file integrity (LAW10-CHARTER)
    agy-governance audit-ledger  Verify event ledger hash chain (LAW9-CHAIN)
    agy-governance status        Show governance kernel status summary
"""

import argparse
import json
import sys
from pathlib import Path


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
    """Show governance kernel status."""
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
    print()

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
    subparsers.add_parser("verify", help="Verify charter integrity (LAW10-CHARTER)")
    subparsers.add_parser("audit-ledger", help="Audit event ledger hash chain (LAW9-CHAIN)")
    subparsers.add_parser("status", help="Show governance kernel status")

    args = parser.parse_args()

    commands = {
        "verify": cmd_verify,
        "audit-ledger": cmd_audit_ledger,
        "status": cmd_status,
    }

    sys.exit(commands[args.command](args))


if __name__ == "__main__":
    main()

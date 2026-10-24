#!/usr/bin/env python3
"""
Autonomous Governance Laws — Charter Integrity Verification Script

Verifies the SHA-256 digests of all constitutional charter documents against
the canonical manifest at config/charter_manifest.json.

Implements: LAW10-CHARTER invariant
Usage:      python scripts/verify_charter.py
Exit Code:  0 = All digests match | 1 = Integrity violation detected
"""

import hashlib
import json
import sys
from pathlib import Path


def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hex digest of a file with normalized LF line endings."""
    with open(file_path, "rb") as f:
        content = f.read().replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()



def verify_charter(repo_root: Path | None = None) -> bool:
    """
    Verify all charter files against config/charter_manifest.json.

    Returns True if all digests match, False otherwise.
    Prints detailed results to stdout.
    """
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent

    manifest_path = repo_root / "config" / "charter_manifest.json"

    print("=" * 72)
    print("  AUTONOMOUS GOVERNANCE LAWS — CHARTER INTEGRITY VERIFICATION")
    print("  Invariant: LAW10-CHARTER")
    print("=" * 72)
    print()

    # 1. Check manifest exists
    if not manifest_path.exists():
        print(f"  ❌ FATAL: Charter manifest not found at {manifest_path}")
        print("     Runtime initialization MUST fail. (LAW10-CHARTER)")
        return False

    # 2. Load manifest
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    algorithm = manifest.get("algorithm", "SHA-256")
    version = manifest.get("version", "unknown")
    charter_files = manifest.get("charter_files", {})

    print(f"  Manifest Version:  {version}")
    print(f"  Hash Algorithm:    {algorithm}")
    print(f"  Charter Files:     {len(charter_files)}")
    print()

    # 3. Verify each charter file
    all_passed = True
    for file_name, expected_hash in charter_files.items():
        file_path = repo_root / file_name
        expected_hash = expected_hash.lower()

        if not file_path.exists():
            print(f"  ❌ MISSING:  {file_name}")
            print(f"              File does not exist!")
            all_passed = False
            continue

        computed_hash = compute_sha256(file_path)

        if computed_hash == expected_hash:
            print(f"  ✅ PASSED:   {file_name}")
            print(f"              {computed_hash}")
        else:
            print(f"  ❌ FAILED:   {file_name}")
            print(f"     Expected: {expected_hash}")
            print(f"     Computed: {computed_hash}")
            all_passed = False

        print()

    # 4. Final verdict
    print("-" * 72)
    if all_passed:
        print("  ✅ VERDICT: ALL CHARTER DIGESTS VERIFIED — INTEGRITY CONFIRMED")
        print("     LAW10-CHARTER: PASSED")
    else:
        print("  ❌ VERDICT: CHARTER INTEGRITY VIOLATION DETECTED")
        print("     LAW10-CHARTER: FAILED")
        print("     Runtime initialization MUST NOT proceed.")
    print("-" * 72)

    return all_passed


if __name__ == "__main__":
    success = verify_charter()
    sys.exit(0 if success else 1)

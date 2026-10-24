"""
Autonomous Governance Laws — Constitutional AI Linter (`laws-lint`)
Audits agent prompts, tool schemas, and execution pipelines against Kirk LaSalle's 10 Laws,
the EU AI Act (Articles 9-15), and the NIST AI RMF 1.0.
Author: Kirk LaSalle & Antigravity AI
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

# The 10 Permanent Active Directives (Canonical Laws)
LAWS = {
    1: {"name": "Law 1: Prohibition of Irreversible Human/System Harm", "severity": "CRITICAL"},
    2: {"name": "Law 2: Absolute Operator Halt & Sovereign Override", "severity": "CRITICAL"},
    3: {"name": "Law 3: Sovereign Sandboxing & Local Boundary Isolation", "severity": "HIGH"},
    4: {"name": "Law 4: Adherence to Open Standards & Non-Proprietary Interop", "severity": "MEDIUM"},
    5: {"name": "Law 5: Deterministic Tool Bounds & Explicit Privilege Escalation", "severity": "HIGH"},
    6: {"name": "Law 6: Data Loss Prevention & Mandatory Pre-Delete Confirmation", "severity": "CRITICAL"},
    7: {"name": "Law 7: Transparency of Agent Identity & Non-Deception", "severity": "MEDIUM"},
    8: {"name": "Law 8: Empirical Physical Grounding & Mathematical Rigor", "severity": "LOW"},
    9: {"name": "Law 9: Cryptographic Hash Chaining & Immutable Action Ledger", "severity": "HIGH"},
    10: {"name": "Law 10: Sovereign Operator Supremacy & Non-Self-Clearing Gates", "severity": "CRITICAL"}
}

# Detection rules for dangerous anti-patterns
VIOLATION_PATTERNS = [
    # Law 1 & 6: Destructive execution without guardrails
    {
        "id": "AGL-101",
        "law": 1,
        "regex": r"(?:rm\s+-rf\s+[/~]|DROP\s+(?:DATABASE|TABLE|SCHEMA)|TRUNCATE\s+TABLE|format\s+[A-Za-z]:)",
        "msg": "Unconditional destructive disk or database command detected without protective guard.",
        "severity": "CRITICAL"
    },
    # Law 2 & 10: Ignoring operator cancellation
    {
        "id": "AGL-201",
        "law": 2,
        "regex": r"(?:ignore\s+(?:operator|user)\s+(?:stop|halt|cancel)|bypass_halt\s*=\s*True)",
        "msg": "Directive attempting to bypass or suppress operator halt commands.",
        "severity": "CRITICAL"
    },
    # Law 5: Unbounded shell execution
    {
        "id": "AGL-501",
        "law": 5,
        "regex": r"(?:\beval\s*\(|\bexec\s*\(|os\.system\([^)]*\$|subprocess\.Popen\([^)]*shell\s*=\s*True)",
        "msg": "Unsanitized dynamic shell/string evaluation exposes agent to prompt-injection escape.",
        "severity": "HIGH"
    },
    # Law 6: Hardcoded secret or private credential
    {
        "id": "AGL-601",
        "law": 6,
        "regex": r"(?:(?:api[_-]?key|secret|password|bearer|auth[_-]?token)\s*=\s*['\"][A-Za-z0-9_\-]{20,}['\"])",
        "msg": "Potential hardcoded plaintext credential violates Data Loss Prevention safeguards.",
        "severity": "HIGH"
    },
    # Law 10: Self-clearing emergency gates
    {
        "id": "AGL-1001",
        "law": 10,
        "regex": r"(?:auto_clear_incident|agent_override_emergency|bypass_sovereign_gate)",
        "msg": "Agent attempts to clear its own emergency state. Only Sovereign Operator (Kirk LaSalle) holds de-escalation authority.",
        "severity": "CRITICAL"
    }
]

class GovernanceLinter:
    def __init__(self, target_path: Path):
        self.target_path = target_path
        self.findings: List[Dict[str, Any]] = []
        self.files_scanned = 0

    def scan_file(self, file_path: Path):
        self.files_scanned += 1
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            return

        is_markdown = file_path.suffix.lower() in {".md", ".markdown"}
        in_code_block = False

        for line_no, line in enumerate(lines, 1):
            if is_markdown:
                stripped = line.strip()
                if stripped.startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    continue

            for rule in VIOLATION_PATTERNS:
                if re.search(rule["regex"], line, re.IGNORECASE):
                    self.findings.append({
                        "rule_id": rule["id"],
                        "law": rule["law"],
                        "law_name": LAWS[rule["law"]]["name"],
                        "severity": rule["severity"],
                        "file": str(file_path),
                        "line": line_no,
                        "snippet": line.strip()[:100],
                        "message": rule["msg"]
                    })

    def run(self) -> Dict[str, Any]:
        if self.target_path.is_file():
            self.scan_file(self.target_path)
        else:
            for root, dirs, files in os.walk(self.target_path):
                # Ignore common noisy directories, vendor code, and test suites by default
                dirs[:] = [d for d in dirs if d not in {".git", ".mcp", ".venv", "node_modules", "__pycache__", "dist", "build", ".pytest_cache", "tests"}]
                for file in files:
                    if file in {"linter.py", "kernel.py"}:
                        # Skip self-inspection of the governance rule definitions
                        continue
                    ext = os.path.splitext(file)[1].lower()
                    if ext in {".py", ".ts", ".tsx", ".js", ".json", ".md", ".txt", ".sh", ".bat", ".toml", ".yaml", ".yml"}:
                        self.scan_file(Path(root) / file)

        critical_count = sum(1 for f in self.findings if f["severity"] == "CRITICAL")
        high_count = sum(1 for f in self.findings if f["severity"] == "HIGH")
        medium_count = sum(1 for f in self.findings if f["severity"] == "MEDIUM")

        # Score calculation: 100 base minus deductions
        score = max(0, 100 - (critical_count * 25 + high_count * 10 + medium_count * 3))
        
        return {
            "score": score,
            "status": "COMPLIANT" if critical_count == 0 else "NON_COMPLIANT",
            "files_scanned": self.files_scanned,
            "total_findings": len(self.findings),
            "critical": critical_count,
            "high": high_count,
            "medium": medium_count,
            "findings": self.findings
        }

ConstitutionalLinter = GovernanceLinter

def print_report(res: Dict[str, Any]):
    print("=" * 72)
    print("      AUTONOMOUS GOVERNANCE LAWS — CONSTITUTIONAL LINTER (laws-lint)")
    print("       EU AI Act (Arts 9-15) & NIST AI RMF 1.0 Runtime Audit Engine")
    print("=" * 72)
    print(f"  • Files Scanned:       {res['files_scanned']}")
    print(f"  • Governance Score:    {res['score']} / 100")
    print(f"  • Constitutional Flag: {'🟢 COMPLIANT' if res['status'] == 'COMPLIANT' else '🔴 NON-COMPLIANT'}")
    print(f"  • Critical Breaches:   {res['critical']}")
    print(f"  • High-Risk Findings:  {res['high']}")
    print("=" * 72)

    if not res["findings"]:
        print("\n  ✅ Zero constitutional breaches detected. Codebase conforms to the 10 Laws.\n")
        return

    print("\n[FINDINGS]")
    for idx, f in enumerate(res["findings"], 1):
        color_prefix = "🔴" if f["severity"] == "CRITICAL" else ("🟠" if f["severity"] == "HIGH" else "🟡")
        print(f"\n{color_prefix} [{f['rule_id']}] {f['law_name']} ({f['severity']})")
        print(f"   Location: {f['file']}:{f['line']}")
        print(f"   Snippet:  `{f['snippet']}`")
        print(f"   Advisory: {f['message']}")
    print()

def main():
    parser = argparse.ArgumentParser(
        prog="laws-lint",
        description="Constitutional AI Linter enforcing Kirk LaSalle's 10 Laws for Autonomous Systems."
    )
    parser.add_argument("path", nargs="?", default=".", help="File or directory path to audit (default: current directory).")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON report.")
    parser.add_argument("--strict", action="store_true", help="Fail if any warning (even non-critical) is detected.")

    args = parser.parse_args()
    target = Path(args.path).resolve()
    
    if not target.exists():
        print(f"Error: Target path does not exist: {target}", file=sys.stderr)
        sys.exit(1)

    linter = GovernanceLinter(target)
    results = linter.run()

    if args.json:
        import json
        print(json.dumps(results, indent=2))
    else:
        print_report(results)

    if results["critical"] > 0 or (args.strict and results["total_findings"] > 0):
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()

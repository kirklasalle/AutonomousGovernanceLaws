"""
Autonomous Governance Laws — Compliance Certification Badge Generator

Generates high-resolution, certified compliance SVG badges and Shields.io endpoint
schemas for autonomous agent swarms and repositories complying with Kirk LaSalle's
10 Laws for Intelligence Systems.
"""

import json
from pathlib import Path
from typing import Any


def audit_repository_compliance(
    repo_root: Path | None = None,
    manifest_path: Path | None = None,
    ledger_path: Path | None = None,
    halt_path: Path | None = None,
) -> dict[str, Any]:
    """Run an automated compliance audit on the repository.

    Evaluates:
    - LAW10-CHARTER: All charter hashes match config/charter_manifest.json
    - LAW1-PROHIBIT / LAW3-SUBORDINATE: Constitutional code linter score (0-100)
    - LAW9-LEDGER / LAW9-CHAIN: Ledger hash-chain validity
    - LAW2-HALT: Absence of active .halt file

    Returns:
        dict with status, score, label, message, color, and audit details
    """
    if repo_root is None:
        repo_root = Path.cwd()

    if manifest_path is None:
        manifest_path = repo_root / "config" / "charter_manifest.json"
    if ledger_path is None:
        ledger_path = repo_root / ".ledger" / "events.jsonl"
    if halt_path is None:
        halt_path = repo_root / ".halt"

    # 1. Check Emergency Halt
    if halt_path.exists():
        return {
            "status": "HALTED",
            "score": 0,
            "label": "Autonomous Governance",
            "message": "EMERGENCY HALT ACTIVE",
            "color": "#ef4444",
            "shields_color": "red",
            "details": {"halt_active": True},
        }

    # 2. Check Charter Manifest Integrity
    from autonomous_governance.kernel import GovernanceKernel

    charter_passed = False
    charter_count = 0
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            charter_files = manifest.get("charter_files", {})
            charter_count = len(charter_files)
            charter_mismatches = 0
            for fn, expected_hash in charter_files.items():
                fpath = repo_root / fn
                if not fpath.exists() or GovernanceKernel._compute_sha256(fpath).lower() != expected_hash.lower():
                    charter_mismatches += 1
            charter_passed = (charter_count > 0 and charter_mismatches == 0)
        except Exception:
            charter_passed = False

    # 3. Check Ledger Integrity
    ledger_valid = True
    if ledger_path.exists():
        try:
            kernel = GovernanceKernel.__new__(GovernanceKernel)
            kernel.ledger_path = ledger_path
            ledger_audit = kernel.audit_ledger()
            ledger_valid = ledger_audit.get("valid", False)
        except Exception:
            ledger_valid = False

    # 4. Check Constitutional Linter
    from autonomous_governance.linter import ConstitutionalLinter
    linter = ConstitutionalLinter(repo_root)
    linter_res = linter.run()
    linter_score = linter_res.get("score", 0)

    # Determine overall certification status
    if not charter_passed:
        status = "NON_COMPLIANT"
        message = "CHARTER INTEGRITY FAILED"
        color = "#ef4444"
        shields_color = "red"
        effective_score = 0
    elif not ledger_valid:
        status = "TAMPERED"
        message = "LEDGER CORRUPTED"
        color = "#f59e0b"
        shields_color = "orange"
        effective_score = min(linter_score, 50)
    elif linter_score == 100:
        status = "COMPLIANT"
        message = "100/100 COMPLIANT"
        color = "#10b981"
        shields_color = "brightgreen"
        effective_score = 100
    elif linter_score >= 80:
        status = "CERTIFIED"
        message = f"{linter_score}/100 CERTIFIED"
        color = "#3b82f6"
        shields_color = "blue"
        effective_score = linter_score
    else:
        status = "REVIEW_REQUIRED"
        message = f"{linter_score}/100 WARNINGS"
        color = "#f59e0b"
        shields_color = "yellow"
        effective_score = linter_score

    return {
        "status": status,
        "score": effective_score,
        "label": "Autonomous Governance",
        "message": message,
        "color": color,
        "shields_color": shields_color,
        "details": {
            "charter_passed": charter_passed,
            "charter_count": charter_count,
            "ledger_valid": ledger_valid,
            "linter_score": linter_score,
            "linter_findings": len(linter_res.get("findings", [])),
        },
    }


def render_svg_badge(
    label: str,
    message: str,
    color: str,
    style: str = "flat",
) -> str:
    """Render a standalone vector SVG badge.

    Args:
        label: Left badge text (e.g. 'Autonomous Governance')
        message: Right badge text (e.g. '100/100 COMPLIANT')
        color: Hex color for the right status box (e.g. '#10b981')
        style: 'flat' or 'flat-square'
    """
    # Estimate widths based on character counts
    label_len = len(label)
    msg_len = len(message)
    label_width = max(label_len * 7 + 16, 80)
    msg_width = max(msg_len * 7 + 16, 70)
    total_width = label_width + msg_width
    height = 22
    rx = 0 if style == "flat-square" else 3

    label_center_x = label_width / 2.0
    msg_center_x = label_width + (msg_width / 2.0)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{height}" role="img" aria-label="{label}: {message}">
  <title>{label}: {message}</title>
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="a">
    <rect width="{total_width}" height="{height}" rx="{rx}" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#a)">
    <rect width="{label_width}" height="{height}" fill="#1e293b"/>
    <rect x="{label_width}" width="{msg_width}" height="{height}" fill="{color}"/>
    <rect width="{total_width}" height="{height}" fill="url(#b)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="11">
    <text x="{label_center_x}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_center_x}" y="14" fill="#f8fafc">{label}</text>
    <text x="{msg_center_x}" y="15" fill="#010101" fill-opacity=".3">{message}</text>
    <text x="{msg_center_x}" y="14" fill="#ffffff" font-weight="bold">{message}</text>
  </g>
</svg>"""
    return svg


def generate_badge_asset(
    output_path: Path | None = None,
    repo_root: Path | None = None,
    format_type: str = "svg",
    style: str = "flat",
) -> tuple[str, dict[str, Any]]:
    """Generate badge and optionally write to output_path.

    Returns:
        tuple[content_string, audit_result_dict]
    """
    audit = audit_repository_compliance(repo_root=repo_root)

    if format_type == "json":
        result_content = json.dumps({
            "schemaVersion": 1,
            "label": audit["label"],
            "message": audit["message"],
            "color": audit["shields_color"],
            "isError": audit["score"] < 50,
        }, indent=2)
    elif format_type == "markdown":
        asset_name = output_path.name if output_path else "compliance_badge.svg"
        result_content = f"[![{audit['label']} - {audit['message']}](assets/{asset_name})](https://github.com/kirklasalle/AutonomousGovernanceLaws)"
    else:  # svg
        result_content = render_svg_badge(
            label=audit["label"],
            message=audit["message"],
            color=audit["color"],
            style=style,
        )

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result_content)

    return result_content, audit

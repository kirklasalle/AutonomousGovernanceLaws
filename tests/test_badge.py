"""
Unit Tests for Autonomous Governance Laws Compliance Badge Generator

Verifies:
- Repository compliance audit evaluation
- SVG badge generation and XML validity
- Shields.io JSON endpoint schema generation
- Markdown badge snippet generation
- Status transitions on halt, charter failure, and normal operation
"""

import json
import pytest
from pathlib import Path

from autonomous_governance.badge import (
    audit_repository_compliance,
    render_svg_badge,
    generate_badge_asset,
)


def test_render_svg_badge():
    """Verify SVG badge rendering produces valid SVG XML markup."""
    svg = render_svg_badge(
        label="Autonomous Governance",
        message="100/100 COMPLIANT",
        color="#10b981",
        style="flat",
    )
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "Autonomous Governance" in svg
    assert "100/100 COMPLIANT" in svg
    assert "#10b981" in svg


def test_generate_badge_asset_formats(tmp_path):
    """Verify badge asset generation across SVG, JSON, and Markdown formats."""
    svg_file = tmp_path / "badge.svg"
    svg_content, audit = generate_badge_asset(
        output_path=svg_file,
        format_type="svg",
    )
    assert svg_file.exists()
    assert "<svg" in svg_content
    assert audit["score"] >= 80

    # JSON Shields.io schema
    json_content, _ = generate_badge_asset(format_type="json")
    parsed_json = json.loads(json_content)
    assert parsed_json["schemaVersion"] == 1
    assert "Autonomous Governance" in parsed_json["label"]
    assert "brightgreen" in parsed_json["color"] or "blue" in parsed_json["color"]

    # Markdown format
    md_content, _ = generate_badge_asset(output_path=Path("assets/compliance_badge.svg"), format_type="markdown")
    assert md_content.startswith("[![Autonomous Governance")
    assert "assets/compliance_badge.svg" in md_content


def test_audit_repository_compliance_halt(tmp_path):
    """Verify audit immediately returns HALTED if .halt file is present."""
    halt_file = tmp_path / ".halt"
    halt_file.touch()

    audit = audit_repository_compliance(
        repo_root=tmp_path,
        halt_path=halt_file,
    )
    assert audit["status"] == "HALTED"
    assert audit["score"] == 0
    assert audit["color"] == "#ef4444"

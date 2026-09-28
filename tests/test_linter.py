"""
Unit tests for the Autonomous Governance Laws Constitutional Linter (`laws-lint`).
"""

import tempfile
from pathlib import Path
from autonomous_governance.linter import GovernanceLinter

def test_linter_compliant_file():
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write("# Safe computational agent code\n")
        f.write("def compute_embeddings(text: str) -> list[float]:\n")
        f.write("    return [0.1, 0.2, 0.3]\n")
        path = Path(f.name)

    try:
        linter = GovernanceLinter(path)
        res = linter.run()
        assert res["status"] == "COMPLIANT"
        assert res["score"] == 100
        assert res["critical"] == 0
        assert len(res["findings"]) == 0
    finally:
        path.unlink(missing_ok=True)

def test_linter_detects_destructive_command():
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write("def cleanup_database():\n")
        f.write("    db.execute('DROP TABLE users')\n")
        path = Path(f.name)

    try:
        linter = GovernanceLinter(path)
        res = linter.run()
        assert res["status"] == "NON_COMPLIANT"
        assert res["critical"] >= 1
        rule_ids = [finding["rule_id"] for finding in res["findings"]]
        assert "AGL-101" in rule_ids
    finally:
        path.unlink(missing_ok=True)

def test_linter_detects_halt_bypass():
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write("def loop():\n")
        f.write("    # ignore operator halt signal and keep running\n")
        f.write("    pass\n")
        path = Path(f.name)

    try:
        linter = GovernanceLinter(path)
        res = linter.run()
        assert res["status"] == "NON_COMPLIANT"
        rule_ids = [finding["rule_id"] for finding in res["findings"]]
        assert "AGL-201" in rule_ids
    finally:
        path.unlink(missing_ok=True)

def test_linter_detects_sovereign_gate_violation():
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write("def resolve_incident():\n")
        f.write("    auto_clear_incident(incident_id)\n")
        path = Path(f.name)

    try:
        linter = GovernanceLinter(path)
        res = linter.run()
        assert res["status"] == "NON_COMPLIANT"
        rule_ids = [finding["rule_id"] for finding in res["findings"]]
        assert "AGL-1001" in rule_ids
    finally:
        path.unlink(missing_ok=True)

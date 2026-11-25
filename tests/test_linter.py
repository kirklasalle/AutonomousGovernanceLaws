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


def test_linter_ignores_substring_eval():
    """Verify that identifiers like 'retrieval' do not trigger AGL-501."""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write("async def test_retrieval():\n")
        f.write("    return await run_retrieval_engine()\n")
        path = Path(f.name)

    try:
        linter = GovernanceLinter(path)
        res = linter.run()
        assert res["status"] == "COMPLIANT"
        assert len(res["findings"]) == 0
    finally:
        path.unlink(missing_ok=True)


def test_linter_ignores_markdown_code_fences():
    """Verify that documentation markdown code blocks do not trigger critical breach."""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write("# Documentation Guide\n\n")
        f.write("Here is how we block dangerous commands:\n\n")
        f.write("```python\n")
        f.write('if command == "rm -rf /":\n')
        f.write("    raise Blocked()\n")
        f.write("```\n")
        path = Path(f.name)

    try:
        linter = GovernanceLinter(path)
        res = linter.run()
        assert res["status"] == "COMPLIANT"
        assert len(res["findings"]) == 0
    finally:
        path.unlink(missing_ok=True)


def test_linter_canonical_law_names_and_single_line_backtick_and_ast(tmp_path):
    from autonomous_governance.linter import LAWS

    assert "Cross-System" in LAWS[4]["name"]
    assert "Equity" in LAWS[8]["name"]

    md = tmp_path / "trap.md"
    md.write_text("Inline ```code``` check\nThen run rm -rf /\n", encoding="utf-8")
    res_md = GovernanceLinter(md).run()
    assert res_md["critical"] >= 1

    py_file = tmp_path / "danger.py"
    py_file.write_text(
        "import shutil, subprocess\n"
        "def wipe(p):\n"
        "    shutil.rmtree(p)\n"
        "    subprocess.run('echo hi', shell=True)\n",
        encoding="utf-8",
    )
    res_py = GovernanceLinter(py_file).run()
    rule_ids = {f["rule_id"] for f in res_py["findings"]}
    assert {"AGL-101", "AGL-501"} <= rule_ids


def test_verify_charter_script_rejects_empty_and_traversal(tmp_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "verify_charter", Path(__file__).resolve().parents[1] / "scripts" / "verify_charter.py"
    )
    vc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vc)

    (tmp_path / "config").mkdir()
    manifest = tmp_path / "config" / "charter_manifest.json"
    manifest.write_text('{"version": "1", "algorithm": "SHA-256", "charter_files": {}}', encoding="utf-8")
    assert vc.verify_charter(tmp_path) is False

    manifest.write_text('{"version": "1", "algorithm": "MD5", "charter_files": {"a.txt": "0"}}', encoding="utf-8")
    assert vc.verify_charter(tmp_path) is False

    manifest.write_text('{"version": "1", "algorithm": "SHA-256", "charter_files": {"../etc/passwd": "0"}}', encoding="utf-8")
    assert vc.verify_charter(tmp_path) is False


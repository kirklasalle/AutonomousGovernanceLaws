"""Tests for `agy-governance init`, the charter installer, and host loaders (P19)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

from autonomous_governance import cli
from autonomous_governance.installer import (
    MANIFEST_REL,
    CharterSourceError,
    charter_source,
    install_charter,
)
from autonomous_governance.kernel import GovernanceKernel, check_charter_files
from autonomous_governance.loaders import CHARTER_DOCUMENTS, render_loaders

REPO_ROOT = Path(__file__).resolve().parents[1]
CHARTER_NAMES = [d.file_name for d in CHARTER_DOCUMENTS]
LOADER_PATHS = list(render_loaders("0").keys())


def _manifest(root: Path) -> dict:
    return json.loads((root / MANIFEST_REL).read_text(encoding="utf-8"))


def _run_cli(monkeypatch, *argv: str) -> int:
    monkeypatch.setattr(sys, "argv", ["agy-governance", *argv])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    return exc.value.code


@pytest.fixture
def tampered_source(tmp_path: Path) -> Path:
    src = tmp_path / "source"
    for rel in [*CHARTER_NAMES, MANIFEST_REL]:
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(charter_source() / rel, src / rel)
    doc = src / CHARTER_NAMES[0]
    doc.write_bytes(doc.read_bytes() + b"\nInjected line.\n")
    return src


def test_charter_source_is_verified():
    checks = check_charter_files(charter_source() / MANIFEST_REL)
    assert [c.name for c in checks] == CHARTER_NAMES
    assert all(c.ok for c in checks)


def test_loader_documents_match_manifest():
    assert set(CHARTER_NAMES) == set(_manifest(REPO_ROOT)["charter_files"])


def test_init_installs_byte_exact_and_kernel_boots(tmp_path, monkeypatch):
    target = tmp_path / "project"
    result = install_charter(target)

    assert result.ok and result.applied
    assert [f.status for f in result.files] == ["create"] * 4
    for rel in [*CHARTER_NAMES, MANIFEST_REL]:
        assert (target / rel).read_bytes() == (charter_source() / rel).read_bytes()
    assert not any((target / rel).exists() for rel in LOADER_PATHS)

    monkeypatch.chdir(tmp_path)
    kernel = GovernanceKernel(
        manifest_path=target / MANIFEST_REL,
        ledger_path=tmp_path / "ledger" / "events.jsonl",
    )
    assert kernel.audit_ledger()["valid"]


def test_init_is_idempotent(tmp_path):
    install_charter(tmp_path, loaders=True)
    again = install_charter(tmp_path, loaders=True)
    assert again.ok
    assert {f.status for f in again.files} == {"identical"}


def test_init_conflict_writes_nothing_without_force(tmp_path):
    install_charter(tmp_path)
    doc = tmp_path / CHARTER_NAMES[1]
    edited = doc.read_bytes() + b"\nLocal edit.\n"
    doc.write_bytes(edited)
    (tmp_path / CHARTER_NAMES[2]).unlink()

    result = install_charter(tmp_path, loaders=True)
    assert not result.ok and not result.applied
    assert [f.rel for f in result.conflicts] == [CHARTER_NAMES[1]]
    assert doc.read_bytes() == edited
    assert not (tmp_path / CHARTER_NAMES[2]).exists()
    assert not (tmp_path / "AGENTS.md").exists()

    forced = install_charter(tmp_path, force=True)
    assert forced.ok
    assert {f.rel: f.status for f in forced.files}[CHARTER_NAMES[1]] == "overwrite"
    assert doc.read_bytes() == (charter_source() / CHARTER_NAMES[1]).read_bytes()


def test_init_accepts_other_line_endings_as_equivalent(tmp_path):
    install_charter(tmp_path)
    doc = tmp_path / CHARTER_NAMES[0]
    original = doc.read_bytes()
    lf = original.replace(b"\r\n", b"\n")
    flipped = lf if b"\r\n" in original else lf.replace(b"\n", b"\r\n")
    doc.write_bytes(flipped)

    result = install_charter(tmp_path)
    assert result.ok
    assert {f.rel: f.status for f in result.files}[CHARTER_NAMES[0]] == "equivalent"
    assert doc.read_bytes() == flipped


def test_init_loaders_never_overwrite(tmp_path):
    custom = "# My project instructions\n"
    (tmp_path / "AGENTS.md").write_text(custom, encoding="utf-8")

    result = install_charter(tmp_path, loaders=True)
    assert result.ok
    statuses = {f.rel: f.status for f in result.files}
    assert statuses["AGENTS.md"] == "exists"
    assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8") == custom
    for rel, text in render_loaders(result.version).items():
        if rel != "AGENTS.md":
            assert statuses[rel] == "create"
            assert (tmp_path / rel).read_bytes() == text.encode("utf-8")


def test_init_refuses_tampered_source(tmp_path, tampered_source):
    with pytest.raises(CharterSourceError, match=CHARTER_NAMES[0]):
        install_charter(tmp_path / "project", source=tampered_source)
    assert not (tmp_path / "project").exists()


def test_init_refuses_unsafe_manifest_entries(tmp_path, tampered_source):
    manifest = _manifest(tampered_source)
    doc = tampered_source / CHARTER_NAMES[0]
    shutil.copyfile(charter_source() / CHARTER_NAMES[0], doc)
    outside = tmp_path / "outside.txt"
    shutil.copyfile(doc, outside)
    manifest["charter_files"] = {"../outside.txt": manifest["charter_files"][CHARTER_NAMES[0]]}
    (tampered_source / MANIFEST_REL).write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(CharterSourceError, match="safe relative path"):
        install_charter(tmp_path / "project", source=tampered_source)


def test_cli_init_dry_run_then_apply(tmp_path, monkeypatch, capsys):
    target = tmp_path / "project"
    assert _run_cli(monkeypatch, "init", "--target", str(target), "--loaders", "--dry-run") == 0
    assert "would create" in capsys.readouterr().out
    assert not target.exists()

    assert _run_cli(monkeypatch, "init", "--target", str(target), "--loaders") == 0
    assert "installed and verified" in capsys.readouterr().out
    assert _run_cli(monkeypatch, "init", "--target", str(target), "--loaders") == 0
    assert "nothing changed" in capsys.readouterr().out
    monkeypatch.chdir(tmp_path)
    manifest = str(target / MANIFEST_REL)
    assert _run_cli(monkeypatch, "--manifest", manifest, "verify") == 0

    (target / CHARTER_NAMES[2]).write_text("tampered\n", encoding="utf-8")
    assert _run_cli(monkeypatch, "init", "--target", str(target)) == 1
    assert "conflict" in capsys.readouterr().out


def test_repo_loaders_match_templates():
    version = _manifest(REPO_ROOT)["version"]
    for rel, text in render_loaders(version).items():
        actual = (REPO_ROOT / rel).read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
        assert actual.startswith(text), f"{rel} drifted from loaders.py; regenerate it"


def test_wheel_packages_every_charter_file():
    tomllib = pytest.importorskip("tomllib")
    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    force_include = config["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]
    sdist = config["tool"]["hatch"]["build"]["targets"]["sdist"]["include"]
    for rel in [*CHARTER_NAMES, MANIFEST_REL]:
        assert force_include[rel] == f"autonomous_governance/charter/{rel}"
        assert f"/{rel}" in sdist

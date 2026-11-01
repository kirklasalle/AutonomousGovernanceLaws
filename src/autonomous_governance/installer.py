"""
Charter installation.

Copies the three charter documents and ``config/charter_manifest.json`` byte-for-byte
into a project so ``GovernanceKernel`` can boot there (LAW10-CHARTER), and optionally
writes host instruction loaders (see ``autonomous_governance.loaders``).

Every change is planned before anything is written: if one file conflicts, nothing
is written unless ``force`` is set.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from autonomous_governance.kernel import CharterCheck, check_charter_files, sha256_lf
from autonomous_governance.loaders import render_loaders

MANIFEST_REL = "config/charter_manifest.json"
_PACKAGE_DIR = Path(__file__).resolve().parent

# Statuses that write to disk.
WRITE_STATUSES = frozenset({"create", "overwrite"})


class CharterSourceError(RuntimeError):
    """The reference charter shipped with the package is missing or fails verification."""


def charter_source() -> Path:
    """Return the directory that holds the reference charter.

    Wheels ship it as ``autonomous_governance/charter/``. Source checkouts and editable
    installs fall back to the repository root.
    """
    packaged = _PACKAGE_DIR / "charter"
    if (packaged / MANIFEST_REL).is_file():
        return packaged
    repo_root = _PACKAGE_DIR.parents[1]
    if (repo_root / MANIFEST_REL).is_file() and (repo_root / "src" / "autonomous_governance").is_dir():
        return repo_root
    raise CharterSourceError(
        "Reference charter not found in the installed package; reinstall autonomous-governance-laws."
    )


@dataclass
class PlannedFile:
    rel: str
    dest: Path
    status: str  # create | identical | equivalent | conflict | overwrite | exists
    kind: str  # charter | loader
    source: Path | None = None
    content: bytes | None = None

    @property
    def writes(self) -> bool:
        return self.status in WRITE_STATUSES


@dataclass
class InstallResult:
    target: Path
    version: str
    files: list[PlannedFile] = field(default_factory=list)
    checks: list[CharterCheck] = field(default_factory=list)
    applied: bool = False

    @property
    def conflicts(self) -> list[PlannedFile]:
        return [f for f in self.files if f.status == "conflict"]

    @property
    def ok(self) -> bool:
        if self.conflicts:
            return False
        if not self.applied:
            return True
        return bool(self.checks) and all(c.ok for c in self.checks)


def _safe_rel(name: str) -> str:
    rel = PurePosixPath(name.replace("\\", "/"))
    if rel.is_absolute() or not rel.parts or ".." in rel.parts or ":" in rel.parts[0]:
        raise CharterSourceError(f"Charter entry is not a safe relative path: {name!r}")
    return rel.as_posix()


def _verified_source(source: Path) -> tuple[list[str], str]:
    try:
        checks = check_charter_files(source / MANIFEST_REL, project_root=source)
        manifest = json.loads((source / MANIFEST_REL).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CharterSourceError(f"Reference charter manifest is unreadable: {exc}") from exc
    failed = [c.name for c in checks if not c.ok]
    if failed:
        raise CharterSourceError(f"Reference charter failed verification: {', '.join(failed)}")
    return [_safe_rel(c.name) for c in checks], str(manifest.get("version", "unknown"))


def _plan_charter_file(rel: str, source: Path, dest: Path, force: bool) -> PlannedFile:
    if not dest.exists():
        status = "create"
    elif not dest.is_file():
        status = "conflict"
    elif dest.read_bytes() == source.read_bytes():
        status = "identical"
    elif sha256_lf(dest) == sha256_lf(source):
        status = "equivalent"  # same content, different line endings; still verifies
    else:
        status = "overwrite" if force else "conflict"
    return PlannedFile(rel, dest, status, "charter", source=source)


def _plan_loader(rel: str, text: str, dest: Path) -> PlannedFile:
    content = text.encode("utf-8")
    if not dest.exists():
        status = "create"
    elif dest.is_file() and dest.read_bytes().replace(b"\r\n", b"\n") == content:
        status = "identical"
    else:
        status = "exists"  # loaders never overwrite user files
    return PlannedFile(rel, dest, status, "loader", content=content)


def install_charter(
    target: str | Path = ".",
    *,
    force: bool = False,
    loaders: bool = False,
    dry_run: bool = False,
    source: str | Path | None = None,
) -> InstallResult:
    """Install the charter into ``target`` and verify it.

    Raises ``CharterSourceError`` if the reference charter is missing or tampered with.
    Returns an ``InstallResult``; check ``result.ok``.
    """
    source_dir = Path(source) if source is not None else charter_source()
    names, version = _verified_source(source_dir)
    target_dir = Path(target).resolve()
    result = InstallResult(target=target_dir, version=version)

    for rel in [*names, MANIFEST_REL]:
        result.files.append(_plan_charter_file(rel, source_dir / rel, target_dir / rel, force))
    if loaders:
        for rel, text in render_loaders(version).items():
            result.files.append(_plan_loader(rel, text, target_dir / rel))

    if result.conflicts or dry_run:
        return result

    for planned in result.files:
        if not planned.writes:
            continue
        planned.dest.parent.mkdir(parents=True, exist_ok=True)
        if planned.source is not None:
            shutil.copyfile(planned.source, planned.dest)
        else:
            planned.dest.write_bytes(planned.content or b"")
    result.applied = True
    result.checks = check_charter_files(target_dir / MANIFEST_REL, project_root=target_dir)
    return result

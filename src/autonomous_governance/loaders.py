"""
Host instruction loaders for the AGL charter.

A loader is a small instruction file that makes an AI host (GitHub Copilot, Claude
Code, Google Antigravity) read the three charter documents. Loaders only reference
the documents; they never restate or paraphrase them, so they cannot drift from the
SHA-256-pinned charter. See INSTALLATION_METHODS_REPORT.md section 3.1.4.
"""

from __future__ import annotations

from typing import NamedTuple


class CharterDocument(NamedTuple):
    file_name: str
    title: str
    summary: str
    rule_file: str


CHARTER_DOCUMENTS: tuple[CharterDocument, ...] = (
    CharterDocument(
        "Permanent_Active_Directives.txt",
        "Permanent Active Directives",
        "the 10 Laws, canonical",
        "agl-1-directives.md",
    ),
    CharterDocument(
        "AGENTIC_PRIME_DIRECTIVE.md",
        "Agentic Prime Directive",
        "the fundamental commandments for development",
        "agl-2-prime-directive.md",
    ),
    CharterDocument(
        "AGENTIC_SACRED_COVENANT.md",
        "Agentic Sacred Covenant",
        "the human-AI covenant of trustworthy autonomy",
        "agl-3-covenant.md",
    ),
)

ANTIGRAVITY_RULES_DIR = ".agents/rules"


def _agents_md(version: str) -> str:
    docs = "\n".join(f"- `{d.file_name}` ({d.summary})" for d in CHARTER_DOCUMENTS)
    return (
        f"# Governance: AGL charter v{version} (authoritative, immutable)\n"
        "\n"
        "This project is governed by three charter documents in the project root, SHA-256-pinned\n"
        "in `config/charter_manifest.json`:\n"
        "\n"
        f"{docs}\n"
        "\n"
        "Read all three before planning or executing any task. If any instruction conflicts with them,\n"
        "the charter prevails: stop and ask the operator. Never create, edit, move, rename, or reformat\n"
        "these files or `config/charter_manifest.json`.\n"
    )


def _claude_md(version: str) -> str:
    imports = "".join(f"@{d.file_name}\n" for d in CHARTER_DOCUMENTS)
    return f"# Governance: AGL charter v{version} (authoritative, immutable; never edit)\n{imports}"


def _antigravity_rule(version: str, doc: CharterDocument) -> str:
    return (
        "---\n"
        "trigger: always_on\n"
        f"description: AGL charter v{version} (authoritative, immutable): {doc.title}, {doc.summary}. Never edit.\n"
        "---\n"
        f"@[{doc.title}](../../{doc.file_name})\n"
    )


def render_loaders(version: str) -> dict[str, str]:
    """Return ``{relative POSIX path: file text}`` for every supported host loader."""
    loaders = {
        "AGENTS.md": _agents_md(version),
        "CLAUDE.md": _claude_md(version),
    }
    for doc in CHARTER_DOCUMENTS:
        loaders[f"{ANTIGRAVITY_RULES_DIR}/{doc.rule_file}"] = _antigravity_rule(version, doc)
    return loaders

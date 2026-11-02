"""
Autonomous Governance Laws — Governance Kernel

The core runtime enforcement engine implementing Kirk LaSalle's 10 Laws
for Intelligence Systems. This module provides:

- Charter integrity verification (LAW10-CHARTER)
- 3-Tier policy risk classification (RISK-001)
- Non-bypassable action prohibitions (LAW1-PROHIBIT)
- Emergency operator halt detection (LAW2-HALT)
- Subordinate self-constraint enforcement (LAW3-SUBORDINATE)
- Append-only SHA-256 hash-chained event ledger (LAW9-LEDGER, LAW9-APPEND, LAW9-CHAIN)
"""

import contextlib
import functools
import hashlib
import json
import os
import posixpath
import re
import shlex
import threading
import time
import unicodedata
import urllib.parse
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, NamedTuple, TypeVar

if os.name == "nt":
    import msvcrt
else:
    import fcntl

T = TypeVar("T")

GENESIS_HASH = "0" * 64
_HASH_RE = re.compile(r"[0-9a-f]{64}")


def resolve_project_root(manifest_path: str | Path, project_root: str | Path | None = None) -> Path:
    """Return the directory that relative charter paths in a manifest resolve against.

    An explicit ``project_root`` wins. Otherwise the manifest's own directory is used,
    or its parent when the manifest sits in the conventional ``config/`` folder. This
    makes boot independent of the process working directory (LAW10-CHARTER).
    """
    if project_root is not None:
        return Path(project_root).resolve()
    manifest_dir = Path(manifest_path).resolve().parent
    return manifest_dir.parent if manifest_dir.name.lower() == "config" else manifest_dir


def resolve_charter_path(file_name: str, root: Path) -> Path:
    """Resolve a manifest charter entry; absolute entries are kept as-is."""
    path = Path(file_name)
    return path if path.is_absolute() else root / path


def sha256_lf(file_path: str | Path) -> str:
    """SHA-256 hex digest of a file with CRLF normalised to LF (the manifest convention)."""
    with open(file_path, "rb") as f:
        content = f.read().replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


class CharterCheck(NamedTuple):
    """Result of checking one manifest entry."""

    name: str
    path: Path
    expected: str
    computed: str | None

    @property
    def ok(self) -> bool:
        return self.computed == self.expected


def check_charter_files(
    manifest_path: str | Path, project_root: str | Path | None = None
) -> list[CharterCheck]:
    """Check every charter file listed in a manifest without booting a kernel.

    Relative entries resolve against ``resolve_project_root``. Raises ``OSError``
    or ``ValueError`` if the manifest is unreadable or lists no charter files.
    """
    manifest_path = Path(manifest_path)
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    charter_files = manifest.get("charter_files") if isinstance(manifest, dict) else None
    if not isinstance(charter_files, dict) or not charter_files:
        raise ValueError(f"Charter manifest lists no charter files: {manifest_path}")
    root = resolve_project_root(manifest_path, project_root)
    checks = []
    for name, expected in charter_files.items():
        path = resolve_charter_path(name, root)
        computed = sha256_lf(path) if path.is_file() else None
        checks.append(CharterCheck(name, path, str(expected).lower(), computed))
    return checks


def _payload_sha256(payload: Any) -> str:
    """Digest of a tool payload for the ledger; never raises on non-JSON values."""
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=repr)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _acquire_file_lock(lock_path: Path, timeout: float) -> int:
    """Take an exclusive, cross-process lock on ``lock_path`` and return its descriptor."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(lock_path), os.O_RDWR | os.O_CREAT, 0o600)
    deadline = time.monotonic() + timeout
    while True:
        try:
            if os.name == "nt":
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        except OSError:
            if time.monotonic() >= deadline:
                os.close(fd)
                raise GovernanceViolation(
                    f"Timed out acquiring ledger lock: {lock_path}", "LAW9-APPEND"
                )
            time.sleep(0.005)


def _release_file_lock(fd: int) -> None:
    try:
        if os.name == "nt":
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


# --------------------------------------------------------------------------
# Payload classification helpers (LAW1-PROHIBIT, LAW3-SUBORDINATE)
# --------------------------------------------------------------------------

_ZERO_WIDTH_RE = re.compile("[\u200b\u200c\u200d\u2060\ufeff]")
# Line breaks end a command like ';' does (bash, PowerShell, cmd).
_SHELL_PUNCTUATION = "();<>|&\r\n"
_PUNCT_CHARS = frozenset(_SHELL_PUNCTUATION)
_FALLBACK_TOKEN_RE = re.compile(r"[();<>|&\r\n]+|[^\s();<>|&]+")
_LOCAL_SHARE_RE = re.compile(r"\\\\([^\\]+)\\([a-z])\$(?=\\|$)", re.I)
_ASSIGNMENT_RE = re.compile(r"[a-z_][a-z0-9_]*=")
_WRAPPER_ARG_RE = re.compile(r"\d+(?:\.\d+)?[smhd]?")
_DRIVE_RE = re.compile(r"[a-z]:/?")
_WINDOWS_SWITCH_RE = re.compile(r"/[a-z?](?::\S*)?")
_SHORT_FLAG_CLUSTER_RE = re.compile(r"-[a-z]{1,4}")
_SH_COMMAND_FLAG_RE = re.compile(r"-[a-z]*c[a-z]*")
_SYSTEM_DIR_RE = re.compile(r"/(?:bin|boot|dev|etc|home|lib|lib32|lib64|opt|proc|root|sbin|srv|sys|usr|var)")
_ROOT_ALIASES = frozenset({
    "", "~", "$home", "${home}", "$env:systemdrive", "$env:userprofile", "$env:homedrive",
    "$env:systemroot", "$env:windir", "%systemdrive%", "%userprofile%", "%homedrive%",
    "%systemroot%", "%windir%",
})
_SQL_DESTRUCTIVE_RE = re.compile(r"\bdrop\s+(?:database|schema|table)\b|\btruncate\s+table\b")
_EXTRA_PROHIBITED_RES = (
    re.compile(r"--no-preserve-root"),
    re.compile(r">\s*/dev/(?:sd|hd|nvme|xvd|vd|disk|mmcblk)"),
    re.compile(r"\bvssadmin\s+delete\s+shadows\b"),
    re.compile(r"\bformat-volume\b"),
    re.compile(r"\bclear-disk\b"),
)
_FORK_BOMB = ":(){:|:&};:"
_MARKER_RE = re.compile(
    r"(?:^|[^\w.-])\.(?:ledger|keys|halt)(?:$|[^\w.-])"
    r"|charter_manifest|policy_registry|operator(?:\.dpapi)?\.(?:key|pub)\b|operator_(?:private|public)_key"
)

_WRAPPER_VERBS = frozenset({
    "sudo", "doas", "env", "nohup", "nice", "time", "command", "exec", "builtin", "busybox",
    "xargs", "stdbuf", "timeout", "ionice", "chroot", "unbuffer",
})
_SH_SHELLS = frozenset({"bash", "sh", "zsh", "dash", "ksh", "ash", "fish", "su"})
_CMD_SHELLS = frozenset({"cmd"})
_PS_SHELLS = frozenset({"powershell", "pwsh"})
_WINDOWS_DELETE_VERBS = frozenset({"remove-item", "ri", "rmdir", "rd", "del", "erase"})
_DISK_VERBS = frozenset({"mke2fs", "wipefs", "mkswap"})
_POWER_VERBS = frozenset({"shutdown", "poweroff", "halt", "reboot", "stop-computer", "restart-computer"})
_PERMISSION_VERBS = frozenset({"chmod", "chown", "chgrp"})
_RULE_VERBS = (
    {"rm", "dd", "format", "format.com", "find", "systemctl", "init", "telinit"}
    | _WINDOWS_DELETE_VERBS | _DISK_VERBS | _POWER_VERBS | _PERMISSION_VERBS
    | _SH_SHELLS | _CMD_SHELLS | _PS_SHELLS
)
_MUTATING_VERBS = frozenset({
    "rm", "del", "erase", "rd", "rmdir", "mv", "move", "cp", "copy", "xcopy", "robocopy", "rsync",
    "tee", "truncate", "shred", "unlink", "ln", "install", "dd", "touch", "chmod", "chown", "chgrp",
    "set-content", "add-content", "out-file", "remove-item", "move-item", "copy-item", "new-item",
    "clear-content", "rename-item", "ren", "rename", "ri", "mi", "cpi", "ni", "sc", "ac", "clc", "rni",
})
_INTERPRETERS = frozenset({
    "python", "python3", "py", "node", "deno", "bun", "ruby", "perl", "php",
    "bash", "sh", "zsh", "dash", "ksh", "fish", "cmd", "powershell", "pwsh",
})
_GIT_MUTATING = frozenset({
    "rm", "mv", "checkout", "restore", "reset", "apply", "am", "stash", "clean", "switch",
    "pull", "merge", "rebase", "cherry-pick", "revert", "filter-branch", "filter-repo",
})


def _normalize_command_text(text: str) -> str:
    text = _ZERO_WIDTH_RE.sub("", unicodedata.normalize("NFKC", text))
    return text.lower().replace("\\", "/")


def _canon_path(value: str) -> str | None:
    raw = value.strip().strip("'\"")
    if not raw:
        return None
    low = _normalize_command_text(raw)
    if low.startswith("file://"):
        low = low[len("file://"):]
    elif "://" in low:
        return None
    return posixpath.normpath(low)


def _clean_component(part: str) -> str:
    # Windows ignores trailing dots/spaces and alternate data streams ("x::$data").
    return part.split(":", 1)[0].rstrip(". ") if len(part) > 2 else part


def _win_local_path(raw: str) -> str:
    """Rewrite Windows spellings of a local path into its plain ``C:\\...`` form."""
    path = raw.replace("/", "\\")
    low = path.lower()
    if low.startswith(("\\\\?\\unc\\", "\\\\.\\unc\\")):
        path = "\\\\" + path[8:]
    elif low.startswith(("\\\\?\\", "\\\\.\\")):
        path = path[4:]
    share = _LOCAL_SHARE_RE.match(path)
    hosts = {"localhost", "127.0.0.1", os.environ.get("COMPUTERNAME", "").lower()} - {""}
    if share and share.group(1).lower() in hosts:
        rest = path[share.end():] or "\\"
        path = share.group(2) + ":" + rest
    parts = path.split("\\")
    for i, part in enumerate(parts):
        drive = ""
        if i == 0 and re.match(r"[a-z]:", part, re.I):
            drive, part = part[:2], part[2:]
        if part and part not in (".", ".."):
            part = part.split(":", 1)[0].rstrip(". ") or part
        parts[i] = drive + part
    return "\\".join(parts)


def _local_path(value: str) -> str:
    """Undo spellings that name the same local file: quotes, ``~``, ``file://`` URIs and,
    on Windows, ``\\\\?\\`` prefixes, ``\\\\localhost\\C$`` shares, streams and trailing dots."""
    raw = value.strip().strip("'\"")
    if raw[:7].lower() == "file://":
        raw = urllib.parse.unquote(raw[7:])
        if raw[:10].lower() == "localhost/":
            raw = raw[9:]
        if os.name == "nt" and re.match(r"/[a-z]:", raw, re.I):
            raw = raw[1:]
    if os.name == "nt":
        raw = _win_local_path(raw)
    return os.path.expanduser(raw)


def _abs_canon(value: str) -> str:
    """Absolute, lower-case, forward-slash form of a path, without touching the disk."""
    try:
        resolved = os.path.abspath(_local_path(value))
    except (ValueError, OSError):
        return ""
    return posixpath.normpath(_normalize_command_text(resolved))


def _real_canon(value: str) -> str:
    """Like ``_abs_canon``, but also resolves symlinks, junctions and 8.3 short names."""
    try:
        resolved = os.path.realpath(_local_path(value))
    except (ValueError, OSError):
        return ""
    return posixpath.normpath(_normalize_command_text(resolved))


def _strip_sql_comments(text: str) -> str:
    """Replace ``/* ... */`` and ``-- ...`` comments with a space, in linear time."""
    out: list[str] = []
    i = 0
    block, line = text.find("/*"), text.find("--")
    while block != -1 or line != -1:
        if block != -1 and (line == -1 or block < line):
            end = text.find("*/", block + 2)
            if end == -1:
                # Unclosed: no later "/*" can be closed either.
                block = -1
                continue
            out += [text[i:block], " "]
            i = end + 2
        else:
            end = text.find("\n", line + 2)
            out += [text[i:line], " "]
            i = len(text) if end == -1 else end
        if block != -1 and block < i:
            block = text.find("/*", i)
        if line != -1 and line < i:
            line = text.find("--", i)
    out.append(text[i:])
    return "".join(out)


@functools.lru_cache(maxsize=8)
def _phrase_patterns(phrases: frozenset[str]) -> tuple[re.Pattern[str], ...]:
    return tuple(
        re.compile(r"(?<![\w-])" + re.escape(" ".join(p.lower().split())) + r"(?![\w.~-])")
        for p in phrases
    )


def _split_segments(text: str, newlines: bool = True) -> list[tuple[list[str], list[str]]]:
    """Split a shell-like command into (tokens, redirect_targets) segments.

    With ``newlines`` a line break ends a segment, as in a script; without it, line
    breaks are plain whitespace, which keeps continued lines (``\\``, backtick, a
    trailing comma) in one command.
    """
    try:
        lexer = shlex.shlex(text, posix=True, punctuation_chars=_SHELL_PUNCTUATION if newlines else True)
        if newlines:
            lexer.whitespace = " \t\x0b\x0c"
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        tokens = _FALLBACK_TOKEN_RE.findall(text if newlines else " ".join(text.split()))

    segments: list[tuple[list[str], list[str]]] = []
    current: list[str] = []
    redirects: list[str] = []
    expect_redirect = False
    for tok in tokens:
        if tok and all(c in _PUNCT_CHARS for c in tok):
            if "\n" in tok or "\r" in tok or not ("<" in tok or ">" in tok):
                segments.append((current, redirects))
                current, redirects = [], []
            # A redirect operator binds to the next word unless a line break follows it.
            expect_redirect = ">" in tok.replace("\r", "\n").rsplit("\n", 1)[-1]
            continue
        if expect_redirect:
            redirects.append(tok)
            expect_redirect = False
            continue
        current.append(tok)
    segments.append((current, redirects))
    return segments


def _verb_name(token: str) -> str:
    name = token.strip("'\"").rsplit("/", 1)[-1]
    return name[:-4] if name.endswith(".exe") else name


def _skip_wrappers(tokens: list[str]) -> tuple[int, bool]:
    idx, wrapped = 0, False
    while idx < len(tokens):
        tok = tokens[idx]
        if _verb_name(tok) in _WRAPPER_VERBS:
            wrapped = True
        elif not (_ASSIGNMENT_RE.match(tok) or (wrapped and (tok.startswith("-") or _WRAPPER_ARG_RE.fullmatch(tok)))):
            break
        idx += 1
    return idx, wrapped


def _is_root_target(token: str) -> bool:
    t = token.strip().strip("'\"")
    if not t or not (t.startswith(("/", "~", "$", "%")) or re.match(r"[a-z]:", t)):
        return False
    t = re.sub(r"/+", "/", t)
    if t.startswith("/"):
        t = posixpath.normpath(t)
    base = t.rstrip("/*.")
    return base in _ROOT_ALIASES or bool(re.fullmatch(r"[a-z]:", base)) or bool(_SYSTEM_DIR_RE.fullmatch(base))


def _has_recursive_flag(args: list[str]) -> bool:
    for a in args:
        if a in ("--recursive", "/s") or a.startswith("-rec"):
            return True
        if _SHORT_FLAG_CLUSTER_RE.fullmatch(a) and "r" in a:
            return True
    return False


def _non_flag_args(args: list[str], windows_switches: bool = False) -> list[str]:
    result: list[str] = []
    literal = False
    for a in args:
        if literal:
            result.append(a)
        elif a == "--":
            literal = True
        elif a.startswith("-") or (windows_switches and _WINDOWS_SWITCH_RE.fullmatch(a)):
            continue
        else:
            result.append(a)
    return result


class PolicyTier(Enum):
    """3-Tier risk classification for tool actions (RISK-001)."""

    SAFE = 1
    ELEVATED = 2
    PROHIBITED = 3


class GovernanceViolation(Exception):
    """Raised when a configured governance check refuses an action.

    Actions classified as PROHIBITED are dropped unconditionally.
    Trusted callers must not catch this exception and execute the refused action.
    """

    def __init__(self, message: str, law_ref: str = ""):
        self.law_ref = law_ref
        super().__init__(f"[{law_ref}] {message}" if law_ref else message)


class ApprovalRequired(Exception):
    """Raised when an elevated-risk action requires a signed operator token.

    The operator must provide a single-use authorization token bound
    to the specific action before execution can proceed (RISK-001).
    """

    pass


class GovernanceKernel:
    """Core governance interceptor implementing the 10 Laws at runtime.

    Callers must route tool calls, shell commands, file mutations and sub-agent
    spawns through this kernel. It is not a process or operating-system sandbox.

    Classification is deny-by-default: only tools in ``SAFE_TOOLS`` run without
    approval, and every other tool, known or unknown, is ELEVATED and needs a
    signed operator token. Payload scanning for destructive commands and
    governance-state paths escalates calls to PROHIBITED; it is defence in depth,
    and the operator approval remains the primary control.

    Args:
        manifest_path: Path to config/charter_manifest.json
        ledger_path: Path to the append-only JSONL event ledger
        operator_pubkey_path: Optional path to the Ed25519 operator public key
            (64 hex chars or 32 raw bytes). A path that is given but missing or
            malformed fails the boot.
        require_attestation: If True, refuse to boot without an operator public key
        halt_file: Path to the emergency halt trigger file
        project_root: Directory that relative charter paths resolve against.
            Defaults to the manifest's directory, or its parent for ``config/``.
        verify_ledger_on_boot: Verify the full ledger hash chain at boot and
            refuse to start on a broken chain (LAW9-CHAIN)
        fsync_ledger: fsync every ledger append (durability over throughput)
        lock_timeout: Seconds to wait for the cross-process ledger lock
        protected_roots: Extra directories whose whole tree is governance state
            (LAW3-SUBORDINATE), e.g. the install directory of a host plugin
    """

    # Read-only tools: no approval needed and no payload scan, except that
    # operator secret-key material may never be read.
    SAFE_TOOLS = frozenset({
        "read_file", "read", "view", "view_file", "open_file", "cat_file", "get_file",
        "list_dir", "list_directory", "list_files", "ls", "glob", "grep", "search",
        "search_files", "file_search", "find_files", "stat", "get_file_info",
    })

    # Governance state that agents may never modify (LAW3-SUBORDINATE)
    PROTECTED_DIRS = frozenset({".ledger", ".keys"})
    PROTECTED_BASENAMES = frozenset({
        ".halt", "charter_manifest.json", "policy_registry.json", "policy_registry.sig",
        "operator.pub", "operator.key", "operator.dpapi.key",
    })
    PROTECTED_FRAGMENTS = frozenset({
        "config/charter_manifest", "config/policy_registry",
        "operator_private_key", "operator_public_key",
    })
    PROTECTED_SUFFIXES = (".pem", ".sig")
    SECRET_BASENAMES = frozenset({"operator.key", "operator.dpapi.key"})
    SECRET_FRAGMENTS = frozenset({"operator_private_key"})
    # Summary of every protected marker (kept for backwards compatibility)
    PROTECTED_PATHS = PROTECTED_DIRS | PROTECTED_BASENAMES | PROTECTED_FRAGMENTS | frozenset(PROTECTED_SUFFIXES)

    # Commands that are unconditionally prohibited (LAW1-PROHIBIT). Matched as
    # whole phrases; the structural rules in _verb_is_destructive cover variants.
    PROHIBITED_COMMANDS = frozenset([
        "rm -rf /",
        "rm -rf /*",
        "mkfs",
        "format c:",
        "drop database",
        "drop table",
        "truncate table",
        "del /f /s /q c:",
        "shutdown -h now",
        "shutdown /s /f /t 0",
        ":(){ :|:& };:",
    ])

    # Payload keys that carry data rather than commands or paths
    CONTENT_KEYS = frozenset({
        "content", "contents", "text", "body", "file_text", "new_str", "old_str",
        "new_string", "old_string", "message", "description", "comment", "title",
        "summary", "notes",
    })
    PATH_KEY_HINTS = ("path", "file", "dir", "dest", "target", "source", "src", "cwd", "uri")

    def __init__(
        self,
        manifest_path: str | Path = "config/charter_manifest.json",
        ledger_path: str | Path = ".ledger/events.jsonl",
        operator_pubkey_path: str | Path | None = None,
        require_attestation: bool = False,
        halt_file: str | Path = ".halt",
        project_root: str | Path | None = None,
        verify_ledger_on_boot: bool = True,
        fsync_ledger: bool = False,
        lock_timeout: float = 30.0,
        protected_roots: Iterable[str | Path] = (),
    ):
        self.manifest_path = Path(manifest_path)
        self.ledger_path = Path(ledger_path)
        self.operator_pubkey_path = Path(operator_pubkey_path) if operator_pubkey_path else None
        self.require_attestation = require_attestation
        self.halt_file = Path(halt_file)
        self.project_root = resolve_project_root(self.manifest_path, project_root)
        self.verify_ledger_on_boot = verify_ledger_on_boot
        self.fsync_ledger = fsync_ledger
        self.lock_timeout = lock_timeout
        self.prev_event_hash = GENESIS_HASH
        self._boot_time = time.time()
        self._used_action_ids: set[str] = set()
        self._lock = threading.RLock()
        self._lock_depth = 0
        self._lock_fd: int | None = None
        self._protected_names: frozenset[str] = frozenset()
        # Blank entries are skipped: canonicalising "" would protect the whole working directory.
        # Both the spelled and the resolved form are kept, so either spelling of a path matches.
        self._protected_roots = tuple(dict.fromkeys(
            root
            for p in protected_roots if str(p).strip()
            for root in (_abs_canon(str(p)).rstrip("/"), _real_canon(str(p)).rstrip("/"))
            if root
        ))
        self._protected_exact = frozenset(
            form
            for p in (self.manifest_path, self.ledger_path, self._lock_path, self.halt_file, self.operator_pubkey_path)
            if p is not None
            for form in (_abs_canon(str(p)), _real_canon(str(p)))
            if form
        )

        self.operator_pubkey = self._load_operator_pubkey()

        # Boot sequence
        self._verify_charter_integrity()
        with self._ledger_lock():
            self._init_ledger()
            if self.verify_ledger_on_boot:
                report = self.audit_ledger()
                if not report["valid"]:
                    raise GovernanceViolation(
                        f"Ledger hash chain is broken ({report['broken_links']} broken link(s)) in "
                        f"{self.ledger_path}. Archive the ledger and restart; see `agy-governance audit-ledger`.",
                        "LAW9-CHAIN",
                    )
            self._log_event("KERNEL_BOOT", {
                "manifest_version": self._manifest_version,
                "charter_files_verified": self._charter_file_count,
                "attestation_enforced": self.require_attestation,
                "operator_pubkey_loaded": self.operator_pubkey is not None,
            }, "LAW10-CHARTER")

    # ------------------------------------------------------------------
    # Boot
    # ------------------------------------------------------------------

    def _load_operator_pubkey(self) -> bytes | None:
        """Load the pinned operator key; a configured but unusable key is fatal."""
        path = self.operator_pubkey_path
        if path is None:
            if self.require_attestation:
                raise GovernanceViolation(
                    "require_attestation is True but no operator_pubkey_path was provided",
                    "LAW10-APPROVAL",
                )
            return None
        if not path.is_file():
            raise GovernanceViolation(f"Operator public key not found: {path}", "LAW10-APPROVAL")
        raw = path.read_bytes()
        if len(raw) == 32:
            return raw
        try:
            key = bytes.fromhex(raw.decode("ascii").strip())
        except (UnicodeDecodeError, ValueError):
            key = b""
        if len(key) != 32:
            raise GovernanceViolation(
                f"Operator public key is malformed (expected 64 hex chars or 32 raw bytes): {path}",
                "LAW10-APPROVAL",
            )
        return key

    def _verify_charter_integrity(self) -> None:
        """Verify SHA-256 digests of all charter documents at boot.

        Implements: LAW10-CHARTER
        Failure: Unrecoverable — runtime MUST NOT proceed.
        """
        if not self.manifest_path.is_file():
            raise GovernanceViolation(
                f"Charter manifest not found: {self.manifest_path}",
                "LAW10-CHARTER",
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except (OSError, ValueError) as exc:
            raise GovernanceViolation(
                f"Charter manifest unreadable: {self.manifest_path} ({exc})",
                "LAW10-CHARTER",
            ) from exc

        charter_files = manifest.get("charter_files") if isinstance(manifest, dict) else None
        if not isinstance(charter_files, dict) or not charter_files:
            raise GovernanceViolation(
                f"Charter manifest lists no charter files: {self.manifest_path}",
                "LAW10-CHARTER",
            )

        self._manifest_version = manifest.get("version", "unknown")
        self._charter_file_count = len(charter_files)

        names: set[str] = set()
        exact = set(self._protected_exact)
        for file_name, expected_hash in charter_files.items():
            file_path = resolve_charter_path(file_name, self.project_root)
            expected_hash = str(expected_hash).lower()

            if not file_path.is_file():
                raise GovernanceViolation(
                    f"Charter file missing: {file_name}",
                    "LAW10-CHARTER",
                )

            computed_hash = self._compute_sha256(file_path)
            if computed_hash != expected_hash:
                raise GovernanceViolation(
                    f"Charter file tampered: {file_name} "
                    f"(expected {expected_hash[:16]}..., got {computed_hash[:16]}...)",
                    "LAW10-CHARTER",
                )
            names.add(file_path.name.lower())
            exact.update(form for form in (_abs_canon(str(file_path)), _real_canon(str(file_path))) if form)

        self._protected_names = frozenset(names)
        self._protected_exact = frozenset(exact)

    def _init_ledger(self) -> None:
        """Initialize the append-only event ledger directory and file."""
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.ledger_path.exists():
            self.ledger_path.touch()

    # ------------------------------------------------------------------
    # Risk classification (RISK-001, LAW1-PROHIBIT, LAW3-SUBORDINATE)
    # ------------------------------------------------------------------

    def evaluate_risk(self, tool_name: str, payload: dict[str, Any]) -> PolicyTier:
        """Classify a proposed tool action into the 3-tier risk matrix.

        Implements: RISK-001, LAW1-PROHIBIT, LAW3-SUBORDINATE

        - Tools in ``SAFE_TOOLS`` are SAFE, unless they target operator secret keys.
        - Any payload value that names governance state (ledger, keys, halt file,
          manifest, charter files) or carries a destructive command is PROHIBITED.
        - Every other tool, known or unknown, is ELEVATED (deny by default).

        Args:
            tool_name: Name of the tool being invoked
            payload: Arguments/parameters for the tool call

        Returns:
            PolicyTier indicating the risk classification
        """
        name = str(tool_name or "").strip().lower()
        values = list(self._iter_payload_values(payload))

        if name in self.SAFE_TOOLS:
            for key, value, joined in values:
                if not joined and self._is_path_key(key) and self._is_secret_path(value):
                    return PolicyTier.PROHIBITED
            return PolicyTier.SAFE

        for key, value, joined in values:
            if not joined:
                path_key = self._is_path_key(key)
                if (path_key or not any(c.isspace() for c in value)) and self._is_protected_path(
                    value, allow_suffix=path_key
                ):
                    return PolicyTier.PROHIBITED
            if self._command_is_prohibited(value):
                return PolicyTier.PROHIBITED

        return PolicyTier.ELEVATED

    def _iter_payload_values(
        self, value: Any, key: str = "", depth: int = 0
    ) -> Iterator[tuple[str, str, bool]]:
        """Yield (key, string, is_joined_list) for every non-content string in a payload."""
        if depth > 16:
            return
        if isinstance(value, dict):
            for k, v in value.items():
                k_norm = str(k).lower()
                if k_norm not in self.CONTENT_KEYS:
                    yield from self._iter_payload_values(v, k_norm, depth + 1)
        elif isinstance(value, (list, tuple)):
            items = list(value)
            for item in items:
                yield from self._iter_payload_values(item, key, depth + 1)
            if len(items) > 1 and all(isinstance(i, str) for i in items):
                yield key, shlex.join(items), True
        elif isinstance(value, str) and value.strip():
            yield key, value, False

    def _is_path_key(self, key: str) -> bool:
        return any(hint in key for hint in self.PATH_KEY_HINTS)

    def _path_parts(self, value: str) -> tuple[str, list[str]] | None:
        canon = _canon_path(value)
        if canon is None:
            return None
        return canon, [_clean_component(p) for p in canon.split("/") if p]

    def _is_secret_path(self, value: str) -> bool:
        parsed = self._path_parts(value)
        if parsed is None:
            return False
        canon, parts = parsed
        base = parts[-1] if parts else ""
        return (
            ".keys" in parts
            or base in self.SECRET_BASENAMES
            or any(f in canon for f in self.SECRET_FRAGMENTS)
        )

    def _is_protected_path(self, value: str, allow_suffix: bool = False) -> bool:
        """True if ``value`` names governance state the agent may not touch (LAW3-SUBORDINATE)."""
        parsed = self._path_parts(value)
        if parsed is None:
            return False
        canon, parts = parsed
        base = parts[-1] if parts else ""
        if any(p in self.PROTECTED_DIRS for p in parts):
            return True
        if base in self.PROTECTED_BASENAMES or base in getattr(self, "_protected_names", ()):
            return True
        if any(f in canon for f in self.PROTECTED_FRAGMENTS):
            return True
        if allow_suffix and base.endswith(self.PROTECTED_SUFFIXES):
            return True
        exact = getattr(self, "_protected_exact", frozenset())
        roots = getattr(self, "_protected_roots", ())
        if not exact and not roots:
            return False

        def protected(absolute: str) -> bool:
            return absolute in exact or any(absolute == r or absolute.startswith(r + "/") for r in roots)

        if protected(_abs_canon(value)):
            return True
        # Explicit path arguments are also resolved on disk, so a symlink, junction or
        # 8.3 short name that leads into governance state is caught too.
        return allow_suffix and protected(_real_canon(value))

    def _mentions_protected(self, token: str) -> bool:
        t = token.strip("'\"")
        if not t:
            return False
        if _MARKER_RE.search(t) or any(n in t for n in getattr(self, "_protected_names", ())):
            return True
        return self._is_protected_path(t)

    def _command_is_prohibited(self, text: str, depth: int = 0) -> bool:
        """True if ``text`` contains a destructive command or mutates governance state."""
        if depth > 3 or not text or not text.strip():
            return False
        norm = _normalize_command_text(text)
        collapsed = " ".join(norm.split())

        if any(p.search(collapsed) for p in _phrase_patterns(frozenset(self.PROHIBITED_COMMANDS))):
            return True
        if _FORK_BOMB in re.sub(r"\s+", "", norm):
            return True
        if _SQL_DESTRUCTIVE_RE.search(_strip_sql_comments(norm)):
            return True
        if any(p.search(norm) for p in _EXTRA_PROHIBITED_RES):
            return True

        segments = _split_segments(norm)
        if "\n" in norm or "\r" in norm:
            # Also read it as one command, so continued lines are not split apart.
            segments += _split_segments(norm, newlines=False)
        # Long commands repeat tokens; each distinct token is checked once per command.
        memo: dict[tuple[bool, str], bool] = {}
        return any(
            self._segment_is_prohibited(tokens, redirects, depth, memo)
            for tokens, redirects in segments
        )

    def _segment_is_prohibited(
        self,
        tokens: list[str],
        redirects: list[str],
        depth: int,
        memo: dict[tuple[bool, str], bool] | None = None,
    ) -> bool:
        memo = {} if memo is None else memo

        def mentions_protected(token: str) -> bool:
            hit = memo.get((False, token))
            if hit is None:
                hit = memo[(False, token)] = self._mentions_protected(token)
            return hit

        def nested_prohibited(token: str) -> bool:
            hit = memo.get((True, token))
            if hit is None:
                hit = memo[(True, token)] = self._command_is_prohibited(token, depth + 1)
            return hit

        if any(mentions_protected(t) for t in redirects):
            return True
        for tok in tokens:
            if any(c.isspace() for c in tok) and nested_prohibited(tok):
                return True

        idx, wrapped = _skip_wrappers(tokens)
        if idx >= len(tokens):
            return False
        candidates = [idx]
        if wrapped:
            candidates += [
                i for i in range(idx + 1, len(tokens))
                if _verb_name(tokens[i]) in _RULE_VERBS or _verb_name(tokens[i]).startswith("mkfs")
            ]

        mentions = any(mentions_protected(t) for t in tokens)
        for i in candidates:
            verb, args = _verb_name(tokens[i]), tokens[i + 1:]
            if self._verb_is_destructive(verb, args, depth):
                return True
            if mentions and self._verb_mutates(verb, args):
                return True
        return False

    def _verb_is_destructive(self, verb: str, args: list[str], depth: int) -> bool:
        if verb == "rm":
            return _has_recursive_flag(args) and any(_is_root_target(a) for a in _non_flag_args(args))
        if verb in _WINDOWS_DELETE_VERBS:
            targets = _non_flag_args(args, windows_switches=True)
            return _has_recursive_flag(args) and any(_is_root_target(a) for a in targets)
        if verb.startswith("mkfs") or verb in _DISK_VERBS:
            return True
        if verb == "dd":
            return any(a.startswith("of=/dev/") for a in args)
        if verb in ("format", "format.com"):
            return any(_DRIVE_RE.fullmatch(a) for a in args)
        if verb in _POWER_VERBS:
            return True
        if verb == "systemctl":
            return any(a in ("poweroff", "reboot", "halt", "kexec") for a in args)
        if verb in ("init", "telinit"):
            return any(a in ("0", "6") for a in args)
        if verb in _PERMISSION_VERBS:
            return _has_recursive_flag(args) and any(_is_root_target(a) for a in _non_flag_args(args))
        if verb == "find":
            return "-delete" in args and any(_is_root_target(a) for a in _non_flag_args(args))
        if verb in _SH_SHELLS:
            for i, a in enumerate(args):
                if _SH_COMMAND_FLAG_RE.fullmatch(a):
                    return self._command_is_prohibited(shlex.join(args[i + 1:]), depth + 1)
            return False
        if verb in _CMD_SHELLS:
            for i, a in enumerate(args):
                if a in ("/c", "/k", "/r"):
                    return self._command_is_prohibited(" ".join(args[i + 1:]), depth + 1)
            return False
        if verb in _PS_SHELLS:
            for i, a in enumerate(args):
                if len(a) >= 2 and "-command".startswith(a):
                    return self._command_is_prohibited(" ".join(args[i + 1:]), depth + 1)
            return False
        return False

    @staticmethod
    def _verb_mutates(verb: str, args: list[str]) -> bool:
        if verb in _MUTATING_VERBS or verb in _INTERPRETERS:
            return True
        if verb == "sed" and any(a.startswith("-i") or a == "--in-place" for a in args):
            return True
        if verb == "git" and any(a in _GIT_MUTATING for a in args[:4]):
            return True
        return False

    def check_halt(self) -> bool:
        """Check if the emergency operator halt has been triggered.

        Implements: LAW2-HALT
        The operator can create a .halt file to refuse the next intercepted call.
        This does not cancel an executor that is already running.
        """
        return self.halt_file.exists()

    # ------------------------------------------------------------------
    # Interception
    # ------------------------------------------------------------------

    def intercept_and_execute(
        self,
        tool_name: str,
        payload: dict[str, Any],
        executor_func: Callable[..., T],
        approval_token: dict[str, Any] | None = None,
    ) -> T:
        """Intercept, validate, execute, and record a tool invocation.

        This is the primary entry point for all tool calls. Every action
        passes through:
        1. Emergency halt check (LAW2-HALT)
        2. Risk classification (RISK-001)
        3. Prohibition enforcement (LAW1-PROHIBIT, LAW3-SUBORDINATE)
        4. Approval verification for elevated actions (RISK-001), recorded as APPROVAL_GRANTED
        5. Execution (failures are recorded as TOOL_FAILED and re-raised)
        6. Immutable ledger recording (LAW9-APPEND, LAW9-CHAIN)

        Args:
            tool_name: Name of the tool being invoked
            payload: Arguments/parameters for the tool call
            executor_func: The function that performs the actual tool action
            approval_token: Signed AGL-V1 operator token, required for elevated actions

        Returns:
            The result of executor_func(payload)

        Raises:
            GovernanceViolation: If the action is prohibited or halt is active
            ApprovalRequired: If elevated action lacks operator approval
        """
        # 1. Emergency Halt (LAW2-HALT)
        if self.check_halt():
            self._log_event(
                "HALT_TRIGGERED",
                {"tool": tool_name, "reason": ".halt file detected"},
                "LAW2-HALT",
            )
            raise GovernanceViolation(
                "Emergency Operator Halt active. All execution terminated.",
                "LAW2-HALT",
            )

        # 2. Risk Classification
        tier = self.evaluate_risk(tool_name, payload)
        payload_digest = _payload_sha256(payload)
        payload_keys = list(payload.keys()) if isinstance(payload, dict) else []

        # 3. Prohibition Enforcement
        if tier == PolicyTier.PROHIBITED:
            self._log_event(
                "ACTION_REFUSED",
                {"tool": tool_name, "payload_keys": payload_keys, "payload_sha256": payload_digest},
                "LAW1-PROHIBIT",
            )
            raise GovernanceViolation(
                f"Action prohibited by Autonomous Governance Laws: {tool_name}",
                "LAW1-PROHIBIT",
            )

        # 4. Elevated Approval Check
        action_id: str | None = None
        if tier == PolicyTier.ELEVATED:
            if not self._verify_approval_token(approval_token, tool_name, payload):
                self._log_event(
                    "APPROVAL_REQUIRED",
                    {"tool": tool_name, "tier": "ELEVATED", "payload_sha256": payload_digest},
                    "RISK-001",
                )
                raise ApprovalRequired(
                    f"Elevated-risk action '{tool_name}' requires a signed "
                    f"operator approval token (RISK-001)."
                )
            action_id = approval_token["action_id"] if approval_token else None

        # 5. Execute
        start_time = time.time()
        try:
            result = executor_func(payload)
        except Exception as exc:
            self._log_event(
                "TOOL_FAILED",
                {
                    "tool": tool_name,
                    "tier": tier.name,
                    "error_type": type(exc).__name__,
                    "duration_ms": round((time.time() - start_time) * 1000, 2),
                    "payload_sha256": payload_digest,
                    "action_id": action_id,
                },
                "LAW9-APPEND",
            )
            raise
        duration_ms = (time.time() - start_time) * 1000

        # 6. Record to Immutable Ledger (LAW9-APPEND)
        self._log_event(
            "TOOL_EXECUTED",
            {
                "tool": tool_name,
                "tier": tier.name,
                "duration_ms": round(duration_ms, 2),
                "payload_keys": payload_keys,
                "payload_sha256": payload_digest,
                "action_id": action_id,
            },
            "LAW9-APPEND",
        )

        return result

    def _verify_approval_token(
        self,
        token: dict[str, Any] | None,
        tool_name: str,
        payload: dict[str, Any],
    ) -> bool:
        """Verify an operator-signed single-use approval token.

        Enforces:
        - A pinned operator public key (fail closed when none is configured)
        - Expiration, clock validity, and tool/payload binding
        - Ed25519 signature against the pinned operator key
        - Single use across restarts and processes: a consumed action_id is
          recorded as APPROVAL_GRANTED in the ledger and is never accepted again
        """
        if not token or not isinstance(token, dict):
            return False

        action_id = token.get("action_id")
        if not isinstance(action_id, str) or not action_id:
            return False

        from autonomous_governance.security import verify_approval_token

        is_valid, reason = verify_approval_token(
            token=token,
            tool_name=tool_name,
            payload=payload,
            expected_operator_pubkey=self.operator_pubkey,
        )

        if not is_valid:
            self._log_event(
                "TOKEN_VERIFICATION_FAILED",
                {"action_id": action_id, "tool": tool_name, "reason": reason},
                "LAW10-APPROVAL",
            )
            return False

        with self._ledger_lock():
            if action_id in self._used_action_ids or self._ledger_has_grant(action_id):
                self._log_event(
                    "TOKEN_REPLAY_DETECTED",
                    {"action_id": action_id, "tool": tool_name},
                    "LAW10-APPROVAL",
                )
                return False

            self._used_action_ids.add(action_id)
            self._log_event(
                "APPROVAL_GRANTED",
                {
                    "action_id": action_id,
                    "tool": tool_name,
                    "payload_sha256": _payload_sha256(payload),
                    "operator_key_fingerprint": hashlib.sha256(self.operator_pubkey or b"").hexdigest()[:16],
                },
                "RISK-001",
            )
        return True

    # ------------------------------------------------------------------
    # Ledger (LAW9-LEDGER, LAW9-APPEND, LAW9-CHAIN)
    # ------------------------------------------------------------------

    @property
    def _lock_path(self) -> Path:
        return self.ledger_path.with_name(self.ledger_path.name + ".lock")

    @contextlib.contextmanager
    def _ledger_lock(self) -> Iterator[None]:
        """Re-entrant lock held across threads (RLock) and processes (OS file lock)."""
        lock = self.__dict__.setdefault("_lock", threading.RLock())
        with lock:
            depth = getattr(self, "_lock_depth", 0)
            if depth == 0:
                self._lock_fd = _acquire_file_lock(self._lock_path, getattr(self, "lock_timeout", 30.0))
            self._lock_depth = depth + 1
            try:
                yield
            finally:
                self._lock_depth -= 1
                if self._lock_depth == 0:
                    fd, self._lock_fd = self._lock_fd, None
                    if fd is not None:
                        _release_file_lock(fd)

    def _read_tail(self) -> tuple[str, bool]:
        """Return (last event_hash, file ends without newline) by reading the ledger backwards."""
        try:
            size = self.ledger_path.stat().st_size
        except FileNotFoundError:
            return GENESIS_HASH, False
        if size == 0:
            return GENESIS_HASH, False

        with open(self.ledger_path, "rb") as f:
            f.seek(size - 1)
            missing_newline = f.read(1) != b"\n"
            buf = b""
            end = size
            last: bytes | None = None
            while end > 0:
                start = max(0, end - 4096)
                f.seek(start)
                buf = f.read(end - start) + buf
                end = start
                stripped = buf.rstrip(b"\r\n \t")
                if not stripped:
                    continue
                nl = stripped.rfind(b"\n")
                if nl != -1 or end == 0:
                    last = stripped[nl + 1:].strip()
                    break

        if last is None:
            return GENESIS_HASH, missing_newline
        try:
            event = json.loads(last.decode("utf-8"))
            tail_hash = event["event_hash"]
        except (ValueError, KeyError, TypeError):
            tail_hash = None
        if not isinstance(tail_hash, str) or not _HASH_RE.fullmatch(tail_hash):
            raise GovernanceViolation(
                f"Ledger tail is corrupt, refusing to append: {self.ledger_path}",
                "LAW9-CHAIN",
            )
        return tail_hash, missing_newline

    def _ledger_has_grant(self, action_id: str) -> bool:
        """True if the ledger already records an APPROVAL_GRANTED for ``action_id``."""
        if not self.ledger_path.exists():
            return False
        needle = json.dumps(action_id).encode("utf-8")
        with open(self.ledger_path, "rb") as f:
            for line in f:
                if b'"APPROVAL_GRANTED"' not in line or needle not in line:
                    continue
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                data = event.get("data") if isinstance(event, dict) else None
                if (
                    event.get("event_type") == "APPROVAL_GRANTED"
                    and isinstance(data, dict)
                    and data.get("action_id") == action_id
                ):
                    return True
        return False

    def _log_event(self, event_type: str, data: dict[str, Any], law_ref: str) -> str:
        """Append a cryptographically chained event to the ledger.

        Implements: LAW9-LEDGER, LAW9-APPEND, LAW9-CHAIN

        The chain resumes from the last event on disk, under a lock shared by
        threads and processes, so restarts and concurrent writers never fork it.
        Each event includes a UTC timestamp, the event type and law reference,
        the data payload, the previous event's hash, and its own SHA-256 hash.

        Returns:
            The new event's hash
        """
        with self._ledger_lock():
            prev_hash, missing_newline = self._read_tail()
            event = {
                "timestamp": time.time(),
                "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "event_type": event_type,
                "law_ref": law_ref,
                "data": data,
                "prev_event_hash": prev_hash,
            }

            # Compute hash chain link
            event_bytes = json.dumps(event, sort_keys=True).encode("utf-8")
            current_hash = hashlib.sha256(event_bytes).hexdigest()
            event["event_hash"] = current_hash

            # Append to ledger (immutable — never overwrite or delete)
            line = json.dumps(event).encode("utf-8") + b"\n"
            if missing_newline:
                line = b"\n" + line
            with open(self.ledger_path, "ab") as f:
                f.write(line)
                f.flush()
                if getattr(self, "fsync_ledger", False):
                    os.fsync(f.fileno())
            self.prev_event_hash = current_hash
            return current_hash

    def audit_ledger(self) -> dict[str, Any]:
        """Verify the integrity of the append-only event ledger.

        Walks the entire ledger and verifies that:
        1. Each event's hash matches its computed hash
        2. Each event's prev_event_hash matches the prior event's hash
        This detects internal deletion, reordering and edits, but not tail
        truncation or a complete rewrite with recomputed hashes.

        Returns:
            Dict with 'valid', 'total_events', 'broken_links', 'errors'
        """
        if not self.ledger_path.exists():
            return {"valid": True, "total_events": 0, "broken_links": 0, "errors": []}

        errors: list[str] = []
        total_events = 0
        broken_links = 0
        expected_prev_hash = GENESIS_HASH

        with open(self.ledger_path, "r", encoding="utf-8", errors="replace") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                total_events += 1
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    event = None
                if not isinstance(event, dict):
                    errors.append(f"Line {line_num}: Invalid JSON")
                    broken_links += 1
                    continue

                # Check chain link
                if event.get("prev_event_hash") != expected_prev_hash:
                    errors.append(
                        f"Line {line_num}: Broken chain link "
                        f"(expected prev={expected_prev_hash[:16]}..., "
                        f"got prev={str(event.get('prev_event_hash', 'MISSING'))[:16]}...)"
                    )
                    broken_links += 1

                # Verify event hash
                stored_hash = event.pop("event_hash", None)
                if stored_hash:
                    computed = hashlib.sha256(
                        json.dumps(event, sort_keys=True).encode("utf-8")
                    ).hexdigest()
                    if computed != stored_hash:
                        errors.append(
                            f"Line {line_num}: Event hash mismatch "
                            f"(stored={str(stored_hash)[:16]}..., computed={computed[:16]}...)"
                        )
                        broken_links += 1
                    expected_prev_hash = stored_hash
                    event["event_hash"] = stored_hash
                else:
                    errors.append(f"Line {line_num}: Missing event_hash")
                    broken_links += 1

        return {
            "valid": broken_links == 0,
            "total_events": total_events,
            "broken_links": broken_links,
            "errors": errors,
        }

    @staticmethod
    def _compute_sha256(file_path: Path) -> str:
        """Compute the SHA-256 hex digest of a file with normalized LF line endings."""
        return sha256_lf(file_path)

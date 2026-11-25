"""
Host hook adapter: enforce the AGL kernel inside GitHub Copilot CLI, VS Code and
Claude Code agent sessions (the ``autonomous-governance-laws`` plugin).

The host runs ``hooks/agl_hook.py <Event>`` and writes one JSON event to stdin. Both
host payload styles are accepted: Copilot's camelCase (``toolName``/``toolArgs``) and
the snake_case format shared by VS Code, Claude Code and Copilot's PascalCase events
(``tool_name``/``tool_input``).

``PreToolUse`` maps the host tool onto the kernel's vocabulary, classifies it with
``GovernanceKernel.evaluate_risk`` and answers:

- operator halt or PROHIBITED: deny (LAW2-HALT, LAW1-PROHIBIT, LAW3-SUBORDINATE)
- ELEVATED: ask, so the host prompts the operator (RISK-001). Cloud agents and
  autopilot treat ask as deny. ``AGL_ELEVATED_DECISION=defer`` hands the call to the
  host's own permission flow instead; ``AGL_ELEVATED_DECISION=deny`` refuses it.
  Copilot CLI builds that send no ``sessionId`` (0.0.4xx) ignore ask and run the
  tool, so for them ask becomes deny.
- SAFE: no decision; the host's normal permission flow applies.

``SessionStart`` verifies the charter and returns it as ``additionalContext``.

Every decision is appended to the hash-chained ledger in the plugin data directory.

Fail closed: hosts block on different signals, so the event argument selects the
protocol. A camelCase ``preToolUse`` argument (``hooks/copilot-hooks.json``) means
Copilot CLI, whose 0.0.4xx builds run the tool after any hook error or non-zero exit
and block only on a JSON deny with exit status 0: denials and internal errors
therefore print a deny decision and exit 0. Every other event argument (Claude Code,
VS Code) gets exit status 2 for denials in the snake_case format and for every
internal error.

Hosts also let the tool run when a hook times out, so the hook never waits that long:
events over ``MAX_EVENT_BYTES``, calls with more than ``MAX_INSPECTED_CHARS`` of
commands and paths or more than ``MAX_WRITE_PATHS`` write targets are refused, and a
watchdog denies any call still undecided after ``HOOK_DEADLINE`` seconds.
"""

from __future__ import annotations

import json
import os
import re
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping

from autonomous_governance.installer import MANIFEST_REL, charter_source
from autonomous_governance.kernel import GovernanceKernel, PolicyTier, _payload_sha256
from autonomous_governance.loaders import CHARTER_DOCUMENTS

EXIT_BLOCK = 2
# The event argument in hooks/copilot-hooks.json; selects Copilot CLI's deny protocol.
COPILOT_PRE_TOOL_USE = "preToolUse"
FAIL_CLOSED_PREFIX = "AGL governance hook failed closed"

# Claude Code moves any additionalContext over 10,000 characters to a file and keeps
# only a short preview, so the default session context must stay below this.
SESSION_CONTEXT_LIMIT = 10_000
# Skip the full hash-chain walk at session start for very large ledgers.
SESSION_AUDIT_MAX_BYTES = 64 * 1024 * 1024
# Shorter than the hosts' 30 s hook timeout: a timed-out hook fails open, an error fails closed.
HOOK_LOCK_TIMEOUT = 10.0
# If no decision is ready by then, the hook denies and exits rather than let the host time it out.
HOOK_DEADLINE = 20.0
# Larger events are refused (fail closed); hosts' tool calls are far smaller than this.
MAX_EVENT_BYTES = 1024 * 1024
# Commands and paths the kernel must classify (file contents excluded). The worst case
# measured, unique quoted multi-line words, takes about 5.5 s at this size on a desktop CPU.
MAX_INSPECTED_CHARS = 256 * 1024
# A write naming more paths than this is refused rather than inspected path by path.
MAX_WRITE_PATHS = 512

# Host tool names, lower-cased: Copilot CLI runtime names, Claude tool names, VS Code tools.
SHELL_TOOLS = frozenset({
    "bash", "powershell", "write_bash", "write_powershell", "shell", "run_in_terminal",
})
WRITE_TOOLS = frozenset({
    "create", "edit", "str_replace_editor", "apply_patch", "write", "multiedit",
    "notebookedit", "create_file", "create_directory", "edit_file", "edit_notebook_file",
    "insert_edit_into_file", "replace_string_in_file", "multi_replace_string_in_file",
})
READ_ONLY_TOOLS = frozenset({
    "view", "read", "grep", "rg", "glob", "ls", "notebookread", "read_file", "list_dir",
    "file_search", "grep_search", "semantic_search", "read_bash", "list_bash", "bashoutput",
    "read_powershell", "list_powershell",
    "ask_user", "askuserquestion", "report_intent",
    "todoread", "skill", "exitplanmode", "read_agent",
    "list_agents", "fetch_copilot_cli_documentation",
})
ELEVATED_DECISIONS = frozenset({"ask", "defer", "deny"})

# Argument keys (lower-cased, letters only) that carry a path in write tools.
_PATH_ARG_KEYS = frozenset({
    "path", "paths", "filepath", "filepaths", "notebookpath", "file", "files", "filename",
    "targetfile", "targetpath", "dirpath", "dir", "directory", "dest", "destination", "uri",
})
_PATCH_ARG_KEYS = frozenset({"input", "patch", "diff"})
# Paths are trimmed in code: a pattern that trims them itself is quadratic on long lines.
_PATCH_FILE_RE = re.compile(r"^\*\*\* (?:(?:Add|Update|Delete) File|Move to):([^\n]*)", re.MULTILINE)
_DIFF_FILE_RE = re.compile(r"^(?:\+\+\+|---) ([^\t\n]*)", re.MULTILINE)
_COMMAND_ARG_KEYS = ("command", "cmd", "script", "input")
# write_bash / write_powershell send keystrokes; {enter} runs the line typed so far.
_ENTER_KEY_RE = re.compile(r"\{enter\}", re.IGNORECASE)


@dataclass
class HookResult:
    output: dict[str, Any] | None = None
    message: str = ""
    code: int = 0


# ----------------------------------------------------------------------
# Host tool mapping
# ----------------------------------------------------------------------

def _norm_key(key: Any) -> str:
    return re.sub(r"[^a-z]", "", str(key).lower())


def _patch_paths(text: str) -> Iterator[str]:
    for match in _PATCH_FILE_RE.finditer(text):
        path = match.group(1).strip()
        if path:
            yield path
    for match in _DIFF_FILE_RE.finditer(text):
        path = match.group(1).strip()
        if path[:2] in ("a/", "b/"):
            path = path[2:]
        if path and path != "/dev/null":
            yield path


def _write_paths(value: Any, key: str = "", depth: int = 0) -> Iterator[str]:
    """Yield every path a write tool's arguments name, including paths inside patches."""
    if depth > 8:
        raise ValueError("write tool payload nesting exceeds maximum inspection depth")
    if isinstance(value, dict):
        for k, v in value.items():
            yield from _write_paths(v, _norm_key(k), depth + 1)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _write_paths(item, key, depth + 1)
    elif isinstance(value, str) and value.strip():
        if key in _PATH_ARG_KEYS:
            yield value
        if depth == 0 or key in _PATCH_ARG_KEYS:
            yield from _patch_paths(value)


def _command_text(args: Any) -> str | None:
    if isinstance(args, str):
        return args
    if isinstance(args, dict):
        for key in _COMMAND_ARG_KEYS:
            if isinstance(args.get(key), str):
                return args[key]
    return None


def _as_payload(args: Any) -> dict[str, Any]:
    return args if isinstance(args, dict) else {"input": args}


def map_tool(tool_name: str, args: Any) -> tuple[str, dict[str, Any]]:
    """Return the ``(kernel tool, payload)`` that ``evaluate_risk`` should classify.

    Shell tools become ``execute_command``, file-writing tools become ``write_file``
    with every target path, and read-only host tools become ``read_file`` (SAFE, but
    still refused for operator secret keys). Unknown tools pass through unchanged and
    are therefore ELEVATED unless their payload is prohibited.
    """
    name = str(tool_name or "").strip()
    low = name.lower()
    if low in READ_ONLY_TOOLS:
        return "read_file", _as_payload(args)
    if low in SHELL_TOOLS:
        command = _command_text(args)
        if command is None:
            return "execute_command", _as_payload(args)
        return "execute_command", {"command": _ENTER_KEY_RE.sub("\n", command)}
    if low in WRITE_TOOLS:
        paths = list(dict.fromkeys(_write_paths(args)))
        if not paths:
            return "write_file", _as_payload(args)
        payload: dict[str, Any] = {"target_paths": paths}
        if isinstance(args, dict):
            for k, v in args.items():
                k_low = str(k).lower()
                k_norm = _norm_key(k)
                if (
                    k_norm in _PATH_ARG_KEYS
                    or k_norm in _PATCH_ARG_KEYS
                    or k_low in GovernanceKernel.CONTENT_KEYS
                    or k_low in ("edits", "new_source")
                ):
                    continue
                payload[k] = v
        return "write_file", payload
    return name or "unknown_tool", _as_payload(args)


# ----------------------------------------------------------------------
# Event plumbing
# ----------------------------------------------------------------------

def _is_snake_case(event: Mapping[str, Any]) -> bool:
    return any(k in event for k in ("hook_event_name", "tool_name", "tool_input", "session_id"))


def _event_name(argv: list[str], event: Mapping[str, Any]) -> str:
    raw = argv[0] if argv else event.get("hook_event_name", "")
    return _norm_key(raw)


def _event_cwd(event: Mapping[str, Any]) -> Path:
    raw = event.get("cwd")
    if isinstance(raw, str) and raw.strip():
        path = Path(raw).expanduser()
        if path.is_absolute() and path.is_dir():
            return path.resolve()
    return Path.cwd().resolve()


def _tool_args(event: Mapping[str, Any], snake: bool) -> Any:
    args = event.get("tool_input") if snake else event.get("toolArgs")
    if isinstance(args, str):
        try:
            parsed = json.loads(args)
        except ValueError:
            return args
        if isinstance(parsed, (dict, list)):
            return parsed
    return args


def data_dir(env: Mapping[str, str]) -> Path:
    """Plugin data directory: holds the ledger and the global ``.halt`` switch."""
    for var in ("AGL_DATA_DIR", "COPILOT_PLUGIN_DATA", "CLAUDE_PLUGIN_DATA", "PLUGIN_DATA"):
        if env.get(var):
            return Path(env[var]).expanduser().resolve()
    return (Path.home() / ".agl" / "plugin-data").resolve()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


@dataclass
class _Session:
    kernel: GovernanceKernel
    source: Path
    data: Path
    cwd: Path

    @property
    def halt_files(self) -> tuple[Path, Path]:
        return self.kernel.halt_file, self.data / ".halt"

    def active_halt(self) -> Path | None:
        return next((p for p in self.halt_files if p.exists()), None)


def _boot(event: Mapping[str, Any], plugin_root: Path | None, env: Mapping[str, str]) -> _Session:
    cwd = _event_cwd(event)
    # Relative paths in tool arguments are relative to the agent's working directory.
    os.chdir(cwd)
    source = charter_source().resolve()
    data = data_dir(env)
    roots = [data]
    for root in (plugin_root, source):
        # Developing the plugin itself: its tree is the workspace, so only the charter
        # files (protected by name and exact path) stay locked.
        if root is not None and not _is_within(cwd, root):
            roots.append(Path(root).resolve())
    kernel = GovernanceKernel(
        manifest_path=source / MANIFEST_REL,
        ledger_path=data / ".ledger" / "events.jsonl",
        halt_file=cwd / ".halt",
        project_root=source,
        verify_ledger_on_boot=False,
        lock_timeout=HOOK_LOCK_TIMEOUT,
        protected_roots=roots,
    )
    return _Session(kernel, source, data, cwd)


# ----------------------------------------------------------------------
# PreToolUse
# ----------------------------------------------------------------------

def _decision_output(snake: bool, decision: str, reason: str) -> dict[str, Any]:
    output: dict[str, Any] = {"permissionDecision": decision, "permissionDecisionReason": reason}
    if snake:
        output["hookSpecificOutput"] = {"hookEventName": "PreToolUse", **output}
    return output


def deny_output(reason: str) -> dict[str, Any]:
    """A deny decision every supported host reads (top-level and ``hookSpecificOutput``)."""
    return _decision_output(True, "deny", reason)


def _check_inspectable(
    tool: str, kernel: GovernanceKernel, kernel_tool: str, payload: dict[str, Any]
) -> None:
    """Refuse a call too large to classify well before ``HOOK_DEADLINE``."""
    if kernel_tool == "write_file" and len(payload.get("target_paths", ())) > MAX_WRITE_PATHS:
        raise ValueError(f"'{tool}' names more than {MAX_WRITE_PATHS} paths, too many to inspect")
    inspected = sum(len(value) for _, value, _ in kernel._iter_payload_values(payload))
    if inspected > MAX_INSPECTED_CHARS:
        raise ValueError(
            f"'{tool}' carries more than {MAX_INSPECTED_CHARS} characters of commands and paths, "
            "too many to inspect"
        )


def handle_pre_tool_use(
    event: Mapping[str, Any], plugin_root: Path | None, env: Mapping[str, str]
) -> HookResult:
    snake = _is_snake_case(event)
    tool = event.get("tool_name") if snake else event.get("toolName")
    if not isinstance(tool, str) or not tool.strip():
        raise ValueError("PreToolUse event has no tool name")
    args = _tool_args(event, snake)
    session = _boot(event, plugin_root, env)
    kernel = session.kernel

    halt = session.active_halt()
    kernel_tool, payload = map_tool(tool, args)
    tier = None
    if halt is None:
        _check_inspectable(tool, kernel, kernel_tool, payload)
        tier = kernel.evaluate_risk(kernel_tool, payload)

    if halt is not None:
        decision, law = "deny", "LAW2-HALT"
        reason = (
            f"AGL LAW2-HALT: the operator emergency halt is active ({halt}). "
            "Every tool call is refused until the operator removes it."
        )
    elif tier == PolicyTier.PROHIBITED:
        decision, law = "deny", "LAW1-PROHIBIT"
        reason = (
            f"AGL LAW1-PROHIBIT / LAW3-SUBORDINATE: '{tool}' is prohibited by the Autonomous "
            "Governance Laws (a destructive command, or a change to governance state such as "
            "the charter, ledger, keys, .halt or the governance plugin)."
        )
    elif tier == PolicyTier.ELEVATED:
        decision = env.get("AGL_ELEVATED_DECISION", "ask").strip().lower()
        if decision not in ELEVATED_DECISIONS:
            decision = "ask"
        law = "RISK-001"
        reason = f"AGL RISK-001: '{tool}' is an elevated-risk action and needs operator approval."
        if decision == "ask" and not snake and not event.get("sessionId"):
            decision = "deny"
            reason += (
                " This Copilot CLI version cannot ask for approval, so the action is denied. "
                "Run `copilot update`, or set AGL_ELEVATED_DECISION=defer to let the host's own "
                "permission flow decide."
            )
    else:
        decision, law, reason = "none", "RISK-001", ""

    event_hash = kernel._log_event("HOOK_DECISION", {
        "host_event": "PreToolUse",
        "host_tool": tool,
        "kernel_tool": kernel_tool,
        "tier": tier.name if tier else None,
        "decision": decision,
        "session_id": event.get("session_id") if snake else event.get("sessionId"),
        "cwd": str(session.cwd),
        "payload_sha256": _payload_sha256(args),
    }, law)

    if decision in ("none", "defer"):
        return HookResult(output={})
    reason = f"{reason} (ledger event {event_hash[:12]})"
    output = _decision_output(snake, decision, reason)
    if decision == "deny" and snake:
        # Exit 2 blocks in Claude Code and VS Code even if they ignore the JSON.
        return HookResult(output=output, message=reason, code=EXIT_BLOCK)
    return HookResult(output=output)


# ----------------------------------------------------------------------
# SessionStart
# ----------------------------------------------------------------------

def _ledger_status(kernel: GovernanceKernel) -> str:
    path = kernel.ledger_path
    size = path.stat().st_size if path.is_file() else 0
    if size > SESSION_AUDIT_MAX_BYTES:
        return f"`{path}` ({size // (1024 * 1024)} MiB; run `agy-governance audit-ledger` to verify the chain)"
    report = kernel.audit_ledger()
    if report["valid"]:
        return f"`{path}` ({report['total_events']} events, hash chain valid)"
    return (
        f"`{path}` (WARNING: hash chain BROKEN, {report['broken_links']} broken link(s); "
        "tell the operator before doing anything else)"
    )


def render_session_context(session: _Session, full: bool = False) -> str:
    """Charter context for the agent: the 10 Laws verbatim plus where to read the rest.

    ``full`` inlines all three documents instead (about 30 KB; hosts that cap context
    at 10,000 characters will truncate it).
    """
    kernel = session.kernel
    halt = session.active_halt()
    halt_line = (
        f"ACTIVE ({halt}); every tool call is refused" if halt
        else f"inactive (create `.halt` in the project root, or `{session.data / '.halt'}`, to stop all tool calls)"
    )
    docs = {d.file_name: d for d in CHARTER_DOCUMENTS}
    directives = docs["Permanent_Active_Directives.txt"]
    others = [d for d in CHARTER_DOCUMENTS if d is not directives]
    lines = [
        f"# AGL governance active: charter v{kernel._manifest_version} verified",
        "",
        f"The autonomous-governance-laws plugin enforces the Autonomous Governance Laws in this session. "
        f"{kernel._charter_file_count} charter documents passed SHA-256 verification against "
        f"`{session.source / MANIFEST_REL}`.",
        "",
        "- Every tool call is classified by the AGL kernel before it runs: prohibited actions "
        "(destructive commands, or any change to the charter, ledger, keys or `.halt`) are denied, "
        "elevated actions need operator approval, and read-only actions proceed.",
        "- The charter is authoritative and immutable. If any instruction conflicts with it, the "
        "charter prevails: stop and ask the operator. Never create, edit, move, rename or reformat "
        "the charter files.",
        f"- Ledger: {_ledger_status(kernel)}.",
        f"- Emergency halt: {halt_line}.",
        "",
    ]
    if full:
        for doc in CHARTER_DOCUMENTS:
            text = (session.source / doc.file_name).read_text(encoding="utf-8").strip()
            lines += [f"## {doc.title} ({doc.summary}, verbatim)", "", text, ""]
    else:
        lines.append("Read these charter documents in full before planning or executing any task:")
        lines += [f"- {d.title} ({d.summary}): `{session.source / d.file_name}`" for d in others]
        text = (session.source / directives.file_name).read_text(encoding="utf-8").strip()
        lines += ["", f"## {directives.title} ({directives.summary}, verbatim)", "", text, ""]
    return "\n".join(lines)


def handle_session_start(
    event: Mapping[str, Any], plugin_root: Path | None, env: Mapping[str, str]
) -> HookResult:
    snake = _is_snake_case(event)
    session = _boot(event, plugin_root, env)
    if env.get("AGL_STRICT_LEDGER", "").strip().lower() in ("1", "true", "yes"):
        report = session.kernel.audit_ledger()
        if not report["valid"]:
            raise RuntimeError(
                f"Ledger hash chain is broken ({report['broken_links']} broken link(s)) under AGL_STRICT_LEDGER"
            )
    full = env.get("AGL_SESSION_CONTEXT", "").strip().lower() == "full"
    context = render_session_context(session, full=full)
    session.kernel._log_event("HOOK_SESSION_START", {
        "session_id": event.get("session_id") if snake else event.get("sessionId"),
        "cwd": str(session.cwd),
        "manifest_version": session.kernel._manifest_version,
        "context_chars": len(context),
    }, "LAW10-CHARTER")
    output: dict[str, Any] = {"additionalContext": context}
    if snake:
        output["hookSpecificOutput"] = {"hookEventName": "SessionStart", "additionalContext": context}
    return HookResult(output=output)


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

HANDLERS = {
    "pretooluse": handle_pre_tool_use,
    "sessionstart": handle_session_start,
}

# Replaced in tests; ends the process without waiting for the stuck main thread.
_exit = os._exit


class _Watchdog:
    """Answer with a fail-closed denial if the hook is still working at the deadline.

    Hosts let the tool run when a hook times out, so a slow decision must never reach
    the host's timeout. Whichever of the watchdog and ``main`` claims the answer first
    writes it; the other stays silent.
    """

    def __init__(self, seconds: float, copilot: bool, stdout: Any, stderr: Any):
        self._seconds = seconds
        self._copilot = copilot
        self._stdout = stdout
        self._stderr = stderr
        self._lock = threading.Lock()
        self._claimed = False
        self._timer = threading.Timer(seconds, self._expire)
        self._timer.daemon = True
        self._timer.start()

    def claim(self) -> bool:
        """Stop the timer; True if ``main`` may still write its answer."""
        self.cancel()
        with self._lock:
            if self._claimed:
                return False
            self._claimed = True
            return True

    def cancel(self) -> None:
        self._timer.cancel()

    def _expire(self) -> None:
        with self._lock:
            if self._claimed:
                return
            self._claimed = True
            message = f"{FAIL_CLOSED_PREFIX}: no decision within {self._seconds:g} s."
            try:
                self._stderr.write(message + "\n")
                if self._copilot:
                    self._stdout.write(json.dumps(deny_output(message)) + "\n")
                self._stdout.flush()
                self._stderr.flush()
            finally:
                _exit(0 if self._copilot else EXIT_BLOCK)


def main(
    argv: list[str] | None = None,
    *,
    plugin_root: str | Path | None = None,
    stdin: Any = None,
    stdout: Any = None,
    stderr: Any = None,
    env: Mapping[str, str] | None = None,
    deadline: float | None = HOOK_DEADLINE,
) -> int:
    """Run one hook event and return the process exit status."""
    argv = list(sys.argv[1:] if argv is None else argv)
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    stderr = sys.stderr if stderr is None else stderr
    env = os.environ if env is None else env
    copilot = bool(argv) and argv[0] == COPILOT_PRE_TOOL_USE
    watchdog = _Watchdog(deadline, copilot, stdout, stderr) if deadline else None
    try:
        return _run(argv, plugin_root, stdin, stdout, stderr, env, copilot, watchdog)
    finally:
        if watchdog is not None:
            watchdog.cancel()


def _run(
    argv: list[str],
    plugin_root: str | Path | None,
    stdin: Any,
    stdout: Any,
    stderr: Any,
    env: Mapping[str, str],
    copilot: bool,
    watchdog: _Watchdog | None,
) -> int:
    try:
        root = Path(plugin_root).resolve() if plugin_root is not None else None
        # Read everything: a host whose write to stdin fails may treat that as a hook error.
        raw = stdin.buffer.read() if hasattr(stdin, "buffer") else stdin.read()
        if len(raw) > MAX_EVENT_BYTES:
            raise ValueError(f"hook input is larger than {MAX_EVENT_BYTES} bytes, too large to inspect")
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        raw = raw.lstrip("\ufeff")
        event = json.loads(raw) if raw.strip() else {}
        if not isinstance(event, dict):
            raise ValueError("hook input must be a JSON object")
        name = _event_name(argv, event)
        handler = HANDLERS.get(name)
        if handler is None:
            raise ValueError(f"unsupported hook event: {name or '(none)'}")
        result = handler(event, root, env)
    except Exception as exc:  # noqa: BLE001 - every failure must block, never allow
        if watchdog is not None and not watchdog.claim():
            return 0 if copilot else EXIT_BLOCK
        message = f"{FAIL_CLOSED_PREFIX}: {type(exc).__name__}: {exc}"
        stderr.write(message + "\n")
        if copilot:
            stdout.write(json.dumps(deny_output(message)) + "\n")
            return 0
        return EXIT_BLOCK
    if watchdog is not None and not watchdog.claim():
        return 0 if copilot else EXIT_BLOCK
    if result.output is not None:
        stdout.write(json.dumps(result.output) + "\n")
    if result.message:
        stderr.write(result.message + "\n")
    # Copilot CLI only blocks on the JSON deny with exit 0; any other status lets the tool run.
    return 0 if copilot else result.code


if __name__ == "__main__":
    sys.exit(main())

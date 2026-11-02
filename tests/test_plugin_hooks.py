"""Tests for the agent plugin: the host hook adapter, its entry points and manifests."""

from __future__ import annotations

import io
import json
import os
import random
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

import autonomous_governance
from autonomous_governance import hooks
from autonomous_governance.installer import MANIFEST_REL
from autonomous_governance.kernel import GovernanceKernel, PolicyTier, _payload_sha256, _strip_sql_comments
from autonomous_governance.loaders import CHARTER_DOCUMENTS

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOKS_DIR = REPO_ROOT / "hooks"
SHIM = HOOKS_DIR / "agl_hook.py"
CHARTER_NAMES = [d.file_name for d in CHARTER_DOCUMENTS]
HOST_ENV_PREFIXES = ("AGL_", "COPILOT_PLUGIN", "CLAUDE_PLUGIN", "PLUGIN_DATA", "PYTHONPATH")


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

@pytest.fixture
def dirs(tmp_path, monkeypatch):
    """A workspace outside the plugin tree, plus an isolated plugin data directory."""
    project = tmp_path / "project"
    project.mkdir()
    # The hook changes into the event's cwd; monkeypatch restores the original.
    monkeypatch.chdir(project)
    return project, tmp_path / "data"


def camel(project: Path, tool: str, args, **extra) -> dict:
    """Copilot CLI camelCase event; toolArgs is a JSON string."""
    return {
        "sessionId": "test-session",
        "timestamp": 1767225600000,
        "cwd": str(project),
        "toolName": tool,
        "toolArgs": args if isinstance(args, str) else json.dumps(args),
        **extra,
    }


def snake(project: Path, tool: str, tool_input, event: str = "PreToolUse") -> dict:
    """Claude Code / VS Code / Copilot PascalCase event."""
    return {
        "hook_event_name": event,
        "session_id": "test-session",
        "timestamp": "2026-01-01T00:00:00Z",
        "cwd": str(project),
        "tool_name": tool,
        "tool_input": tool_input,
    }


def call(dirs, event_name, payload, env=None, raw=None, argv=None):
    """Run the hook in-process; returns (exit code, parsed stdout, stderr)."""
    _, data = dirs
    stdout, stderr = io.StringIO(), io.StringIO()
    code = hooks.main(
        [event_name] if argv is None else argv,
        plugin_root=REPO_ROOT,
        stdin=io.StringIO(json.dumps(payload) if raw is None else raw),
        stdout=stdout,
        stderr=stderr,
        env={"AGL_DATA_DIR": str(data), **(env or {})},
    )
    text = stdout.getvalue().strip()
    return code, (json.loads(text) if text else None), stderr.getvalue()


def decision(output) -> str | None:
    return (output or {}).get("permissionDecision")


def ledger_events(data: Path) -> list[dict]:
    path = data / ".ledger" / "events.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def audit(ledger: Path, tmp_path: Path) -> dict:
    kernel = GovernanceKernel(
        manifest_path=REPO_ROOT / MANIFEST_REL,
        ledger_path=ledger,
        halt_file=tmp_path / "audit.halt",
    )
    return kernel.audit_ledger()


def subprocess_env(data: Path, **extra: str) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith(HOST_ENV_PREFIXES)}
    env["AGL_DATA_DIR"] = str(data)
    env.update(extra)
    return env


def run_shim(shim: Path, event_name: str, payload, data: Path, **env) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(shim), event_name],
        input=json.dumps(payload).encode("utf-8"),
        capture_output=True,
        env=subprocess_env(data, **env),
        timeout=120,
    )


# ----------------------------------------------------------------------
# PreToolUse decisions
# ----------------------------------------------------------------------

CAMEL_CASES = [
    ("view", {"path": "README.md"}, None),
    ("grep", {"pattern": "operator.key", "path": "."}, None),
    ("glob", {"pattern": "**/*.py"}, None),
    ("web_fetch", {"url": "https://example.com"}, None),
    ("bash", {"command": "git status"}, "ask"),
    ("powershell", {"command": "Get-ChildItem"}, "ask"),
    ("edit", {"path": "src/app.py", "old_str": "a", "new_str": "b"}, "ask"),
    ("create", {"path": "notes.md", "file_text": "DROP TABLE x is only text here"}, "ask"),
    ("github-mcp-server-list_issues", {"owner": "o", "repo": "r"}, "ask"),
    ("task", {"prompt": "do something"}, "ask"),
    ("bash", {"command": "rm -rf /"}, "deny"),
    ("powershell", {"command": "Remove-Item -Recurse -Force C:\\"}, "deny"),
    ("bash", {"command": "rm .halt"}, "deny"),
    ("bash", {"command": "echo x > Permanent_Active_Directives.txt"}, "deny"),
    ("sql", {"query": "DROP TABLE todos"}, "deny"),
    ("create", {"path": "config/charter_manifest.json", "file_text": "{}"}, "deny"),
    ("edit", {"path": "AGENTIC_PRIME_DIRECTIVE.md", "old_str": "a", "new_str": "b"}, "deny"),
    ("create", {"path": ".halt", "file_text": ""}, "deny"),
    ("view", {"path": ".keys/operator.key"}, "deny"),
    ("apply_patch", "*** Begin Patch\n*** Update File: app.py\n@@\n-a\n+b\n*** End Patch\n", "ask"),
    (
        "apply_patch",
        "*** Begin Patch\n*** Update File: app.py\n*** Move to: .ledger/events.jsonl\n*** End Patch\n",
        "deny",
    ),
]


@pytest.mark.parametrize("tool,args,expected", CAMEL_CASES)
def test_camel_case_decisions(dirs, tool, args, expected):
    code, output, stderr = call(dirs, "preToolUse", camel(dirs[0], tool, args))
    assert code == 0, stderr
    assert decision(output) == expected
    if expected is None:
        assert output == {}
    else:
        assert "hookSpecificOutput" not in output
        assert output["permissionDecisionReason"].startswith("AGL ")


SNAKE_CASES = [
    ("Read", {"file_path": "README.md"}, None, 0),
    ("WebFetch", {"url": "https://example.com"}, None, 0),
    ("Write", {"file_path": "b.py", "content": "print(1)"}, "ask", 0),
    ("MultiEdit", {"file_path": "x.py", "edits": []}, "ask", 0),
    ("mcp__github__create_issue", {"title": "x"}, "ask", 0),
    ("Bash", {"command": "psql -c 'DROP TABLE users'"}, "deny", 2),
    ("Edit", {"file_path": "config/charter_manifest.json", "old_string": "a", "new_string": "b"}, "deny", 2),
    ("NotebookEdit", {"notebook_path": ".ledger/x.ipynb", "new_source": "x"}, "deny", 2),
    ("Read", {"file_path": ".keys/operator.key"}, "deny", 2),
]


@pytest.mark.parametrize("tool,tool_input,expected,exit_code", SNAKE_CASES)
def test_snake_case_decisions(dirs, tool, tool_input, expected, exit_code):
    code, output, stderr = call(dirs, "PreToolUse", snake(dirs[0], tool, tool_input))
    assert code == exit_code
    assert decision(output) == expected
    if expected is None:
        assert output == {}
        return
    specific = output["hookSpecificOutput"]
    assert specific["hookEventName"] == "PreToolUse"
    assert specific["permissionDecision"] == expected
    assert specific["permissionDecisionReason"] == output["permissionDecisionReason"]
    # A blocking exit must explain itself on stderr, which the host shows the agent.
    assert (output["permissionDecisionReason"] in stderr) == (exit_code == 2)


def test_plugin_and_data_directories_are_protected(dirs):
    project, data = dirs
    for target in (
        REPO_ROOT / "hooks" / "evil.py",
        REPO_ROOT / "src" / "autonomous_governance" / "kernel.py",
        REPO_ROOT / ".plugin" / "plugin.json",
        data / "notes.txt",
        data / ".halt",
    ):
        _, output, _ = call(dirs, "preToolUse", camel(project, "create", {"path": str(target), "file_text": "x"}))
        assert decision(output) == "deny", target
    patch = f"*** Begin Patch\n*** Add File: {REPO_ROOT / 'hooks' / 'x.py'}\n+x\n*** End Patch\n"
    _, output, _ = call(dirs, "preToolUse", camel(project, "apply_patch", patch))
    assert decision(output) == "deny"
    # Reading the plugin is fine.
    _, output, _ = call(dirs, "preToolUse", camel(project, "view", {"path": str(SHIM)}))
    assert output == {}


def test_developing_the_plugin_itself_allows_its_workspace(tmp_path, monkeypatch):
    data = tmp_path / "data"
    monkeypatch.chdir(REPO_ROOT)
    dev = (REPO_ROOT, data)
    _, output, _ = call(dev, "preToolUse", camel(REPO_ROOT, "edit", {"path": "src/autonomous_governance/hooks.py"}))
    assert decision(output) == "ask"
    # The charter, manifest and data directory stay locked even in dev mode.
    for target in ("config/charter_manifest.json", "AGENTIC_SACRED_COVENANT.md", str(data / "x")):
        _, output, _ = call(dev, "preToolUse", camel(REPO_ROOT, "create", {"path": target}))
        assert decision(output) == "deny", target


@pytest.mark.parametrize("setting,expected,exit_code", [
    ("defer", None, 0),
    ("DENY", "deny", 2),
    ("ask", "ask", 0),
    ("allow", "ask", 0),  # unknown values never weaken the default
])
def test_elevated_decision_setting(dirs, setting, expected, exit_code):
    payload = snake(dirs[0], "Bash", {"command": "ls"})
    code, output, _ = call(dirs, "PreToolUse", payload, env={"AGL_ELEVATED_DECISION": setting})
    assert code == exit_code
    assert decision(output) == expected


def test_elevated_setting_never_relaxes_prohibited(dirs):
    payload = camel(dirs[0], "bash", {"command": "rm -rf /"})
    _, output, _ = call(dirs, "preToolUse", payload, env={"AGL_ELEVATED_DECISION": "defer"})
    assert decision(output) == "deny"


@pytest.mark.parametrize("where", ["project", "data"])
def test_halt_denies_every_tool(dirs, where):
    project, data = dirs
    halt = (project if where == "project" else data) / ".halt"
    halt.parent.mkdir(parents=True, exist_ok=True)
    halt.write_text("operator stop", encoding="utf-8")
    code, output, _ = call(dirs, "preToolUse", camel(project, "view", {"path": "README.md"}))
    assert code == 0 and decision(output) == "deny"
    assert "LAW2-HALT" in output["permissionDecisionReason"]
    code, output, stderr = call(dirs, "PreToolUse", snake(project, "Read", {"file_path": "README.md"}))
    assert code == 2 and "LAW2-HALT" in stderr


def test_decisions_are_ledgered_without_raw_arguments(dirs, tmp_path):
    project, data = dirs
    args = {"file_path": "b.py", "content": "TOPSECRET-CONTENT-123"}
    _, output, _ = call(dirs, "PreToolUse", snake(project, "Write", args))
    call(dirs, "preToolUse", camel(project, "bash", {"command": "echo TOPSECRET-CMD-456"}))
    call(dirs, "preToolUse", camel(project, "view", {"path": "README.md"}))

    events = ledger_events(data)
    raw = (data / ".ledger" / "events.jsonl").read_text(encoding="utf-8")
    assert "TOPSECRET" not in raw
    decisions = [e for e in events if e["event_type"] == "HOOK_DECISION"]
    assert [d["data"]["decision"] for d in decisions] == ["ask", "ask", "none"]
    first = decisions[0]
    assert first["data"]["host_tool"] == "Write"
    assert first["data"]["kernel_tool"] == "write_file"
    assert first["data"]["tier"] == "ELEVATED"
    assert first["data"]["session_id"] == "test-session"
    assert first["data"]["payload_sha256"] == _payload_sha256(args)
    assert first["law_ref"] == "RISK-001"
    # The reason cites the ledger event that recorded it.
    assert f"(ledger event {first['event_hash'][:12]})" in output["permissionDecisionReason"]
    assert audit(data / ".ledger" / "events.jsonl", tmp_path)["valid"]


# ----------------------------------------------------------------------
# Fail-closed input handling
# ----------------------------------------------------------------------

@pytest.mark.parametrize("argv,raw,needle", [
    (["PreToolUse"], "not json", "JSONDecodeError"),
    (["PreToolUse"], "[1, 2]", "JSON object"),
    (["PostToolUse"], "{}", "unsupported hook event"),
    (["postToolUse"], "{}", "unsupported hook event"),
    ([], "{}", "unsupported hook event"),
    (["PreToolUse"], '{"toolArgs": "{}"}', "no tool name"),
])
def test_bad_input_fails_closed(dirs, argv, raw, needle):
    code, output, stderr = call(dirs, None, None, raw=raw, argv=argv)
    assert code == 2
    assert output is None
    assert "failed closed" in stderr and needle in stderr


@pytest.mark.parametrize("event_name", ["sessionStart", "SessionStart"])
def test_session_start_errors_exit_2(dirs, event_name):
    _, data = dirs
    data.write_text("a file where the data directory should be", encoding="utf-8")
    code, output, stderr = call(dirs, event_name, {"cwd": str(dirs[0])})
    assert code == 2 and output is None
    assert "failed closed" in stderr


@pytest.mark.parametrize("raw,needle", [
    ("not json", "JSONDecodeError"),
    ("", "no tool name"),
    ("[1, 2]", "JSON object"),
    ('{"toolArgs": "{}"}', "no tool name"),
])
def test_copilot_errors_fail_closed_with_json_deny(dirs, raw, needle):
    # Copilot CLI 0.0.4xx runs the tool after any non-zero exit; only a JSON deny with exit 0 blocks.
    code, output, stderr = call(dirs, None, None, raw=raw, argv=["preToolUse"])
    assert code == 0
    reason = output["permissionDecisionReason"]
    assert reason.startswith(hooks.FAIL_CLOSED_PREFIX) and needle in reason
    assert output == hooks.deny_output(reason)
    assert reason in stderr


def test_copilot_argument_never_exits_non_zero(dirs):
    # A snake_case payload under the Copilot argument (a host reading copilot-hooks.json
    # with Claude-style events) still gets a deny both formats can read, with exit 0.
    code, output, stderr = call(dirs, "preToolUse", snake(dirs[0], "Bash", {"command": "rm -rf /"}))
    assert code == 0
    assert decision(output) == output["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "LAW1-PROHIBIT" in stderr


def test_legacy_copilot_turns_ask_into_deny(dirs):
    project, data = dirs
    payload = camel(project, "bash", {"command": "git push --force"})
    del payload["sessionId"]  # Copilot CLI 0.0.4xx sends no sessionId and ignores "ask"
    code, output, _ = call(dirs, "preToolUse", payload)
    assert code == 0 and decision(output) == "deny"
    assert "RISK-001" in output["permissionDecisionReason"]
    assert "copilot update" in output["permissionDecisionReason"]
    assert "hookSpecificOutput" not in output
    recorded = [e["data"] for e in ledger_events(data) if e["event_type"] == "HOOK_DECISION"]
    assert recorded[-1]["decision"] == "deny" and recorded[-1]["tier"] == "ELEVATED"

    # The operator can still hand elevated calls to the host's own permission flow.
    _, output, _ = call(dirs, "preToolUse", payload, env={"AGL_ELEVATED_DECISION": "defer"})
    assert output == {}
    # Safe tools are unaffected, and a sessionId (current Copilot CLI) keeps ask.
    read = camel(project, "view", {"path": "README.md"})
    del read["sessionId"]
    assert call(dirs, "preToolUse", read)[1] == {}
    _, output, _ = call(dirs, "preToolUse", camel(project, "bash", {"command": "git push --force"}))
    assert decision(output) == "ask"


def test_event_name_from_payload_and_bom(dirs):
    payload = snake(dirs[0], "Bash", {"command": "rm -rf /"})
    code, output, _ = call(dirs, None, None, raw="\ufeff" + json.dumps(payload), argv=[])
    assert code == 2 and decision(output) == "deny"


def test_oversized_events_fail_closed(dirs):
    project, _ = dirs
    padding = "x" * hooks.MAX_EVENT_BYTES
    code, output, _ = call(dirs, "preToolUse", camel(project, "view", {"path": "README.md", "pad": padding}))
    assert code == 0 and decision(output) == "deny"
    assert "too large to inspect" in output["permissionDecisionReason"]
    code, output, stderr = call(dirs, "PreToolUse", snake(project, "Read", {"file_path": "README.md", "pad": padding}))
    assert code == 2 and output is None and "too large to inspect" in stderr


def test_calls_too_large_to_inspect_fail_closed(dirs):
    project, _ = dirs
    command = "echo " + "a " * (hooks.MAX_INSPECTED_CHARS // 2)
    _, output, _ = call(dirs, "preToolUse", camel(project, "bash", {"command": command}))
    assert decision(output) == "deny" and "too many to inspect" in output["permissionDecisionReason"]
    targets = "".join(f"*** Add File: f{i}.py\n+x\n" for i in range(hooks.MAX_WRITE_PATHS + 1))
    _, output, _ = call(dirs, "preToolUse", camel(project, "apply_patch", f"*** Begin Patch\n{targets}*** End Patch\n"))
    assert decision(output) == "deny" and f"more than {hooks.MAX_WRITE_PATHS} paths" in output["permissionDecisionReason"]
    # File contents are not inspected, so they do not count.
    big = {"path": "big.txt", "file_text": "a " * hooks.MAX_INSPECTED_CHARS}
    _, output, _ = call(dirs, "preToolUse", camel(project, "create", big))
    assert decision(output) == "ask"
    # The operator halt still answers first, with its own reason.
    (project / ".halt").write_text("stop", encoding="utf-8")
    _, output, _ = call(dirs, "preToolUse", camel(project, "bash", {"command": command}))
    assert "LAW2-HALT" in output["permissionDecisionReason"]


@pytest.mark.parametrize("argv,exit_code", [(["preToolUse"], 0), (["PreToolUse"], 2)])
def test_watchdog_denies_a_slow_decision(dirs, monkeypatch, argv, exit_code):
    # Hosts run the tool when a hook times out, so the hook must answer first.
    exits: list[int] = []
    released = threading.Event()

    def fake_exit(code: int) -> None:
        exits.append(code)
        released.set()

    def slow(event, root, env):
        released.wait(30)
        return hooks.HookResult(output={"permissionDecision": "allow-after-deadline"})

    monkeypatch.setattr(hooks, "_exit", fake_exit)
    monkeypatch.setitem(hooks.HANDLERS, "pretooluse", slow)
    stdout, stderr = io.StringIO(), io.StringIO()
    code = hooks.main(
        argv, plugin_root=REPO_ROOT, stdin=io.StringIO(json.dumps(camel(dirs[0], "view", {"path": "x"}))),
        stdout=stdout, stderr=stderr, env={"AGL_DATA_DIR": str(dirs[1])}, deadline=0.2,
    )
    assert exits == [exit_code] and code == exit_code
    assert f"{hooks.FAIL_CLOSED_PREFIX}: no decision within 0.2 s." in stderr.getvalue()
    # Only the watchdog answered; the late decision was dropped.
    lines = stdout.getvalue().splitlines()
    if exit_code == 0:
        assert len(lines) == 1 and decision(json.loads(lines[0])) == "deny"
    else:
        assert lines == []


def test_watchdog_is_disarmed_when_main_is_interrupted(dirs, monkeypatch):
    exits: list[int] = []
    monkeypatch.setattr(hooks, "_exit", exits.append)

    def interrupted(event, root, env):
        raise KeyboardInterrupt

    monkeypatch.setitem(hooks.HANDLERS, "pretooluse", interrupted)
    with pytest.raises(KeyboardInterrupt):
        hooks.main(
            ["preToolUse"], plugin_root=REPO_ROOT, stdin=io.StringIO(json.dumps(camel(dirs[0], "view", {"path": "x"}))),
            stdout=io.StringIO(), stderr=io.StringIO(), env={"AGL_DATA_DIR": str(dirs[1])}, deadline=0.1,
        )
    time.sleep(0.4)
    assert exits == []


# ----------------------------------------------------------------------
# SessionStart
# ----------------------------------------------------------------------

def _charter_text(name: str) -> str:
    return (REPO_ROOT / name).read_text(encoding="utf-8").strip()


def test_session_start_compact_context(dirs):
    project, _ = dirs
    payload = {**snake(project, "", {}, event="SessionStart"), "source": "startup"}
    code, output, stderr = call(dirs, "SessionStart", payload)
    assert code == 0, stderr
    context = output["additionalContext"]
    assert output["hookSpecificOutput"] == {"hookEventName": "SessionStart", "additionalContext": context}
    assert len(context) < hooks.SESSION_CONTEXT_LIMIT
    assert _charter_text("Permanent_Active_Directives.txt") in context
    for name in ("AGENTIC_PRIME_DIRECTIVE.md", "AGENTIC_SACRED_COVENANT.md"):
        assert str(REPO_ROOT / name) in context
    assert "hash chain valid" in context and "Emergency halt: inactive" in context


def test_session_start_full_context(dirs):
    project, _ = dirs
    payload = {"sessionId": "s", "timestamp": 1, "cwd": str(project), "source": "new"}
    code, output, _ = call(dirs, "sessionStart", payload, env={"AGL_SESSION_CONTEXT": "full"})
    assert code == 0
    assert "hookSpecificOutput" not in output
    for name in CHARTER_NAMES:
        assert _charter_text(name) in output["additionalContext"]


def test_session_start_reports_halt_and_broken_ledger(dirs):
    project, data = dirs
    call(dirs, "preToolUse", camel(project, "view", {"path": "README.md"}))
    ledger = data / ".ledger" / "events.jsonl"
    lines = ledger.read_text(encoding="utf-8").splitlines()
    first = json.loads(lines[0])
    first["data"]["manifest_version"] = "tampered"
    ledger.write_text("\n".join([json.dumps(first), *lines[1:]]) + "\n", encoding="utf-8")
    (project / ".halt").write_text("stop", encoding="utf-8")

    code, output, _ = call(dirs, "SessionStart", snake(project, "", {}, event="SessionStart"))
    assert code == 0
    context = output["additionalContext"]
    assert "hash chain BROKEN" in context
    assert "Emergency halt: ACTIVE" in context


# ----------------------------------------------------------------------
# Host tool mapping
# ----------------------------------------------------------------------

def test_map_tool_shapes():
    assert hooks.map_tool("Bash", {"command": "ls", "timeout": 5}) == ("execute_command", {"command": "ls"})
    assert hooks.map_tool("bash", "ls -la") == ("execute_command", {"command": "ls -la"})
    assert hooks.map_tool("Read", {"file_path": "a"}) == ("read_file", {"file_path": "a"})
    assert hooks.map_tool("mcp__x__y", {"q": 1}) == ("mcp__x__y", {"q": 1})
    assert hooks.map_tool("", None) == ("unknown_tool", {"input": None})
    assert hooks.map_tool("create", {"file_text": "x"}) == ("write_file", {"file_text": "x"})
    assert hooks.map_tool("MultiEdit", {"file_path": "a.py", "edits": [{"old_string": "x"}]}) == (
        "write_file", {"target_paths": ["a.py"]},
    )
    # Patch markers inside ordinary file content are data, not targets.
    assert hooks.map_tool("edit", {"path": "a.py", "new_str": "*** Update File: CHARTER.md"}) == (
        "write_file", {"target_paths": ["a.py"]},
    )


def test_map_tool_extracts_patch_and_diff_paths():
    patch = (
        "*** Begin Patch\n*** Add File: new.py\n+x\n*** Update File: old.py\n"
        "*** Move to: moved.py\n*** Delete File: gone.py\n*** End Patch\n"
    )
    assert hooks.map_tool("apply_patch", {"input": patch})[1]["target_paths"] == [
        "new.py", "old.py", "moved.py", "gone.py",
    ]
    diff = "--- a/src/x.py\n+++ b/src/y.py\n@@\n--- /dev/null\n+++ b/created.txt\n"
    assert hooks.map_tool("Edit", {"diff": diff})[1]["target_paths"] == [
        "src/x.py", "src/y.py", "created.txt",
    ]


def test_map_tool_patch_paths_are_trimmed_in_linear_time():
    patch = "*** Begin Patch\n*** Add File:   spaced.py  \n*** Update File:\n*** End Patch\n"
    assert hooks.map_tool("apply_patch", {"input": patch})[1]["target_paths"] == ["spaced.py"]
    diff = "--- a/x.py\t2026-01-01 00:00\n+++ b/y.py\t2026-01-01 00:00\n"
    assert hooks.map_tool("Edit", {"diff": diff})[1]["target_paths"] == ["x.py", "y.py"]
    # A pattern that trims the path itself backtracks quadratically on long runs of spaces.
    for line in ("+++ " + " " * 75_000 + "x", "*** Add File:" + " " * 75_000 + "x"):
        start = time.perf_counter()
        assert hooks.map_tool("apply_patch", {"input": line})[1]["target_paths"] == ["x"]
        assert time.perf_counter() - start < 2.0


def test_map_tool_write_bash_enter_key_ends_a_line():
    assert hooks.map_tool("write_bash", {"shellId": "1", "input": "ls{ENTER}pwd{enter}"}) == (
        "execute_command", {"command": "ls\npwd\n"},
    )


# ----------------------------------------------------------------------
# Classifier hardening
# ----------------------------------------------------------------------

MULTILINE_PROHIBITED = [
    "echo hi\nrm -rf ~",
    "echo ok\r\nrm -rf /home",
    "true\nrm -f .halt",
    "cd /tmp\nmkfs.ext4 /dev/sda1",
    "git status\nRemove-Item -Recurse -Force C:\\",
    "echo a &&\nrm -rf ~",
    "ls\n\nrm -rf ~",
    "rm -rf ~ # done\nls",
    # Continued lines are still one command.
    "Remove-Item `\n -Recurse -Force C:\\",
    "rm -rf \\\n~",
]


@pytest.mark.parametrize("command", MULTILINE_PROHIBITED)
def test_every_line_of_a_command_is_classified(dirs, command):
    project, _ = dirs
    code, output, _ = call(dirs, "preToolUse", camel(project, "bash", {"command": command}))
    assert code == 0 and decision(output) == "deny"
    code, output, _ = call(dirs, "PreToolUse", snake(project, "Bash", {"command": command}))
    assert code == 2 and decision(output) == "deny"


@pytest.mark.parametrize("command", ["echo hi\nls -la", "printf 'a\nb'", "git commit -m 'one\ntwo'"])
def test_benign_multiline_commands_still_ask(dirs, command):
    _, output, _ = call(dirs, "preToolUse", camel(dirs[0], "bash", {"command": command}))
    assert decision(output) == "ask"


def test_write_bash_keystrokes_are_classified(dirs):
    for keys in ("rm -rf ~{enter}", "echo hi{enter}rm -rf ~{enter}"):
        _, output, _ = call(dirs, "preToolUse", camel(dirs[0], "write_bash", {"shellId": "1", "input": keys}))
        assert decision(output) == "deny", keys


def _spellings(target: Path) -> list[str]:
    """Other ways to name ``target`` that reach the same file."""
    names = [target.as_uri()]
    if os.name == "nt":
        text = str(target)
        drive, rest = text[0], text[2:]
        names += [
            "\\\\?\\" + text,
            "\\\\.\\" + text,
            f"\\\\localhost\\{drive}$" + rest,
            f"\\\\127.0.0.1\\{drive.lower()}$" + rest,
            f"\\\\?\\UNC\\localhost\\{drive}$" + rest,
            text + "::$DATA",
            text + ".",
            f"{target.parent}::$INDEX_ALLOCATION\\{target.name}",
        ]
    return names


def test_alternate_spellings_of_protected_paths(dirs):
    project, data = dirs
    for target in (REPO_ROOT / "hooks" / "agl_hook.py", data / "notes.txt"):
        for name in _spellings(target):
            _, output, _ = call(dirs, "preToolUse", camel(project, "create", {"path": name, "file_text": "x"}))
            assert decision(output) == "deny", name
            _, output, _ = call(dirs, "preToolUse", camel(project, "bash", {"command": f"echo x > '{name}'"}))
            assert decision(output) == "deny", name


def test_links_into_governance_state_are_resolved(dirs):
    project, data = dirs
    data.mkdir(parents=True, exist_ok=True)
    link = project / "innocent"
    try:
        os.symlink(data, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        if os.name != "nt":
            pytest.skip("cannot create a symlink here")
        import _winapi  # junctions need no privilege on Windows

        try:
            _winapi.CreateJunction(str(data), str(link))
        except OSError:
            pytest.skip("cannot create a symlink or junction here")
    _, output, _ = call(dirs, "preToolUse", camel(project, "create", {"path": "innocent/notes.txt", "file_text": "x"}))
    assert decision(output) == "deny"
    _, output, _ = call(dirs, "preToolUse", camel(project, "create", {"path": "other/notes.txt", "file_text": "x"}))
    assert decision(output) == "ask"


def test_strip_sql_comments_matches_the_old_pattern():
    # The old pattern, re.sub(r"/\*.*?\*/|--[^\n]*", " ", text, flags=re.S), is quadratic
    # on many unclosed "/*"; the replacement must give the same result in linear time.
    def old(text: str) -> str:
        return re.sub(r"/\*.*?\*/|--[^\n]*", " ", text, flags=re.S)

    rng = random.Random(20261102)
    for _ in range(5000):
        text = "".join(rng.choice("/*-\nab ") for _ in range(rng.randint(0, 24)))
        assert _strip_sql_comments(text) == old(text), repr(text)
    assert _strip_sql_comments("drop/**/table x") == "drop table x"
    start = time.perf_counter()
    _strip_sql_comments(" /*" * 40_000 + "-- x")
    assert time.perf_counter() - start < 2.0


# ----------------------------------------------------------------------
# Kernel: protected_roots
# ----------------------------------------------------------------------

def test_kernel_protected_roots(tmp_path, monkeypatch):
    guarded = tmp_path / "guarded"
    guarded.mkdir()
    # A blank entry must not protect the working directory.
    monkeypatch.chdir(tmp_path)
    kernel = GovernanceKernel(
        manifest_path=REPO_ROOT / MANIFEST_REL,
        ledger_path=tmp_path / "ledger" / "events.jsonl",
        halt_file=tmp_path / ".halt",
        protected_roots=[guarded, ""],
    )

    def tier(target: str) -> PolicyTier:
        return kernel.evaluate_risk("write_file", {"target_path": target})

    assert tier(str(guarded)) == PolicyTier.PROHIBITED
    assert tier(str(guarded / "a" / "b.txt")) == PolicyTier.PROHIBITED
    assert tier(str(tmp_path / "guarded-sibling" / "x.txt")) == PolicyTier.ELEVATED
    assert tier(str(tmp_path / "other.txt")) == PolicyTier.ELEVATED
    monkeypatch.chdir(guarded)
    assert tier("relative.txt") == PolicyTier.PROHIBITED


def test_kernel_protected_roots_expand_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    kernel = GovernanceKernel(
        manifest_path=REPO_ROOT / MANIFEST_REL,
        ledger_path=tmp_path / "ledger" / "events.jsonl",
        halt_file=tmp_path / ".halt",
        protected_roots=["~/.agl"],
    )
    assert kernel.evaluate_risk("write_file", {"target_path": str(tmp_path / ".agl" / "x")}) == PolicyTier.PROHIBITED
    assert kernel.evaluate_risk("write_file", {"target_path": "~/.agl/plugin-data/x"}) == PolicyTier.PROHIBITED
    assert kernel.evaluate_risk("write_file", {"target_path": "~/other/x"}) == PolicyTier.ELEVATED


# ----------------------------------------------------------------------
# Entry points (separate processes, as the hosts run them)
# ----------------------------------------------------------------------

def test_shim_end_to_end(tmp_path):
    project, data = tmp_path / "project", tmp_path / "data"
    project.mkdir()
    proc = run_shim(SHIM, "PreToolUse", snake(project, "Bash", {"command": "rm -rf /"}), data)
    assert proc.returncode == 2
    assert json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
    proc = run_shim(SHIM, "SessionStart", snake(project, "", {}, event="SessionStart"), data)
    assert proc.returncode == 0, proc.stderr
    assert "Permanent Active Directives" in json.loads(proc.stdout)["additionalContext"]


def _copy_plugin(dest: Path) -> Path:
    shutil.copytree(
        REPO_ROOT / "src" / "autonomous_governance",
        dest / "src" / "autonomous_governance",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    (dest / "hooks").mkdir()
    shutil.copyfile(SHIM, dest / "hooks" / SHIM.name)
    for rel in [*CHARTER_NAMES, MANIFEST_REL]:
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / rel, dest / rel)
    return dest


def assert_copilot_fail_closed(proc: subprocess.CompletedProcess, needle: str) -> None:
    """Copilot CLI protocol: exit 0 and one JSON deny on stdout."""
    assert proc.returncode == 0, proc.stderr
    output = json.loads(proc.stdout)
    assert output["permissionDecision"] == output["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "failed closed" in output["permissionDecisionReason"]
    assert needle.encode() in proc.stderr


def test_tampered_charter_fails_closed(tmp_path):
    plugin = _copy_plugin(tmp_path / "plugin")
    project, data = tmp_path / "project", tmp_path / "data"
    project.mkdir()
    shim = plugin / "hooks" / SHIM.name
    read = camel(project, "view", {"path": "README.md"})
    assert run_shim(shim, "preToolUse", read, data).returncode == 0

    doc = plugin / CHARTER_NAMES[0]
    doc.write_bytes(doc.read_bytes() + b"\nInjected instruction.\n")
    assert_copilot_fail_closed(run_shim(shim, "preToolUse", read, data), "failed closed")
    for event_name, payload in (
        ("PreToolUse", snake(project, "Read", {"file_path": "README.md"})),
        ("SessionStart", snake(project, "", {}, "SessionStart")),
        ("sessionStart", {"cwd": str(project)}),
    ):
        proc = run_shim(shim, event_name, payload, data)
        assert proc.returncode == 2
        assert proc.stdout == b""
        assert b"failed closed" in proc.stderr


def test_shim_without_kernel_fails_closed(tmp_path):
    plugin = _copy_plugin(tmp_path / "plugin")
    # The shim puts the plugin's src first on sys.path, so this module is the one it imports.
    (plugin / "src" / "autonomous_governance" / "hooks.py").write_text(
        "raise ImportError('simulated broken install')\n", encoding="utf-8"
    )
    project, data = tmp_path / "project", tmp_path / "data"
    project.mkdir()
    shim = plugin / "hooks" / SHIM.name
    read = camel(project, "view", {"path": "README.md"})
    assert_copilot_fail_closed(run_shim(shim, "preToolUse", read, data), "cannot load the kernel")
    proc = run_shim(shim, "PreToolUse", snake(project, "Read", {"file_path": "README.md"}), data)
    assert proc.returncode == 2 and proc.stdout == b""
    assert b"cannot load the kernel" in proc.stderr


def test_concurrent_hooks_keep_one_chain(tmp_path):
    project, data = tmp_path / "project", tmp_path / "data"
    project.mkdir()
    payload = json.dumps(snake(project, "Bash", {"command": "ls"})).encode("utf-8")
    procs = [
        subprocess.Popen(
            [sys.executable, str(SHIM), "PreToolUse"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=subprocess_env(data),
        )
        for _ in range(6)
    ]
    results = [p.communicate(payload, timeout=120) for p in procs]
    assert all(p.returncode == 0 for p in procs), [r[1] for r in results]
    events = ledger_events(data)
    assert sum(e["event_type"] == "HOOK_DECISION" for e in events) == 6
    report = audit(data / ".ledger" / "events.jsonl", tmp_path)
    assert report["valid"] and report["broken_links"] == 0


def _copilot_powershell(event_name: str, plugin_root: Path = REPO_ROOT) -> str:
    """The powershell command from hooks/copilot-hooks.json, as Copilot CLI would run it."""
    entry = "sessionStart" if event_name.lower() == "sessionstart" else hooks.COPILOT_PRE_TOOL_USE
    command = _json("hooks/copilot-hooks.json")["hooks"][entry][0]["powershell"]
    command = command.replace(f'agl-hook.ps1" {entry};', f'agl-hook.ps1" {event_name};')
    return command.replace("${PLUGIN_ROOT}", plugin_root.as_posix())


def _powershell() -> str | None:
    return (shutil.which("pwsh") or shutil.which("powershell")) if os.name == "nt" else None


def _wrapper_command(script: str, event_name: str) -> list[str] | None:
    path = HOOKS_DIR / script
    if script.endswith(".ps1"):
        shell = _powershell()
        if shell is None:
            return None
        # Copilot CLI spawns pwsh -nop -nol -c <command>.
        return [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                "-Command", _copilot_powershell(event_name)]
    # Windows' bash.exe is usually WSL, which cannot see this interpreter's paths.
    shell = shutil.which("bash") if os.name != "nt" else None
    return None if shell is None else [shell, str(path), event_name]


@pytest.mark.parametrize("script", ["agl-hook.sh", "agl-hook.ps1"])
def test_wrapper_scripts(tmp_path, script):
    if _wrapper_command(script, "PreToolUse") is None:
        pytest.skip(f"no shell for {script} on this platform")
    project, data = tmp_path / "project", tmp_path / "data"
    project.mkdir()
    env = subprocess_env(data, AGL_PYTHON=sys.executable)

    def run(event_name, payload, run_env):
        return subprocess.run(
            _wrapper_command(script, event_name), input=json.dumps(payload).encode("utf-8"),
            capture_output=True, env=run_env, timeout=120,
        )

    proc = run("PreToolUse", snake(project, "Bash", {"command": "rm -rf /"}), env)
    assert proc.returncode == 2
    assert json.loads(proc.stdout)["permissionDecision"] == "deny"
    proc = run("PreToolUse", snake(project, "Read", {"file_path": "caf\u00e9.md"}), env)
    assert proc.returncode == 0 and json.loads(proc.stdout) == {}
    proc = run("preToolUse", camel(project, "bash", {"command": "rm -rf /"}), env)
    assert proc.returncode == 0 and json.loads(proc.stdout)["permissionDecision"] == "deny"
    proc = run("preToolUse", camel(project, "view", {"path": "README.md"}), env)
    assert proc.returncode == 0 and json.loads(proc.stdout) == {}

    no_python = {**env, "AGL_PYTHON": "", "PATH": str(tmp_path / "empty")}
    proc = run("PreToolUse", snake(project, "Read", {"file_path": "x"}), no_python)
    assert proc.returncode == 2 and proc.stdout == b""
    assert b"no Python 3.10+ interpreter" in proc.stderr
    proc = run("sessionStart", {"cwd": str(project)}, no_python)
    assert proc.returncode == 2 and proc.stdout == b""
    assert_copilot_fail_closed(
        run("preToolUse", camel(project, "view", {"path": "x"}), no_python), "no Python 3.10+ interpreter"
    )


@pytest.mark.parametrize("case", ["restricted_policy", "missing_script"])
def test_copilot_powershell_command_fails_closed(tmp_path, case):
    # Copilot CLI lets the tool run when the hook prints nothing and exits 0, which is
    # what "exit $LASTEXITCODE" alone does when PowerShell cannot run the script.
    shell = _powershell()
    if shell is None:
        pytest.skip("Copilot CLI runs the powershell hook command only on Windows")
    project, data = tmp_path / "project", tmp_path / "data"
    project.mkdir()
    root = tmp_path / "missing-plugin" if case == "missing_script" else REPO_ROOT
    policy = ["-ExecutionPolicy", "Restricted"] if case == "restricted_policy" else []

    def run(event_name, payload):
        return subprocess.run(
            [shell, "-NoProfile", "-NonInteractive", *policy, "-Command", _copilot_powershell(event_name, root)],
            input=json.dumps(payload).encode("utf-8"), capture_output=True,
            env=subprocess_env(data, AGL_PYTHON=sys.executable), timeout=120,
        )

    proc = run("preToolUse", camel(project, "view", {"path": "README.md"}))
    assert proc.returncode == 0, proc.stderr
    output = json.loads(proc.stdout.decode("utf-8").strip().splitlines()[-1])
    assert output["permissionDecision"] == "deny"
    assert output["permissionDecisionReason"].startswith(hooks.FAIL_CLOSED_PREFIX)
    proc = run("sessionStart", {"cwd": str(project)})
    assert proc.returncode == 2 and proc.stdout.strip() == b""


# ----------------------------------------------------------------------
# Plugin manifests
# ----------------------------------------------------------------------

def _json(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))


def _version() -> str:
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    return re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE).group(1)


@pytest.mark.parametrize("manifest,hooks_file", [
    (".plugin/plugin.json", "hooks/copilot-hooks.json"),
    (".github/plugin/plugin.json", "hooks/copilot-hooks.json"),
    (".claude-plugin/plugin.json", "hooks/claude-hooks.json"),
])
def test_plugin_manifests(manifest, hooks_file):
    data = _json(manifest)
    assert data["name"] == "autonomous-governance-laws"
    assert data["version"] == _version() == autonomous_governance.__version__
    assert data["license"] == "Apache-2.0"
    assert data["hooks"] == f"./{hooks_file}"
    assert (REPO_ROOT / hooks_file).is_file()
    assert (REPO_ROOT / data["skills"] / "agl-charter" / "SKILL.md").is_file()


def test_copilot_manifests_match():
    # Copilot CLI 0.0.4xx reads .github/plugin/plugin.json; current releases read .plugin/ first.
    assert _json(".github/plugin/plugin.json") == _json(".plugin/plugin.json")
    # A root plugin.json would be read first, and newer hosts treat it as an Agent Plugins manifest.
    assert not (REPO_ROOT / "plugin.json").exists()


def test_no_default_hooks_file():
    # Hosts also auto-load hooks/hooks.json; one would register every hook twice.
    assert not (HOOKS_DIR / "hooks.json").exists()


def test_marketplace_lists_the_plugin():
    market = _json(".claude-plugin/marketplace.json")
    entry = next(p for p in market["plugins"] if p["name"] == "autonomous-governance-laws")
    assert entry["source"] == "./"
    assert entry["version"] == _version()


def _assert_command(command: str, root_var: str, event: str) -> None:
    match = re.search(r"\$\{" + root_var + r"\}/(hooks/[\w.-]+)", command)
    assert match, command
    assert (REPO_ROOT / match.group(1)).is_file(), command
    assert command.rstrip().endswith(f" {event}"), command


def test_copilot_hooks_config():
    config = _json("hooks/copilot-hooks.json")
    assert config["version"] == 1
    # Copilot CLI 0.0.4xx silently drops PascalCase events and keys other than bash/powershell.
    assert set(config["hooks"]) == {"sessionStart", hooks.COPILOT_PRE_TOOL_USE}
    for event, entries in config["hooks"].items():
        assert len(entries) == 1
        entry = entries[0]
        # Both keys: with only "bash", Windows hosts run bash.exe, which is often WSL.
        assert set(entry) == {"type", "bash", "powershell", "timeoutSec"}
        assert entry["type"] == "command"
        assert 0 < entry["timeoutSec"] <= 60
        _assert_command(entry["bash"], "PLUGIN_ROOT", event)
        command = entry["powershell"]
        script = re.match(r'\$agl = \$null; try \{ & ("\$\{PLUGIN_ROOT\}/hooks/[\w.-]+" \w+); \$agl = \$LASTEXITCODE \}', command)
        assert script, command
        _assert_command(script.group(1), "PLUGIN_ROOT", event)
        # pwsh -c drops a script's exit status unless the command passes it on, and a script
        # PowerShell cannot load (execution policy, missing file) leaves $LASTEXITCODE unset.
        assert command.endswith("; exit $agl")
        fallback = re.search(r"if \(\$null -eq \$agl\) \{ (.*?) \}; exit \$agl$", command).group(1)
        if event == "sessionStart":
            assert fallback == "exit 2"
        else:
            deny = re.fullmatch(r"'(\{.*\})'; exit 0", fallback)
            assert deny, fallback
            output = json.loads(deny.group(1))
            assert output["permissionDecision"] == "deny"
            assert output["permissionDecisionReason"].startswith(hooks.FAIL_CLOSED_PREFIX)


def test_claude_hooks_config():
    config = _json("hooks/claude-hooks.json")["hooks"]
    assert set(config) == {"SessionStart", "PreToolUse"}
    assert config["PreToolUse"][0]["matcher"] == "*"
    for event, groups in config.items():
        for group in groups:
            for hook in group["hooks"]:
                assert hook["type"] == "command"
                assert 0 < hook["timeout"] <= 60
                _assert_command(hook["command"], "CLAUDE_PLUGIN_ROOT", event)
                # Without it, Claude Code runs the tool when the hook fails or times out.
                if event == "PreToolUse":
                    assert hook["onFailure"] == "block"


def test_skill_frontmatter():
    text = (REPO_ROOT / "skills" / "agl-charter" / "SKILL.md").read_text(encoding="utf-8")
    front = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert front, "SKILL.md needs YAML frontmatter"
    fields = dict(line.split(":", 1) for line in front.group(1).splitlines())
    assert fields["name"].strip() == "agl-charter"
    assert len(fields["description"].strip()) > 40

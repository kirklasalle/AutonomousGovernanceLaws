"""Plugin entry point for the AGL governance hook (see autonomous_governance.hooks).

Usage: python hooks/agl_hook.py <preToolUse|sessionStart|PreToolUse|SessionStart>
(host event JSON on stdin)

Fails closed: if the bundled kernel cannot be loaded, block the tool call instead of
running it ungoverned. Copilot CLI (camelCase ``preToolUse``) only blocks on a JSON
deny with exit status 0; every other host blocks on exit status 2.
"""

import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
EXIT_BLOCK = 2


def _fail_closed(message: str) -> int:
    sys.stderr.write(message + "\n")
    if sys.argv[1:2] == ["preToolUse"]:
        decision = {"permissionDecision": "deny", "permissionDecisionReason": message}
        sys.stdout.write(json.dumps({**decision, "hookSpecificOutput": {"hookEventName": "PreToolUse", **decision}}) + "\n")
        return 0
    return EXIT_BLOCK


def run() -> int:
    sys.path.insert(0, str(PLUGIN_ROOT / "src"))
    try:
        from autonomous_governance.hooks import main
    except Exception as exc:  # noqa: BLE001 - any load failure must block
        return _fail_closed(f"AGL governance hook failed closed: cannot load the kernel ({exc})")
    return main(sys.argv[1:], plugin_root=PLUGIN_ROOT)


if __name__ == "__main__":
    sys.exit(run())

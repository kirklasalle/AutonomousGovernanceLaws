#!/usr/bin/env bash
# Runs the AGL governance hook with the first Python 3.10+ interpreter found.
# Usage: agl-hook.sh <preToolUse|sessionStart|PreToolUse|SessionStart>  (host event JSON on stdin)
# Fails closed when no interpreter is found or the hook crashes: Copilot CLI (camelCase
# preToolUse) only blocks on a JSON deny with exit 0; every other host blocks on exit 2.
# Set AGL_PYTHON to choose the interpreter.
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
hook_event="${1:-}"

fail_closed() {
  echo "$1" >&2
  [ "$hook_event" = "preToolUse" ] || exit 2
  # Messages are fixed ASCII text without quotes or backslashes, so they are valid JSON strings.
  printf '{"permissionDecision":"deny","permissionDecisionReason":"%s","hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$1" "$1"
  exit 0
}

for py in "${AGL_PYTHON:-}" python3 python py; do
  [ -n "$py" ] || continue
  if "$py" -c 'import sys; sys.exit(sys.version_info < (3, 10))' </dev/null >/dev/null 2>&1; then
    "$py" "$here/agl_hook.py" "$@"
    status=$?
    [ "$status" -eq 0 ] && exit 0
    [ "$hook_event" = "preToolUse" ] || exit 2
    fail_closed "AGL governance hook failed closed: the hook exited with status $status."
  fi
done
fail_closed "AGL governance hook failed closed: no Python 3.10+ interpreter found (set AGL_PYTHON)."

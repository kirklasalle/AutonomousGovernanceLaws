# Runs the AGL governance hook with the first Python 3.10+ interpreter found.
# Usage: agl-hook.ps1 <preToolUse|sessionStart|PreToolUse|SessionStart>  (host event JSON on stdin)
# Fails closed when no interpreter is found or the hook crashes: Copilot CLI (camelCase
# preToolUse) only blocks on a JSON deny with exit 0; every other host blocks on exit 2.
# Set AGL_PYTHON to choose the interpreter.
$hook = Join-Path $PSScriptRoot 'agl_hook.py'
$hookEvent = if ($args.Count -gt 0) { [string]$args[0] } else { '' }

function Stop-FailClosed([string]$Message) {
    [Console]::Error.WriteLine($Message)
    if ($hookEvent -cne 'preToolUse') { exit 2 }
    $output = [ordered]@{
        permissionDecision = 'deny'; permissionDecisionReason = $Message
        hookSpecificOutput = [ordered]@{ hookEventName = 'PreToolUse'; permissionDecision = 'deny'; permissionDecisionReason = $Message }
    }
    [Console]::Out.WriteLine(($output | ConvertTo-Json -Compress -Depth 3))
    exit 0
}

foreach ($py in @($env:AGL_PYTHON, 'python', 'py', 'python3')) {
    if (-not $py -or -not (Get-Command $py -ErrorAction SilentlyContinue)) { continue }
    & $py -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { continue }
    # The interpreter inherits this script's stdin, so the event reaches it unchanged.
    & $py $hook @args
    $status = $LASTEXITCODE
    if ($status -eq 0) { exit 0 }
    if ($hookEvent -cne 'preToolUse') { exit 2 }
    Stop-FailClosed "AGL governance hook failed closed: the hook exited with status $status."
}
Stop-FailClosed 'AGL governance hook failed closed: no Python 3.10+ interpreter found (set AGL_PYTHON).'

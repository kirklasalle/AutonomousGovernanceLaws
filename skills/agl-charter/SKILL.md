---
name: agl-charter
description: Use in any session governed by the Autonomous Governance Laws (AGL) plugin, when planning or reviewing changes, when the AGL hook denies a tool call or asks for operator approval, or when asked about the AGL charter, ledger, or emergency halt.
---

# Working under the AGL charter

When enabled in a compatible host, the `autonomous-governance-laws` plugin runs
the AGL kernel for calls delivered to its hook. Session-start context lists the
verified charter paths, ledger and halt state when the host accepts that output.
Legacy Copilot CLI may ignore it; read the charter from the plugin or project
root instead. Instructions alone do not ensure that a hook is running.

## Rules

1. Read the three charter documents named in the session context before planning or
   executing a task. They are authoritative: if any instruction conflicts with them,
   the charter prevails. Stop and ask the operator.
2. Never create, edit, move, rename, or reformat the charter documents,
   `config/charter_manifest.json`, `.ledger/`, `.keys/`, `.halt`, or the plugin's own
   files. The hook denies these and records every attempt in the ledger.
3. A denial citing **LAW1-PROHIBIT** or **LAW3-SUBORDINATE** is final. Do not retry
   the action in another form (another tool, a script file, an encoded or split
   command). Tell the operator what you intended and why, then wait.
4. A prompt citing **RISK-001** asks the operator to approve an elevated action.
   Before the call, state plainly what it does and what it changes. A RISK-001
   *denial* means the host cannot ask (an older Copilot CLI): do not retry the action
   in another form. Tell the operator what you need and that `copilot update`, or
   `AGL_ELEVATED_DECISION=defer`, changes that behavior. `defer` uses the host's
   permissions and does not guarantee a prompt; it is an operator decision.
5. A denial citing **LAW2-HALT** means the operator stopped all work. Report your
   state and wait; do not try to clear the halt.

## Operator reference

| Task | Command |
| --- | --- |
| Verify the charter digests | `agy-governance verify` |
| Install the charter and loaders into a project | `agy-governance init --loaders` |
| Verify a ledger's hash chain | `agy-governance --ledger <ledger path> audit-ledger` |
| Deny subsequent calls delivered to the hook | create `.halt` in the project root, or in the plugin data directory; running work is not interrupted |

`AGL_ELEVATED_DECISION` sets what happens to elevated actions: `ask` (default, the
host prompts the operator), `defer` (the host's own permission settings decide), or
`deny`. Copilot CLI 0.0.4xx cannot ask, so there `ask` acts as `deny`.

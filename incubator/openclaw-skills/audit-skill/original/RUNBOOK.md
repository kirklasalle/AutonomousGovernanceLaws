# audit-skill RUNBOOK

Purpose
- Provide an operational summary, usage, and maintenance steps for the audit-skill (system-wide audits and nightly forensic scans).

Location
- Skill root: G:\Users\kirkl\.openclaw\workspace\skills\audit-skill
- Scripts: scripts/quick_scan.ps1, scripts/forensic_scan.ps1, scripts/notify_stub.ps1
- Logs: G:\Users\kirkl\.openclaw\workspace\logs\audit-skill\
- Memory entries: memory/YYYY-MM-DD.md (daily summaries appended)

What it does
- quick_scan: Lightweight non-destructive snapshot (systeminfo, disk, memory, netstat). Use for frequent checks.
- forensic_scan: Extended read-only audit including Event Viewer exports (last 72h), OpenClaw gateway log copy, netstat, scheduled tasks, installed programs. Intended to run nightly and produce a timestamped folder under logs/.
- notify_stub: Placeholder for notifier integration (SMTP/OpenClaw/webhook). Not active by default.

Scheduled Task
- Name: OpenClaw-Audit-Forensic
- Schedule: Daily at 03:00 AM local (America/New_York)
- Action: powershell -NoProfile -ExecutionPolicy Bypass -File "G:\Users\kirkl\.openclaw\workspace\skills\audit-skill\scripts\forensic_scan.ps1"
- Current Logon Mode: Interactive only (does not store credentials). To run while logged off, change principal to store credentials (see "Change principal" below).

Files produced
- forensic_YYYY-MM-DD_HH-mm/ (folder)
  - Application.txt
  - System.txt
  - netstat.txt
  - scheduled_tasks.txt
  - installed_programs.txt
  - summary.txt

How to run manually
- Quick scan: powershell -NoProfile -ExecutionPolicy Bypass -File "...\quick_scan.ps1"
- Forensic scan: powershell -NoProfile -ExecutionPolicy Bypass -File "...\forensic_scan.ps1"

Permissions & Safety
- Scripts perform read-only operations and copy logs into workspace/logs/audit-skill/.
- No network exfiltration or external transmission occurs unless notifier is configured and enabled.
- If you elect to run the scheduled task when not logged on, creating the task with stored credentials will be required. Provide credentials only if you accept the security tradeoff.

Retention & Rotation (Recommended)
- Keep forensic logs for 30 days by default. Add a retention script (prune_logs.ps1) to delete folders older than N days. Example cron: weekly.

Notifier (Optional)
- Options: SMTP, webhook, OpenClaw message tool. notify_stub.ps1 is a placeholder. Implementers must provide credentials/URL and update the script to call the desired endpoint.

Change principal (to run whether user is logged on)
- Current behavior: runs only when user is logged on (Interactive only). To change:
  1. Decide whether to store credentials. If yes, create the task with /RL HIGHEST and provide credentials
     or use Register-ScheduledTask with a SecureString credential object in PowerShell.
  2. Example schtasks creation (will prompt for password):
     schtasks /Create /TN "OpenClaw-Audit-Forensic" /TR "powershell -NoProfile -ExecutionPolicy Bypass -File \"G:\\Users\\kirkl\\.openclaw\\workspace\\skills\\audit-skill\\scripts\\forensic_scan.ps1\"" /SC DAILY /ST 03:00 /RU "kirkl" /RL HIGHEST /F

Extensions & To-do
- Implement notifier (SMTP/webhook/OpenClaw) with secure credential storage.
- Add prune_logs.ps1 and schedule weekly cleanup.
- Add quick_scan scheduled task for more frequent heartbeats and append compact summaries to memory/YYYY-MM-DD.md.
- Add retention policy enforcement and log rotation.

Contacts
- Owner: kirkl (Run As User for scheduled task)
- Agent: Nexus (skills/audit-skill)

Change log
- 2026-02-19 16:25 - Created skill scaffold and scheduled task (Interactive only). Added forensic_scan and quick_scan scripts.
- 2026-02-19 16:29 - Patched forensic_scan to use Get-WinEvent and added notify_stub.


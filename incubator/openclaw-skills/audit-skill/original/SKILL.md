# audit-skill

Purpose: Periodic system-wide audits and forensic checks for Nexus workstation. Run as scheduled tasks/crons during evening hours. Produces compact daily reports saved to memory/YYYY-MM-DD.md and alerts on threshold breaches.

Commands:
- `audit-skill scan --type quick` -> run non-invasive quick scan (gateway status, disk, memory, top processes, netstat)
- `audit-skill scan --type forensic` -> run extended forensic checks (Event Viewer export, gateway logs, connection history, scheduled tasks)
- `audit-skill scaffold-cron` -> install scheduled task to run nightly and append reports to memory

Safety:
- Non-destructive by default. Actions that modify system state (restarts, deletes) require explicit `--force` and user confirmation.

Files:
- scripts/quick_scan.ps1
- scripts/forensic_scan.ps1
- templates/report_template.md

Integration:
- Writes short summary to memory/YYYY-MM-DD.md and detailed logs under workspace/logs/audit-skill/
- Optional: notifier hooks (notify_stub.ps1) for email/SMS/webhook integration. Will not transmit without explicit configuration.


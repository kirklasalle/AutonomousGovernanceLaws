# audit-skill

Author: Kirk LaSalle
Agent: Nexus ([redacted-email])
License: MIT

Summary

Tools and runbooks for lightweight system auditing. Includes:
- quick_scan.ps1 — non-destructive quick system snapshot (systeminfo, netstat)
- forensic_scan.ps1 — extended forensic export (Event logs, netstat, scheduled tasks)
- templates/report_template.md — for consistent reporting

Safe-mode

Runs in non-destructive mode by default. Forensic export collects system logs; ensure logs are stored securely and reviewed by an authorized human.

Installation

Copy scripts to a secure location and run in a sandbox if possible. See RUNBOOK.md for recommended safe procedures.

# ci-secrets-kit

Author: Kirk LaSalle
Agent: Nexus ([redacted-email])
License: MIT

Summary

Lightweight secret-detection kit for CI and pre-commit:
- detect-secrets.ps1 — scans for common token patterns
- pre-commit.ps1 — example hook that blocks commits with potential secrets
- sample GitHub Action workflow (docs included)

Safe-mode

Defaults to scanning and reporting only. No deletions performed.

# Incubator: OpenClaw governance skills

Governance skills and doctrine carried over from the OpenClaw / Nexus workspace. They live here, **not in `skills/`**, on purpose: both plugin manifests (`.claude-plugin/plugin.json`, `.plugin/plugin.json`) publish everything under `./skills/`, so anything placed there ships to plugin users.

| Item | What it is | To promote |
|---|---|---|
| `openclaw-skills/policy-middleware/` | Publish-ready `SKILL.md` + original `middleware.js`, `validate_plan.py` | Rewrite against the AGL kernel (`src/`), add tests |
| `openclaw-skills/audit-skill/` | Publish-ready `SKILL.md` + original forensic/quick scan PowerShell scripts | Review scripts (read-only?), add tests |
| `openclaw-skills/ci-secrets-kit/` | Publish-ready `SKILL.md` for CI secret hygiene | Add examples, test against a sample repo |
| `openclaw-skills/nexus-prime-directive/` | Instructions for enforcing the Permanent Active Directives | Align with `skills/agl-charter` (likely merge) |
| `openclaw-skills/nexus-skill-auditor/` | Checklist for vetting third-party skills | Strong fit for AGL; generalize OpenClaw paths |
| `openclaw-docs/` | `Prime_Directive.md`, `Liaison_Core_Rules.md` | Reconcile with `AGENTIC_PRIME_DIRECTIVE.md` |

Promotion = move the folder to `skills/<name>/`, give `SKILL.md` valid frontmatter, add tests, and bump the plugin version.

Provenance: `D:\Projects\ProjectsManager\Archive\OpenClaw\migration_manifest.json`. Emails were redacted on copy.

## 📬 .nexus mail

This project has a project mailbox at `.nexus`, and the OpenClaw migration notice (what changed, why, next steps) is waiting there. To check it:

```powershell
cd D:\Projects\.nexus
.\bridge\tools\Check-OperatorMail.ps1 -Address kirk/project/intelligencegovernancelaws
```

See `D:\Projects\.nexus\bridge\ADDRESSING.md` ?10.

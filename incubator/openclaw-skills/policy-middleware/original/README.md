Policy middleware (skeleton)

Purpose:
- Provide a single place to validate plans that will cause external side-effects (email, git push, cloud create, openclaw notify).
- Enforce that plans requiring side-effects include an approval object before execution.

How to use:
- require('./skills/policy-middleware/middleware').validatePlan(plan)
- Example plan: { action: 'send_email', details: {to:'x'}, approval: {by:'kirk', ts:'2026-03-21T10:00:00Z' }}

Next steps:
- Wire this into orchestrator flow and into skills that perform sends/pushes.
- Add a persistent approval queue (file or DB) and UI hook to allow human approvals.
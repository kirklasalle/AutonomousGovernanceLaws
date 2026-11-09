// Policy middleware skeleton for Nexus
// Purpose: Validate and approve outbound side-effect actions before execution.
// Usage: Import and call validatePlan(plan) before executing actions that affect external state.

const fs = require('fs');
const path = require('path');

// Simple policy check: ensure actions requiring write permissions include an approval token
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function queuePlan(plan) {
  const approvalsDir = path.join(__dirname, '..', 'approvals');
  ensureDir(approvalsDir);
  const id = crypto.randomUUID ? crypto.randomUUID() : crypto.randomBytes(16).toString('hex');
  const fn = path.join(approvalsDir, `pending_${id}.json`);
  fs.writeFileSync(fn, JSON.stringify({ plan: plan, status: 'pending', id: id }, null, 2), { encoding: 'utf8' });
  return fn;
}

function validatePlan(plan) {
  // plan: { action: 'send_email'|'git_push'|'openclaw_notify'|'other', details: {...}, approval: null|{by:'user',ts:'...'} }
  const result = { allowed: false, reason: null, queued: null };
  if (!plan || !plan.action) {
    result.reason = 'Malformed plan';
    return result;
  }

  // Actions that require approval
  const requireApproval = new Set(['send_email','git_push','cloud_create','openclaw_notify']);
  if (requireApproval.has(plan.action)) {
    if (plan.approval && plan.approval.by) {
      result.allowed = true;
      return result;
    } else {
      result.reason = 'Approval required';
      const q = queuePlan(plan);
      result.queued = q;
      return result;
    }
  }

  // Default: allow read-only or safe actions
  result.allowed = true;
  return result;
}

module.exports = { validatePlan, queuePlan };

module.exports = { validatePlan };

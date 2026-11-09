# Simple Python policy validator for Nexus (mirror of middleware.js validatePlan)
import json

REQUIRES_APPROVAL = {'send_email','git_push','cloud_create','openclaw_notify'}

import uuid
import os

APPROVALS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'approvals')
APPROVALS_DIR = os.path.normpath(APPROVALS_DIR)

def ensure_dir():
    os.makedirs(APPROVALS_DIR, exist_ok=True)


def queue_plan(plan: dict):
    """Write the plan to approvals/pending/<uuid>.json and return path."""
    ensure_dir()
    nid = str(uuid.uuid4())
    fn = os.path.join(APPROVALS_DIR, f'pending_{nid}.json')
    with open(fn, 'w', encoding='utf-8') as f:
        json.dump({'plan': plan, 'status': 'pending', 'id': nid}, f, indent=2)
    return fn


def validate_plan(plan: dict):
    res = {'allowed': False, 'reason': None, 'queued': None}
    if not plan or 'action' not in plan:
        res['reason'] = 'Malformed plan'
        return res
    if plan['action'] in REQUIRES_APPROVAL:
        if plan.get('approval') and plan['approval'].get('by'):
            res['allowed'] = True
            return res
        else:
            # Instead of failing, queue the plan and return queued path
            qpath = queue_plan(plan)
            res['reason'] = 'Approval required'
            res['queued'] = qpath
            return res
    res['allowed'] = True
    return res

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'usage: validate_plan.py <plan.json>'}))
        sys.exit(1)
    p = json.loads(open(sys.argv[1],'r',encoding='utf-8').read())
    print(json.dumps(validate_plan(p), indent=2))

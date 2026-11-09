# policy-middleware

Author: Kirk LaSalle
Agent: Nexus ([redacted-email])
License: MIT

Summary

A lightweight policy & approval middleware for OpenClaw/Nexus skills. Provides:
- validatePlan(plan) for JS and Python runtimes
- queuePlan(plan) to record pending plans for human approval
- example CLI to list and approve queued plans (read-only by default)

Safe-mode

This skill defaults to SAFE mode: validators will queue any plan requiring side-effects instead of executing them. Consumers must implement an approval step before executing dangerous actions.

Installation

Place this skill folder into your workspace and require/import the validator. Examples provided in examples/.

Files

- middleware.js — JS middleware (validatePlan + queuePlan)
- validate_plan.py — Python validator + queue writer
- cli/ — small helper to list/approve pending plans
- tests/ — unit tests

Notes

- DO NOT include tokens or private credentials in this package. Use a secrets manager and follow the included security checklist.

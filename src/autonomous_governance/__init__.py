"""
Autonomous Governance Laws — Constitutional Runtime Framework

Implements Kirk LaSalle's 10 Laws for Intelligence Systems as
deterministic runtime enforcement middleware for autonomous AI agents.

Usage:
    from autonomous_governance import GovernanceKernel, PolicyTier

    kernel = GovernanceKernel(
        manifest_path="config/charter_manifest.json",
        ledger_path=".ledger/events.jsonl",
    )

    # Every tool call passes through the governance interceptor
    result = kernel.intercept_and_execute(
        tool_name="write_file",
        payload={"target_path": "/app/output.txt", "content": "..."},
        executor_func=my_write_function,
    )
"""

from autonomous_governance.kernel import (
    GovernanceKernel,
    GovernanceViolation,
    ApprovalRequired,
    PolicyTier,
)

__version__ = "0.1.0"
__author__ = "Kirk LaSalle"
__all__ = [
    "GovernanceKernel",
    "GovernanceViolation",
    "ApprovalRequired",
    "PolicyTier",
]

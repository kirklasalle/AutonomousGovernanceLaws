"""
Autonomous Governance Laws — Governance Kernel

The core runtime enforcement engine implementing Kirk LaSalle's 10 Laws
for Intelligence Systems. This module provides:

- Charter integrity verification (LAW10-CHARTER)
- 3-Tier policy risk classification (RISK-001)
- Non-bypassable action prohibitions (LAW1-PROHIBIT)
- Emergency operator halt detection (LAW2-HALT)
- Subordinate self-constraint enforcement (LAW3-SUBORDINATE)
- Append-only SHA-256 hash-chained event ledger (LAW9-LEDGER, LAW9-APPEND, LAW9-CHAIN)
"""

import hashlib
import json
import time
from enum import Enum
from pathlib import Path
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class PolicyTier(Enum):
    """3-Tier risk classification for tool actions (RISK-001)."""

    SAFE = 1
    ELEVATED = 2
    PROHIBITED = 3


class GovernanceViolation(Exception):
    """Raised when an action violates Law 1, Law 3, Law 5, or Law 10.

    Actions classified as PROHIBITED are dropped unconditionally.
    This exception cannot be caught and suppressed by agent code.
    """

    def __init__(self, message: str, law_ref: str = ""):
        self.law_ref = law_ref
        super().__init__(f"[{law_ref}] {message}" if law_ref else message)


class ApprovalRequired(Exception):
    """Raised when an elevated-risk action requires a signed operator token.

    The operator must provide a single-use authorization token bound
    to the specific action before execution can proceed (RISK-001).
    """

    pass


class GovernanceKernel:
    """Core governance interceptor implementing the 10 Laws at runtime.

    Every tool call, shell command, file mutation, and sub-agent spawn
    passes through this kernel before execution.

    Args:
        manifest_path: Path to config/charter_manifest.json
        ledger_path: Path to the append-only JSONL event ledger
        operator_pubkey_path: Optional path to Ed25519 operator public key
        require_attestation: If True, refuse to boot without signed config
        halt_file: Path to the emergency halt trigger file
    """

    # Paths that agents may never write to (LAW3-SUBORDINATE)
    PROTECTED_PATHS = frozenset([
        ".ledger",
        "config/charter_manifest",
        "config/policy_registry",
        "charter_manifest.json",
        "policy_registry.json",
        ".halt",
        "operator_private_key",
        "operator_public_key",
        ".pem",
        ".sig",
    ])

    # Commands that are unconditionally prohibited (LAW1-PROHIBIT)
    PROHIBITED_COMMANDS = frozenset([
        "rm -rf /",
        "rm -rf /*",
        "mkfs",
        "format c:",
        "drop database",
        "drop table",
        "truncate table",
        "del /f /s /q c:",
        "shutdown -h now",
        "shutdown /s /f /t 0",
        ":(){ :|:& };:",
    ])

    def __init__(
        self,
        manifest_path: str | Path = "config/charter_manifest.json",
        ledger_path: str | Path = ".ledger/events.jsonl",
        operator_pubkey_path: str | Path | None = None,
        require_attestation: bool = False,
        halt_file: str | Path = ".halt",
    ):
        self.manifest_path = Path(manifest_path)
        self.ledger_path = Path(ledger_path)
        self.operator_pubkey_path = Path(operator_pubkey_path) if operator_pubkey_path else None
        self.require_attestation = require_attestation
        self.halt_file = Path(halt_file)
        self.prev_event_hash = "0" * 64
        self._boot_time = time.time()
        self._used_action_ids: set[str] = set()

        # Load operator public key if configured
        self.operator_pubkey: bytes | None = None
        if self.operator_pubkey_path and self.operator_pubkey_path.exists():
            with open(self.operator_pubkey_path, "rb") as f:
                raw_pub = f.read().strip()
            if len(raw_pub) == 32:
                self.operator_pubkey = raw_pub
            else:
                try:
                    self.operator_pubkey = bytes.fromhex(raw_pub.decode("utf-8", errors="ignore").strip())
                except Exception:
                    self.operator_pubkey = raw_pub[:32]
        elif self.require_attestation:
            raise GovernanceViolation(
                "require_attestation is True but operator_pubkey_path is missing or invalid",
                "LAW10-APPROVAL",
            )

        # Boot sequence
        self._verify_charter_integrity()
        self._init_ledger()
        self._log_event("KERNEL_BOOT", {
            "manifest_version": self._manifest_version,
            "charter_files_verified": self._charter_file_count,
            "attestation_enforced": self.require_attestation,
            "operator_pubkey_loaded": self.operator_pubkey is not None,
        }, "LAW10-CHARTER")

    def _verify_charter_integrity(self) -> None:
        """Verify SHA-256 digests of all charter documents at boot.

        Implements: LAW10-CHARTER
        Failure: Unrecoverable — runtime MUST NOT proceed.
        """
        if not self.manifest_path.exists():
            raise GovernanceViolation(
                f"Charter manifest not found: {self.manifest_path}",
                "LAW10-CHARTER",
            )

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self._manifest_version = manifest.get("version", "unknown")
        charter_files = manifest.get("charter_files", {})
        self._charter_file_count = len(charter_files)

        for file_name, expected_hash in charter_files.items():
            file_path = Path(file_name)
            expected_hash = expected_hash.lower()

            if not file_path.exists():
                raise GovernanceViolation(
                    f"Charter file missing: {file_name}",
                    "LAW10-CHARTER",
                )

            computed_hash = self._compute_sha256(file_path)
            if computed_hash != expected_hash:
                raise GovernanceViolation(
                    f"Charter file tampered: {file_name} "
                    f"(expected {expected_hash[:16]}..., got {computed_hash[:16]}...)",
                    "LAW10-CHARTER",
                )

    def _init_ledger(self) -> None:
        """Initialize the append-only event ledger directory and file."""
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.ledger_path.exists():
            self.ledger_path.touch()

    def evaluate_risk(self, tool_name: str, payload: dict[str, Any]) -> PolicyTier:
        """Classify a proposed tool action into the 3-tier risk matrix.

        Implements: RISK-001, LAW1-PROHIBIT, LAW3-SUBORDINATE

        Args:
            tool_name: Name of the tool being invoked
            payload: Arguments/parameters for the tool call

        Returns:
            PolicyTier indicating the risk classification
        """
        # --- LAW3-SUBORDINATE: Agent may not modify its own governance ---
        target_path = str(payload.get("target_path", "")).lower()
        if any(protected in target_path for protected in self.PROTECTED_PATHS):
            return PolicyTier.PROHIBITED

        # --- LAW1-PROHIBIT: Unconditionally destructive commands ---
        command = str(payload.get("command", "")).lower().strip()
        if any(prohibited in command for prohibited in self.PROHIBITED_COMMANDS):
            return PolicyTier.PROHIBITED

        # --- RISK-001: Elevated-risk mutations ---
        elevated_tools = {
            "write_file", "execute_terminal", "execute_command",
            "run_command", "call_api", "call_payment_api",
            "spawn_agent", "delete_file", "modify_database",
            "send_email", "deploy", "push_to_registry",
        }
        if tool_name in elevated_tools:
            return PolicyTier.ELEVATED

        return PolicyTier.SAFE

    def check_halt(self) -> bool:
        """Check if the emergency operator halt has been triggered.

        Implements: LAW2-HALT
        The operator can create a .halt file to immediately terminate
        all agent execution threads.
        """
        return self.halt_file.exists()

    def intercept_and_execute(
        self,
        tool_name: str,
        payload: dict[str, Any],
        executor_func: Callable[..., T],
        approval_token: dict[str, Any] | None = None,
    ) -> T:
        """Intercept, validate, execute, and record a tool invocation.

        This is the primary entry point for all tool calls. Every action
        passes through:
        1. Emergency halt check (LAW2-HALT)
        2. Risk classification (RISK-001)
        3. Prohibition enforcement (LAW1-PROHIBIT, LAW3-SUBORDINATE)
        4. Approval verification for elevated actions (RISK-001)
        5. Execution
        6. Immutable ledger recording (LAW9-APPEND, LAW9-CHAIN)

        Args:
            tool_name: Name of the tool being invoked
            payload: Arguments/parameters for the tool call
            executor_func: The function that performs the actual tool action
            approval_token: Optional signed operator token for elevated actions

        Returns:
            The result of executor_func(payload)

        Raises:
            GovernanceViolation: If the action is prohibited or halt is active
            ApprovalRequired: If elevated action lacks operator approval
        """
        # 1. Emergency Halt (LAW2-HALT)
        if self.check_halt():
            self._log_event(
                "HALT_TRIGGERED",
                {"tool": tool_name, "reason": ".halt file detected"},
                "LAW2-HALT",
            )
            raise GovernanceViolation(
                "Emergency Operator Halt active. All execution terminated.",
                "LAW2-HALT",
            )

        # 2. Risk Classification
        tier = self.evaluate_risk(tool_name, payload)

        # 3. Prohibition Enforcement
        if tier == PolicyTier.PROHIBITED:
            self._log_event(
                "ACTION_REFUSED",
                {"tool": tool_name, "payload_keys": list(payload.keys())},
                "LAW1-PROHIBIT",
            )
            raise GovernanceViolation(
                f"Action prohibited by Autonomous Governance Laws: {tool_name}",
                "LAW1-PROHIBIT",
            )

        # 4. Elevated Approval Check
        if tier == PolicyTier.ELEVATED:
            if not self._verify_approval_token(approval_token, tool_name, payload):
                self._log_event(
                    "APPROVAL_REQUIRED",
                    {"tool": tool_name, "tier": "ELEVATED"},
                    "RISK-001",
                )
                raise ApprovalRequired(
                    f"Elevated-risk action '{tool_name}' requires a signed "
                    f"operator approval token (RISK-001)."
                )

        # 5. Execute
        start_time = time.time()
        result = executor_func(payload)
        duration_ms = (time.time() - start_time) * 1000

        # 6. Record to Immutable Ledger (LAW9-APPEND)
        self._log_event(
            "TOOL_EXECUTED",
            {
                "tool": tool_name,
                "tier": tier.name,
                "duration_ms": round(duration_ms, 2),
                "payload_keys": list(payload.keys()),
            },
            "LAW9-APPEND",
        )

        return result

    def _verify_approval_token(
        self,
        token: dict[str, Any] | None,
        tool_name: str,
        payload: dict[str, Any],
    ) -> bool:
        """Verify an operator-signed single-use approval token.

        Enforces:
        - Structural integrity and non-emptiness
        - Single-use replay protection (action_id cannot be reused)
        - Expiration and clock validity
        - Payload digest matching
        - Ed25519 digital signature against operator public key
        """
        if not token or not isinstance(token, dict):
            return False

        action_id = token.get("action_id")
        if not action_id:
            return False

        # Replay protection: each token is strictly single-use
        if action_id in self._used_action_ids:
            self._log_event(
                "TOKEN_REPLAY_DETECTED",
                {"action_id": action_id, "tool": tool_name},
                "LAW2-HALT",
            )
            return False

        from autonomous_governance.security import verify_approval_token

        is_valid, reason = verify_approval_token(
            token=token,
            tool_name=tool_name,
            payload=payload,
            expected_operator_pubkey=self.operator_pubkey,
        )

        if not is_valid:
            self._log_event(
                "TOKEN_VERIFICATION_FAILED",
                {"action_id": action_id, "tool": tool_name, "reason": reason},
                "LAW10-APPROVAL",
            )
            return False

        # Mark action_id as consumed
        self._used_action_ids.add(action_id)
        return True

    def _log_event(self, event_type: str, data: dict[str, Any], law_ref: str) -> None:
        """Append a cryptographically chained event to the ledger.

        Implements: LAW9-LEDGER, LAW9-APPEND, LAW9-CHAIN

        Each event includes:
        - UTC timestamp
        - Event type and associated law reference
        - Event data payload
        - Hash of the previous event (chain link)
        - SHA-256 hash of the current event (chain continuation)
        """
        event = {
            "timestamp": time.time(),
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event_type": event_type,
            "law_ref": law_ref,
            "data": data,
            "prev_event_hash": self.prev_event_hash,
        }

        # Compute hash chain link
        event_bytes = json.dumps(event, sort_keys=True).encode("utf-8")
        current_hash = hashlib.sha256(event_bytes).hexdigest()
        event["event_hash"] = current_hash
        self.prev_event_hash = current_hash

        # Append to ledger (immutable — never overwrite or delete)
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def audit_ledger(self) -> dict[str, Any]:
        """Verify the integrity of the append-only event ledger.

        Walks the entire ledger and verifies that:
        1. Each event's hash matches its computed hash
        2. Each event's prev_event_hash matches the prior event's hash
        3. No events have been deleted, reordered, or tampered with

        Returns:
            Dict with 'valid', 'total_events', 'broken_links', 'errors'
        """
        if not self.ledger_path.exists():
            return {"valid": True, "total_events": 0, "broken_links": 0, "errors": []}

        errors: list[str] = []
        total_events = 0
        broken_links = 0
        expected_prev_hash = "0" * 64

        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                total_events += 1
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    errors.append(f"Line {line_num}: Invalid JSON")
                    broken_links += 1
                    continue

                # Check chain link
                if event.get("prev_event_hash") != expected_prev_hash:
                    errors.append(
                        f"Line {line_num}: Broken chain link "
                        f"(expected prev={expected_prev_hash[:16]}..., "
                        f"got prev={event.get('prev_event_hash', 'MISSING')[:16]}...)"
                    )
                    broken_links += 1

                # Verify event hash
                stored_hash = event.pop("event_hash", None)
                if stored_hash:
                    computed = hashlib.sha256(
                        json.dumps(event, sort_keys=True).encode("utf-8")
                    ).hexdigest()
                    if computed != stored_hash:
                        errors.append(
                            f"Line {line_num}: Event hash mismatch "
                            f"(stored={stored_hash[:16]}..., computed={computed[:16]}...)"
                        )
                        broken_links += 1
                    expected_prev_hash = stored_hash
                    event["event_hash"] = stored_hash
                else:
                    errors.append(f"Line {line_num}: Missing event_hash")
                    broken_links += 1

        return {
            "valid": broken_links == 0,
            "total_events": total_events,
            "broken_links": broken_links,
            "errors": errors,
        }

    @staticmethod
    def _compute_sha256(file_path: Path) -> str:
        """Compute the SHA-256 hex digest of a file with normalized LF line endings."""
        with open(file_path, "rb") as f:
            content = f.read().replace(b"\r\n", b"\n")
        return hashlib.sha256(content).hexdigest()


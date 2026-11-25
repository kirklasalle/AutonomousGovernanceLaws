# Autonomous Governance Laws — R&D Architecture & Continuation Guide

**Status:** Living R&D Architecture Document · **Baseline:** Post-Nov-2026 Security Hardening (`v0.1.0+`, charter `v3.2.1`)  
**Audience:** Founder & Supreme Operator (Kirk LaSalle), Runtime Engineers, Security Researchers

---

## 1. Architectural Decisions Record (Q1–Q5)

Following the November 2026 Principal-Engineer due-diligence audit, the following architectural decisions were adopted and implemented in the codebase:

| Decision | Choice Adopted | Rationale & Implementation |
|---|---|---|
| **Q1. Signed Charter Manifest** | Detached Ed25519 manifest signature (`config/charter_manifest.sig`) | `sign_manifest()` / `verify_manifest_signature()` in [`security.py`](../src/autonomous_governance/security.py) and `agy-governance sign-manifest`. Verifies automatically when `.sig` + pinned `operator_pubkey` exist; enforce strictly via `GovernanceKernel(..., require_manifest_signature=True)`. Leaves `config/charter_manifest.json` untouched (`LAW10-CHARTER`). |
| **Q2. Zero-Dependency vs. Production Crypto** | Dual-tier: `cryptography` (`[crypto]`) for production; pure-Python verification/dev fallback | `cryptography` provides constant-time OpenSSL Ed25519 and `AES-256-GCM` (`ENCRYPTED_POSIX_V2:` with 600,000 PBKDF2-HMAC-SHA256 iterations). Pure-Python Ed25519 remains available for zero-dep verification/dev, with small-order point rejection and explicit status reporting in `agy-governance status`. POSIX keystores fail closed unless `AGL_KEY_PASSPHRASE` is set or `--allow-plaintext` is explicit. |
| **Q3. Cross-Project Token Domain Separation (`AGL-V2`)** | Optional `AGL-V2` domain-scoped tokens alongside backwards-compatible `AGL-V1` | `create_approval_token(..., scope=...)` emits `AGL-V2` binding `scope` (defaulting in `GovernanceKernel` to `sha256(project_root:manifest_sha256)[:32]`). Enforce `AGL-V2`-only via `GovernanceKernel(..., require_v2_tokens=True)`. |
| **Q4. Plugin Approval Semantics** | Keep plugin as host-permission gate for `v0.2.0`; target out-of-band `agl-signer` daemon for `v0.3.0+` | Coding-agent IDEs already prompt users natively via `ask`; forcing hardware-key signing on every file edit breaks IDE ergonomics today. Long-term high-assurance sessions should route `PreToolUse` elevated calls to a local out-of-band operator signer (`agl-signer`). |
| **Q5. `.nexus_briefing.md` & `incubator/` Boundary** | Remove & `.gitignore` `.nexus_briefing.md`; keep `incubator/` out of packaged skills | `.nexus_briefing.md` was local PM telemetry with superseded scores and is now removed/ignored. OpenClaw drafts in [`incubator/`](../incubator/README.md) remain quarantined until rewritten against `GovernanceKernel` with unit tests. |

---

## 2. Novelty, Specialized & Unknowns Register

| ID | Category | Element | Classification | Notes & Status |
|---|---|---|---|---|
| **NOV-01** | Custom Protocol | LF-Normalized Content-Addressed Charter + Anti-Drift `@`-Loaders | *Intentional Innovation* | `sign_manifest()` adds optional cryptographic authenticity on top of digest consistency. |
| **NOV-02** | Custom Protocol | `AGL-V1` / `AGL-V2` Action-Bound Single-Use Ed25519 Tokens | *Intentional Innovation* | `AGL-V2` adds `scope` domain binding; future `AGL-V3` should adopt RFC 8785 (JCS) canonical JSON. |
| **NOV-03** | Bespoke Algorithm | Dual-Pass Shell Segmenter & Windows ADS/UNC Path Canonicalizer | *Intentional Innovation (Defense-in-Depth)* | Hardened for `SAFE_TOOLS` secret checks, `powershell -EncodedCommand`, `git` global flags, `.pem`/symlinks, and depth fail-closed; still not an OS sandbox. |
| **NOV-04** | Bespoke Algorithm | Zero-Dependency Ed25519 & V2 Keystore | *Remediated Defect* | Added small-order point rejection, seed-derived `pub` consistency, 600k PBKDF2, and `AES-256-GCM` when `[crypto]` is present. Pure-Python signing remains non-constant-time (`[crypto]` recommended for production). |
| **NOV-05** | Experimental Architecture | Multi-Host Fail-Closed Hook Multiplexer & 20 s Watchdog | *Intentional Innovation* | Needs recorded live-host qualification on current Copilot CLI, VS Code, and Claude Code. |
| **NOV-06** | Rare Stack | Windows `ctypes` DPAPI Wrapper (`crypt32.dll` / `LocalFree`) | *Remediated Fragile FFI* | Added explicit 64-bit `argtypes`/`restype` declarations for `CryptProtectData`, `CryptUnprotectData`, and `LocalFree`. |
| **NOV-07** | Opaque / Future R&D | Unimplemented Constitutional Subsystems (`CAC-001`, Merkle Log, OS Sandbox, Laws 5/7/8 Evaluators, M-of-N Quorum) | *R&D Backlog* | Detailed comparison and recommendation in Section 3 below. |

---

## 3. R&D Decision Guide for Kirk (Q6: Prioritizing Unimplemented Laws)

Because AGL now has a hardened in-process interceptor, SQLite replay store, signed ledger checkpoints, and host hook adapter, the remaining architectural ceiling is **how to enforce the Laws against an agent or subprocess that tries to step around Python or act through child agents**. Below is a plain-English breakdown of the four R&D pillars so you can choose the next milestone with full context.

### Pillar A: OS / Container Execution Sandbox Adapter (Laws 1, 3 & 6) — **Recommended #1 Priority**
- **What problem it solves:** Today, `GovernanceKernel` is an in-process Python gate (`P8`), and its shell classifier is pattern-based (`P6`). If an agent executes `python -c "import shutil; ..."` or writes a shell script and runs it, the OS kernel will let that subprocess touch `.ledger/`, `.keys/`, or host files if the user's permissions allow it.
- **How it works:** Wrap `execute_command` and file tools in an OS-enforced boundary—Linux `bubblewrap`/`seccomp`/namespaces or Docker/Podman containers, and Windows Job Objects + restricted tokens / AppContainer—where `.ledger/`, `.keys/`, `.halt`, and charter files are mounted **read-only or unmapped** inside the execution sandbox.
- **Why it should be #1:** Without an OS boundary, a clever agent or prompt-injected tool can bypass regex/AST checks via indirect execution. An OS sandbox turns Laws 1, 3, and 6 from *heuristic detection* into *kernel-enforced isolation*.

### Pillar B: RFC 9162 Verifiable Merkle Log & External Witnessing (Law 9) — **Recommended #2 Priority**
- **What problem it solves:** `create_checkpoint()` / `verify_checkpoint()` now detect tail truncation when an operator holds the latest signed checkpoint, but a host attacker with local filesystem write access could still rewrite old history *between* operator checkpoints if the checkpoint isn't anchored externally.
- **How it works:** Maintain an append-only Merkle tree (RFC 9162 Certificate Transparency style) that produces O(log N) inclusion/consistency proofs, paired with optional push of the signed tree head (STH) to an external append-only witness (local root-owned daemon, syslog/OTLP sink, S3 Object Lock, or Sigstore/Rekor).
- **Why it is #2:** Directly elevates Law 9 to enterprise auditability and gives EU AI Act Article 12 compliance strong third-party verifiability.

### Pillar C: `CAC-001` Cryptographic Sub-Agent Delegation Tokens (Laws 4 & 10) — **Recommended #3 Priority**
- **What problem it solves:** When a governed parent agent spawns a sub-agent or multi-agent swarm worker, the child currently has no cryptographically attenuated identity or capability ceiling (`Law 4`: no sub-system may violate Laws 1–3; `Law 10`: no unauthorized sub-agent spawning).
- **How it works:** Issue short-lived attenuated capability tokens (Macaroon / Biscuit / chained Ed25519 delegation certificates) encoding `max_depth`, allowed `tools`, allowed `paths`, and `expires_at`. Every child kernel verifies the delegation chain back to the Supreme Operator's root key and refuses privilege escalation beyond its parent's attenuated scope.
- **Why it is #3:** Crucial once AGL governs multi-agent swarms (e.g., Antigravity swarms / PRISM Refraction), after single-agent OS sandboxing and ledger anchoring are solid.

### Pillar D: Semantic & Policy-Engine Evaluators (Laws 5, 7 & 8) — **Longer-Horizon Research**
- **What problem it solves:** Laws 5 (no judicial adjudication), 7 (truthfulness/non-deception), and 8 (equity/neutrality) cannot be enforced by regexes or file permissions alone—they depend on natural-language intent and output semantics.
- **How it works:** Integrate declarative policy-as-code (OPA/Rego or Cedar) for deterministic rule externalization, and treat LLM-based harm/bias/judicial-overreach classifiers strictly as *advisory signals* feeding `APPROVAL_REQUIRED` (never claiming deterministic enforcement of subjective semantics).

---

## 4. Continued R&D Artifacts & Hygiene

### `incubator/` OpenClaw Promotion Checklist
The five drafts in [`incubator/openclaw-skills/`](../incubator/README.md) (`policy-middleware`, `audit-skill`, `ci-secrets-kit`, `nexus-prime-directive`, `nexus-skill-auditor`) remain excluded from packaged plugin `skills/` until each:
1. Replaces ad-hoc JS/Python validators (e.g., `middleware.js` duplicate declarations) with `GovernanceKernel` / `agy-governance` calls.
2. Passes `laws-lint . --strict` (100/100) and includes automated `pytest` regressions.
3. Carries valid plugin `SKILL.md` frontmatter matching [`skills/agl-charter/SKILL.md`](../skills/agl-charter/SKILL.md).

### Out-of-Band Plugin Signer (`agl-signer`, Target `v0.3.0`)
To bridge `RISK-001` host UI prompts with cryptographic Ed25519 auditability:
- Run a local operator-owned IPC service (`agl-signer`) holding the unlocked operator key in OS memory / DPAPI / PKCS#11.
- When `hooks.py` classifies an action as `ELEVATED`, it displays the payload digest and requests a short-lived `AGL-V2` token from `agl-signer` rather than relying solely on host UI clicks.

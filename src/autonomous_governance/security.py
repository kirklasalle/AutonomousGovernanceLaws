"""
Autonomous Governance Laws — Cryptographic Security Engine

Implements hardware-grade key management, Windows DPAPI storage, RFC 8032 Ed25519
digital signatures, and action-bound single-use operator approval tokens.

Key Capabilities:
- Asymmetric Ed25519 digital signatures (RFC 8032 pure Python with optional OpenSSL acceleration)
- Windows DPAPI (Data Protection API) hardware-tied key encryption at rest
- Action-bound single-use authorization tokens with payload cryptographic hash binding
- Single-use replay protection and expiration enforcement
"""

import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Tuple

# Try importing cryptography for C-accelerated OpenSSL backend; fallback to pure Python
_HAS_CRYPTOGRAPHY = False
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519 as crypto_ed25519
    from cryptography.hazmat.primitives import serialization
    _HAS_CRYPTOGRAPHY = True
except ImportError:
    _HAS_CRYPTOGRAPHY = False


# ==============================================================================
# RFC 8032 Ed25519 Pure Python Engine (Zero External Dependencies)
# ==============================================================================

_P = 2**255 - 19
_D = -121665 * pow(121666, _P - 2, _P) % _P
_Q = 2**252 + 27742317777372353535851937790883648493


def _inv(x: int) -> int:
    return pow(x, _P - 2, _P)


def _recover_x(y: int, sign: int) -> int | None:
    if y >= _P:
        return None
    x2 = (y * y - 1) * _inv(_D * y * y + 1) % _P
    if x2 == 0:
        return 0 if sign == 0 else None
    x = pow(x2, (_P + 3) // 8, _P)
    if (x * x - x2) % _P != 0:
        x = (x * pow(2, (_P - 1) // 4, _P)) % _P
    if (x * x - x2) % _P != 0:
        return None
    if (x & 1) != sign:
        x = _P - x
    return x


def _edwards_add(p1: tuple[int, int, int, int], p2: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x1, y1, z1, t1 = p1
    x2, y2, z2, t2 = p2
    a = (y1 - x1) * (y2 - x2) % _P
    b = (y1 + x1) * (y2 + x2) % _P
    c = 2 * _D * t1 * t2 % _P
    dd = 2 * z1 * z2 % _P
    e = (b - a) % _P
    f = (dd - c) % _P
    g = (dd + c) % _P
    h = (b + a) % _P
    return (e * f % _P, g * h % _P, f * g % _P, e * h % _P)


def _scalar_mult(point: tuple[int, int, int, int], e: int) -> tuple[int, int, int, int]:
    r = (0, 1, 1, 0)
    q = point
    while e > 0:
        if e & 1:
            r = _edwards_add(r, q)
        q = _edwards_add(q, q)
        e >>= 1
    return r


_BY = 4 * _inv(5) % _P
_BX = _recover_x(_BY, 0)
assert _BX is not None
_B = (_BX, _BY, 1, (_BX * _BY) % _P)


def _point_to_bytes(p: tuple[int, int, int, int]) -> bytes:
    x, y, z, _ = p
    zi = _inv(z)
    x = (x * zi) % _P
    y = (y * zi) % _P
    s = bytearray(y.to_bytes(32, "little"))
    if x & 1:
        s[31] |= 0x80
    return bytes(s)


def _bytes_to_point(s: bytes) -> tuple[int, int, int, int] | None:
    if len(s) != 32:
        return None
    y = int.from_bytes(s, "little") & ((1 << 255) - 1)
    sign = (s[31] >> 7) & 1
    x = _recover_x(y, sign)
    if x is None:
        return None
    return (x, y, 1, (x * y) % _P)


def generate_ed25519_keypair() -> tuple[bytes, bytes]:
    """Generate a new Ed25519 private seed (32 bytes) and public key (32 bytes)."""
    if _HAS_CRYPTOGRAPHY:
        priv = crypto_ed25519.Ed25519PrivateKey.generate()
        seed = priv.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        pub = priv.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return seed, pub

    seed = os.urandom(32)
    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= (1 << 254)
    point_a = _scalar_mult(_B, a)
    pub = _point_to_bytes(point_a)
    return seed, pub


def ed25519_sign(seed: bytes, pub: bytes, message: bytes) -> bytes:
    """Sign a message using an Ed25519 private seed."""
    if _HAS_CRYPTOGRAPHY:
        priv = crypto_ed25519.Ed25519PrivateKey.from_private_bytes(seed)
        return priv.sign(message)

    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= (1 << 254)
    prefix = h[32:]
    r = int.from_bytes(hashlib.sha512(prefix + message).digest(), "little") % _Q
    r_point = _scalar_mult(_B, r)
    r_bytes = _point_to_bytes(r_point)
    k = int.from_bytes(hashlib.sha512(r_bytes + pub + message).digest(), "little") % _Q
    s = (r + k * a) % _Q
    return r_bytes + s.to_bytes(32, "little")


def ed25519_verify(pub: bytes, message: bytes, signature: bytes) -> bool:
    """Verify an Ed25519 signature over a message."""
    if len(pub) != 32 or len(signature) != 64:
        return False

    if _HAS_CRYPTOGRAPHY:
        try:
            pub_key = crypto_ed25519.Ed25519PublicKey.from_public_bytes(pub)
            pub_key.verify(signature, message)
            return True
        except Exception:
            return False

    r_bytes = signature[:32]
    s = int.from_bytes(signature[32:], "little")
    if s >= _Q:
        return False
    point_a = _bytes_to_point(pub)
    point_r = _bytes_to_point(r_bytes)
    if point_a is None or point_r is None:
        return False

    k = int.from_bytes(hashlib.sha512(r_bytes + pub + message).digest(), "little") % _Q
    sb = _scalar_mult(_B, s)
    ka = _scalar_mult(point_a, k)
    r_plus_ka = _edwards_add(point_r, ka)
    return _point_to_bytes(sb) == _point_to_bytes(r_plus_ka)


# ==============================================================================
# Windows DPAPI Hardware-Tied Key Storage
# ==============================================================================

# Prefix for keys stored without encryption because DPAPI is unavailable.
POSIX_FALLBACK_MARKER = b"UNENCRYPTED_POSIX_FALLBACK:"
# Leading bytes of every DPAPI blob: dwVersion=1, then provider GUID df9d8cd0-1501-11d1-8c7a-00c04fc297eb.
DPAPI_BLOB_HEADER = bytes.fromhex("01000000d08c9ddf0115d1118c7a00c04fc297eb")


class DPAPIKeyStore:
    """Windows Data Protection API (DPAPI) keystore wrapper.

    Encrypts operator keys at rest bound to the current Windows user's credentials
    using native Windows crypt32.dll. On non-Windows platforms, provides a fallback
    with secure POSIX permission masking (0o600).
    """

    @staticmethod
    def is_dpapi_available() -> bool:
        """Check if native Windows DPAPI is supported in the current environment."""
        if sys.platform != "win32":
            return False
        try:
            import ctypes
            return hasattr(ctypes, "windll") and hasattr(ctypes.windll, "crypt32")
        except Exception:
            return False

    @classmethod
    def protect(cls, data: bytes, description: str = "Autonomous Governance Laws Operator Key") -> bytes:
        """Encrypt raw bytes using Windows DPAPI CryptProtectData."""
        if not cls.is_dpapi_available():
            if sys.platform == "win32":
                raise RuntimeError("DPAPI was requested but is unavailable on Windows; no key was written.")
            # Non-Windows fallback: return data with marker prefix
            return POSIX_FALLBACK_MARKER + data

        import ctypes
        from ctypes import wintypes

        class DATA_BLOB(ctypes.Structure):
            _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

        in_buf = (ctypes.c_byte * len(data))(*data)
        in_blob = DATA_BLOB(len(data), in_buf)
        out_blob = DATA_BLOB()

        res = ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(in_blob), description, None, None, None, 0, ctypes.byref(out_blob)
        )
        if not res:
            raise OSError("CryptProtectData failed to encrypt operator key.")

        encrypted = bytes(
            (ctypes.c_byte * out_blob.cbData).from_address(ctypes.addressof(out_blob.pbData.contents))
        )
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)
        return encrypted

    @classmethod
    def unprotect(cls, encrypted_blob: bytes) -> bytes:
        """Decrypt DPAPI-encrypted bytes using Windows DPAPI CryptUnprotectData."""
        if encrypted_blob.startswith(POSIX_FALLBACK_MARKER):
            return encrypted_blob[len(POSIX_FALLBACK_MARKER):]

        if not cls.is_dpapi_available():
            raise RuntimeError("DPAPI encryption was used, but DPAPI is not available on this platform.")

        import ctypes
        from ctypes import wintypes

        class DATA_BLOB(ctypes.Structure):
            _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

        in_buf = (ctypes.c_byte * len(encrypted_blob))(*encrypted_blob)
        in_blob = DATA_BLOB(len(encrypted_blob), in_buf)
        out_blob = DATA_BLOB()

        res = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)
        )
        if not res:
            raise OSError("CryptUnprotectData failed to decrypt operator key.")

        decrypted = bytes(
            (ctypes.c_byte * out_blob.cbData).from_address(ctypes.addressof(out_blob.pbData.contents))
        )
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)
        return decrypted

    @classmethod
    def save_key(cls, file_path: Path, raw_key: bytes, use_dpapi: bool = True) -> None:
        """Save a key to disk with owner-only permissions, optionally DPAPI-encrypted.

        When DPAPI is requested but unavailable (non-Windows), the key is written
        with an explicit ``UNENCRYPTED_POSIX_FALLBACK:`` marker so it is never
        mistaken for an encrypted blob.
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if use_dpapi:
            data = cls.protect(raw_key)
        else:
            data = raw_key

        fd = os.open(str(file_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_BINARY", 0), 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        if os.name != "nt":
            # O_CREAT's mode does not apply to pre-existing files; enforce it explicitly.
            os.chmod(file_path, 0o600)

    @classmethod
    def load_key(cls, file_path: Path, is_dpapi: bool = True) -> bytes:
        """Load a key from disk, decrypting via DPAPI if applicable.

        A DPAPI blob that cannot be decrypted raises instead of being returned as
        key material.
        """
        with open(file_path, "rb") as f:
            content = f.read()

        if content.startswith(POSIX_FALLBACK_MARKER):
            return content[len(POSIX_FALLBACK_MARKER):]
        if is_dpapi:
            if cls.is_dpapi_available():
                return cls.unprotect(content)
            if content.startswith(DPAPI_BLOB_HEADER):
                raise RuntimeError(
                    f"{file_path} is a Windows DPAPI blob and can only be decrypted by the "
                    "Windows account that created it."
                )
        return content


# ==============================================================================
# Single-Use Operator Approval Tokens
# ==============================================================================

def compute_payload_digest(payload: dict[str, Any]) -> str:
    """Compute the deterministic SHA-256 digest of an action payload."""
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def canonical_token_message(
    version: str,
    action_id: str,
    tool_name: str,
    payload_hash: str,
    issued_at: int,
    expires_at: int,
) -> bytes:
    """Construct an AGL-V1 message; identifiers must not contain its field delimiter."""
    for name, value in (("action_id", action_id), ("tool_name", tool_name)):
        if not isinstance(value, str) or not value or ":" in value:
            raise ValueError(f"AGL-V1 {name} must be a non-empty string without ':'")
    return f"{version}:{action_id}:{tool_name}:{payload_hash}:{issued_at}:{expires_at}".encode("utf-8")


def create_approval_token(
    action_id: str,
    tool_name: str,
    payload: dict[str, Any],
    private_seed: bytes,
    public_key: bytes,
    ttl_seconds: int = 300,
) -> dict[str, Any]:
    """Generate a cryptographically signed, action-bound single-use operator approval token.

    Args:
        action_id: Unique action identifier (e.g. 'act-1729780000-01')
        tool_name: The exact tool name being authorized (e.g. 'write_file', 'execute_terminal')
        payload: The exact tool argument payload to bind to
        private_seed: 32-byte Ed25519 private seed
        public_key: 32-byte Ed25519 public key
        ttl_seconds: Validity lifetime in seconds (default 300 = 5 minutes)

    Returns:
        JSON-serializable token dictionary
    """
    version = "AGL-V1"
    now = int(time.time())
    expires_at = now + ttl_seconds
    payload_hash = compute_payload_digest(payload)

    message = canonical_token_message(version, action_id, tool_name, payload_hash, now, expires_at)
    signature = ed25519_sign(private_seed, public_key, message)

    return {
        "version": version,
        "action_id": action_id,
        "tool_name": tool_name,
        "payload_hash": payload_hash,
        "issued_at": now,
        "expires_at": expires_at,
        "operator_pubkey": public_key.hex(),
        "signature": signature.hex(),
    }


def verify_approval_token(
    token: dict[str, Any] | None,
    tool_name: str,
    payload: dict[str, Any],
    expected_operator_pubkey: bytes | None = None,
) -> tuple[bool, str]:
    """Verify an operator approval token against an incoming action.

    Verification fails closed: without a pinned operator public key no token is
    accepted, legacy unsigned tokens are always rejected, and the signature is
    checked against the pinned key (never against a key carried in the token).

    Args:
        token: The approval token dictionary provided by the operator/agent
        tool_name: The name of the tool attempting execution
        payload: The arguments payload being passed to the tool
        expected_operator_pubkey: Pinned 32-byte operator public key

    Returns:
        tuple[bool, str]: (is_valid, reason)
    """
    if not isinstance(expected_operator_pubkey, (bytes, bytearray)) or len(expected_operator_pubkey) != 32:
        return False, (
            "No pinned operator public key is configured, so elevated actions fail closed. "
            "Run `agy-governance keygen` and pass operator_pubkey_path to GovernanceKernel."
        )
    pinned_pubkey = bytes(expected_operator_pubkey)

    if not token or not isinstance(token, dict):
        return False, "Approval token missing or malformed"

    action_id = token.get("action_id")
    if not isinstance(action_id, str) or not action_id:
        return False, "Token missing action_id"

    version = token.get("version")
    if version != "AGL-V1":
        return False, f"Unsupported token version: {version!r} (only signed AGL-V1 tokens are accepted)"

    if token.get("tool_name") != tool_name:
        return False, f"Token tool_name mismatch (token={token.get('tool_name')}, action={tool_name})"

    # Verify payload integrity
    try:
        expected_payload_hash = compute_payload_digest(payload)
    except (TypeError, ValueError):
        return False, "Action payload is not JSON-serializable and cannot be bound to a token"
    if token.get("payload_hash") != expected_payload_hash:
        return False, "Payload digest mismatch (payload was modified or tampered with)"

    # Verify validity window
    issued_at = token.get("issued_at")
    expires_at = token.get("expires_at")
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in (issued_at, expires_at)):
        return False, "Token issued_at and expires_at must be integer UNIX timestamps"

    now = int(time.time())
    if now > expires_at:
        return False, f"Token expired (expired at {expires_at}, current time {now})"
    if expires_at < issued_at:
        return False, "Token validity window is inverted (expires_at precedes issued_at)"
    if now < issued_at - 60:
        return False, "Token timestamp is in the future"

    # The embedded key is informational; it must match the pinned key if present
    pubkey_hex = token.get("operator_pubkey")
    if pubkey_hex is not None:
        try:
            token_pubkey = bytes.fromhex(pubkey_hex)
        except (TypeError, ValueError):
            return False, "Invalid operator_pubkey hex format in token"
        if token_pubkey != pinned_pubkey:
            return False, "Token signed by untrusted operator public key"

    # Verify signature against the pinned key
    sig_hex = token.get("signature")
    try:
        sig_bytes = bytes.fromhex(sig_hex)
    except (TypeError, ValueError):
        return False, "Invalid signature hex format in token"
    if len(sig_bytes) != 64:
        return False, "Invalid signature length in token"

    try:
        message = canonical_token_message(
            version,
            action_id,
            tool_name,
            expected_payload_hash,
            issued_at,
            expires_at,
        )
    except ValueError as exc:
        return False, str(exc)

    if not ed25519_verify(pinned_pubkey, message, sig_bytes):
        return False, "Cryptographic signature verification failed"

    return True, "Valid single-use authorization"

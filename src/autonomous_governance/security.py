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
_HAS_AESGCM = False
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519 as crypto_ed25519
    from cryptography.hazmat.primitives import serialization
    _HAS_CRYPTOGRAPHY = True
    try:
        from cryptography.exceptions import InvalidTag as _CryptoInvalidTag
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM as _CryptoAESGCM
        _HAS_AESGCM = True
    except ImportError:
        _HAS_AESGCM = False
except ImportError:
    _HAS_CRYPTOGRAPHY = False
    _HAS_AESGCM = False


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


_IDENTITY_BYTES = bytes([1]) + bytes(31)


def derive_ed25519_public_key(seed: bytes) -> bytes:
    """Derive the 32-byte Ed25519 public key from a 32-byte private seed."""
    if not isinstance(seed, (bytes, bytearray)) or len(seed) != 32:
        raise ValueError("Ed25519 private seed must be 32 bytes")
    seed_bytes = bytes(seed)
    if _HAS_CRYPTOGRAPHY:
        priv = crypto_ed25519.Ed25519PrivateKey.from_private_bytes(seed_bytes)
        return priv.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    h = hashlib.sha512(seed_bytes).digest()
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= (1 << 254)
    return _point_to_bytes(_scalar_mult(_B, a))


def is_small_order_point(point_bytes: bytes) -> bool:
    """Return True if ``point_bytes`` is invalid or lies in the small-order torsion subgroup."""
    if not isinstance(point_bytes, (bytes, bytearray)) or len(point_bytes) != 32:
        return True
    p = _bytes_to_point(bytes(point_bytes))
    if p is None:
        return True
    p2 = _edwards_add(p, p)
    p4 = _edwards_add(p2, p2)
    p8 = _edwards_add(p4, p4)
    return _point_to_bytes(p8) == _IDENTITY_BYTES


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
    return seed, derive_ed25519_public_key(seed)


def ed25519_sign(seed: bytes, pub: bytes, message: bytes) -> bytes:
    """Sign a message using an Ed25519 private seed."""
    derived_pub = derive_ed25519_public_key(seed)
    if pub and pub != derived_pub:
        raise ValueError("Public key does not match private seed")

    if _HAS_CRYPTOGRAPHY:
        priv = crypto_ed25519.Ed25519PrivateKey.from_private_bytes(bytes(seed))
        return priv.sign(message)

    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= (1 << 254)
    prefix = h[32:]
    r = int.from_bytes(hashlib.sha512(prefix + message).digest(), "little") % _Q
    r_point = _scalar_mult(_B, r)
    r_bytes = _point_to_bytes(r_point)
    k = int.from_bytes(hashlib.sha512(r_bytes + derived_pub + message).digest(), "little") % _Q
    s = (r + k * a) % _Q
    return r_bytes + s.to_bytes(32, "little")


def ed25519_verify(pub: bytes, message: bytes, signature: bytes) -> bool:
    """Verify an Ed25519 signature over a message (rejecting small-order keys)."""
    if len(pub) != 32 or len(signature) != 64 or is_small_order_point(pub):
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
# Prefix for legacy V1 passphrase-protected POSIX keys (100k PBKDF2 + SHA-256 CTR + HMAC-SHA256).
POSIX_ENCRYPTED_MARKER = b"ENCRYPTED_POSIX_PBKDF2_V1:"
# Prefix for V2 passphrase-protected POSIX keys (600k PBKDF2 + AES-256-GCM or HMAC-SHA256 CTR).
POSIX_ENCRYPTED_V2_MARKER = b"ENCRYPTED_POSIX_V2:"
PBKDF2_ITERATIONS = 600_000
# Leading bytes of every DPAPI blob: dwVersion=1, then provider GUID df9d8cd0-1501-11d1-8c7a-00c04fc297eb.
DPAPI_BLOB_HEADER = bytes.fromhex("01000000d08c9ddf0115d1118c7a00c04fc297eb")


def _posix_ctr_xor(enc_key: bytes, salt: bytes, data: bytes) -> bytes:
    """Deterministic SHA-256 counter-mode XOR keystream for dependency-free POSIX key protection."""
    out = bytearray(len(data))
    offset = 0
    counter = 0
    while offset < len(data):
        block = hashlib.sha256(enc_key + salt + counter.to_bytes(4, "big")).digest()
        chunk = min(len(block), len(data) - offset)
        for i in range(chunk):
            out[offset + i] = data[offset + i] ^ block[i]
        offset += chunk
        counter += 1
    return bytes(out)


def _dpapi_call(encrypt: bool, blob_in_bytes: bytes, description: str = "") -> bytes:
    """Invoke Windows DPAPI CryptProtectData / CryptUnprotectData with explicit 64-bit FFI signatures."""
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

    p_blob = ctypes.POINTER(DATA_BLOB)
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p

    in_buf = (ctypes.c_byte * len(blob_in_bytes))(*blob_in_bytes)
    in_blob = DATA_BLOB(len(blob_in_bytes), in_buf)
    out_blob = DATA_BLOB()

    if encrypt:
        crypt32.CryptProtectData.argtypes = [
            p_blob, wintypes.LPCWSTR, p_blob, ctypes.c_void_p,
            ctypes.c_void_p, wintypes.DWORD, p_blob,
        ]
        crypt32.CryptProtectData.restype = wintypes.BOOL
        res = crypt32.CryptProtectData(
            ctypes.byref(in_blob), description, None, None, None, 0, ctypes.byref(out_blob)
        )
        if not res:
            raise OSError("CryptProtectData failed to encrypt operator key.")
    else:
        crypt32.CryptUnprotectData.argtypes = [
            p_blob, ctypes.c_void_p, p_blob, ctypes.c_void_p,
            ctypes.c_void_p, wintypes.DWORD, p_blob,
        ]
        crypt32.CryptUnprotectData.restype = wintypes.BOOL
        res = crypt32.CryptUnprotectData(
            ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)
        )
        if not res:
            raise OSError("CryptUnprotectData failed to decrypt operator key.")

    try:
        return bytes(
            (ctypes.c_byte * out_blob.cbData).from_address(ctypes.addressof(out_blob.pbData.contents))
        )
    finally:
        if out_blob.pbData:
            kernel32.LocalFree(ctypes.cast(out_blob.pbData, ctypes.c_void_p))


class DPAPIKeyStore:
    """Windows Data Protection API (DPAPI) keystore wrapper.

    Encrypts operator keys at rest bound to the current Windows user's credentials
    using native Windows crypt32.dll. On non-Windows platforms, encrypts using
    PBKDF2-HMAC-SHA256 (600,000 iterations + AES-256-GCM or HMAC-SHA256) when
    ``AGL_KEY_PASSPHRASE`` is set, failing closed unless ``allow_plaintext_fallback=True``.
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
    def protect_with_passphrase(
        cls, data: bytes, passphrase: str, iterations: int = PBKDF2_ITERATIONS
    ) -> bytes:
        """Encrypt raw key bytes with PBKDF2-HMAC-SHA256 (600k default) + AES-256-GCM or HMAC-CTR."""
        if not passphrase:
            raise ValueError("Passphrase must be non-empty for POSIX encrypted keystore")
        if iterations < 100_000:
            raise ValueError("PBKDF2 iteration count must be at least 100,000")
        salt = os.urandom(16)
        iter_bytes = iterations.to_bytes(4, "big")
        if _HAS_AESGCM:
            key = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, iterations, dklen=32)
            nonce = os.urandom(12)
            header = POSIX_ENCRYPTED_V2_MARKER + b"A" + iter_bytes + salt + nonce
            ct = _CryptoAESGCM(key).encrypt(nonce, data, header)
            return header + ct
        derived = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, iterations, dklen=64)
        enc_key, mac_key = derived[:32], derived[32:]
        header = POSIX_ENCRYPTED_V2_MARKER + b"H" + iter_bytes + salt
        ciphertext = _posix_ctr_xor(enc_key, salt, data)
        tag = hmac.new(mac_key, header + ciphertext, hashlib.sha256).digest()
        return header + ciphertext + tag

    @classmethod
    def unprotect_with_passphrase(cls, encrypted_blob: bytes, passphrase: str) -> bytes:
        """Authenticate and decrypt a V2 or legacy V1 POSIX passphrase-encrypted blob."""
        if not passphrase:
            raise ValueError("Invalid passphrase or corrupted POSIX encrypted key blob")

        if encrypted_blob.startswith(POSIX_ENCRYPTED_V2_MARKER):
            body = encrypted_blob[len(POSIX_ENCRYPTED_V2_MARKER):]
            if len(body) < 1 + 4 + 16:
                raise ValueError("Invalid passphrase or corrupted POSIX encrypted key blob")
            mode = body[:1]
            iterations = int.from_bytes(body[1:5], "big")
            if iterations < 100_000:
                raise ValueError("Invalid passphrase or corrupted POSIX encrypted key blob")
            salt = body[5:21]
            rest = body[21:]
            if mode == b"A":
                if not _HAS_AESGCM or len(rest) < 12 + 16:
                    raise ValueError("AES-GCM backend unavailable or corrupted POSIX encrypted key blob")
                nonce, ct = rest[:12], rest[12:]
                header = POSIX_ENCRYPTED_V2_MARKER + body[:21] + nonce
                key = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, iterations, dklen=32)
                try:
                    return _CryptoAESGCM(key).decrypt(nonce, ct, header)
                except _CryptoInvalidTag as exc:
                    raise ValueError("Invalid passphrase or corrupted POSIX encrypted key blob") from exc
            if mode == b"H":
                if len(rest) < 32:
                    raise ValueError("Invalid passphrase or corrupted POSIX encrypted key blob")
                ciphertext, tag = rest[:-32], rest[-32:]
                header = POSIX_ENCRYPTED_V2_MARKER + body[:21]
                derived = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, iterations, dklen=64)
                enc_key, mac_key = derived[:32], derived[32:]
                expected = hmac.new(mac_key, header + ciphertext, hashlib.sha256).digest()
                if not hmac.compare_digest(tag, expected):
                    raise ValueError("Invalid passphrase or corrupted POSIX encrypted key blob")
                return _posix_ctr_xor(enc_key, salt, ciphertext)
            raise ValueError("Invalid passphrase or corrupted POSIX encrypted key blob")

        if not encrypted_blob.startswith(POSIX_ENCRYPTED_MARKER):
            raise ValueError("Blob does not carry a recognized POSIX encrypted key header")
        body = encrypted_blob[len(POSIX_ENCRYPTED_MARKER):]
        if len(body) < 16 + 32:
            raise ValueError("Invalid passphrase or corrupted POSIX encrypted key blob")
        salt = body[:16]
        tag = body[-32:]
        ciphertext = body[16:-32]
        derived = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, 100_000, dklen=64)
        enc_key, mac_key = derived[:32], derived[32:]
        expected = hmac.new(mac_key, POSIX_ENCRYPTED_MARKER + salt + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected):
            raise ValueError("Invalid passphrase or corrupted POSIX encrypted key blob")
        return _posix_ctr_xor(enc_key, salt, ciphertext)

    @classmethod
    def protect(
        cls,
        data: bytes,
        description: str = "Autonomous Governance Laws Operator Key",
        allow_plaintext_fallback: bool = False,
    ) -> bytes:
        """Encrypt raw bytes using Windows DPAPI or POSIX passphrase-based AEAD."""
        if not cls.is_dpapi_available():
            if sys.platform == "win32":
                raise RuntimeError("DPAPI was requested but is unavailable on Windows; no key was written.")
            passphrase = os.environ.get("AGL_KEY_PASSPHRASE", "")
            if passphrase:
                return cls.protect_with_passphrase(data, passphrase)
            if allow_plaintext_fallback:
                return POSIX_FALLBACK_MARKER + data
            raise RuntimeError(
                "Encryption requested on POSIX but AGL_KEY_PASSPHRASE is not set; "
                "set AGL_KEY_PASSPHRASE or pass allow_plaintext_fallback=True."
            )

        return _dpapi_call(True, data, description=description)

    @classmethod
    def unprotect(cls, encrypted_blob: bytes) -> bytes:
        """Decrypt DPAPI-encrypted or POSIX passphrase-encrypted bytes."""
        if encrypted_blob.startswith((POSIX_ENCRYPTED_V2_MARKER, POSIX_ENCRYPTED_MARKER)):
            return cls.unprotect_with_passphrase(encrypted_blob, os.environ.get("AGL_KEY_PASSPHRASE", ""))
        if encrypted_blob.startswith(POSIX_FALLBACK_MARKER):
            return encrypted_blob[len(POSIX_FALLBACK_MARKER):]

        if not cls.is_dpapi_available():
            raise RuntimeError("DPAPI encryption was used, but DPAPI is not available on this platform.")

        return _dpapi_call(False, encrypted_blob)

    @classmethod
    def save_key(
        cls,
        file_path: Path,
        raw_key: bytes,
        use_dpapi: bool = True,
        allow_plaintext_fallback: bool = False,
    ) -> None:
        """Save a key to disk with owner-only permissions, optionally encrypted.

        On Windows, encrypts via DPAPI. On POSIX with ``use_dpapi=True``, requires
        ``AGL_KEY_PASSPHRASE`` unless ``allow_plaintext_fallback=True``.
        """
        file_path = Path(file_path)
        if use_dpapi:
            data = cls.protect(raw_key, allow_plaintext_fallback=allow_plaintext_fallback)
        else:
            data = raw_key

        file_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(file_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_BINARY", 0), 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        if os.name != "nt":
            # O_CREAT's mode does not apply to pre-existing files; enforce it explicitly.
            os.chmod(file_path, 0o600)

    @classmethod
    def load_key(cls, file_path: Path, is_dpapi: bool = True) -> bytes:
        """Load a key from disk, decrypting via DPAPI or POSIX passphrase if applicable.

        An encrypted blob that cannot be decrypted raises instead of being returned as
        key material.
        """
        with open(file_path, "rb") as f:
            content = f.read()

        if content.startswith((POSIX_ENCRYPTED_V2_MARKER, POSIX_ENCRYPTED_MARKER)):
            return cls.unprotect_with_passphrase(content, os.environ.get("AGL_KEY_PASSPHRASE", ""))
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
    scope: str | None = None,
) -> bytes:
    """Construct an AGL-V1 or AGL-V2 message; identifiers must not contain its field delimiter."""
    for name, value in (("action_id", action_id), ("tool_name", tool_name)):
        if not isinstance(value, str) or not value or ":" in value:
            raise ValueError(f"{version} {name} must be a non-empty string without ':'")
    if version == "AGL-V2":
        if not isinstance(scope, str) or not scope or ":" in scope:
            raise ValueError("AGL-V2 scope must be a non-empty string without ':'")
        return f"AGL-V2:{scope}:{action_id}:{tool_name}:{payload_hash}:{issued_at}:{expires_at}".encode("utf-8")
    if version == "AGL-V1":
        return f"AGL-V1:{action_id}:{tool_name}:{payload_hash}:{issued_at}:{expires_at}".encode("utf-8")
    raise ValueError(f"Unsupported token version: {version!r}")


def create_approval_token(
    action_id: str,
    tool_name: str,
    payload: dict[str, Any],
    private_seed: bytes,
    public_key: bytes | None = None,
    ttl_seconds: int = 300,
    scope: str | None = None,
) -> dict[str, Any]:
    """Generate a cryptographically signed, action-bound single-use operator approval token.

    When ``scope`` is provided, emits an ``AGL-V2`` domain-scoped token bound to that
    project/manifest scope; otherwise emits a backwards-compatible ``AGL-V1`` token.
    """
    derived_pub = derive_ed25519_public_key(private_seed)
    if public_key is not None and public_key != derived_pub:
        raise ValueError("Public key does not match private seed")

    version = "AGL-V2" if scope is not None else "AGL-V1"
    now = int(time.time())
    expires_at = now + ttl_seconds
    payload_hash = compute_payload_digest(payload)

    message = canonical_token_message(
        version, action_id, tool_name, payload_hash, now, expires_at, scope=scope
    )
    signature = ed25519_sign(private_seed, derived_pub, message)

    token: dict[str, Any] = {
        "version": version,
        "action_id": action_id,
        "tool_name": tool_name,
        "payload_hash": payload_hash,
        "issued_at": now,
        "expires_at": expires_at,
        "operator_pubkey": derived_pub.hex(),
        "signature": signature.hex(),
    }
    if scope is not None:
        token["scope"] = scope
    return token


def verify_approval_token(
    token: dict[str, Any] | None,
    tool_name: str,
    payload: dict[str, Any],
    expected_operator_pubkey: bytes | None = None,
    expected_scope: str | None = None,
    require_v2: bool = False,
) -> tuple[bool, str]:
    """Verify an operator approval token against an incoming action.

    Verification fails closed: without a pinned operator public key no token is
    accepted, legacy unsigned tokens are always rejected, and the signature is
    checked against the pinned key (never against a key carried in the token).
    Supports ``AGL-V1`` and domain-scoped ``AGL-V2`` tokens.
    """
    if not isinstance(expected_operator_pubkey, (bytes, bytearray)) or len(expected_operator_pubkey) != 32:
        return False, (
            "No pinned operator public key is configured, so elevated actions fail closed. "
            "Run `agy-governance keygen` and pass operator_pubkey_path to GovernanceKernel."
        )
    if is_small_order_point(bytes(expected_operator_pubkey)):
        return False, "Configured operator public key is a disallowed small-order or invalid point"
    pinned_pubkey = bytes(expected_operator_pubkey)

    if not token or not isinstance(token, dict):
        return False, "Approval token missing or malformed"

    action_id = token.get("action_id")
    if not isinstance(action_id, str) or not action_id:
        return False, "Token missing action_id"

    version = token.get("version")
    allowed_versions = ("AGL-V2",) if require_v2 else ("AGL-V1", "AGL-V2")
    if version not in allowed_versions:
        return False, f"Unsupported token version: {version!r} (expected {' or '.join(allowed_versions)})"

    token_scope: str | None = None
    if version == "AGL-V2":
        token_scope = token.get("scope")
        if not isinstance(token_scope, str) or not token_scope or ":" in token_scope:
            return False, "AGL-V2 token missing valid scope"
        if expected_scope is not None and token_scope != expected_scope:
            return False, f"Token scope mismatch (token={token_scope!r}, expected={expected_scope!r})"

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
            scope=token_scope,
        )
    except ValueError as exc:
        return False, str(exc)

    if not ed25519_verify(pinned_pubkey, message, sig_bytes):
        return False, "Cryptographic signature verification failed"

    return True, "Valid single-use authorization"


# ==============================================================================
# Detached Charter Manifest & Ledger Checkpoint Signatures
# ==============================================================================

def _manifest_digest_lf(manifest_path: str | Path) -> str:
    content = Path(manifest_path).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def sign_manifest(
    manifest_path: str | Path,
    private_seed: bytes,
    sig_path: str | Path | None = None,
) -> str:
    """Create a detached Ed25519 signature (hex) over ``manifest_path`` (LF-normalized)."""
    digest = _manifest_digest_lf(manifest_path)
    pub = derive_ed25519_public_key(private_seed)
    message = f"AGL-MANIFEST-V1:{digest}".encode("ascii")
    sig_hex = ed25519_sign(private_seed, pub, message).hex()
    if sig_path is not None:
        out = Path(sig_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(sig_hex + "\n", encoding="utf-8")
    return sig_hex


def verify_manifest_signature(
    manifest_path: str | Path,
    signature_hex: str,
    expected_operator_pubkey: bytes,
) -> tuple[bool, str]:
    """Verify a detached Ed25519 signature over ``manifest_path`` against ``expected_operator_pubkey``."""
    if (
        not isinstance(expected_operator_pubkey, (bytes, bytearray))
        or len(expected_operator_pubkey) != 32
        or is_small_order_point(bytes(expected_operator_pubkey))
    ):
        return False, "No valid pinned operator public key for manifest verification"
    try:
        sig_bytes = bytes.fromhex(signature_hex.strip())
    except (AttributeError, ValueError):
        return False, "Malformed manifest signature hex"
    if len(sig_bytes) != 64:
        return False, "Invalid manifest signature length"
    try:
        digest = _manifest_digest_lf(manifest_path)
    except OSError as exc:
        return False, f"Cannot read manifest for signature verification: {exc}"
    message = f"AGL-MANIFEST-V1:{digest}".encode("ascii")
    if not ed25519_verify(bytes(expected_operator_pubkey), message, sig_bytes):
        return False, "Manifest signature verification failed"
    return True, "Valid detached manifest signature"


def sign_ledger_checkpoint(
    event_count: int,
    head_hash: str,
    private_seed: bytes,
    scope: str = "",
) -> dict[str, Any]:
    """Sign an immutable ledger head checkpoint (event_count + head_hash) to detect tail truncation."""
    if not isinstance(event_count, int) or isinstance(event_count, bool) or event_count < 0:
        raise ValueError("event_count must be a non-negative integer")
    if not isinstance(head_hash, str) or len(head_hash) != 64:
        raise ValueError("head_hash must be a 64-character hex SHA-256 digest")
    bytes.fromhex(head_hash)
    if not isinstance(scope, str) or ":" in scope:
        raise ValueError("scope must be a string without ':'")
    pub = derive_ed25519_public_key(private_seed)
    issued_at = int(time.time())
    message = f"AGL-CHECKPOINT-V1:{scope}:{event_count}:{head_hash}:{issued_at}".encode("utf-8")
    sig = ed25519_sign(private_seed, pub, message)
    return {
        "version": "AGL-CHECKPOINT-V1",
        "scope": scope,
        "event_count": event_count,
        "head_hash": head_hash,
        "issued_at": issued_at,
        "operator_pubkey": pub.hex(),
        "signature": sig.hex(),
    }


def verify_ledger_checkpoint(
    checkpoint: dict[str, Any],
    expected_operator_pubkey: bytes,
    expected_scope: str | None = None,
) -> tuple[bool, str]:
    """Verify a signed ledger checkpoint against ``expected_operator_pubkey``."""
    if (
        not isinstance(expected_operator_pubkey, (bytes, bytearray))
        or len(expected_operator_pubkey) != 32
        or is_small_order_point(bytes(expected_operator_pubkey))
    ):
        return False, "No valid pinned operator public key for checkpoint verification"
    if not isinstance(checkpoint, dict) or checkpoint.get("version") != "AGL-CHECKPOINT-V1":
        return False, "Unsupported or malformed ledger checkpoint"
    scope = checkpoint.get("scope", "")
    event_count = checkpoint.get("event_count")
    head_hash = checkpoint.get("head_hash")
    issued_at = checkpoint.get("issued_at")
    if not isinstance(scope, str) or ":" in scope:
        return False, "Invalid checkpoint scope"
    if expected_scope is not None and scope != expected_scope:
        return False, f"Checkpoint scope mismatch (got={scope!r}, expected={expected_scope!r})"
    if not isinstance(event_count, int) or isinstance(event_count, bool) or event_count < 0:
        return False, "Invalid checkpoint event_count"
    if not isinstance(head_hash, str) or len(head_hash) != 64:
        return False, "Invalid checkpoint head_hash"
    if not isinstance(issued_at, int) or isinstance(issued_at, bool):
        return False, "Invalid checkpoint issued_at"
    try:
        sig_bytes = bytes.fromhex(str(checkpoint.get("signature", "")))
    except ValueError:
        return False, "Malformed checkpoint signature hex"
    if len(sig_bytes) != 64:
        return False, "Invalid checkpoint signature length"
    message = f"AGL-CHECKPOINT-V1:{scope}:{event_count}:{head_hash}:{issued_at}".encode("utf-8")
    if not ed25519_verify(bytes(expected_operator_pubkey), message, sig_bytes):
        return False, "Checkpoint signature verification failed"
    return True, "Valid signed ledger checkpoint"

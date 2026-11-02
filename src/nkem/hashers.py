"""Django PBKDF2 hashing with a Pyodide-compatible cryptography backend.

Cloudflare's Python runtime omits OpenSSL's hashlib.pbkdf2_hmac, and its
Web Crypto PBKDF2 implementation rejects work factors above 100,000 rounds.
The cryptography package provides an optimized PBKDF2 implementation that
supports the full work factor while preserving Django's standard hash format.
"""
import base64
import hashlib

from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.utils.encoding import force_bytes


def _cryptography_pbkdf2(hash_name, password, salt, iterations, dklen):
    """Use the compiled cryptography backend for high-work-factor PBKDF2."""
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    except ImportError as exc:
        raise RuntimeError(
            "TIANA requires the cryptography package for PBKDF2 on Cloudflare Workers."
        ) from exc

    digest_name = hash_name.replace("-", "").lower()
    algorithms = {
        "sha1": hashes.SHA1,
        "sha224": hashes.SHA224,
        "sha256": hashes.SHA256,
        "sha384": hashes.SHA384,
        "sha512": hashes.SHA512,
    }
    algorithm_factory = algorithms.get(digest_name)
    if algorithm_factory is None:
        raise ValueError("Unsupported PBKDF2 digest: %s" % hash_name)

    algorithm = algorithm_factory()
    kdf = PBKDF2HMAC(
        algorithm=algorithm,
        length=dklen,
        salt=force_bytes(salt),
        iterations=iterations,
    )
    return kdf.derive(force_bytes(password))


def portable_pbkdf2(hash_name, password, salt, iterations, dklen=None):
    """Derive PBKDF2 natively where available, otherwise via cryptography."""
    if not isinstance(iterations, int) or iterations < 1:
        raise ValueError("iterations must be a positive integer")

    digest = getattr(hashlib, hash_name.replace("-", "_"), None)
    digest_size = digest().digest_size if digest is not None else 32
    length = dklen or digest_size
    if not isinstance(length, int) or length < 1:
        raise ValueError("dklen must be a positive integer")

    native_pbkdf2 = getattr(hashlib, "pbkdf2_hmac", None)
    if native_pbkdf2 is not None:
        try:
            return native_pbkdf2(
                hash_name,
                force_bytes(password),
                force_bytes(salt),
                iterations,
                dklen=length,
            )
        except (AttributeError, NotImplementedError):
            # Pyodide builds may expose hashlib but omit OpenSSL PBKDF2.
            pass

    return _cryptography_pbkdf2(hash_name, password, salt, iterations, length)


class PortablePBKDF2PasswordHasher(PBKDF2PasswordHasher):
    """Django PBKDF2-SHA256 hasher for Cloudflare's Python runtime.

    New hashes use 600,000 PBKDF2-HMAC-SHA256 rounds. The encoded round count
    remains part of each hash, so older 120k temporary hashes and stronger
    pre-existing hashes can still be verified without changing their format.
    """

    iterations = 600_000

    def encode(self, password, salt, iterations=None):
        iterations = iterations or self.iterations
        hash_value = portable_pbkdf2(
            self.digest().name,
            password,
            salt,
            iterations,
        )
        encoded_hash = base64.b64encode(hash_value).decode("ascii").strip()
        return "%s$%d$%s$%s" % (self.algorithm, iterations, salt, encoded_hash)

    def must_update(self, encoded):
        # Upgrade the temporary 120k work factor on next successful login,
        # while preserving any older hash that already uses stronger rounds.
        try:
            _, rounds, _, _ = encoded.split("$", 3)
            return int(rounds) < self.iterations
        except (TypeError, ValueError):
            return True


class PortablePBKDF2SHA1PasswordHasher(PortablePBKDF2PasswordHasher):
    """Compatibility hasher for existing Django PBKDF2-SHA1 passwords."""

    algorithm = "pbkdf2_sha1"
    digest = hashlib.sha1

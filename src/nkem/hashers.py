"""PBKDF2 password hashing compatible with Pyodide/Cloudflare Workers.

Pyodide does not ship OpenSSL-backed hashlib.pbkdf2_hmac. This module keeps
Django's existing PBKDF2 encoding unchanged and computes the same RFC 8018
PBKDF2 result using the portable hashlib SHA digest + HMAC implementation.
"""
import base64
import hashlib
import hmac

from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.utils.encoding import force_bytes


def portable_pbkdf2(hash_name, password, salt, iterations, dklen=None):
    """Portable PBKDF2-HMAC implementation for runtimes without OpenSSL."""
    if not isinstance(iterations, int) or iterations < 1:
        raise ValueError("iterations must be a positive integer")

    digest = getattr(hashlib, hash_name, None)
    if digest is None:
        raise ValueError("Unsupported hash digest: %s" % hash_name)

    password = force_bytes(password)
    salt = force_bytes(salt)
    digest_size = digest().digest_size
    if dklen is None:
        dklen = digest_size
    if not isinstance(dklen, int) or dklen < 1:
        raise ValueError("dklen must be a positive integer")

    block_count = (dklen + digest_size - 1) // digest_size
    if block_count > 0xFFFFFFFF:
        raise OverflowError("derived key is too long")

    derived = bytearray()
    for block_index in range(1, block_count + 1):
        u_value = hmac.digest(
            password,
            salt + block_index.to_bytes(4, byteorder="big"),
            digest,
        )
        accumulator = bytearray(u_value)
        for _ in range(iterations - 1):
            u_value = hmac.digest(password, u_value, digest)
            for byte_index, value in enumerate(u_value):
                accumulator[byte_index] ^= value
        derived.extend(accumulator)

    return bytes(derived[:dklen])


def _derive_pbkdf2(hash_name, password, salt, iterations):
    native_pbkdf2 = getattr(hashlib, "pbkdf2_hmac", None)
    if native_pbkdf2 is not None:
        try:
            return native_pbkdf2(hash_name, password, salt, iterations)
        except (AttributeError, NotImplementedError):
            # Some WebAssembly builds expose hashlib but omit OpenSSL-backed
            # key-derivation functions. Fall through to the portable version.
            pass
    return portable_pbkdf2(hash_name, password, salt, iterations)


class PortablePBKDF2PasswordHasher(PBKDF2PasswordHasher):
    """Django PBKDF2-SHA256 hasher with a Pyodide-safe fallback."""

    def encode(self, password, salt, iterations=None):
        iterations = iterations or self.iterations
        hash_value = _derive_pbkdf2(
            self.digest().name,
            force_bytes(password),
            force_bytes(salt),
            iterations,
        )
        encoded_hash = base64.b64encode(hash_value).decode("ascii").strip()
        return "%s$%d$%s$%s" % (self.algorithm, iterations, salt, encoded_hash)


class PortablePBKDF2SHA1PasswordHasher(PortablePBKDF2PasswordHasher):
    """Compatibility hasher for existing Django PBKDF2-SHA1 passwords."""

    algorithm = "pbkdf2_sha1"
    digest = hashlib.sha1

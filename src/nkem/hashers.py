"""Django PBKDF2 password hashing using Cloudflare's native Web Crypto API.

Cloudflare's Python runtime omits OpenSSL's hashlib.pbkdf2_hmac. Calling a
Python-level PBKDF2 loop in Pyodide is too slow. Pyodide's run_sync bridge lets
Django's synchronous WSGI code await the Workers Web Crypto PBKDF2 primitive,
while retaining Django's standard encoded password format.
"""
import base64
import hashlib

from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.utils.encoding import force_bytes


def _webcrypto_pbkdf2(hash_name, password, salt, iterations, dklen):
    """Use native Workers Web Crypto from synchronous Django code."""
    try:
        from js import Object, Uint8Array, crypto
        from pyodide.ffi import run_sync
    except ImportError as exc:
        raise RuntimeError(
            "Cloudflare password hashing requires Pyodide run_sync and Web Crypto."
        ) from exc

    digest_name = hash_name.replace("-", "").lower()
    web_digests = {
        "sha1": "SHA-1",
        "sha256": "SHA-256",
        "sha384": "SHA-384",
        "sha512": "SHA-512",
    }
    web_digest = web_digests.get(digest_name)
    if web_digest is None:
        raise ValueError("Unsupported Web Crypto PBKDF2 digest: %s" % hash_name)

    password_bytes = force_bytes(password)
    salt_bytes = force_bytes(salt)

    password_buffer = Uint8Array.new(len(password_bytes))
    for index, value in enumerate(password_bytes):
        password_buffer[index] = value

    salt_buffer = Uint8Array.new(len(salt_bytes))
    for index, value in enumerate(salt_bytes):
        salt_buffer[index] = value

    key_algorithm = Object.new()
    key_algorithm.name = "PBKDF2"

    async def derive():
        key = await crypto.subtle.importKey(
            "raw",
            password_buffer,
            key_algorithm,
            False,
            ["deriveBits"],
        )

        parameters = Object.new()
        parameters.name = "PBKDF2"
        parameters.salt = salt_buffer
        parameters.iterations = iterations
        parameters.hash = web_digest

        buffer = await crypto.subtle.deriveBits(
            parameters,
            key,
            dklen * 8,
        )
        result = Uint8Array.new(buffer)
        return bytes(int(result[index]) for index in range(dklen))

    # This is Pyodide's supported sync-over-async bridge for APIs such as
    # crypto.subtle.deriveBits; it avoids doing hundreds of thousands of HMAC
    # rounds in Python/WebAssembly bytecode.
    return run_sync(derive())


def portable_pbkdf2(hash_name, password, salt, iterations, dklen=None):
    """Derive PBKDF2 using native hashlib locally or Web Crypto on Workers."""
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
            return native_pbkdf2(hash_name, force_bytes(password), force_bytes(salt), iterations, dklen=length)
        except (AttributeError, NotImplementedError):
            # Some WebAssembly builds expose hashlib without OpenSSL PBKDF2.
            pass

    return _webcrypto_pbkdf2(hash_name, password, salt, iterations, length)


class PortablePBKDF2PasswordHasher(PBKDF2PasswordHasher):
    """Django PBKDF2-SHA256 hasher tuned for Cloudflare's Worker runtime.

    New hashes use OWASP's 600,000-round PBKDF2-HMAC-SHA256 recommendation.
    Existing hashes keep their encoded work factor when verified; stronger
    historical hashes are never silently downgraded.
    """

    iterations = 600_000

    def encode(self, password, salt, iterations=None):
        iterations = iterations or self.iterations
        hash_value = portable_pbkdf2(
            self.digest().name,
            force_bytes(password),
            force_bytes(salt),
            iterations,
        )
        encoded_hash = base64.b64encode(hash_value).decode("ascii").strip()
        return "%s$%d$%s$%s" % (self.algorithm, iterations, salt, encoded_hash)

    def must_update(self, encoded):
        # Upgrade weak legacy rounds (e.g. the temporary 120k Worker hashes),
        # but never downgrade prior Django hashes that used 1.2M iterations.
        try:
            _, rounds, _, _ = encoded.split("$", 3)
            return int(rounds) < self.iterations
        except (TypeError, ValueError):
            return True


class PortablePBKDF2SHA1PasswordHasher(PortablePBKDF2PasswordHasher):
    """Compatibility hasher for existing Django PBKDF2-SHA1 passwords."""

    algorithm = "pbkdf2_sha1"
    digest = hashlib.sha1

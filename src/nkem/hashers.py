"""Fast PBKDF2 password hashing for Pyodide/Cloudflare Workers.

Pyodide does not expose OpenSSL-backed hashlib.pbkdf2_hmac. Reimplementing
Django's production PBKDF2 iteration count in Python is prohibitively slow.
The cryptography wheel included in Pyodide provides an optimized WebAssembly
implementation while preserving Django's standard PBKDF2 hash format.
"""
import base64
import hashlib

from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.utils.encoding import force_bytes


def portable_pbkdf2(hash_name, password, salt, iterations, dklen=None):
    """Derive PBKDF2 using the optimized cryptography backend."""
    if not isinstance(iterations, int) or iterations < 1:
        raise ValueError("iterations must be a positive integer")

    # cryptography is built for Pyodide and runs the KDF in compiled WASM code.
    # Import lazily so non-Worker environments may still use native hashlib.
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    except ImportError as exc:
        raise RuntimeError(
            "TIANA requires the cryptography Pyodide package to hash passwords "
            "when hashlib.pbkdf2_hmac is unavailable."
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
    length = dklen or algorithm.digest_size
    if length < 1:
        raise ValueError("dklen must be a positive integer")

    kdf = PBKDF2HMAC(
        algorithm=algorithm,
        length=length,
        salt=force_bytes(salt),
        iterations=iterations,
    )
    return kdf.derive(force_bytes(password))


def _derive_pbkdf2(hash_name, password, salt, iterations):
    native_pbkdf2 = getattr(hashlib, "pbkdf2_hmac", None)
    if native_pbkdf2 is not None:
        try:
            return native_pbkdf2(hash_name, password, salt, iterations)
        except (AttributeError, NotImplementedError):
            # Some WebAssembly builds expose hashlib but omit OpenSSL-backed
            # PBKDF2. Use the optimized cryptography implementation instead.
            pass
    return portable_pbkdf2(hash_name, password, salt, iterations)


class PortablePBKDF2PasswordHasher(PBKDF2PasswordHasher):
    """Django PBKDF2-SHA256 hasher tuned for the Cloudflare WASM runtime.

    Cloudflare's Python runtime has a much smaller CPU budget than a typical
    server. New hashes use 120,000 PBKDF2 rounds to keep registration/login
    responsive. verify() still honors the iteration count stored in existing
    hashes, so this does not invalidate previously created accounts.
    """

    iterations = 120_000

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

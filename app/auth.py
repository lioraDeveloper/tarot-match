"""Password hashing and signed session cookies."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from base64 import urlsafe_b64decode, urlsafe_b64encode

ITERATIONS = 120_000
SECRET = os.getenv("APP_SECRET", "dev-tarot-match-change-me").encode("utf-8")


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS)
    return f"pbkdf2${ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt, hexdigest = stored.split("$")
        if algo != "pbkdf2":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iters)
        )
        return hmac.compare_digest(digest.hex(), hexdigest)
    except ValueError:
        return False


def sign_session(user_id: str) -> str:
    payload = user_id.encode("utf-8")
    sig = hmac.new(SECRET, payload, hashlib.sha256).digest()
    return urlsafe_b64encode(payload).decode("ascii") + "." + urlsafe_b64encode(sig).decode("ascii")


def read_session(token: str | None) -> str | None:
    if not token:
        return None
    try:
        payload_b64, sig_b64 = token.split(".", 1)
        payload = urlsafe_b64decode(payload_b64.encode("ascii"))
        sig = urlsafe_b64decode(sig_b64.encode("ascii"))
        expected = hmac.new(SECRET, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            return None
        return payload.decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None

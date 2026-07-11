"""Inbound webhook signature verification.

GitHub signs each webhook body with an HMAC-SHA256 keyed by the webhook secret
and sends it in the ``X-Hub-Signature-256: sha256=<hex>`` header. We recompute
the digest over the *raw* request body and compare in constant time.

Kept dependency-free (``hmac``/``hashlib`` are stdlib) and provider-agnostic in
shape so GitLab/Bitbucket verifiers can live beside this later.
"""
from __future__ import annotations

import hashlib
import hmac


def compute_github_signature(secret: str, body: bytes) -> str:
    """Return the ``sha256=<hex>`` header value GitHub would send for ``body``.

    Exposed so tests (and the local simulator) can sign payloads exactly as
    GitHub does without duplicating the algorithm.
    """
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def verify_github_signature(secret: str, body: bytes, header: str | None) -> bool:
    """Constant-time check of the ``X-Hub-Signature-256`` header.

    Returns ``True`` when the secret is empty (verification disabled for local
    dev) or when the header matches. Any malformed/absent header with a
    configured secret returns ``False``.
    """
    if not secret:
        return True
    if not header:
        return False
    expected = compute_github_signature(secret, body)
    return hmac.compare_digest(expected, header)

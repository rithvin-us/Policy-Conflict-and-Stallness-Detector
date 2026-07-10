"""Self-describing, sortable entity IDs (``pol_``, ``cfl_``, ``whk_`` ...).

A monotonic timestamp prefix keeps IDs roughly time-ordered without requiring a
ULID dependency; the random suffix avoids collisions within the same millisecond.
"""
from __future__ import annotations

import secrets
import time

_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"


def _b36(n: int) -> str:
    out = ""
    while n:
        n, r = divmod(n, 36)
        out = _ALPHABET[r] + out
    return out or "0"


def new_id(prefix: str) -> str:
    ts = _b36(int(time.time() * 1000))
    rand = "".join(secrets.choice(_ALPHABET) for _ in range(6))
    return f"{prefix}_{ts}{rand}"

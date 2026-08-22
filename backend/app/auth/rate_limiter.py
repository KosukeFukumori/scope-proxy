"""In-process login rate limiter.

This app is a single-worker, single-process SQLite-backed service (see
CLAUDE.md), so brute-force protection is implemented as a simple in-memory
counter rather than depending on external infrastructure such as Redis. State
is process-local and reset on restart, which is acceptable for this use case.
"""

from __future__ import annotations

import threading
import time

from app.config import settings


class LoginRateLimiter:
    """Tracks failed attempts per key (e.g. an IP address or username) within a
    sliding time window and reports whether a key should currently be blocked.
    """

    def __init__(self, max_attempts: int, window_seconds: float) -> None:
        self._max_attempts = max_attempts
        self._window_seconds = window_seconds
        self._attempts: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _prune_locked(self, key: str, now: float) -> list[float]:
        """Remove timestamps outside the window. Caller must hold the lock."""
        timestamps = self._attempts.get(key, [])
        cutoff = now - self._window_seconds
        fresh = [t for t in timestamps if t > cutoff]
        if fresh:
            self._attempts[key] = fresh
        else:
            self._attempts.pop(key, None)
        return fresh

    def is_blocked(self, key: str) -> bool:
        with self._lock:
            now = time.monotonic()
            timestamps = self._prune_locked(key, now)
            return len(timestamps) >= self._max_attempts

    def record_failure(self, key: str) -> None:
        with self._lock:
            now = time.monotonic()
            timestamps = self._prune_locked(key, now)
            timestamps.append(now)
            self._attempts[key] = timestamps

    def reset(self, key: str) -> None:
        with self._lock:
            self._attempts.pop(key, None)

    def clear(self) -> None:
        """Clear all tracked state. Intended for use in tests."""
        with self._lock:
            self._attempts.clear()


# Process-wide singleton used by the login endpoint.
login_rate_limiter = LoginRateLimiter(
    max_attempts=settings.login_rate_limit_max_attempts,
    window_seconds=settings.login_rate_limit_window_seconds,
)

"""In-memory progressive login throttle keyed by (account, client).

Suitable for the single-process local deployment. Keys on both the normalized
username and the client identifier so one actor cannot lock another out
system-wide, and the lock is bounded and self-recovering.
"""

from __future__ import annotations

import threading
import time

from ..core.config import get_settings


class LoginThrottle:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        # key -> (failure_count, first_failure_ts, locked_until_ts)
        self._state: dict[tuple[str, str], tuple[int, float, float]] = {}

    @staticmethod
    def _key(username_normalized: str, client: str) -> tuple[str, str]:
        return (username_normalized, client)

    def is_locked(self, username_normalized: str, client: str) -> bool:
        settings = get_settings()
        now = time.time()
        with self._lock:
            entry = self._state.get(self._key(username_normalized, client))
            if not entry:
                return False
            _count, _first, locked_until = entry
            return now < locked_until

    def record_failure(self, username_normalized: str, client: str) -> None:
        settings = get_settings()
        now = time.time()
        key = self._key(username_normalized, client)
        with self._lock:
            count, first, locked_until = self._state.get(key, (0, now, 0.0))
            # Reset the window if it has elapsed.
            if now - first > settings.login_failure_window_seconds:
                count, first, locked_until = 0, now, 0.0
            count += 1
            if count >= settings.login_max_failures:
                locked_until = now + settings.login_lock_seconds
            self._state[key] = (count, first, locked_until)

    def reset(self, username_normalized: str, client: str) -> None:
        with self._lock:
            self._state.pop(self._key(username_normalized, client), None)


# Process-wide singleton.
login_throttle = LoginThrottle()

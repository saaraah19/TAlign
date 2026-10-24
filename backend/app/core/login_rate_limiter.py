"""
Throttling of failed sign-ins.

Without this, a login endpoint answers wrong passwords as fast as the
server can hash them, so anyone can try a stolen email address against
millions of passwords. The limiter counts WRONG passwords per
(client address, email) and, once a pair has failed too often within
the window, refuses further attempts for that pair until the oldest
failures age out — even with the right password, which is the point.
A successful sign-in clears the pair's count.

Design notes, so the trade-offs are not rediscovered the hard way:

* In-memory, per process. Correct for one server instance (the MVP
  deployment). With several instances each keeps its own counts, so the
  effective limit multiplies; the fix then is a shared store (Redis) —
  `LoginAttemptLimiter` is the only thing that would change.
* Keyed by (address, email), not by address alone. A limit per address
  across every email would be easy to hit by accident and, behind a proxy
  that hides real client addresses, would lock out the whole site at
  once. The cost: credential stuffing across many different emails from
  one address is not slowed by this layer.
* The address must be the real client's. Behind a reverse proxy (Render,
  nginx) that means telling uvicorn to trust the proxy's forwarded
  headers (FORWARDED_ALLOW_IPS); otherwise every visitor shares the
  proxy's address and one attacker could lock any account out. See the
  deployment notes in the README.
* The clock is injected (`time.monotonic` by default) so tests can move
  time without sleeping.
"""

import math
import time
from collections import deque
from collections.abc import Callable

from app.core.config import settings
from app.core.exceptions import TalignError


class TooManyLoginAttemptsError(TalignError):
    http_status = 429

    def __init__(self, retry_after_seconds: int) -> None:
        minutes = max(1, math.ceil(retry_after_seconds / 60))
        super().__init__(
            f"Too many failed sign-in attempts. Try again in {minutes} "
            f"{'minute' if minutes == 1 else 'minutes'}."
        )
        self.headers = {"Retry-After": str(retry_after_seconds)}


class LoginAttemptLimiter:
    def __init__(
        self,
        *,
        max_failures: int,
        window_seconds: int,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_failures = max_failures
        self._window = window_seconds
        self._clock = clock
        self._failures: dict[str, deque[float]] = {}

    @staticmethod
    def key(client_address: str | None, email: str) -> str:
        return f"{client_address or 'unknown'}|{email.strip().lower()}"

    def check(self, key: str) -> None:
        """Raise TooManyLoginAttemptsError if this pair is currently locked out."""
        failures = self._recent(key)
        if len(failures) >= self._max_failures:
            retry_after = math.ceil(failures[0] + self._window - self._clock())
            raise TooManyLoginAttemptsError(max(1, retry_after))

    def record_failure(self, key: str) -> None:
        self._recent(key)
        self._failures.setdefault(key, deque()).append(self._clock())

    def reset(self, key: str) -> None:
        self._failures.pop(key, None)

    def clear(self) -> None:
        """Forget everything (used by tests)."""
        self._failures.clear()

    def _recent(self, key: str) -> deque[float]:
        """Drop failures that have aged out of the window; forget empty keys."""
        failures = self._failures.get(key)
        if failures is None:
            return deque()
        cutoff = self._clock() - self._window
        while failures and failures[0] <= cutoff:
            failures.popleft()
        if not failures:
            del self._failures[key]
            return deque()
        return failures


login_limiter = LoginAttemptLimiter(
    max_failures=settings.login_max_failed_attempts,
    window_seconds=settings.login_lockout_window_seconds,
)

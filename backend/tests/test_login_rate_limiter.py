"""
The login limiter, tested with an injected clock — no sleeping, so a
15-minute window is checked in microseconds.
"""

import pytest

from app.core.login_rate_limiter import LoginAttemptLimiter, TooManyLoginAttemptsError


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def limiter(clock: FakeClock) -> LoginAttemptLimiter:
    return LoginAttemptLimiter(max_failures=3, window_seconds=600, clock=clock)


KEY = LoginAttemptLimiter.key("10.0.0.1", "sam@example.com")


def test_attempts_below_the_limit_are_allowed(limiter: LoginAttemptLimiter) -> None:
    limiter.record_failure(KEY)
    limiter.record_failure(KEY)
    limiter.check(KEY)  # two failures of three allowed: still fine


def test_reaching_the_limit_locks_the_pair_out(limiter: LoginAttemptLimiter) -> None:
    for _ in range(3):
        limiter.record_failure(KEY)

    with pytest.raises(TooManyLoginAttemptsError) as excinfo:
        limiter.check(KEY)

    assert excinfo.value.http_status == 429
    assert "Too many failed sign-in attempts" in excinfo.value.message


def test_the_error_says_how_long_to_wait(limiter: LoginAttemptLimiter, clock: FakeClock) -> None:
    for _ in range(3):
        limiter.record_failure(KEY)
    clock.advance(90)

    with pytest.raises(TooManyLoginAttemptsError) as excinfo:
        limiter.check(KEY)

    # first failure was 90s ago in a 600s window: 510s left
    assert excinfo.value.headers == {"Retry-After": "510"}
    assert "9 minutes" in excinfo.value.message


def test_a_single_minute_reads_naturally() -> None:
    assert "1 minute." in TooManyLoginAttemptsError(30).message


def test_the_lockout_ends_when_old_failures_age_out(
    limiter: LoginAttemptLimiter, clock: FakeClock
) -> None:
    for _ in range(3):
        limiter.record_failure(KEY)
    clock.advance(601)

    limiter.check(KEY)  # window passed: allowed again


def test_failures_age_out_one_by_one(limiter: LoginAttemptLimiter, clock: FakeClock) -> None:
    limiter.record_failure(KEY)  # t=0
    clock.advance(400)
    limiter.record_failure(KEY)  # t=400
    limiter.record_failure(KEY)  # t=400  -> locked
    with pytest.raises(TooManyLoginAttemptsError):
        limiter.check(KEY)

    clock.advance(201)  # t=601: the first failure aged out, two remain
    limiter.check(KEY)


def test_a_successful_login_clears_the_count(limiter: LoginAttemptLimiter) -> None:
    limiter.record_failure(KEY)
    limiter.record_failure(KEY)
    limiter.reset(KEY)
    limiter.record_failure(KEY)
    limiter.record_failure(KEY)

    limiter.check(KEY)  # would be locked (4 failures) without the reset


def test_pairs_are_independent(limiter: LoginAttemptLimiter) -> None:
    other_email = LoginAttemptLimiter.key("10.0.0.1", "someone-else@example.com")
    other_address = LoginAttemptLimiter.key("10.0.0.2", "sam@example.com")
    for _ in range(3):
        limiter.record_failure(KEY)

    limiter.check(other_email)
    limiter.check(other_address)
    with pytest.raises(TooManyLoginAttemptsError):
        limiter.check(KEY)


def test_email_case_and_whitespace_do_not_dodge_the_limit() -> None:
    assert LoginAttemptLimiter.key("1.1.1.1", " Sam@Example.COM ") == LoginAttemptLimiter.key(
        "1.1.1.1", "sam@example.com"
    )


def test_an_unknown_address_is_still_throttled() -> None:
    assert LoginAttemptLimiter.key(None, "a@b.c") == "unknown|a@b.c"


def test_idle_keys_do_not_accumulate(limiter: LoginAttemptLimiter, clock: FakeClock) -> None:
    limiter.record_failure(KEY)
    clock.advance(601)
    limiter.check(KEY)  # expiring prunes the key

    assert limiter._failures == {}

"""Tests for app.core.security — no DB or app context needed."""

import uuid

import pytest

from app.core.exceptions import InvalidTokenError
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_round_trip() -> None:
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_round_trip() -> None:
    user_id = uuid.uuid4()
    company_id = uuid.uuid4()
    token = create_access_token(
        user_id=user_id, company_id=company_id, account_type="internal", roles=["admin"]
    )
    payload = decode_token(token, expected_type=TokenType.ACCESS)

    assert payload["sub"] == str(user_id)
    assert payload["company_id"] == str(company_id)
    assert payload["account_type"] == "internal"
    assert payload["roles"] == ["admin"]


def test_refresh_token_round_trip() -> None:
    user_id = uuid.uuid4()
    token = create_refresh_token(user_id=user_id)
    payload = decode_token(token, expected_type=TokenType.REFRESH)
    assert payload["sub"] == str(user_id)


def test_decode_rejects_wrong_token_type() -> None:
    user_id = uuid.uuid4()
    access_token = create_access_token(
        user_id=user_id, company_id=None, account_type="candidate", roles=["candidate"]
    )
    with pytest.raises(InvalidTokenError):
        decode_token(access_token, expected_type=TokenType.REFRESH)


def test_decode_rejects_garbage_token() -> None:
    with pytest.raises(InvalidTokenError):
        decode_token("not-a-real-token", expected_type=TokenType.ACCESS)

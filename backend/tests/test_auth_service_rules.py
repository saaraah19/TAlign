"""
Tests for the company-assignment rule enforcement (service-layer half).

`AuthService._assert_company_assignment_valid` is tested directly and in
isolation — it's a pure function of (account_type, company_id) with no
I/O, which is exactly why the rule was factored out as a staticmethod
rather than being inlined into `_register_user`. This is the payoff of
that separation: no database, no fixtures, no mocking required.

The DB-level half (ck_users_company_assignment) is exercised separately
once a real Postgres instance is available — see
docs/01_slice1_authentication.md "Verifying Slice 1".
"""

import uuid

import pytest

from app.core.exceptions import InvalidCompanyAssignmentError
from app.core.roles import AccountType
from app.services.auth_service import AuthService


def test_candidate_with_company_id_is_rejected() -> None:
    with pytest.raises(InvalidCompanyAssignmentError):
        AuthService._assert_company_assignment_valid(
            account_type=AccountType.CANDIDATE, company_id=uuid.uuid4()
        )


def test_candidate_without_company_id_is_accepted() -> None:
    AuthService._assert_company_assignment_valid(
        account_type=AccountType.CANDIDATE, company_id=None
    )  # does not raise


def test_internal_user_without_company_id_is_rejected() -> None:
    with pytest.raises(InvalidCompanyAssignmentError):
        AuthService._assert_company_assignment_valid(
            account_type=AccountType.INTERNAL, company_id=None
        )


def test_internal_user_with_company_id_is_accepted() -> None:
    AuthService._assert_company_assignment_valid(
        account_type=AccountType.INTERNAL, company_id=uuid.uuid4()
    )  # does not raise

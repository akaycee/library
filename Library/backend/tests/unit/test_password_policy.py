import pytest

from src.core.password_policy import PasswordPolicyError, validate_password


def test_accepts_valid_password():
    validate_password("abcd1234")


@pytest.mark.parametrize("bad", ["short1", "aaaaaaaa", "12345678", ""])
def test_rejects_weak_passwords(bad):
    with pytest.raises(PasswordPolicyError):
        validate_password(bad)

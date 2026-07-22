import pytest

from src.core.username import UsernameError, normalize_username, validate_username


def test_normalize_trims_and_casefolds():
    assert normalize_username("  Alice  ") == "alice"


def test_validate_rejects_empty():
    with pytest.raises(UsernameError):
        validate_username("   ")


def test_validate_rejects_disallowed_chars():
    with pytest.raises(UsernameError):
        validate_username("alice space")
    with pytest.raises(UsernameError):
        validate_username("a@b")


def test_validate_rejects_too_long():
    with pytest.raises(UsernameError):
        validate_username("a" * 64)


def test_validate_returns_display_and_normalized():
    display, normalized = validate_username("Bob.Smith_1")
    assert display == "Bob.Smith_1"
    assert normalized == "bob.smith_1"

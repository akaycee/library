from src.core.security import (
    generate_token,
    hash_password,
    hash_token,
    verify_password,
)


def test_password_hash_roundtrip():
    h = hash_password("correct horse1")
    assert h != "correct horse1"
    assert verify_password("correct horse1", h)
    assert not verify_password("wrong", h)


def test_token_is_opaque_and_hashed():
    t = generate_token()
    assert len(t) > 20
    assert hash_token(t) == hash_token(t)
    assert hash_token(t) != t


def test_throttle_locks_after_threshold(monkeypatch):
    from src.core.config import get_settings
    from src.services.throttle import LoginThrottle

    settings = get_settings()
    throttle = LoginThrottle()
    user, client = "alice", "1.2.3.4"
    for _ in range(settings.login_max_failures):
        assert not throttle.is_locked(user, client)
        throttle.record_failure(user, client)
    assert throttle.is_locked(user, client)
    # Different client for the same account is not locked (keyed by both).
    assert not throttle.is_locked(user, "9.9.9.9")
    throttle.reset(user, client)
    assert not throttle.is_locked(user, client)

"""Bootstrap setup command is idempotent and safe."""

from sqlalchemy import func, select

from src.models.base import Role
from src.models.user import User


def test_setup_creates_admin_only_when_no_users(db_session, monkeypatch):
    from src.core import setup

    # Force non-interactive generated password path.
    monkeypatch.setattr(setup, "create_all", lambda: None)
    monkeypatch.setattr(setup, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(setup.sys.stdin, "isatty", lambda: False, raising=False)

    setup.run(username="admin")
    admins = db_session.scalars(select(User).where(User.role == Role.administrator)).all()
    assert len(admins) == 1
    assert admins[0].force_password_change is True

    # Re-run is a no-op.
    setup.run(username="admin")
    total = db_session.scalar(select(func.count()).select_from(User))
    assert total == 1

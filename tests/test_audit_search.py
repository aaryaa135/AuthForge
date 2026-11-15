from app.db.session import SessionLocal
from app.modules.audit.models import AuditLog
from app.modules.audit.repository import AuditRepository
from app.modules.users.models import User


def _seed_user(db, email="audituser@example.com"):
    user = db.execute(
        __import__("sqlalchemy").select(User).where(User.email == email)
    ).scalar_one_or_none()
    if user is None:
        user = User(
            email=email,
            username="audituser",
            hashed_password="h",
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def test_audit_repository_search_filter_sort():
    db = SessionLocal()
    try:
        user = _seed_user(db)
        repo = AuditRepository(db)

        logs = [
            AuditLog(
                user_id=user.id,
                action="LOGIN",
                success=True,
                ip_address="1.2.3.4",
            ),
            AuditLog(
                user_id=user.id,
                action="LOGOUT",
                success=True,
                ip_address="1.2.3.4",
            ),
            AuditLog(
                user_id=None,
                action="REGISTER",
                success=False,
                ip_address="5.6.7.8",
            ),
        ]
        for log in logs:
            db.add(log)
        db.commit()

        # search by action
        items, total = repo.get_paginated(search="LOGIN")
        assert total == 1
        assert items[0].action == "LOGIN"

        # exact action filter
        items, total = repo.get_paginated(action="LOGOUT")
        assert total == 1

        # success filter
        items, total = repo.get_paginated(success=False)
        assert total == 1
        assert items[0].action == "REGISTER"

        # user_id filter
        items, total = repo.get_paginated(user_id=user.id)
        assert total == 2

        # sort asc by action
        items, _ = repo.get_paginated(sort_by="action", sort_order="asc")
        assert [log.action for log in items] == ["LOGIN", "LOGOUT", "REGISTER"]

        # pagination
        items, total = repo.get_paginated(offset=0, limit=1)
        assert total == 3
        assert len(items) == 1
    finally:
        db.close()

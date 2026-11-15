from app.db.session import SessionLocal
from app.modules.roles.models import Role
from app.modules.roles.repository import RoleRepository
from app.modules.users.models import User
from app.modules.users.repository import UserRepository


def _seed_roles_and_users(db):
    for name in ["Admin", "User", "Manager"]:
        if RoleRepository(db).get_by_name(name) is None:
            db.add(Role(name=name, description=f"{name} role"))
    db.commit()

    users = [
        User(
            email="alice@example.com",
            username="alice",
            hashed_password="h",
            role_id=RoleRepository(db).get_by_name("Admin").id,
            is_active=True,
            is_verified=True,
        ),
        User(
            email="bob@example.com",
            username="bob",
            hashed_password="h",
            role_id=RoleRepository(db).get_by_name("User").id,
            is_active=True,
            is_verified=False,
        ),
        User(
            email="carol@example.com",
            username="carol_inactive",
            hashed_password="h",
            role_id=RoleRepository(db).get_by_name("User").id,
            is_active=False,
            is_verified=True,
        ),
    ]
    for u in users:
        db.add(u)
    db.commit()
    return users


def test_user_repository_search_filter_sort():
    db = SessionLocal()
    try:
        _seed_roles_and_users(db)
        repo = UserRepository(db)

        # search by email
        items, total = repo.get_paginated(search="alice")
        assert total == 1
        assert items[0].email == "alice@example.com"

        # search by username
        items, total = repo.get_paginated(search="bob")
        assert total == 1

        # role filter
        items, total = repo.get_paginated(role="Admin")
        assert total == 1
        assert items[0].email == "alice@example.com"

        # is_active filter
        items, total = repo.get_paginated(is_active=False)
        assert total == 1
        assert items[0].email == "carol@example.com"

        # sort asc by username
        items, _ = repo.get_paginated(sort_by="username", sort_order="asc")
        assert [u.username for u in items] == ["alice", "bob", "carol_inactive"]

        # pagination
        items, total = repo.get_paginated(offset=0, limit=1)
        assert total == 3
        assert len(items) == 1
    finally:
        db.close()

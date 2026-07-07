import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import os

from app.db.session import SessionLocal
from app.core.security import get_password_hash
from app.modules.roles.models import Role
from app.modules.users.models import User


ADMIN_EMAIL = os.getenv("TEST_ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("TEST_ADMIN_PASSWORD")


def seed_admin():
    db = SessionLocal()

    admin_role = db.query(Role).filter(Role.name == "Admin").first()

    if admin_role is None:
        print("Admin role not found.")
        return

    existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()

    if existing:
        print("Admin already exists.")
        return

    admin = User(
        email=ADMIN_EMAIL,
        username="admin",
        hashed_password=get_password_hash(ADMIN_PASSWORD),
        is_active=True,
        is_verified=True,
        role_id=admin_role.id,
    )

    db.add(admin)
    db.commit()

    print("Admin created successfully.")


if __name__ == "__main__":
    seed_admin()

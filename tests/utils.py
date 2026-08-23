import os

from dotenv import load_dotenv
from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.modules.roles.models import Role
from app.modules.users.models import User

load_dotenv(".env.test")


def create_test_admin():
    db = SessionLocal()

    try:
        admin = db.execute(
            select(User).where(User.email == os.getenv("TEST_ADMIN_EMAIL"))
        ).scalar_one_or_none()

        if admin:
            return admin

        role = db.execute(select(Role).where(Role.name == "Admin")).scalar_one()

        admin = User(
            email=os.getenv("TEST_ADMIN_EMAIL"),
            username="admin",
            hashed_password=hash_password(os.getenv("TEST_ADMIN_PASSWORD")),
            is_active=True,
            is_verified=True,
            role_id=role.id,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        return admin

    finally:
        db.close()

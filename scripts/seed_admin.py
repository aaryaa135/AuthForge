import os

from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv(".env.test", override=False)

from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.modules.roles.models import Role  # noqa: E402
from app.modules.users.models import User  # noqa: E402

ADMIN_EMAIL = os.getenv("TEST_ADMIN_EMAIL") or os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("TEST_ADMIN_PASSWORD") or os.getenv("ADMIN_PASSWORD")


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

    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        print("TEST_ADMIN_EMAIL / TEST_ADMIN_PASSWORD not set. Check .env/.env.test")
        return

    admin = User(
        email=ADMIN_EMAIL,
        username="admin",
        hashed_password=hash_password(ADMIN_PASSWORD),
        is_active=True,
        is_verified=True,
        role_id=admin_role.id,
    )

    db.add(admin)
    db.commit()

    print("Admin created successfully.")


if __name__ == "__main__":
    seed_admin()

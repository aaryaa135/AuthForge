from sqlalchemy import select

from app.db.session import SessionLocal
from app.modules.roles.models import Role


DEFAULT_ROLES = [
    {
        "name": "Admin",
        "description": "System Administrator",
    },
    {
        "name": "Manager",
        "description": "Manager",
    },
    {
        "name": "User",
        "description": "Default User",
    },
]


def seed_roles():
    db = SessionLocal()

    try:
        for role_data in DEFAULT_ROLES:
            existing_role = db.execute(
                select(Role).where(Role.name == role_data["name"])
            ).scalar_one_or_none()

            if not existing_role:
                db.add(Role(**role_data))

        db.commit()

        print("✅ Roles seeded successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_roles()

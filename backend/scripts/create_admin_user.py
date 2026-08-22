"""CLI to create the initial admin user.

Usage: uv run scripts/create_admin_user.py

Non-interactive mode: if both ADMIN_EMAIL and ADMIN_PASSWORD environment
variables are set, the user is created without prompting (useful for Docker
Compose initialization). Otherwise, falls back to the interactive prompts.
"""

import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session, select

from app.auth.password import hash_password
from app.db import engine, init_db
from app.models.user import User


def main() -> None:
    init_db()

    env_email = os.environ.get("ADMIN_EMAIL")
    env_password = os.environ.get("ADMIN_PASSWORD")

    if env_email and env_password:
        email = env_email.strip()
        password = env_password
    else:
        email = input("Email: ").strip()
        password = getpass.getpass("Password: ")

    with Session(engine) as session:
        existing = session.exec(select(User).where(User.email == email)).first()
        if existing is not None:
            print(f"User {email} already exists.", file=sys.stderr)
            sys.exit(1)

        user = User(email=email, password_hash=hash_password(password))
        session.add(user)
        session.commit()
        print(f"Created user {email}.")


if __name__ == "__main__":
    main()

"""CLI to create the initial admin user.

Usage: uv run scripts/create_admin_user.py

Non-interactive mode: if both the ADMIN_EMAIL and ADMIN_PASSWORD environment
variables are set, the script runs without prompting (useful for Docker
Compose initialization). Otherwise it falls back to the interactive prompts.
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
    non_interactive = bool(env_email and env_password)

    if non_interactive and env_email is not None and env_password is not None:
        email = env_email.strip()
        password = env_password
    else:
        email = input("Email: ").strip()
        password = getpass.getpass("Password: ")

    with Session(engine) as session:
        existing = session.exec(select(User).where(User.email == email)).first()
        if existing is not None:
            # In non-interactive mode this script may run on every container
            # startup, so an existing user is not an error: skip silently.
            if non_interactive:
                print(f"User {email} already exists; skipping.")
                return
            print(f"User {email} already exists.", file=sys.stderr)
            sys.exit(1)

        user = User(email=email, password_hash=hash_password(password))
        session.add(user)
        session.commit()
        print(f"Created user {email}.")


if __name__ == "__main__":
    main()

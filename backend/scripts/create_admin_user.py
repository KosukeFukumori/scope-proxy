"""CLI to create the initial admin user.

Usage: uv run scripts/create_admin_user.py

Non-interactive mode: if both the ADMIN_USERNAME and ADMIN_PASSWORD environment
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

    env_username = os.environ.get("ADMIN_USERNAME")
    env_password = os.environ.get("ADMIN_PASSWORD")
    non_interactive = bool(env_username and env_password)

    if non_interactive and env_username is not None and env_password is not None:
        username = env_username.strip()
        password = env_password
    else:
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")

    with Session(engine) as session:
        existing = session.exec(select(User).where(User.username == username)).first()
        if existing is not None:
            # In non-interactive mode this script may run on every container
            # startup, so an existing user is not an error: skip silently.
            if non_interactive:
                print(f"User {username} already exists; skipping.")
                return
            print(f"User {username} already exists.", file=sys.stderr)
            sys.exit(1)

        user = User(username=username, password_hash=hash_password(password))
        session.add(user)
        session.commit()
        print(f"Created user {username}.")


if __name__ == "__main__":
    main()

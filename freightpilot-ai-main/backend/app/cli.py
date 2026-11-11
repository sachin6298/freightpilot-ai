"""Operational CLI commands for controlled administrative bootstrap."""
import argparse
import getpass

from app.core.security import hash_password, normalize_email
from app.db.models import User
from app.db.session import SessionLocal


def create_admin(email: str) -> None:
    normalized = normalize_email(email)
    password = getpass.getpass("Admin password (minimum 10 characters): ")
    confirmation = getpass.getpass("Confirm admin password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")
    password_hash = hash_password(password)
    with SessionLocal() as db:
        if db.query(User).filter(User.email == normalized).first():
            raise SystemExit("An account with this email already exists. Use a controlled role-change procedure instead.")
        user = User(email=normalized, password_hash=password_hash, role="ADMIN", is_active=True,
                    email_verified=True, phone_verified=False)
        db.add(user)
        db.commit()
    print(f"Administrator account created: {normalized}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="freightpilot-admin")
    sub = parser.add_subparsers(dest="command", required=True)
    admin_parser = sub.add_parser("create-admin", help="Create the initial administrator account")
    admin_parser.add_argument("--email", required=True)
    args = parser.parse_args()
    if args.command == "create-admin":
        create_admin(args.email)


if __name__ == "__main__":
    main()

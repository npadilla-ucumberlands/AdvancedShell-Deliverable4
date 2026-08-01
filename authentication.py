"""User authentication system for Advanced Shell - Deliverable 4."""

from __future__ import annotations

import getpass
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AuthenticatedUser:
    """Represents the user currently authenticated in the shell."""

    username: str
    role: str


class AuthenticationManager:
    """Loads user accounts and authenticates shell users."""

    DEFAULT_USERS = {
        "admin": {
            "password": "Admin123!",
            "role": "admin",
        },
        "student": {
            "password": "Student123!",
            "role": "standard",
        },
    }

    def __init__(self, users_file: str = "users.json") -> None:
        self.users_file = Path(users_file)
        self.current_user: AuthenticatedUser | None = None
        self._ensure_users_file()

    @staticmethod
    def _hash_password(password: str, salt: bytes) -> str:
        """Hash a password with PBKDF2-HMAC-SHA256."""
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            200_000,
        )
        return digest.hex()

    def _create_account_record(
        self,
        password: str,
        role: str,
    ) -> dict[str, str]:
        salt = os.urandom(16)

        return {
            "salt": salt.hex(),
            "password_hash": self._hash_password(password, salt),
            "role": role,
        }

    def _ensure_users_file(self) -> None:
        """Create default demonstration accounts when none exist."""
        if self.users_file.exists():
            return

        users: dict[str, dict[str, str]] = {}

        for username, account in self.DEFAULT_USERS.items():
            users[username] = self._create_account_record(
                password=account["password"],
                role=account["role"],
            )

        data = {"users": users}

        try:
            self.users_file.write_text(
                json.dumps(data, indent=4),
                encoding="utf-8",
            )
        except OSError as exc:
            raise RuntimeError(
                f"Unable to create {self.users_file}: {exc}"
            ) from exc

    def _load_users(self) -> dict[str, Any]:
        try:
            data = json.loads(
                self.users_file.read_text(encoding="utf-8")
            )
        except FileNotFoundError as exc:
            raise RuntimeError("The user database was not found.") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"The user database contains invalid JSON: {exc}"
            ) from exc
        except OSError as exc:
            raise RuntimeError(
                f"Unable to read the user database: {exc}"
            ) from exc

        users = data.get("users")

        if not isinstance(users, dict):
            raise RuntimeError(
                "The user database does not contain a valid users section."
            )

        return users

    def authenticate(
        self,
        username: str,
        password: str,
    ) -> AuthenticatedUser | None:
        """Validate a username and password."""
        users = self._load_users()
        account = users.get(username)

        if not isinstance(account, dict):
            return None

        try:
            salt = bytes.fromhex(account["salt"])
            expected_hash = account["password_hash"]
            role = account["role"]
        except (KeyError, TypeError, ValueError):
            return None

        supplied_hash = self._hash_password(password, salt)

        if not hmac.compare_digest(supplied_hash, expected_hash):
            return None

        user = AuthenticatedUser(
            username=username,
            role=role,
        )
        self.current_user = user
        return user

    def login(self, maximum_attempts: int = 3) -> AuthenticatedUser | None:
        """Prompt for credentials until login succeeds or attempts expire."""
        print("User Authentication")
        print("-------------------")

        for attempt in range(1, maximum_attempts + 1):
            try:
                username = input("Username: ").strip()
                password = getpass.getpass("Password: ")
            except (EOFError, KeyboardInterrupt):
                print()
                return None

            user = self.authenticate(username, password)

            if user is not None:
                print(
                    f"Authentication successful. "
                    f"Welcome, {user.username}."
                )
                print(f"Permission level: {user.role}")
                return user

            remaining = maximum_attempts - attempt
            print("Authentication failed: invalid username or password.")

            if remaining:
                print(f"Attempts remaining: {remaining}\n")

        print("Maximum login attempts exceeded.")
        return None

    def logout(self) -> None:
        """Clear the current authenticated session."""
        self.current_user = None
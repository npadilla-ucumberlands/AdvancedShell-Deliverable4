"""Role-based file permissions for Advanced Shell - Deliverable 4."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from authentication import AuthenticatedUser


PermissionAction = Literal["read", "write", "execute"]


@dataclass(frozen=True)
class PermissionDecision:
    """Describes whether a file operation is permitted."""

    allowed: bool
    reason: str


class FilePermissionManager:
    """Simulates file access restrictions based on users and roles."""

    DEFAULT_CONFIGURATION = {
        "protected_paths": {
            "test_files/system_config.txt": {
                "owner": "admin",
                "admin": ["read", "write", "execute"],
                "standard": ["read"],
            },
            "test_files/admin_script.py": {
                "owner": "admin",
                "admin": ["read", "write", "execute"],
                "standard": [],
            },
            "test_files/public.txt": {
                "owner": "admin",
                "admin": ["read", "write", "execute"],
                "standard": ["read", "write"],
            },
        }
    }

    def __init__(
        self,
        permissions_file: str = "file_permissions.json",
    ) -> None:
        self.permissions_file = Path(permissions_file)
        self._ensure_permissions_file()

    def _ensure_permissions_file(self) -> None:
        if self.permissions_file.exists():
            return

        try:
            self.permissions_file.write_text(
                json.dumps(
                    self.DEFAULT_CONFIGURATION,
                    indent=4,
                ),
                encoding="utf-8",
            )
        except OSError as exc:
            raise RuntimeError(
                f"Unable to create {self.permissions_file}: {exc}"
            ) from exc

    def _load_configuration(self) -> dict:
        try:
            return json.loads(
                self.permissions_file.read_text(encoding="utf-8")
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                "The file-permission database was not found."
            ) from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Invalid permission database: {exc}"
            ) from exc
        except OSError as exc:
            raise RuntimeError(
                f"Unable to read permission database: {exc}"
            ) from exc

    @staticmethod
    def _normalize_path(path: Path) -> str:
        """Produce a normalized, portable relative-path representation."""
        resolved = path.expanduser().resolve()
        current = Path.cwd().resolve()

        try:
            relative = resolved.relative_to(current)
            return relative.as_posix()
        except ValueError:
            return resolved.as_posix()

    def check(
        self,
        user: AuthenticatedUser,
        path: Path,
        action: PermissionAction,
    ) -> PermissionDecision:
        """Check whether a user may perform an operation on a path."""
        if user.role == "admin":
            return PermissionDecision(
                allowed=True,
                reason="administrators have full simulated access",
            )

        configuration = self._load_configuration()
        protected_paths = configuration.get("protected_paths", {})
        normalized_path = self._normalize_path(path)
        rule = protected_paths.get(normalized_path)

        # Files without an explicit rule use normal standard-user access.
        if not isinstance(rule, dict):
            return PermissionDecision(
                allowed=True,
                reason="no simulated restriction applies",
            )

        role_permissions = rule.get(user.role, [])

        if action in role_permissions:
            return PermissionDecision(
                allowed=True,
                reason=(
                    f"the {user.role} role includes "
                    f"{action} permission"
                ),
            )

        return PermissionDecision(
            allowed=False,
            reason=(
                f"the {user.role} role does not have "
                f"{action} permission for {normalized_path}"
            ),
        )

    def require(
        self,
        user: AuthenticatedUser,
        path: Path,
        action: PermissionAction,
    ) -> bool:
        """Print an access-denied message when permission is absent."""
        decision = self.check(user, path, action)

        if decision.allowed:
            return True

        print(
            f"security: access denied for user '{user.username}'\n"
            f"security: requested operation: {action}\n"
            f"security: reason: {decision.reason}"
        )
        return False

    def describe(
        self,
        user: AuthenticatedUser,
        path: Path,
    ) -> str:
        """Return the current user's simulated permissions for a file."""
        normalized_path = self._normalize_path(path)
        permissions = []

        for action in ("read", "write", "execute"):
            decision = self.check(user, path, action)

            if decision.allowed:
                permissions.append(action)

        permission_text = ", ".join(permissions) if permissions else "none"

        return (
            f"Path        : {normalized_path}\n"
            f"User        : {user.username}\n"
            f"Role        : {user.role}\n"
            f"Permissions : {permission_text}"
        )
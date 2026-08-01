"""Advanced Shell - Deliverable 4.

A secure Unix-like shell simulation with built-in commands, foreground
and background process execution, job tracking, CPU scheduling, memory
management, process synchronization, command piping, authentication,
and role-based file permissions.
"""

from __future__ import annotations

import os
import shlex
import sys

from authentication import AuthenticatedUser, AuthenticationManager
from commands import BuiltInCommands
from jobs import JobTable
from permissions import FilePermissionManager
from piping import PipelineExecutor
from process_manager import ProcessManager


class AdvancedShell:
    """Main command loop for the integrated secure shell."""

    def __init__(self) -> None:
        self.running = True
        self.current_user: AuthenticatedUser | None = None

        self.authentication = AuthenticationManager()
        self.permission_manager = FilePermissionManager()

        self.jobs = JobTable()
        self.process_manager = ProcessManager(self.jobs)

        self.builtins = BuiltInCommands(
            jobs=self.jobs,
            process_manager=self.process_manager,
            exit_callback=self.stop,
        )

        # These objects are assigned here so the existing command class
        # remains compatible while Deliverable 4 security commands are added.
        self.builtins.current_user = None
        self.builtins.permission_manager = self.permission_manager

        self.pipeline_executor = PipelineExecutor(
            builtin_executor=self.builtins.execute,
        )

    def stop(self) -> None:
        active_jobs = self.jobs.active_jobs()

        if active_jobs:
            print(
                f"Warning: {len(active_jobs)} background job(s) "
                "are still active."
            )

        self.running = False

    def prompt(self) -> str:
        current_directory = os.path.basename(os.getcwd()) or os.getcwd()

        if self.current_user is None:
            identity = "unauthenticated"
        else:
            identity = (
                f"{self.current_user.username}"
                f"({self.current_user.role})"
            )

        return f"AdvancedShell:{identity}:{current_directory}$ "

    @staticmethod
    def parse_command(command_line: str) -> tuple[list[str], bool]:
        """Split a command line and detect a trailing background operator."""
        try:
            if os.name == "nt":
                parts = shlex.split(command_line, posix=False)
                parts = [part.strip('"') for part in parts]
            else:
                parts = shlex.split(command_line)
        except ValueError as exc:
            print(f"shell: parsing error: {exc}")
            return [], False

        background = bool(parts and parts[-1] == "&")

        if background:
            parts.pop()

        return parts, background

    def execute_line(self, command_line: str) -> None:
        command_line = command_line.strip()

        if not command_line:
            return

        if "|" in command_line:
            if command_line.rstrip().endswith("&"):
                print(
                    "shell: background execution of pipelines "
                    "is not supported"
                )
                return

            self.pipeline_executor.execute(command_line)
            return

        parts, background = self.parse_command(command_line)

        if not parts:
            return

        command, *args = parts

        if self.builtins.execute(command, args):
            if background:
                print(
                    f"shell: built-in command '{command}' runs inside "
                    "the shell and cannot be placed in the background"
                )
            return

        display_command = " ".join(parts)

        self.process_manager.start_process(
            command_parts=parts,
            command_text=display_command,
            background=background,
        )

    def authenticate_user(self) -> bool:
        """Require a successful login before shell access."""
        user = self.authentication.login()

        if user is None:
            return False

        self.current_user = user
        self.builtins.current_user = user
        return True

    def run(self) -> None:
        print("=" * 60)
        print("Advanced Shell - Deliverable 4")
        print("Integration and Security Implementation")
        print("=" * 60)
        print(
            "Includes process management, CPU scheduling, paging, "
            "synchronization, command piping, authentication, and "
            "role-based file permissions."
        )
        print()

        if not self.authenticate_user():
            print("Shell access denied.")
            return

        print()
        print("Type 'help' to view commands.")
        print("Use 'exit' to terminate the shell.\n")

        while self.running:
            try:
                command_line = input(self.prompt())
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print()
                continue

            self.execute_line(command_line)

        self.authentication.logout()
        self.current_user = None
        print("Shell terminated. User session closed.")


def main() -> int:
    shell = AdvancedShell()

    try:
        shell.run()
    except Exception as exc:
        print(f"Fatal shell error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
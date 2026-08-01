"""Command piping support for Advanced Shell - Deliverable 4."""

from __future__ import annotations

import contextlib
import io
import os
import shlex
import subprocess
from typing import Callable, Sequence


BuiltinExecutor = Callable[[str, Sequence[str]], bool]


class PipelineExecutor:
    """Executes commands connected by one or more pipe operators."""

    def __init__(self, builtin_executor: BuiltinExecutor) -> None:
        self.builtin_executor = builtin_executor

    @staticmethod
    def _parse_stage(stage: str) -> list[str]:
        """Split one pipeline stage into command arguments."""
        if os.name == "nt":
            parts = shlex.split(stage, posix=False)
            return [part.strip('"') for part in parts]

        return shlex.split(stage)

    def execute(self, command_line: str) -> None:
        """Execute all stages in a command pipeline."""
        stages = [
            stage.strip()
            for stage in command_line.split("|")
            if stage.strip()
        ]

        if len(stages) < 2:
            print("pipe: at least two commands are required")
            return

        pipeline_input = ""

        for index, stage in enumerate(stages):
            try:
                parts = self._parse_stage(stage)
            except ValueError as exc:
                print(f"pipe: parsing error: {exc}")
                return

            if not parts:
                print("pipe: empty command stage")
                return

            command, *args = parts

            try:
                pipeline_input = self._execute_stage(
                    command=command,
                    args=args,
                    input_text=pipeline_input,
                    first_stage=index == 0,
                )
            except RuntimeError as exc:
                print(f"pipe: {exc}")
                return

        if pipeline_input:
            print(pipeline_input, end="")

            if not pipeline_input.endswith("\n"):
                print()

    def _execute_stage(
        self,
        command: str,
        args: Sequence[str],
        input_text: str,
        first_stage: bool,
    ) -> str:
        normalized = command.lower()

        # Cross-platform pipeline filters implemented inside the shell.
        if normalized == "grep":
            return self._grep(args, input_text)

        if normalized == "sort":
            return self._sort(args, input_text)

        if normalized in {"count", "wc"}:
            return self._count(args, input_text)

        if normalized == "head":
            return self._head(args, input_text)

        if normalized == "tail":
            return self._tail(args, input_text)

        # Built-in commands print to standard output, so capture their output.
        builtin_output = io.StringIO()

        with contextlib.redirect_stdout(builtin_output):
            handled = self.builtin_executor(command, args)

        if handled:
            output = builtin_output.getvalue()

            if not first_stage and input_text:
                raise RuntimeError(
                    f"built-in command '{command}' does not accept "
                    "pipeline input"
                )

            return output

        # External programs receive previous output through stdin.
        try:
            completed = subprocess.run(
                [command, *args],
                input=input_text if not first_stage else None,
                text=True,
                capture_output=True,
                check=False,
            )
        except FileNotFoundError:
            raise RuntimeError(f"command not found: {command}")
        except PermissionError:
            raise RuntimeError(f"permission denied: {command}")
        except OSError as exc:
            raise RuntimeError(
                f"unable to execute {command}: {exc}"
            ) from exc

        if completed.stderr:
            print(completed.stderr, end="")

        return completed.stdout

    @staticmethod
    def _grep(args: Sequence[str], input_text: str) -> str:
        if len(args) != 1:
            raise RuntimeError("Usage: grep <text>")

        search_text = args[0].lower()
        matches = [
            line
            for line in input_text.splitlines()
            if search_text in line.lower()
        ]

        return "\n".join(matches) + ("\n" if matches else "")

    @staticmethod
    def _sort(args: Sequence[str], input_text: str) -> str:
        reverse = False

        if args:
            if list(args) == ["-r"]:
                reverse = True
            else:
                raise RuntimeError("Usage: sort [-r]")

        lines = input_text.splitlines()
        lines.sort(key=str.lower, reverse=reverse)

        return "\n".join(lines) + ("\n" if lines else "")

    @staticmethod
    def _count(args: Sequence[str], input_text: str) -> str:
        if args:
            raise RuntimeError("Usage: count")

        lines = input_text.splitlines()
        words = input_text.split()
        characters = len(input_text)

        return (
            f"Lines      : {len(lines)}\n"
            f"Words      : {len(words)}\n"
            f"Characters : {characters}\n"
        )

    @staticmethod
    def _head(args: Sequence[str], input_text: str) -> str:
        count = 10

        if args:
            if len(args) != 1:
                raise RuntimeError("Usage: head [line_count]")

            try:
                count = int(args[0])
            except ValueError as exc:
                raise RuntimeError(
                    f"invalid line count: {args[0]}"
                ) from exc

            if count < 0:
                raise RuntimeError("line count cannot be negative")

        lines = input_text.splitlines()[:count]
        return "\n".join(lines) + ("\n" if lines else "")

    @staticmethod
    def _tail(args: Sequence[str], input_text: str) -> str:
        count = 10

        if args:
            if len(args) != 1:
                raise RuntimeError("Usage: tail [line_count]")

            try:
                count = int(args[0])
            except ValueError as exc:
                raise RuntimeError(
                    f"invalid line count: {args[0]}"
                ) from exc

            if count < 0:
                raise RuntimeError("line count cannot be negative")

        lines = input_text.splitlines()

        if count == 0:
            return ""

        selected = lines[-count:]
        return "\n".join(selected) + ("\n" if selected else "")
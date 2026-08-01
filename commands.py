"""Built-in commands for Advanced Shell."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence

from authentication import AuthenticatedUser
from jobs import JobTable
from memory_manager import MemoryManager
from permissions import FilePermissionManager
from process_manager import ProcessManager
from scheduler import Scheduler, SchedulingResult, print_result
from synchronization import ProducerConsumerSimulation


class BuiltInCommands:
    """Implements shell commands handled without launching another program."""

    def __init__(
        self,
        jobs: JobTable,
        process_manager: ProcessManager,
        exit_callback: Callable[[], None],
    ) -> None:
        self.jobs = jobs
        self.process_manager = process_manager
        self.exit_callback = exit_callback

        # Deliverable 2 scheduling simulator.
        self.scheduler = Scheduler(sleep_per_unit=0.05)
        self.last_scheduling_result: SchedulingResult | None = None

        # Deliverable 3 simulators.
        self.memory_manager = MemoryManager()
        self.synchronization = ProducerConsumerSimulation()

        # Deliverable 4 security context. The shell assigns the authenticated
        # user after a successful login.
        self.current_user: AuthenticatedUser | None = None
        self.permission_manager: FilePermissionManager | None = None

    def execute(self, command: str, args: Sequence[str]) -> bool:
        handlers = {
            "cd": self.cd,
            "pwd": self.pwd,
            "exit": self.exit_shell,
            "echo": self.echo,
            "clear": self.clear,
            "cls": self.clear,
            "ls": self.ls,
            "dir": self.ls,
            "cat": self.cat,
            "type": self.cat,
            "mkdir": self.mkdir,
            "rmdir": self.rmdir,
            "rm": self.rm,
            "del": self.rm,
            "touch": self.touch,
            "kill": self.kill,
            "jobs": self.show_jobs,
            "fg": self.fg,
            "bg": self.bg,
            "help": self.help,

            # Deliverable 4 security commands.
            "whoami": self.whoami,
            "permissions": self.show_permissions,
            "write": self.write_file,
            "runfile": self.run_file,

            # Deliverable 2 commands.
            "addproc": self.add_process,
            "psim": self.show_simulated_processes,
            "schedule": self.run_schedule,
            "metrics": self.show_metrics,
            "clearprocs": self.clear_processes,

            # Deliverable 3 memory-management commands.
            "memconfig": self.configure_memory,
            "memalloc": self.allocate_memory,
            "memaccess": self.access_memory,
            "memfree": self.free_memory,
            "memstat": self.show_memory_status,
            "memreset": self.reset_memory,
            "memdemo": self.run_memory_demo,

            # Deliverable 3 synchronization commands.
            "producerconsumer": self.run_producer_consumer,
            "syncstat": self.show_synchronization_status,
        }

        handler = handlers.get(command.lower())
        if handler is None:
            return False

        handler(args)
        return True

    @staticmethod
    def _require_argument(args: Sequence[str], usage: str) -> bool:
        if args:
            return True
        print(f"Usage: {usage}")
        return False

    def _require_permission(
        self,
        path: Path,
        action: str,
    ) -> bool:
        """Check the active user's simulated file permission."""
        if self.current_user is None or self.permission_manager is None:
            print("security: no authenticated user session is available")
            return False

        return self.permission_manager.require(
            self.current_user,
            path,
            action,
        )

    def cd(self, args: Sequence[str]) -> None:
        target = args[0] if args else str(Path.home())

        try:
            os.chdir(Path(target).expanduser())
        except FileNotFoundError:
            print(f"cd: directory not found: {target}")
        except NotADirectoryError:
            print(f"cd: not a directory: {target}")
        except PermissionError:
            print(f"cd: permission denied: {target}")
        except OSError as exc:
            print(f"cd: {exc}")

    @staticmethod
    def pwd(args: Sequence[str]) -> None:
        if args:
            print("pwd: this command does not accept arguments")
            return
        print(Path.cwd())

    def exit_shell(self, args: Sequence[str]) -> None:
        if args:
            print("exit: this command does not accept arguments")
            return
        self.exit_callback()

    @staticmethod
    def echo(args: Sequence[str]) -> None:
        print(" ".join(args))

    @staticmethod
    def clear(args: Sequence[str]) -> None:
        if args:
            print("clear: this command does not accept arguments")
            return
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def ls(args: Sequence[str]) -> None:
        target = Path(args[0]).expanduser() if args else Path.cwd()

        try:
            entries = sorted(
                target.iterdir(),
                key=lambda path: (not path.is_dir(), path.name.lower()),
            )
            for entry in entries:
                suffix = "/" if entry.is_dir() else ""
                print(f"{entry.name}{suffix}")
        except FileNotFoundError:
            print(f"ls: path not found: {target}")
        except NotADirectoryError:
            print(target.name)
        except PermissionError:
            print(f"ls: permission denied: {target}")
        except OSError as exc:
            print(f"ls: {exc}")

    def cat(self, args: Sequence[str]) -> None:
        if not self._require_argument(args, "cat <filename>"):
            return

        for filename in args:
            path = Path(filename).expanduser()

            if not self._require_permission(path, "read"):
                continue

            try:
                content = path.read_text(encoding="utf-8")
                print(content, end="")
                if content and not content.endswith("\n"):
                    print()
            except FileNotFoundError:
                print(f"cat: file not found: {filename}")
            except IsADirectoryError:
                print(f"cat: {filename} is a directory")
            except UnicodeDecodeError:
                print(f"cat: {filename} is not a readable text file")
            except PermissionError:
                print(f"cat: permission denied: {filename}")
            except OSError as exc:
                print(f"cat: {exc}")

    def mkdir(self, args: Sequence[str]) -> None:
        if not self._require_argument(args, "mkdir <directory>"):
            return

        for dirname in args:
            try:
                Path(dirname).expanduser().mkdir()
            except FileExistsError:
                print(f"mkdir: already exists: {dirname}")
            except FileNotFoundError:
                print(f"mkdir: parent directory not found: {dirname}")
            except PermissionError:
                print(f"mkdir: permission denied: {dirname}")
            except OSError as exc:
                print(f"mkdir: {exc}")

    def rmdir(self, args: Sequence[str]) -> None:
        if not self._require_argument(args, "rmdir <directory>"):
            return

        for dirname in args:
            try:
                Path(dirname).expanduser().rmdir()
            except FileNotFoundError:
                print(f"rmdir: directory not found: {dirname}")
            except OSError as exc:
                print(f"rmdir: unable to remove {dirname}: {exc}")

    def rm(self, args: Sequence[str]) -> None:
        if not self._require_argument(args, "rm <filename>"):
            return

        for filename in args:
            path = Path(filename).expanduser()

            if not self._require_permission(path, "write"):
                continue

            try:
                if path.is_dir():
                    print(
                        f"rm: {filename} is a directory; "
                        "use rmdir for empty directories"
                    )
                else:
                    path.unlink()
            except FileNotFoundError:
                print(f"rm: file not found: {filename}")
            except PermissionError:
                print(f"rm: permission denied: {filename}")
            except OSError as exc:
                print(f"rm: unable to remove {filename}: {exc}")

    def touch(self, args: Sequence[str]) -> None:
        if not self._require_argument(args, "touch <filename>"):
            return

        for filename in args:
            path = Path(filename).expanduser()

            if not self._require_permission(path, "write"):
                continue

            try:
                path.touch(exist_ok=True)
            except FileNotFoundError:
                print(f"touch: parent directory not found: {filename}")
            except PermissionError:
                print(f"touch: permission denied: {filename}")
            except OSError as exc:
                print(f"touch: {exc}")

    def kill(self, args: Sequence[str]) -> None:
        if not self._require_argument(args, "kill <pid>"):
            return

        try:
            pid = int(args[0])
            if pid <= 0:
                raise ValueError
        except ValueError:
            print(f"kill: invalid PID: {args[0]}")
            return

        if self.process_manager.terminate_pid(pid):
            for job in self.jobs.all_jobs():
                if job.pid == pid:
                    job.status = "Terminated"
                    break

    def show_jobs(self, args: Sequence[str]) -> None:
        if args:
            print("jobs: this command does not accept arguments")
            return

        jobs = self.jobs.all_jobs()
        if not jobs:
            print("No background jobs.")
            return

        for job in jobs:
            print(
                f"[{job.job_id}] {job.status:<12} "
                f"PID={job.pid:<7} {job.command}"
            )

    def fg(self, args: Sequence[str]) -> None:
        if not self._require_argument(args, "fg <job_id>"):
            return

        job_id = self._parse_job_id(args[0], "fg")
        if job_id is None:
            return

        job = self.jobs.get(job_id)
        if job is None:
            print(f"fg: no such job: {job_id}")
            return

        self.process_manager.bring_to_foreground(job)

    def bg(self, args: Sequence[str]) -> None:
        if not self._require_argument(args, "bg <job_id>"):
            return

        job_id = self._parse_job_id(args[0], "bg")
        if job_id is None:
            return

        job = self.jobs.get(job_id)
        if job is None:
            print(f"bg: no such job: {job_id}")
            return

        self.process_manager.resume_job(job)

    @staticmethod
    def _parse_job_id(value: str, command: str) -> int | None:
        value = value.lstrip("%")
        try:
            job_id = int(value)
            if job_id <= 0:
                raise ValueError
            return job_id
        except ValueError:
            print(f"{command}: invalid job ID: {value}")
            return None

    # ------------------------------------------------------------------
    # Deliverable 4: Authentication and file-permission commands
    # ------------------------------------------------------------------

    def whoami(self, args: Sequence[str]) -> None:
        """Display the active authenticated user and role."""
        if args:
            print("whoami: this command does not accept arguments")
            return

        if self.current_user is None:
            print("No authenticated user session is available.")
            return

        print(f"Username : {self.current_user.username}")
        print(f"Role     : {self.current_user.role}")

    def show_permissions(self, args: Sequence[str]) -> None:
        """Display the active user's simulated permissions for a path."""
        if len(args) != 1:
            print("Usage: permissions <filename>")
            return

        if self.current_user is None or self.permission_manager is None:
            print("security: no authenticated user session is available")
            return

        path = Path(args[0]).expanduser()
        print(self.permission_manager.describe(self.current_user, path))

    def write_file(self, args: Sequence[str]) -> None:
        """Append text to a file after checking write permission."""
        if len(args) < 2:
            print("Usage: write <filename> <text>")
            return

        path = Path(args[0]).expanduser()

        if not self._require_permission(path, "write"):
            return

        text = " ".join(args[1:])

        try:
            with path.open("a", encoding="utf-8") as file:
                file.write(text + "\n")
            print(f"write: appended text to {path}")
        except FileNotFoundError:
            print(f"write: parent directory not found: {path}")
        except IsADirectoryError:
            print(f"write: {path} is a directory")
        except PermissionError:
            print(f"write: operating-system permission denied: {path}")
        except OSError as exc:
            print(f"write: {exc}")

    def run_file(self, args: Sequence[str]) -> None:
        """Execute a permitted Python or batch script."""
        if len(args) != 1:
            print("Usage: runfile <filename>")
            return

        path = Path(args[0]).expanduser()

        if not self._require_permission(path, "execute"):
            return

        if not path.exists():
            print(f"runfile: file not found: {path}")
            return
        if path.is_dir():
            print(f"runfile: {path} is a directory")
            return

        suffix = path.suffix.lower()

        if suffix == ".py":
            command = [sys.executable, str(path)]
        elif suffix in {".bat", ".cmd"} and os.name == "nt":
            command = ["cmd", "/c", str(path)]
        else:
            print(
                "runfile: supported executable file types are "
                ".py, .bat, and .cmd"
            )
            return

        try:
            completed = subprocess.run(command, check=False)
        except PermissionError:
            print(f"runfile: operating-system permission denied: {path}")
        except OSError as exc:
            print(f"runfile: unable to execute {path}: {exc}")
        else:
            print(
                f"runfile: {path} finished with exit code "
                f"{completed.returncode}"
            )

    # ------------------------------------------------------------------
    # Deliverable 2: Process scheduling commands
    # ------------------------------------------------------------------

    def add_process(self, args: Sequence[str]) -> None:
        if len(args) not in (3, 4):
            print(
                "Usage: addproc <name> <burst_time> "
                "<priority> [arrival_time]"
            )
            return

        name = args[0]

        try:
            burst_time = int(args[1])
            priority = int(args[2])
            arrival_time = int(args[3]) if len(args) == 4 else 0

            process = self.scheduler.add_process(
                name=name,
                burst_time=burst_time,
                priority=priority,
                arrival_time=arrival_time,
            )
        except ValueError as exc:
            print(f"addproc: {exc}")
            return

        print(
            f"Added simulated process P{process.pid}: "
            f"name={process.name}, burst={process.burst_time}, "
            f"priority={process.priority}, arrival={process.arrival_time}"
        )

    def show_simulated_processes(self, args: Sequence[str]) -> None:
        if args:
            print("psim: this command does not accept arguments")
            return
        print(self.scheduler.list_processes())

    def run_schedule(self, args: Sequence[str]) -> None:
        if not args:
            print("Usage: schedule rr <quantum> | schedule priority")
            return

        algorithm = args[0].lower()

        try:
            if algorithm in {"rr", "roundrobin", "round-robin"}:
                if len(args) != 2:
                    print("Usage: schedule rr <quantum>")
                    return

                try:
                    quantum = int(args[1])
                except ValueError:
                    print(f"schedule: invalid quantum: {args[1]}")
                    return

                self.last_scheduling_result = self.scheduler.round_robin(quantum)
                print_result(self.last_scheduling_result)
                return

            if algorithm in {"priority", "prio"}:
                if len(args) != 1:
                    print("Usage: schedule priority")
                    return

                self.last_scheduling_result = (
                    self.scheduler.priority_preemptive()
                )
                print_result(self.last_scheduling_result)
                return

            print(
                f"schedule: unknown algorithm: {args[0]}\n"
                "Available algorithms: rr, priority"
            )
        except (ValueError, RuntimeError) as exc:
            print(f"schedule: {exc}")

    def show_metrics(self, args: Sequence[str]) -> None:
        if args:
            print("metrics: this command does not accept arguments")
            return

        if self.last_scheduling_result is None:
            print("No scheduling results are available. Run schedule first.")
            return

        print(f"Algorithm: {self.last_scheduling_result.algorithm}")
        print(self.last_scheduling_result.metrics_table())

    def clear_processes(self, args: Sequence[str]) -> None:
        if args:
            print("clearprocs: this command does not accept arguments")
            return

        self.scheduler.clear()
        self.last_scheduling_result = None
        print("All simulated processes and scheduling results were cleared.")

    # ------------------------------------------------------------------
    # Deliverable 3: Memory-management commands
    # ------------------------------------------------------------------

    def configure_memory(self, args: Sequence[str]) -> None:
        if len(args) != 3:
            print("Usage: memconfig <frames> <page_size_kb> <fifo|lru>")
            return

        try:
            frames = int(args[0])
            page_size = int(args[1])
            self.memory_manager.configure(frames, page_size, args[2])
        except ValueError as exc:
            print(f"memconfig: {exc}")
            return

        print(
            f"Memory configured: {frames} frame(s), "
            f"{page_size} KB per frame, "
            f"{self.memory_manager.algorithm.upper()} replacement."
        )

    def allocate_memory(self, args: Sequence[str]) -> None:
        if len(args) != 2:
            print("Usage: memalloc <pid> <pages>")
            return

        try:
            self.memory_manager.allocate_process(
                int(args[0]),
                int(args[1]),
            )
        except ValueError as exc:
            print(f"memalloc: {exc}")

    def access_memory(self, args: Sequence[str]) -> None:
        if len(args) != 2:
            print("Usage: memaccess <pid> <page_number>")
            return

        try:
            self.memory_manager.access_page(
                int(args[0]),
                int(args[1]),
            )
        except ValueError as exc:
            print(f"memaccess: {exc}")
        except RuntimeError as exc:
            print(f"memaccess: internal memory error: {exc}")

    def free_memory(self, args: Sequence[str]) -> None:
        if len(args) != 1:
            print("Usage: memfree <pid>")
            return

        try:
            self.memory_manager.free_process(int(args[0]))
        except ValueError as exc:
            print(f"memfree: {exc}")

    def show_memory_status(self, args: Sequence[str]) -> None:
        if args:
            print("memstat: this command does not accept arguments")
            return
        print(self.memory_manager.status())

    def reset_memory(self, args: Sequence[str]) -> None:
        if args:
            print("memreset: this command does not accept arguments")
            return

        self.memory_manager.reset()
        print("Memory simulation and statistics were reset.")

    def run_memory_demo(self, args: Sequence[str]) -> None:
        if len(args) != 1:
            print("Usage: memdemo <fifo|lru>")
            return

        try:
            self.memory_manager.run_demo(args[0])
        except ValueError as exc:
            print(f"memdemo: {exc}")

    # ------------------------------------------------------------------
    # Deliverable 3: Process-synchronization commands
    # ------------------------------------------------------------------

    def run_producer_consumer(self, args: Sequence[str]) -> None:
        if len(args) not in (0, 4):
            print(
                "Usage: producerconsumer "
                "[producers consumers items_per_producer buffer_size]"
            )
            return

        try:
            if not args:
                self.synchronization.run()
            else:
                self.synchronization.run(
                    producer_count=int(args[0]),
                    consumer_count=int(args[1]),
                    items_per_producer=int(args[2]),
                    buffer_size=int(args[3]),
                )
        except ValueError as exc:
            print(f"producerconsumer: {exc}")

    def show_synchronization_status(self, args: Sequence[str]) -> None:
        if args:
            print("syncstat: this command does not accept arguments")
            return
        print(self.synchronization.status())

    @staticmethod
    def help(args: Sequence[str]) -> None:
        if args:
            print("help: this command does not accept arguments")
            return

        print(
            """
Advanced Shell Commands
-----------------------
Deliverable 1 Commands
cd [directory]       Change the current directory
pwd                  Print the current directory
exit                 Exit the shell
echo [text]          Print text
clear                Clear the terminal
ls [directory]       List files and directories
cat <filename>       Display a text file
mkdir <directory>    Create a directory
rmdir <directory>    Remove an empty directory
rm <filename>        Delete a file
touch <filename>     Create/update a file
kill <pid>           Terminate a process
jobs                 List tracked background jobs
fg <job_id>          Wait for a background job in foreground
bg <job_id>          Resume a stopped job

Deliverable 4 Security Commands
whoami               Display the authenticated username and role
permissions <file>   Display read, write, and execute permissions
write <file> <text>  Append text when write access is allowed
runfile <file>       Execute a permitted Python or Windows script

Deliverable 2 Scheduling Commands
addproc <name> <burst> <priority> [arrival]
                     Add a simulated process
psim                 List simulated processes
schedule rr <quantum>
                     Run Round-Robin scheduling
schedule priority    Run preemptive priority scheduling
metrics              Display the most recent performance metrics
clearprocs           Remove all simulated processes and results

Deliverable 3 Memory Commands
memconfig <frames> <page_size_kb> <fifo|lru>
                     Configure and reset physical memory
memalloc <pid> <pages>
                     Allocate virtual pages to a process
memaccess <pid> <page>
                     Access a page and handle page faults
memfree <pid>        Deallocate a process and release frames
memstat              Display frames, processes, and statistics
memreset             Reset the memory simulation
memdemo <fifo|lru>   Run a page-replacement demonstration

Deliverable 3 Synchronization Commands
producerconsumer
                     Run the default bounded-buffer demonstration
producerconsumer <producers> <consumers> <items> <buffer>
                     Run a custom producer-consumer demonstration
syncstat             Display the most recent synchronization result

General
help                 Display this help

Notes
- Lower priority numbers represent higher priorities.
- Memory allocation uses demand paging.
- FIFO replaces the oldest loaded page.
- LRU replaces the least recently accessed page.
- Producer-consumer uses a mutex and two counting semaphores.
- Authentication supports administrator and standard-user roles.
- File operations enforce simulated read, write, and execute access.
- Append & to run an external command in the background.
- Use | to connect commands in a pipeline.

Deliverable 4 Security Examples
whoami
permissions test_files/system_config.txt
cat test_files/system_config.txt
write test_files/system_config.txt attempted-change
runfile test_files/admin_script.py

Deliverable 3 Examples
memconfig 3 4 fifo
memalloc 101 5
memaccess 101 0
memaccess 101 1
memaccess 101 2
memaccess 101 3
memstat
memfree 101
memdemo fifo
memdemo lru
producerconsumer 2 2 5 3
syncstat
""".strip()
        )

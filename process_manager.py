"""Process creation, termination, and job-control helpers."""

from __future__ import annotations

import os
import signal
import subprocess
from typing import Sequence

from jobs import Job, JobTable


class ProcessManager:
    """Creates foreground/background processes and manages their lifecycle."""

    def __init__(self, job_table: JobTable) -> None:
        self.job_table = job_table

    @staticmethod
    def _creation_flags() -> int:
        if os.name == "nt":
            return subprocess.CREATE_NEW_PROCESS_GROUP
        return 0

    def start_process(
        self,
        command_parts: Sequence[str],
        command_text: str,
        background: bool = False,
    ) -> None:
        if not command_parts:
            return

        try:
            process = subprocess.Popen(
                list(command_parts),
                creationflags=self._creation_flags(),
            )
        except FileNotFoundError:
            print(f"shell: command not found: {command_parts[0]}")
            return
        except PermissionError:
            print(f"shell: permission denied: {command_parts[0]}")
            return
        except OSError as exc:
            print(f"shell: unable to execute command: {exc}")
            return

        if background:
            job = self.job_table.add(command_text, process)
            print(f"[{job.job_id}] {job.pid}")
            return

        try:
            process.wait()
        except KeyboardInterrupt:
            self.terminate_pid(process.pid)
            print()

    def bring_to_foreground(self, job: Job) -> None:
        job.refresh_status()

        if job.status not in {"Running", "Stopped"}:
            print(f"fg: job {job.job_id} has already completed")
            self.job_table.remove(job.job_id)
            return

        if job.status == "Stopped":
            self.resume_job(job)

        print(f"{job.command}")
        try:
            job.process.wait()
        except KeyboardInterrupt:
            self.terminate_pid(job.pid)
            print()

        job.refresh_status()
        self.job_table.remove(job.job_id)

    def resume_job(self, job: Job) -> bool:
        """Resume a stopped process where the platform supports it."""
        job.refresh_status()

        if job.status == "Running":
            print(f"bg: job {job.job_id} is already running")
            return True

        if job.status != "Stopped":
            print(f"bg: job {job.job_id} is not stopped")
            return False

        try:
            if os.name == "nt":
                try:
                    import psutil
                except ImportError:
                    print(
                        "bg: resuming stopped jobs on Windows requires psutil. "
                        "Install it with: pip install psutil"
                    )
                    return False

                psutil.Process(job.pid).resume()
            else:
                os.kill(job.pid, signal.SIGCONT)

            job.status = "Running"
            print(f"[{job.job_id}] {job.command} &")
            return True
        except (ProcessLookupError, PermissionError, OSError) as exc:
            print(f"bg: unable to resume job: {exc}")
            return False

    @staticmethod
    def terminate_pid(pid: int) -> bool:
        """Terminate a process by PID."""
        try:
            if os.name == "nt":
                try:
                    import psutil
                except ImportError:
                    os.kill(pid, signal.SIGTERM)
                else:
                    process = psutil.Process(pid)
                    process.terminate()
            else:
                os.kill(pid, signal.SIGTERM)

            print(f"Process {pid} terminated.")
            return True
        except ProcessLookupError:
            print(f"kill: no process found with PID {pid}")
        except PermissionError:
            print(f"kill: permission denied for PID {pid}")
        except ValueError:
            print(f"kill: invalid PID {pid}")
        except OSError as exc:
            print(f"kill: unable to terminate PID {pid}: {exc}")

        return False

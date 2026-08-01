"""Background job tracking for Advanced Shell."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from subprocess import Popen
from typing import Dict, Optional


@dataclass
class Job:
    """Represents a foreground or background process managed by the shell."""

    job_id: int
    command: str
    process: Popen
    status: str = "Running"
    started_at: datetime = datetime.now()

    @property
    def pid(self) -> int:
        return self.process.pid

    def refresh_status(self) -> str:
        """Update and return the current process status."""
        return_code = self.process.poll()

        if return_code is None:
            if self.status not in {"Stopped", "Terminated"}:
                self.status = "Running"
        elif self.status != "Terminated":
            self.status = "Done" if return_code == 0 else f"Exited ({return_code})"

        return self.status


class JobTable:
    """Stores and manages shell jobs."""

    def __init__(self) -> None:
        self._jobs: Dict[int, Job] = {}
        self._next_job_id = 1

    def add(self, command: str, process: Popen) -> Job:
        job = Job(
            job_id=self._next_job_id,
            command=command,
            process=process,
            started_at=datetime.now(),
        )
        self._jobs[job.job_id] = job
        self._next_job_id += 1
        return job

    def get(self, job_id: int) -> Optional[Job]:
        return self._jobs.get(job_id)

    def remove(self, job_id: int) -> None:
        self._jobs.pop(job_id, None)

    def refresh_all(self) -> None:
        for job in self._jobs.values():
            job.refresh_status()

    def active_jobs(self) -> list[Job]:
        self.refresh_all()
        return [
            job
            for job in self._jobs.values()
            if job.status in {"Running", "Stopped"}
        ]

    def all_jobs(self) -> list[Job]:
        self.refresh_all()
        return list(self._jobs.values())

    def cleanup_completed(self) -> None:
        """Remove jobs that have already completed."""
        self.refresh_all()
        completed = [
            job_id
            for job_id, job in self._jobs.items()
            if job.status not in {"Running", "Stopped"}
        ]
        for job_id in completed:
            self.remove(job_id)

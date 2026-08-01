"""
scheduler.py
Deliverable 2: Process Scheduling

Implements:
1. Round-Robin scheduling with configurable quantum.
2. Preemptive priority scheduling with FCFS tie-breaking.
3. Waiting time, turnaround time, and response time metrics.

The scheduler is simulation-based. One simulated time unit may optionally
sleep for a small amount of real time so process switching is visible.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import heapq
import itertools
import time
from typing import Iterable, Optional


@dataclass
class SimulatedProcess:
    """Represents a process used by the scheduling simulator."""

    pid: int
    name: str
    burst_time: int
    priority: int = 0
    arrival_time: int = 0

    remaining_time: int = field(init=False)
    first_run_time: Optional[int] = field(default=None, init=False)
    completion_time: Optional[int] = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.pid <= 0:
            raise ValueError("PID must be greater than zero.")
        if not self.name.strip():
            raise ValueError("Process name cannot be empty.")
        if self.burst_time <= 0:
            raise ValueError("Burst time must be greater than zero.")
        if self.arrival_time < 0:
            raise ValueError("Arrival time cannot be negative.")

        self.name = self.name.strip()
        self.remaining_time = self.burst_time

    def reset(self) -> None:
        """Reset runtime values so the process can be scheduled again."""
        self.remaining_time = self.burst_time
        self.first_run_time = None
        self.completion_time = None

    @property
    def turnaround_time(self) -> int:
        if self.completion_time is None:
            raise RuntimeError(f"Process {self.pid} has not completed.")
        return self.completion_time - self.arrival_time

    @property
    def waiting_time(self) -> int:
        return self.turnaround_time - self.burst_time

    @property
    def response_time(self) -> int:
        if self.first_run_time is None:
            raise RuntimeError(f"Process {self.pid} has not started.")
        return self.first_run_time - self.arrival_time


@dataclass
class SchedulingResult:
    """Stores the final output of a scheduling simulation."""

    algorithm: str
    processes: list[SimulatedProcess]
    timeline: list[str]
    total_time: int

    def averages(self) -> dict[str, float]:
        count = len(self.processes)
        if count == 0:
            return {
                "waiting_time": 0.0,
                "turnaround_time": 0.0,
                "response_time": 0.0,
            }

        return {
            "waiting_time": sum(p.waiting_time for p in self.processes) / count,
            "turnaround_time": sum(p.turnaround_time for p in self.processes) / count,
            "response_time": sum(p.response_time for p in self.processes) / count,
        }

    def metrics_table(self) -> str:
        headers = (
            "PID",
            "Name",
            "Arrival",
            "Burst",
            "Priority",
            "Completion",
            "Waiting",
            "Turnaround",
            "Response",
        )

        rows = [
            (
                str(p.pid),
                p.name,
                str(p.arrival_time),
                str(p.burst_time),
                str(p.priority),
                str(p.completion_time),
                str(p.waiting_time),
                str(p.turnaround_time),
                str(p.response_time),
            )
            for p in sorted(self.processes, key=lambda item: item.pid)
        ]

        widths = [
            max(len(headers[i]), *(len(row[i]) for row in rows))
            for i in range(len(headers))
        ]

        def format_row(row: Iterable[str]) -> str:
            return " | ".join(
                value.ljust(widths[index])
                for index, value in enumerate(row)
            )

        separator = "-+-".join("-" * width for width in widths)
        output = [format_row(headers), separator]
        output.extend(format_row(row) for row in rows)

        avg = self.averages()
        output.extend(
            [
                "",
                f"Average waiting time:    {avg['waiting_time']:.2f}",
                f"Average turnaround time: {avg['turnaround_time']:.2f}",
                f"Average response time:   {avg['response_time']:.2f}",
                f"Total simulated time:    {self.total_time}",
            ]
        )
        return "\n".join(output)


class Scheduler:
    """Manages simulated processes and runs scheduling algorithms."""

    def __init__(self, sleep_per_unit: float = 0.0) -> None:
        if sleep_per_unit < 0:
            raise ValueError("sleep_per_unit cannot be negative.")

        self.sleep_per_unit = sleep_per_unit
        self._processes: list[SimulatedProcess] = []
        self._pid_counter = itertools.count(1)

    @property
    def processes(self) -> list[SimulatedProcess]:
        return list(self._processes)

    def add_process(
        self,
        name: str,
        burst_time: int,
        priority: int = 0,
        arrival_time: int = 0,
    ) -> SimulatedProcess:
        process = SimulatedProcess(
            pid=next(self._pid_counter),
            name=name,
            burst_time=burst_time,
            priority=priority,
            arrival_time=arrival_time,
        )
        self._processes.append(process)
        return process

    def clear(self) -> None:
        self._processes.clear()
        self._pid_counter = itertools.count(1)

    def list_processes(self) -> str:
        if not self._processes:
            return "No simulated processes have been added."

        lines = [
            "PID | Name | Burst | Priority | Arrival",
            "----+------+-------+----------+--------",
        ]
        for process in self._processes:
            lines.append(
                f"{process.pid:<3} | "
                f"{process.name:<4} | "
                f"{process.burst_time:<5} | "
                f"{process.priority:<8} | "
                f"{process.arrival_time}"
            )
        return "\n".join(lines)

    def _prepare(self) -> list[SimulatedProcess]:
        if not self._processes:
            raise RuntimeError("No processes are available to schedule.")

        for process in self._processes:
            process.reset()

        return sorted(
            self._processes,
            key=lambda process: (process.arrival_time, process.pid),
        )

    def _run_one_unit(self) -> None:
        if self.sleep_per_unit > 0:
            time.sleep(self.sleep_per_unit)

    def round_robin(self, quantum: int) -> SchedulingResult:
        """
        Run Round-Robin scheduling.

        Processes that arrive while another process is running are added to the
        ready queue before the current process is requeued.
        """
        if quantum <= 0:
            raise ValueError("Quantum must be greater than zero.")

        processes = self._prepare()
        ready_queue: deque[SimulatedProcess] = deque()
        timeline: list[str] = []

        current_time = 0
        next_arrival_index = 0
        completed = 0

        while completed < len(processes):
            while (
                next_arrival_index < len(processes)
                and processes[next_arrival_index].arrival_time <= current_time
            ):
                process = processes[next_arrival_index]
                ready_queue.append(process)
                timeline.append(
                    f"[t={current_time}] P{process.pid} ({process.name}) entered ready queue."
                )
                next_arrival_index += 1

            if not ready_queue:
                next_arrival = processes[next_arrival_index].arrival_time
                timeline.append(
                    f"[t={current_time}] CPU idle until t={next_arrival}."
                )
                current_time = next_arrival
                continue

            process = ready_queue.popleft()

            if process.first_run_time is None:
                process.first_run_time = current_time

            run_time = min(quantum, process.remaining_time)
            start_time = current_time

            timeline.append(
                f"[t={start_time}] Running P{process.pid} ({process.name}) "
                f"for up to {run_time} unit(s)."
            )

            for _ in range(run_time):
                self._run_one_unit()
                process.remaining_time -= 1
                current_time += 1

                while (
                    next_arrival_index < len(processes)
                    and processes[next_arrival_index].arrival_time <= current_time
                ):
                    arriving = processes[next_arrival_index]
                    ready_queue.append(arriving)
                    timeline.append(
                        f"[t={current_time}] P{arriving.pid} ({arriving.name}) "
                        "entered ready queue."
                    )
                    next_arrival_index += 1

                if process.remaining_time == 0:
                    break

            if process.remaining_time == 0:
                process.completion_time = current_time
                completed += 1
                timeline.append(
                    f"[t={current_time}] P{process.pid} ({process.name}) completed."
                )
            else:
                ready_queue.append(process)
                timeline.append(
                    f"[t={current_time}] Quantum expired for P{process.pid}; "
                    f"{process.remaining_time} unit(s) remain."
                )

        return SchedulingResult(
            algorithm=f"Round Robin (quantum={quantum})",
            processes=processes,
            timeline=timeline,
            total_time=current_time,
        )

    def priority_preemptive(self) -> SchedulingResult:
        """
        Run preemptive priority scheduling.

        Lower numeric values represent higher priorities.
        Processes with equal priorities use FCFS ordering.
        """
        processes = self._prepare()
        ready_heap: list[tuple[int, int, int, SimulatedProcess]] = []
        timeline: list[str] = []

        current_time = 0
        next_arrival_index = 0
        completed = 0
        current_process: Optional[SimulatedProcess] = None
        insertion_order = itertools.count()

        while completed < len(processes):
            while (
                next_arrival_index < len(processes)
                and processes[next_arrival_index].arrival_time <= current_time
            ):
                process = processes[next_arrival_index]
                heapq.heappush(
                    ready_heap,
                    (
                        process.priority,
                        process.arrival_time,
                        next(insertion_order),
                        process,
                    ),
                )
                timeline.append(
                    f"[t={current_time}] P{process.pid} ({process.name}) arrived "
                    f"with priority {process.priority}."
                )
                next_arrival_index += 1

            if current_process is None and ready_heap:
                _, _, _, current_process = heapq.heappop(ready_heap)

                if current_process.first_run_time is None:
                    current_process.first_run_time = current_time

                timeline.append(
                    f"[t={current_time}] Running P{current_process.pid} "
                    f"({current_process.name}), priority {current_process.priority}."
                )

            if current_process is None:
                next_arrival = processes[next_arrival_index].arrival_time
                timeline.append(
                    f"[t={current_time}] CPU idle until t={next_arrival}."
                )
                current_time = next_arrival
                continue

            self._run_one_unit()
            current_process.remaining_time -= 1
            current_time += 1

            while (
                next_arrival_index < len(processes)
                and processes[next_arrival_index].arrival_time <= current_time
            ):
                process = processes[next_arrival_index]
                heapq.heappush(
                    ready_heap,
                    (
                        process.priority,
                        process.arrival_time,
                        next(insertion_order),
                        process,
                    ),
                )
                timeline.append(
                    f"[t={current_time}] P{process.pid} ({process.name}) arrived "
                    f"with priority {process.priority}."
                )
                next_arrival_index += 1

            if current_process.remaining_time == 0:
                current_process.completion_time = current_time
                completed += 1
                timeline.append(
                    f"[t={current_time}] P{current_process.pid} "
                    f"({current_process.name}) completed."
                )
                current_process = None
                continue

            if ready_heap and ready_heap[0][0] < current_process.priority:
                higher_priority = ready_heap[0][3]
                timeline.append(
                    f"[t={current_time}] Preempting P{current_process.pid} "
                    f"for P{higher_priority.pid}, which has higher priority."
                )

                heapq.heappush(
                    ready_heap,
                    (
                        current_process.priority,
                        current_process.arrival_time,
                        next(insertion_order),
                        current_process,
                    ),
                )
                _, _, _, current_process = heapq.heappop(ready_heap)

                if current_process.first_run_time is None:
                    current_process.first_run_time = current_time

                timeline.append(
                    f"[t={current_time}] Running P{current_process.pid} "
                    f"({current_process.name}), priority {current_process.priority}."
                )

        return SchedulingResult(
            algorithm="Preemptive Priority",
            processes=processes,
            timeline=timeline,
            total_time=current_time,
        )


def print_result(result: SchedulingResult) -> None:
    """Print the algorithm name, event timeline, and final metrics."""
    print(f"\n=== {result.algorithm} ===")
    for event in result.timeline:
        print(event)

    print("\n=== Performance Metrics ===")
    print(result.metrics_table())


def demo() -> None:
    """Standalone demonstration for testing scheduler.py directly."""
    scheduler = Scheduler(sleep_per_unit=0.05)

    scheduler.add_process("P1", burst_time=5, priority=3, arrival_time=0)
    scheduler.add_process("P2", burst_time=4, priority=1, arrival_time=1)
    scheduler.add_process("P3", burst_time=3, priority=2, arrival_time=2)

    print("Configured processes:")
    print(scheduler.list_processes())

    print_result(scheduler.round_robin(quantum=2))
    print_result(scheduler.priority_preemptive())


if __name__ == "__main__":
    demo()

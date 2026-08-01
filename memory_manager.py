"""Memory management simulator for Advanced Shell - Deliverable 3."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class Frame:
    """Represents one physical-memory page frame."""

    frame_number: int
    pid: Optional[int] = None
    page_number: Optional[int] = None
    loaded_at: int = 0
    last_accessed: int = 0

    @property
    def is_free(self) -> bool:
        return self.pid is None


@dataclass
class ProcessMemory:
    """Tracks virtual-memory information for one simulated process."""

    pid: int
    page_count: int
    page_faults: int = 0
    page_hits: int = 0


class MemoryManager:
    """Simulates fixed-size paging with FIFO and LRU replacement."""

    def __init__(
        self,
        frame_count: int = 4,
        page_size_kb: int = 4,
        algorithm: str = "fifo",
    ) -> None:
        self.frame_count = 0
        self.page_size_kb = 0
        self.algorithm = "fifo"
        self.frames: List[Frame] = []
        self.processes: Dict[int, ProcessMemory] = {}
        self.page_table: Dict[Tuple[int, int], int] = {}
        self.fifo_queue: deque[int] = deque()
        self.clock = 0
        self.total_faults = 0
        self.total_hits = 0
        self.total_replacements = 0
        self.configure(frame_count, page_size_kb, algorithm)

    def configure(
        self,
        frame_count: int,
        page_size_kb: int,
        algorithm: str,
    ) -> None:
        """Configure physical memory and clear the current simulation."""
        if frame_count <= 0:
            raise ValueError("frame count must be greater than zero")
        if page_size_kb <= 0:
            raise ValueError("page size must be greater than zero")

        normalized = algorithm.lower()
        if normalized not in {"fifo", "lru"}:
            raise ValueError("algorithm must be FIFO or LRU")

        self.frame_count = frame_count
        self.page_size_kb = page_size_kb
        self.algorithm = normalized
        self.reset()

    def reset(self) -> None:
        """Clear processes, frames, page tables, and statistics."""
        self.frames = [Frame(number) for number in range(self.frame_count)]
        self.processes.clear()
        self.page_table.clear()
        self.fifo_queue.clear()
        self.clock = 0
        self.total_faults = 0
        self.total_hits = 0
        self.total_replacements = 0

    def allocate_process(self, pid: int, page_count: int) -> None:
        """Create a virtual address space for a process."""
        if pid <= 0:
            raise ValueError("PID must be greater than zero")
        if page_count <= 0:
            raise ValueError("page count must be greater than zero")
        if pid in self.processes:
            raise ValueError(f"PID {pid} is already allocated")

        self.processes[pid] = ProcessMemory(pid=pid, page_count=page_count)
        print(
            f"[ALLOCATED] PID {pid}: {page_count} virtual page(s), "
            f"{page_count * self.page_size_kb} KB total"
        )
        print(
            "Pages are loaded into physical memory only when accessed "
            "(demand paging)."
        )

    def free_process(self, pid: int) -> None:
        """Deallocate a process and release all resident frames."""
        process = self.processes.get(pid)
        if process is None:
            raise ValueError(f"PID {pid} is not allocated")

        released = 0
        for frame in self.frames:
            if frame.pid == pid:
                self.page_table.pop((pid, frame.page_number), None)
                self._remove_from_fifo(frame.frame_number)
                self._clear_frame(frame)
                released += 1

        del self.processes[pid]
        print(
            f"[DEALLOCATED] PID {pid}: released {released} physical frame(s)"
        )

    def access_page(self, pid: int, page_number: int) -> bool:
        """
        Access one virtual page.

        Returns True for a page hit and False for a page fault.
        """
        process = self.processes.get(pid)
        if process is None:
            raise ValueError(f"PID {pid} is not allocated")
        if page_number < 0 or page_number >= process.page_count:
            raise ValueError(
                f"page {page_number} is outside PID {pid}'s valid range "
                f"0-{process.page_count - 1}"
            )

        self.clock += 1
        key = (pid, page_number)

        if key in self.page_table:
            frame_number = self.page_table[key]
            frame = self.frames[frame_number]
            frame.last_accessed = self.clock
            process.page_hits += 1
            self.total_hits += 1
            print(
                f"[PAGE HIT] PID {pid} page {page_number} "
                f"is in frame {frame_number}"
            )
            return True

        process.page_faults += 1
        self.total_faults += 1
        print(f"[PAGE FAULT] PID {pid} requested page {page_number}")

        frame = self._find_free_frame()
        if frame is None:
            frame = self._select_victim()
            old_pid = frame.pid
            old_page = frame.page_number

            if old_pid is not None and old_page is not None:
                self.page_table.pop((old_pid, old_page), None)

            self.total_replacements += 1
            print(
                f"[{self.algorithm.upper()} REPLACEMENT] "
                f"Evicted PID {old_pid} page {old_page} "
                f"from frame {frame.frame_number}"
            )
            self._remove_from_fifo(frame.frame_number)

        frame.pid = pid
        frame.page_number = page_number
        frame.loaded_at = self.clock
        frame.last_accessed = self.clock
        self.page_table[key] = frame.frame_number
        self.fifo_queue.append(frame.frame_number)

        print(
            f"[LOAD] PID {pid} page {page_number} "
            f"loaded into frame {frame.frame_number}"
        )
        return False

    def _find_free_frame(self) -> Optional[Frame]:
        return next((frame for frame in self.frames if frame.is_free), None)

    def _select_victim(self) -> Frame:
        if self.algorithm == "fifo":
            while self.fifo_queue:
                frame_number = self.fifo_queue.popleft()
                frame = self.frames[frame_number]
                if not frame.is_free:
                    return frame
            raise RuntimeError("FIFO queue is empty while memory is full")

        occupied = [frame for frame in self.frames if not frame.is_free]
        if not occupied:
            raise RuntimeError("no occupied frame is available for LRU")
        return min(
            occupied,
            key=lambda frame: (frame.last_accessed, frame.frame_number),
        )

    def _remove_from_fifo(self, frame_number: int) -> None:
        try:
            self.fifo_queue.remove(frame_number)
        except ValueError:
            pass

    @staticmethod
    def _clear_frame(frame: Frame) -> None:
        frame.pid = None
        frame.page_number = None
        frame.loaded_at = 0
        frame.last_accessed = 0

    def status(self) -> str:
        """Return formatted memory and process statistics."""
        used_frames = sum(not frame.is_free for frame in self.frames)
        physical_kb = self.frame_count * self.page_size_kb
        used_kb = used_frames * self.page_size_kb
        utilization = (
            (used_frames / self.frame_count) * 100
            if self.frame_count
            else 0.0
        )

        lines = [
            "Memory Configuration",
            "--------------------",
            f"Replacement algorithm : {self.algorithm.upper()}",
            f"Page/frame size       : {self.page_size_kb} KB",
            f"Physical frames       : {self.frame_count}",
            f"Physical memory       : {physical_kb} KB",
            f"Used frames           : {used_frames}/{self.frame_count}",
            f"Used physical memory  : {used_kb}/{physical_kb} KB",
            f"Frame utilization     : {utilization:.2f}%",
            f"Total page faults     : {self.total_faults}",
            f"Total page hits       : {self.total_hits}",
            f"Page replacements     : {self.total_replacements}",
            "",
            "Frame Table",
            "-----------",
            f"{'Frame':<8}{'PID':<10}{'Page':<10}{'Loaded':<10}{'Last Used':<10}",
        ]

        for frame in self.frames:
            pid = "-" if frame.pid is None else str(frame.pid)
            page = "-" if frame.page_number is None else str(frame.page_number)
            loaded = "-" if frame.is_free else str(frame.loaded_at)
            last_used = "-" if frame.is_free else str(frame.last_accessed)
            lines.append(
                f"{frame.frame_number:<8}{pid:<10}{page:<10}"
                f"{loaded:<10}{last_used:<10}"
            )

        lines.extend(
            [
                "",
                "Process Memory",
                "--------------",
                f"{'PID':<8}{'Pages':<10}{'Virtual KB':<12}"
                f"{'Resident':<10}{'Faults':<10}{'Hits':<10}",
            ]
        )

        if not self.processes:
            lines.append("No processes are currently allocated.")
        else:
            for pid in sorted(self.processes):
                process = self.processes[pid]
                resident = sum(
                    1 for frame in self.frames if frame.pid == pid
                )
                lines.append(
                    f"{pid:<8}{process.page_count:<10}"
                    f"{process.page_count * self.page_size_kb:<12}"
                    f"{resident:<10}{process.page_faults:<10}"
                    f"{process.page_hits:<10}"
                )

        return "\n".join(lines)

    def run_demo(self, algorithm: str) -> None:
        """Run a repeatable page-replacement demonstration."""
        normalized = algorithm.lower()
        if normalized not in {"fifo", "lru"}:
            raise ValueError("demo algorithm must be FIFO or LRU")

        self.configure(frame_count=3, page_size_kb=4, algorithm=normalized)
        pid = 101
        reference_string = [0, 1, 2, 0, 3, 0, 4]
        self.allocate_process(pid, 5)

        print()
        print(f"{normalized.upper()} Page Replacement Demonstration")
        print("-----------------------------------")
        print(f"Reference string: {' '.join(map(str, reference_string))}")
        print("Physical frames: 3")
        print()

        for page in reference_string:
            self.access_page(pid, page)
            print(self._compact_frames())
            print()

        print("Demonstration Summary")
        print("---------------------")
        print(f"Algorithm    : {normalized.upper()}")
        print(f"Page faults : {self.total_faults}")
        print(f"Page hits   : {self.total_hits}")
        print(f"Replacements: {self.total_replacements}")

    def _compact_frames(self) -> str:
        values = []
        for frame in self.frames:
            if frame.is_free:
                values.append(f"Frame {frame.frame_number}=[free]")
            else:
                values.append(
                    f"Frame {frame.frame_number}="
                    f"[P{frame.pid}:Page{frame.page_number}]"
                )
        return " | ".join(values)

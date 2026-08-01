"""Process synchronization demonstrations for Advanced Shell."""

from __future__ import annotations

import random
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, List


@dataclass
class SynchronizationResult:
    """Summary of the most recent producer-consumer run."""

    producers: int
    consumers: int
    items_per_producer: int
    buffer_size: int
    produced: int
    consumed: int
    remaining: int
    race_conditions: int


class ProducerConsumerSimulation:
    """Bounded-buffer producer-consumer simulation using semaphores."""

    def __init__(self) -> None:
        self.last_result: SynchronizationResult | None = None
        self._print_lock = threading.Lock()

    def run(
        self,
        producer_count: int = 2,
        consumer_count: int = 2,
        items_per_producer: int = 5,
        buffer_size: int = 3,
    ) -> SynchronizationResult:
        self._validate(
            producer_count,
            consumer_count,
            items_per_producer,
            buffer_size,
        )

        buffer: Deque[str] = deque()
        buffer_mutex = threading.Lock()
        empty_slots = threading.Semaphore(buffer_size)
        filled_slots = threading.Semaphore(0)
        stats_lock = threading.Lock()

        produced_count = 0
        consumed_count = 0
        race_conditions = 0
        total_items = producer_count * items_per_producer

        # Distribute the total number of required consumptions fairly.
        base = total_items // consumer_count
        extra = total_items % consumer_count
        consumer_targets = [
            base + (1 if index < extra else 0)
            for index in range(consumer_count)
        ]

        def safe_print(message: str) -> None:
            with self._print_lock:
                print(message)

        def producer(producer_id: int) -> None:
            nonlocal produced_count, race_conditions

            for item_number in range(1, items_per_producer + 1):
                item = f"P{producer_id}-Item{item_number}"
                time.sleep(random.uniform(0.01, 0.05))

                empty_slots.acquire()
                with buffer_mutex:
                    if len(buffer) >= buffer_size:
                        with stats_lock:
                            race_conditions += 1
                    buffer.append(item)
                    snapshot = list(buffer)

                with stats_lock:
                    produced_count += 1

                safe_print(
                    f"Producer-{producer_id} produced {item:<12} "
                    f"| Buffer: {snapshot}"
                )
                filled_slots.release()

        def consumer(consumer_id: int, target: int) -> None:
            nonlocal consumed_count, race_conditions

            for _ in range(target):
                filled_slots.acquire()

                with buffer_mutex:
                    if not buffer:
                        with stats_lock:
                            race_conditions += 1
                        item = "<missing>"
                    else:
                        item = buffer.popleft()
                    snapshot = list(buffer)

                with stats_lock:
                    consumed_count += 1

                safe_print(
                    f"Consumer-{consumer_id} consumed {item:<12} "
                    f"| Buffer: {snapshot}"
                )
                empty_slots.release()
                time.sleep(random.uniform(0.01, 0.05))

        print("Producer-Consumer Synchronization Demonstration")
        print("---------------------------------------------")
        print(f"Producers          : {producer_count}")
        print(f"Consumers          : {consumer_count}")
        print(f"Items per producer : {items_per_producer}")
        print(f"Buffer capacity    : {buffer_size}")
        print("Mechanisms         : mutex lock + empty/filled semaphores")
        print()

        threads: List[threading.Thread] = []

        for producer_id in range(1, producer_count + 1):
            threads.append(
                threading.Thread(
                    target=producer,
                    args=(producer_id,),
                    name=f"Producer-{producer_id}",
                )
            )

        for index, target in enumerate(consumer_targets, start=1):
            threads.append(
                threading.Thread(
                    target=consumer,
                    args=(index, target),
                    name=f"Consumer-{index}",
                )
            )

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        result = SynchronizationResult(
            producers=producer_count,
            consumers=consumer_count,
            items_per_producer=items_per_producer,
            buffer_size=buffer_size,
            produced=produced_count,
            consumed=consumed_count,
            remaining=len(buffer),
            race_conditions=race_conditions,
        )
        self.last_result = result

        print()
        print("Synchronization Complete")
        print("------------------------")
        print(f"Produced             : {result.produced}")
        print(f"Consumed             : {result.consumed}")
        print(f"Remaining in buffer  : {result.remaining}")
        print(f"Race conditions found: {result.race_conditions}")
        print("Deadlock detected    : No")
        print(
            "Result                : Shared-buffer access was "
            "successfully synchronized."
        )

        return result

    def status(self) -> str:
        """Return the summary of the most recent simulation."""
        if self.last_result is None:
            return (
                "No synchronization result is available. "
                "Run producerconsumer first."
            )

        result = self.last_result
        return "\n".join(
            [
                "Most Recent Synchronization Result",
                "----------------------------------",
                f"Producers            : {result.producers}",
                f"Consumers            : {result.consumers}",
                f"Items per producer   : {result.items_per_producer}",
                f"Buffer capacity      : {result.buffer_size}",
                f"Items produced       : {result.produced}",
                f"Items consumed       : {result.consumed}",
                f"Items remaining      : {result.remaining}",
                f"Race conditions found: {result.race_conditions}",
                "Deadlock detected     : No",
            ]
        )

    @staticmethod
    def _validate(
        producer_count: int,
        consumer_count: int,
        items_per_producer: int,
        buffer_size: int,
    ) -> None:
        values = {
            "producer count": producer_count,
            "consumer count": consumer_count,
            "items per producer": items_per_producer,
            "buffer size": buffer_size,
        }
        for name, value in values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")

        if producer_count > 20 or consumer_count > 20:
            raise ValueError("producer and consumer counts cannot exceed 20")
        if items_per_producer > 100:
            raise ValueError("items per producer cannot exceed 100")
        if buffer_size > 100:
            raise ValueError("buffer size cannot exceed 100")

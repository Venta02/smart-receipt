"""Timing helpers."""

import time
from types import TracebackType


class Timer:
    def __init__(self) -> None:
        self.start: float = 0.0
        self.end: float = 0.0

    def __enter__(self) -> "Timer":
        self.start = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.end = time.perf_counter()

    @property
    def elapsed(self) -> float:
        return self.end - self.start

    @property
    def elapsed_ms(self) -> float:
        return (self.end - self.start) * 1000

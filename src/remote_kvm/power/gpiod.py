from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Protocol


class OutputLine(Protocol):
    def set_value(self, value: int) -> None: ...


@dataclass
class GpiodPowerController:
    line: OutputLine
    chip_name: str
    line_offset: int
    active_low: bool = True
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    @classmethod
    def open(
        cls,
        chip_name: str,
        line_offset: int,
        active_low: bool = True,
    ) -> "GpiodPowerController":
        import gpiod

        chip = gpiod.Chip(chip_name)
        line = chip.get_line(line_offset)
        inactive = 1 if active_low else 0
        line.request(
            consumer="remote-kvm-power",
            type=gpiod.LINE_REQ_DIR_OUT,
            default_vals=[inactive],
        )
        controller = cls(
            line=line,
            chip_name=chip_name,
            line_offset=line_offset,
            active_low=active_low,
        )
        controller._chip = chip
        return controller

    @property
    def active_value(self) -> int:
        return 0 if self.active_low else 1

    @property
    def inactive_value(self) -> int:
        return 1 if self.active_low else 0

    def _pulse(self, seconds: float) -> None:
        with self._lock:
            self.line.set_value(self.active_value)
            try:
                time.sleep(seconds)
            finally:
                self.line.set_value(self.inactive_value)

    def power_press(self, seconds: float = 0.2) -> None:
        self._pulse(seconds)

    def force_off(self, seconds: float = 5.0) -> None:
        self._pulse(seconds)

    def status(self) -> dict[str, object]:
        return {
            "available": True,
            "backend": "libgpiod",
            "chip": self.chip_name,
            "line": self.line_offset,
            "active_low": self.active_low,
            "busy": self._lock.locked(),
        }

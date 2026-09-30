from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .keycodes import KEY_CODES, MODIFIERS

WriteReport = Callable[[bytes], None]


def _device_writer(path: Path) -> WriteReport:
    def write(report: bytes) -> None:
        descriptor = os.open(path, os.O_WRONLY | os.O_NONBLOCK)
        try:
            written = os.write(descriptor, report)
            if written != len(report):
                raise OSError(f"short HID write: {written}/{len(report)}")
        finally:
            os.close(descriptor)

    return write


@dataclass
class KeyboardDevice:
    path: Path = Path("/dev/hidg0")
    press_seconds: float = 0.04
    writer: WriteReport | None = None

    def __post_init__(self) -> None:
        self._write = self.writer or _device_writer(self.path)
        self._lock = threading.Lock()

    @staticmethod
    def report(key: str, modifiers: tuple[str, ...] = ()) -> bytes:
        normalized_key = key.lower()
        if normalized_key == "esc":
            normalized_key = "escape"
        try:
            key_code = KEY_CODES[normalized_key]
        except KeyError as error:
            raise ValueError(f"unknown key: {key}") from error

        modifier_byte = 0
        for modifier in modifiers:
            try:
                modifier_byte |= MODIFIERS[modifier.lower()]
            except KeyError as error:
                raise ValueError(f"unknown modifier: {modifier}") from error
        return bytes((modifier_byte, 0, key_code, 0, 0, 0, 0, 0))

    def press(self, key: str, modifiers: tuple[str, ...] = ()) -> None:
        pressed = self.report(key, modifiers)
        released = bytes(8)
        with self._lock:
            self._write(pressed)
            try:
                time.sleep(self.press_seconds)
            finally:
                self._write(released)

    def available(self) -> bool:
        return self.path.exists()


@dataclass
class MouseDevice:
    path: Path = Path("/dev/hidg1")
    click_seconds: float = 0.04
    writer: WriteReport | None = None

    BUTTONS = {"left": 0x01, "right": 0x02, "middle": 0x04}

    def __post_init__(self) -> None:
        self._write = self.writer or _device_writer(self.path)
        self._lock = threading.Lock()

    @staticmethod
    def report(buttons: int = 0, dx: int = 0, dy: int = 0, wheel: int = 0) -> bytes:
        for name, value in (("dx", dx), ("dy", dy), ("wheel", wheel)):
            if not -127 <= value <= 127:
                raise ValueError(f"{name} must be between -127 and 127")
        if not 0 <= buttons <= 7:
            raise ValueError("buttons must be between 0 and 7")
        return bytes((buttons, dx & 0xFF, dy & 0xFF, wheel & 0xFF))

    def move(self, dx: int, dy: int, wheel: int = 0) -> None:
        with self._lock:
            self._write(self.report(dx=dx, dy=dy, wheel=wheel))

    def click(self, button: str) -> None:
        try:
            button_code = self.BUTTONS[button.lower()]
        except KeyError as error:
            raise ValueError(f"unknown mouse button: {button}") from error
        with self._lock:
            self._write(self.report(buttons=button_code))
            try:
                time.sleep(self.click_seconds)
            finally:
                self._write(self.report())

    def available(self) -> bool:
        return self.path.exists()


@dataclass
class HIDController:
    keyboard: KeyboardDevice
    mouse: MouseDevice

    @classmethod
    def system_default(cls) -> "HIDController":
        return cls(keyboard=KeyboardDevice(), mouse=MouseDevice())

    def status(self) -> dict[str, bool]:
        return {
            "keyboard_available": self.keyboard.available(),
            "mouse_available": self.mouse.available(),
        }

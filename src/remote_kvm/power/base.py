from typing import Protocol


class PowerController(Protocol):
    def power_press(self, seconds: float = 0.2) -> None: ...

    def reset_press(self, seconds: float = 0.2) -> None: ...

    def status(self) -> dict[str, object]: ...


class UnavailablePowerController:
    def power_press(self, seconds: float = 0.2) -> None:
        raise RuntimeError("GPIO power backend is not configured")

    def reset_press(self, seconds: float = 0.2) -> None:
        raise RuntimeError("GPIO power backend is not configured")

    def status(self) -> dict[str, object]:
        return {"available": False, "backend": "unconfigured"}

from typing import Protocol


class VideoProvider(Protocol):
    def status(self) -> dict[str, object]: ...


class UnavailableVideoProvider:
    def status(self) -> dict[str, object]:
        return {"available": False, "backend": "unconfigured"}

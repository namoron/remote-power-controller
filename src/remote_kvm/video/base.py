from collections.abc import Iterator
from typing import Protocol


class VideoProvider(Protocol):
    def status(self) -> dict[str, object]: ...

    def stream(self) -> Iterator[bytes]: ...


class UnavailableVideoProvider:
    def status(self) -> dict[str, object]:
        return {"available": False, "backend": "unconfigured"}

    def stream(self) -> Iterator[bytes]:
        raise RuntimeError("video backend is not configured")
        yield b""  # pragma: no cover

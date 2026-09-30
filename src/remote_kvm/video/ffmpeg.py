from __future__ import annotations

import shutil
import subprocess
import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FFmpegMjpegProvider:
    device: Path = Path(
        "/dev/v4l/by-id/usb-MACROSILICON_USB_Video-video-index0"
    )
    resolution: str = "1280x720"
    fps: int = 30
    ffmpeg: str = "/usr/bin/ffmpeg"
    _stream_lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    def __post_init__(self) -> None:
        self.device = Path(self.device)

    def status(self) -> dict[str, object]:
        return {
            "available": self.device.exists() and shutil.which(self.ffmpeg) is not None,
            "backend": "ffmpeg-mjpeg",
            "device": str(self.device),
            "resolution": self.resolution,
            "fps": self.fps,
            "client_connected": self._stream_lock.locked(),
        }

    def command(self) -> list[str]:
        return [
            self.ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "v4l2",
            "-input_format",
            "mjpeg",
            "-video_size",
            self.resolution,
            "-framerate",
            str(self.fps),
            "-i",
            str(self.device),
            "-an",
            "-c:v",
            "copy",
            "-f",
            "image2pipe",
            "pipe:1",
        ]

    def stream(self) -> Iterator[bytes]:
        if not self._stream_lock.acquire(blocking=False):
            raise RuntimeError("the video capture already has a viewer")

        process: subprocess.Popen[bytes] | None = None
        try:
            process = subprocess.Popen(
                self.command(),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=0,
            )
            if process.stdout is None:  # pragma: no cover
                raise RuntimeError("ffmpeg stdout is unavailable")

            buffer = bytearray()
            while True:
                chunk = process.stdout.read(64 * 1024)
                if not chunk:
                    if process.poll() is not None:
                        break
                    continue
                buffer.extend(chunk)

                while True:
                    start = buffer.find(b"\xff\xd8")
                    if start < 0:
                        buffer.clear()
                        break
                    end = buffer.find(b"\xff\xd9", start + 2)
                    if end < 0:
                        if start:
                            del buffer[:start]
                        break
                    frame = bytes(buffer[start : end + 2])
                    del buffer[: end + 2]
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n"
                        + f"Content-Length: {len(frame)}\r\n\r\n".encode()
                        + frame
                        + b"\r\n"
                    )
        finally:
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            self._stream_lock.release()

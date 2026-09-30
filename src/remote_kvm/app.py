from __future__ import annotations

import errno
import os
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field

from .hid import HIDController
from .power import GpiodPowerController, PowerController, UnavailablePowerController
from .video import FFmpegMjpegProvider, VideoProvider
from .web import CONTROL_PAGE


class KeyPressRequest(BaseModel):
    key: str = Field(min_length=1, max_length=32)
    modifiers: list[str] = Field(default_factory=list, max_length=8)


class MouseMoveRequest(BaseModel):
    dx: int = Field(ge=-127, le=127)
    dy: int = Field(ge=-127, le=127)
    wheel: int = Field(default=0, ge=-127, le=127)


class MouseClickRequest(BaseModel):
    button: str = "left"


class ForceOffRequest(BaseModel):
    confirmation: Literal["FORCE_OFF"]


def power_from_environment() -> PowerController:
    line = os.getenv("REMOTE_KVM_POWER_LINE")
    if line is None:
        return UnavailablePowerController()
    return GpiodPowerController.open(
        chip_name=os.getenv("REMOTE_KVM_POWER_CHIP", "/dev/gpiochip1"),
        line_offset=int(line),
        active_low=os.getenv("REMOTE_KVM_POWER_ACTIVE_LOW", "true").lower()
        in {"1", "true", "yes", "on"},
    )


def create_app(
    hid: HIDController | None = None,
    power: PowerController | None = None,
    video: VideoProvider | None = None,
) -> FastAPI:
    application = FastAPI(title="Orange Pi Remote KVM", version="0.1.0")
    application.state.hid = hid or HIDController.system_default()
    application.state.power = power or power_from_environment()
    application.state.video = video or FFmpegMjpegProvider(
        device=os.getenv(
            "REMOTE_KVM_VIDEO_DEVICE",
            "/dev/v4l/by-id/usb-MACROSILICON_USB_Video-video-index0",
        ),
        resolution=os.getenv("REMOTE_KVM_VIDEO_RESOLUTION", "1280x720"),
        fps=int(os.getenv("REMOTE_KVM_VIDEO_FPS", "30")),
    )

    def hid_error(error: Exception) -> HTTPException:
        if isinstance(error, ValueError):
            return HTTPException(status_code=422, detail=str(error))
        if isinstance(error, OSError):
            if error.errno in (errno.EAGAIN, errno.ENODEV, errno.ENOENT):
                return HTTPException(
                    status_code=503,
                    detail="HID host is unavailable or not connected",
                )
            return HTTPException(status_code=500, detail=f"HID write failed: {error}")
        return HTTPException(status_code=500, detail="unexpected HID error")

    @application.get("/", response_class=HTMLResponse)
    def root() -> str:
        return CONTROL_PAGE

    @application.get("/api/v1/status")
    def status() -> dict[str, object]:
        return {
            "hid": application.state.hid.status(),
            "power": application.state.power.status(),
            "video": application.state.video.status(),
        }

    @application.post("/api/v1/keyboard/press")
    def keyboard_press(request: KeyPressRequest) -> dict[str, object]:
        try:
            application.state.hid.keyboard.press(
                request.key, tuple(request.modifiers)
            )
        except (OSError, ValueError) as error:
            raise hid_error(error) from error
        return {"sent": request.key, "modifiers": request.modifiers}

    @application.post("/api/v1/mouse/move")
    def mouse_move(request: MouseMoveRequest) -> dict[str, int]:
        try:
            application.state.hid.mouse.move(request.dx, request.dy, request.wheel)
        except (OSError, ValueError) as error:
            raise hid_error(error) from error
        return request.model_dump()

    @application.post("/api/v1/mouse/click")
    def mouse_click(request: MouseClickRequest) -> dict[str, str]:
        try:
            application.state.hid.mouse.click(request.button)
        except (OSError, ValueError) as error:
            raise hid_error(error) from error
        return {"clicked": request.button}

    @application.post("/api/v1/power/press")
    def power_press() -> dict[str, object]:
        try:
            application.state.power.power_press()
        except RuntimeError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        return {"action": "power", "seconds": 0.2}

    @application.post("/api/v1/power/force-off")
    def power_force_off(request: ForceOffRequest) -> dict[str, object]:
        try:
            application.state.power.force_off()
        except RuntimeError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        return {"action": "force_off", "seconds": 5.0}

    @application.get("/api/v1/video/stream.mjpg")
    def video_stream() -> StreamingResponse:
        if not application.state.video.status()["available"]:
            raise HTTPException(status_code=503, detail="video capture is unavailable")
        return StreamingResponse(
            application.state.video.stream(),
            media_type="multipart/x-mixed-replace; boundary=frame",
            headers={"Cache-Control": "no-store"},
        )

    return application


app = create_app()

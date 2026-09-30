from __future__ import annotations

import errno

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .hid import HIDController
from .power import PowerController, UnavailablePowerController
from .video import UnavailableVideoProvider, VideoProvider


class KeyPressRequest(BaseModel):
    key: str = Field(min_length=1, max_length=32)
    modifiers: list[str] = Field(default_factory=list, max_length=8)


class MouseMoveRequest(BaseModel):
    dx: int = Field(ge=-127, le=127)
    dy: int = Field(ge=-127, le=127)
    wheel: int = Field(default=0, ge=-127, le=127)


class MouseClickRequest(BaseModel):
    button: str = "left"


def create_app(
    hid: HIDController | None = None,
    power: PowerController | None = None,
    video: VideoProvider | None = None,
) -> FastAPI:
    application = FastAPI(title="Orange Pi Remote KVM", version="0.1.0")
    application.state.hid = hid or HIDController.system_default()
    application.state.power = power or UnavailablePowerController()
    application.state.video = video or UnavailableVideoProvider()

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

    @application.get("/")
    def root() -> dict[str, str]:
        return {"status": "Remote KVM API running", "docs": "/docs"}

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

    return application


app = create_app()

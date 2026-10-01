from __future__ import annotations

import os
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .power import GpiodPowerController, PowerController, UnavailablePowerController
from .web import CONTROL_PAGE


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


def create_app(power: PowerController | None = None) -> FastAPI:
    application = FastAPI(
        title="Orange Pi Remote Power Control",
        version="0.2.0",
    )
    force_off_seconds = float(os.getenv("REMOTE_KVM_FORCE_OFF_SECONDS", "8.0"))
    if not 4.0 <= force_off_seconds <= 15.0:
        raise ValueError("REMOTE_KVM_FORCE_OFF_SECONDS must be between 4 and 15")
    application.state.force_off_seconds = force_off_seconds
    application.state.power = power or power_from_environment()

    @application.get("/", response_class=HTMLResponse, include_in_schema=False)
    def root() -> str:
        return CONTROL_PAGE

    @application.get("/api/v1/status")
    def status() -> dict[str, object]:
        power_status = application.state.power.status()
        power_status["force_off_seconds"] = application.state.force_off_seconds
        return {"power": power_status}

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
            application.state.power.force_off(
                seconds=application.state.force_off_seconds
            )
        except RuntimeError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        return {
            "action": "force_off",
            "seconds": application.state.force_off_seconds,
        }

    return application


app = create_app()

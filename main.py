from fastapi import FastAPI
import time

app = FastAPI()

KEYBOARD = "/dev/hidg0"
MOUSE = "/dev/hidg1"

KEYS = {
    "a": 0x04,
    "b": 0x05,
    "c": 0x06,
    "d": 0x07,
    "e": 0x08,
    "enter": 0x28,
    "esc": 0x29,
    "space": 0x2C,
}

def key_press(code: int):
    with open(KEYBOARD, "wb", buffering=0) as f:
        f.write(bytes([0, 0, code, 0, 0, 0, 0, 0]))
        time.sleep(0.05)
        f.write(bytes(8))

@app.get("/")
def root():
    return {"status": "Remote KVM API running"}

@app.post("/key/{key}")
def send_key(key: str):
    if key not in KEYS:
        return {"error": "unknown key"}

    key_press(KEYS[key])

    return {"sent": key}

@app.post("/mouse/move")
def mouse_move(dx: int = 0, dy: int = 0):
    dx = max(-127, min(127, dx))
    dy = max(-127, min(127, dy))

    with open(MOUSE, "wb", buffering=0) as f:
        f.write(bytes([
            0,
            dx & 0xff,
            dy & 0xff,
            0,
        ]))

    return {"dx": dx, "dy": dy}

@app.post("/mouse/click")
def mouse_click():
    with open(MOUSE, "wb", buffering=0) as f:
        f.write(bytes([1, 0, 0, 0]))
        time.sleep(0.05)
        f.write(bytes([0, 0, 0, 0]))

    return {"clicked": True}

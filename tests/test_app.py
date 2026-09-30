import unittest

from remote_kvm.app import create_app
from remote_kvm.hid import HIDController, KeyboardDevice, MouseDevice
from remote_kvm.video import UnavailableVideoProvider


class ApplicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.keyboard_reports: list[bytes] = []
        self.mouse_reports: list[bytes] = []
        hid = HIDController(
            keyboard=KeyboardDevice(
                press_seconds=0,
                writer=self.keyboard_reports.append,
            ),
            mouse=MouseDevice(
                click_seconds=0,
                writer=self.mouse_reports.append,
            ),
        )
        self.app = create_app(hid=hid, video=UnavailableVideoProvider())

    def test_routes_are_present(self) -> None:
        paths = self.app.openapi()["paths"]
        self.assertIn("/api/v1/keyboard/press", paths)
        self.assertIn("/api/v1/mouse/move", paths)
        self.assertIn("/api/v1/mouse/click", paths)
        self.assertIn("/api/v1/status", paths)
        self.assertIn("/api/v1/video/stream.mjpg", paths)

    def test_extension_backends_are_unconfigured(self) -> None:
        self.assertEqual(
            self.app.state.power.status(),
            {"available": False, "backend": "unconfigured"},
        )
        self.assertEqual(
            self.app.state.video.status(),
            {"available": False, "backend": "unconfigured"},
        )


if __name__ == "__main__":
    unittest.main()

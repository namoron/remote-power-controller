import os
import unittest
from unittest.mock import patch

from remote_kvm.app import create_app


class ApplicationTests(unittest.TestCase):
    def test_only_power_api_routes_are_present(self) -> None:
        paths = create_app().openapi()["paths"]
        self.assertEqual(
            {path for path in paths if path.startswith("/api/")},
            {
                "/api/v1/status",
                "/api/v1/power/press",
                "/api/v1/power/force-off",
            },
        )

    def test_power_backend_is_unconfigured_without_gpio_environment(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            app = create_app()
        self.assertEqual(
            app.state.power.status(),
            {"available": False, "backend": "unconfigured"},
        )

    def test_force_off_duration_is_validated(self) -> None:
        with patch.dict(
            os.environ,
            {"REMOTE_KVM_FORCE_OFF_SECONDS": "3"},
            clear=True,
        ):
            with self.assertRaises(ValueError):
                create_app()


if __name__ == "__main__":
    unittest.main()

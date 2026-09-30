import unittest

from remote_kvm.power.gpiod import GpiodPowerController


class FakeLine:
    def __init__(self) -> None:
        self.values: list[int] = []

    def set_value(self, value: int) -> None:
        self.values.append(value)


class GpiodPowerControllerTests(unittest.TestCase):
    def test_active_low_power_pulse_returns_inactive(self) -> None:
        line = FakeLine()
        controller = GpiodPowerController(
            line=line,
            chip_name="/dev/gpiochip1",
            line_offset=20,
            active_low=True,
        )
        controller.power_press(seconds=0)
        self.assertEqual(line.values, [0, 1])

    def test_active_high_force_off_returns_inactive(self) -> None:
        line = FakeLine()
        controller = GpiodPowerController(
            line=line,
            chip_name="/dev/gpiochip1",
            line_offset=20,
            active_low=False,
        )
        controller.force_off(seconds=0)
        self.assertEqual(line.values, [1, 0])


if __name__ == "__main__":
    unittest.main()

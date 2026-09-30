import unittest

from remote_kvm.hid.devices import KeyboardDevice, MouseDevice


class KeyboardReportTests(unittest.TestCase):
    def test_letter_with_modifiers(self) -> None:
        report = KeyboardDevice.report("a", ("left_ctrl", "left_shift"))
        self.assertEqual(report, bytes((0x03, 0, 0x04, 0, 0, 0, 0, 0)))

    def test_unknown_key_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown key"):
            KeyboardDevice.report("definitely-not-a-key")


class MouseReportTests(unittest.TestCase):
    def test_signed_values_are_encoded(self) -> None:
        self.assertEqual(
            MouseDevice.report(dx=-1, dy=127, wheel=-127),
            bytes((0, 0xFF, 0x7F, 0x81)),
        )

    def test_out_of_range_movement_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "dx"):
            MouseDevice.report(dx=128)


if __name__ == "__main__":
    unittest.main()

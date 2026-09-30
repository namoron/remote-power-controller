import unittest
from pathlib import Path

from remote_kvm.video import FFmpegMjpegProvider


class FFmpegMjpegProviderTests(unittest.TestCase):
    def test_command_passes_through_mjpeg(self) -> None:
        provider = FFmpegMjpegProvider(
            device=Path("/dev/test-video"),
            resolution="1280x720",
            fps=30,
            ffmpeg="/usr/bin/ffmpeg",
        )
        command = provider.command()
        self.assertIn("/dev/test-video", command)
        self.assertIn("1280x720", command)
        self.assertEqual(command[command.index("-c:v") + 1], "copy")


if __name__ == "__main__":
    unittest.main()

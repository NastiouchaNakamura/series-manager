import subprocess
import tempfile
import os
from typing import Callable
from optimizatron.codecs import VideoCodec


class Video:
    def __init__(self, codec: VideoCodec, file_path: str, temp_dir: tempfile.TemporaryDirectory):
        self.codec: VideoCodec = codec
        self.file_path: str = file_path
        self.temp_dir: tempfile.TemporaryDirectory = temp_dir

        self.size = os.path.getsize(self.file_path)
        self.width = int(subprocess.run(["ffprobe", "-v", "error", "-of", "default=noprint_wrappers=1:nokey=1", "-select_streams", "v:0", "-show_entries", "stream=width", self.file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout)
        self.height = int(subprocess.run(["ffprobe", "-v", "error", "-of", "default=noprint_wrappers=1:nokey=1", "-select_streams", "v:0", "-show_entries", "stream=height", self.file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout)
        if self.width == 3840 or self.height == 2160:
            self.definition = "4K"
        elif self.width == 1920 or self.height == 1440:
            self.definition = "1440p"
        elif self.width == 1920 or self.height == 1080:
            self.definition = "1080p"
        elif self.width == 1280 or self.height == 720:
            self.definition = "720p"
        elif self.width == 720 or self.height == 480:
            self.definition = "480p"
        elif self.width == 640 or self.height == 360:
            self.definition = "360p"
        else:
            self.definition = f"{self.width}x{self.height}"

    def optimize(self, increment_progress_bar: Callable[[], None]) -> None:
        if self.codec is VideoCodec.H265:
            increment_progress_bar()
            return
        elif self.codec is VideoCodec.H264:
            increment_progress_bar()
            return
        else:
            raise ValueError(f"Codec '{self.codec}' unsupported")

    def get_optimization_steps(self) -> int:
        if self.codec is VideoCodec.H265:
            return 1
        elif self.codec is VideoCodec.H264:
            return 1
        else:
            raise ValueError(f"Codec '{self.codec}' unsupported")

import re
import subprocess
import tempfile
import os
from time import sleep
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
            # Correction du chemin
            # Obligé de transcoder en MKV H265, et pas en H265 direct, pour éviter les bugs (frames manquantes, audio désynchronisé, etc…)
            mkv_file_path = f"{self.temp_dir.name}/{id(self)}_h265.mkv"
            # https://scottstuff.net/posts/2025/03/17/benchmarking-ffmpeg-h265/
            proc = subprocess.Popen(["ffmpeg", "-i", self.file_path, "-codec:v", "libx265", "-crf", "20.6", "-tune", "fastdecode", "-preset", "slow", mkv_file_path], stderr = subprocess.PIPE, stdout = subprocess.PIPE)
            if proc.stderr is None:
                raise ValueError("Popen process stderr is None")
    
            # Pour la barre de progression
            line = b""
            previously_transcoded_seconds = 0
            total_seconds_to_transcode = self.get_optimization_steps()
            while proc.poll() is None:
                next_b = proc.stderr.read(1)
                if next_b == b"\r":
                    finds = re.findall(r"time= ?(\d\d):(\d\d):(\d\d).\d\d", line.decode("utf-8"))
                    if len(finds) == 0:
                        continue
                    transcoded_seconds = int(finds[0][0]) * 3600 + int(finds[0][1]) * 60 + int(float(f"{finds[0][2]}"))
                    for _ in range(transcoded_seconds - previously_transcoded_seconds):
                        increment_progress_bar()
                    previously_transcoded_seconds = transcoded_seconds
                    line = b""
                    sleep(0.5)
                else:
                    line += next_b
            
            for _ in range(total_seconds_to_transcode - previously_transcoded_seconds):
                increment_progress_bar()

            proc.wait()
    
            # Mise à jour des champs
            self.file_path = mkv_file_path
            self.codec = VideoCodec.H265
        else:
            raise ValueError(f"Codec '{self.codec}' unsupported")

    def get_optimization_steps(self) -> int:
        if self.codec is VideoCodec.H265:
            return 1
        elif self.codec is VideoCodec.H264:
            # 1 étape = 1 seconde de vidéo
            proc = subprocess.run(['ffprobe', "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", self.file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            return int(float(proc.stdout))
        else:
            raise ValueError(f"Codec '{self.codec}' unsupported")

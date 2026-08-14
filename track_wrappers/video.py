import re
import subprocess
import tempfile
import os
from time import sleep
from typing import Callable
from model.codecs import VideoCodec


class Video:
    def __init__(self, codec: VideoCodec, file_path: str, temp_dir: tempfile.TemporaryDirectory):
        self.codec: VideoCodec = codec
        self.file_path: str = file_path
        self.temp_dir: tempfile.TemporaryDirectory = temp_dir
        self.size: int
        self.duration: float
        self.metric: float
        self.fetch_infos()
        self.width = int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width", "-of", "default=noprint_wrappers=1:nokey=1", self.file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout)
        self.height = int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=height", "-of", "default=noprint_wrappers=1:nokey=1", self.file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout)
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


    def fetch_infos(self) -> None:
        self.size = os.path.getsize(self.file_path)
        self.duration = float(subprocess.run(['ffprobe', "-v", "error", "-select_streams", "v:0", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", self.file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout)
        self.metric = (self.size / 1e9) / (self.duration / 3600) # Métrique en Go/h (Gigaocter par heure), plus c'est bas, plus c'est compressé

    def should_be_optimized(self) -> bool:
        # Modifier ici pour forcer la conversion sous d'autres conditions.
        # 1.2 Go/h est normalement supérieur à la métrique d'un fichier AV1
        # (en résolution 1080p ou inférieur). Un fichier H265 ou même H264 peut
        # être inférieur s'il est très compressé en amont, mais parmi les
        # sources disponibles, c'est rare.
        return self.metric > 1.2

    def optimize(self, increment_progress_bar: Callable[[], None], force_av1: bool = False) -> None:
        if self.codec is VideoCodec.AV1:
            increment_progress_bar()

        elif self.codec is VideoCodec.H265:
            if force_av1 or self.should_be_optimized():
                self.transcode_to_av1(increment_progress_bar)
            else:
                increment_progress_bar()

        elif self.codec is VideoCodec.H264:
            if force_av1 or self.should_be_optimized():
                self.transcode_to_av1(increment_progress_bar)
            else:
                increment_progress_bar()
        
        else:
            raise ValueError(f"Codec '{self.codec}' unsupported")

    def get_optimization_steps(self, force_av1: bool = False) -> int:
        if self.codec is VideoCodec.AV1:
            return 1

        elif self.codec is VideoCodec.H265:
            if force_av1 or self.should_be_optimized():
                return int(self.duration)
            else:
                return 1

        elif self.codec is VideoCodec.H264:
            if force_av1 or self.should_be_optimized():
                return int(self.duration)
            else:
                return 1
        
        else:
            raise ValueError(f"Codec '{self.codec}' unsupported")

    def transcode_to_av1(self, increment_progress_bar: Callable[[], None]) -> None:
        # Correction du chemin
        # Obligé de transcoder en MKV H265, et pas en H265 direct, pour éviter les bugs (frames manquantes, audio désynchronisé, etc…)
        opt_file_path = f"{self.temp_dir.name}/{id(self)}_opt.mkv"

        # Pour une compression en H.265 (outdated) :
        # https://scottstuff.net/posts/2025/03/17/benchmarking-ffmpeg-h265/
        #proc = subprocess.Popen(["ffmpeg", "-i", self.file_path, "-codec:v", "libx265", "-crf", "20.6", "-tune", "fastdecode", "-preset", "slow", mkv_file_path], stderr = subprocess.PIPE, stdout = subprocess.PIPE)
        
        # Pour une compression en AV1 (à jour) :
        # https://www.reddit.com/r/ffmpeg/comments/1d0ci91/comment/l5m8322/?context=3
        proc = subprocess.Popen(["ffmpeg", "-i", self.file_path, "-codec:v", "libsvtav1", "-crf", "30", "-preset", "4", "-g", "240", "-pix_fmt", "yuv420p10le", "-svtav1-params", "tune=0", opt_file_path], stderr = subprocess.PIPE, stdout = subprocess.PIPE)

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
        self.file_path = opt_file_path
        self.codec = VideoCodec.AV1
        self.fetch_infos()
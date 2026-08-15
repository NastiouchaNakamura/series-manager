import os
import re
import subprocess
import tempfile
from time import sleep
from typing import Callable
from model.codecs import AudioCodec


class Audio:
    def __init__(self, codec: AudioCodec, file_path: str, temp_dir: tempfile.TemporaryDirectory, language: str = "UND", flag_default: bool = False, flag_forced: bool = False, flag_hearing_impaired: bool = False, flag_visual_impaired: bool = False, flag_original: bool = False):
        self.codec: AudioCodec = codec
        self.file_path: str = file_path
        self.temp_dir: tempfile.TemporaryDirectory = temp_dir
        self.language: str = language.upper()
        self.flag_default: bool = flag_default
        self.flag_forced: bool = flag_forced
        self.flag_hearing_impaired: bool = flag_hearing_impaired
        self.flag_visual_impaired: bool = flag_visual_impaired
        self.flag_original: bool = flag_original
        self.fetch_infos()

    def fetch_infos(self) -> None:
        self.size: int = os.path.getsize(self.file_path)
        self.duration: float = float(subprocess.run(['ffprobe', "-v", "error", "-select_streams", "a:0", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", self.file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout)

    def optimize(self, increment_progress_bar: Callable[[], None] = lambda: None) -> None:
        if self.codec is AudioCodec.AAC:
            increment_progress_bar()
            
        elif self.codec is AudioCodec.AC3:
            increment_progress_bar()
            
        elif self.codec is AudioCodec.EAC3:
            increment_progress_bar()
            
        elif self.codec is AudioCodec.VORBIS:
            self.transcode_to_acc(increment_progress_bar)
        
        else:
            raise ValueError(f"Codec '{self.codec}' unsupported")

    def get_optimization_steps(self) -> int:
        if self.codec is AudioCodec.AAC:
            return 0
        
        elif self.codec is AudioCodec.AC3:
            return 0
        
        elif self.codec is AudioCodec.EAC3:
            return 0
        
        elif self.codec is AudioCodec.VORBIS:
            return int(self.duration)
        
        else:
            raise ValueError(f"Codec '{self.codec}' unsupported")

    def transcode_to_acc(self, increment_progress_bar: Callable[[], None]) -> None:
        # Chemin
        acc_file_path = f"{self.temp_dir.name}/{id(self)}.aac"

        # Transcodage ACC :
        proc = subprocess.Popen(["ffmpeg", "-i", self.file_path, "-codec:a", "aac", acc_file_path], stderr = subprocess.PIPE, stdout = subprocess.PIPE)

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
        self.file_path = acc_file_path
        self.codec = AudioCodec.AAC
        self.fetch_infos()

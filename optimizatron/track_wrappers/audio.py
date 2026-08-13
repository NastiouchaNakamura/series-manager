import os
import tempfile
from typing import Callable
from optimizatron.codecs import AudioCodec


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
        self.size = os.path.getsize(self.file_path)

    def optimize(self, increment_progress_bar: Callable[[], None]) -> None:
        if self.codec is AudioCodec.AC3:
            increment_progress_bar()
            return
        elif self.codec is AudioCodec.AAC:
            increment_progress_bar()
            return
        elif self.codec is AudioCodec.EAC3:
            increment_progress_bar()
            return
        else:
            raise ValueError(f"Codec '{self.codec}' unsupported")

    def get_optimization_steps(self) -> int:
        if self.codec is AudioCodec.AC3:
            return 1
        elif self.codec is AudioCodec.AAC:
            return 1
        elif self.codec is AudioCodec.EAC3:
            return 1
        else:
            raise ValueError(f"Codec '{self.codec}' unsupported")

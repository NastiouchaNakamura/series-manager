import tempfile
from enum import StrEnum
from typing import Any, Callable, Literal
from wrappers.pgs import Pgs


class SupportedCodec(StrEnum):
    SRT = "SubRip/SRT" # Optimized
    PGS = "HDMV PGS"

class Subtitles:
    def __init__(self, codec: str, file_path: str, temp_dir: tempfile.TemporaryDirectory, language: str = "UND", language_codes: list[str] | None = None, flag_default: bool = False, flag_forced: bool = False, flag_hearing_impaired: bool = False, flag_visual_impaired: bool = False, flag_original: bool = False):
        if codec not in SupportedCodec:
            raise ValueError(f"Codec '{self.codec}' unsupported")
        
        self.codec: SupportedCodec = SupportedCodec(codec)
        self.file_path: str = file_path
        self.temp_dir: tempfile.TemporaryDirectory = temp_dir
        self.language: str = language.upper()
        self.language_codes: list[str] = [self.language] if language_codes is None else language_codes
        self.flag_default: bool = flag_default
        self.flag_forced: bool = flag_forced
        self.flag_hearing_impaired: bool = flag_hearing_impaired
        self.flag_visual_impaired: bool = flag_visual_impaired
        self.flag_original: bool = flag_original
        self.subfile: Any | None = None

    def optimize(self, step_done_callback: Callable[[], None]) -> None:
        # step_done_callback: à appeler à chaque itération achevée (nb d'itérations donné par get_optimization_steps)
        if self.codec is SupportedCodec.SRT:
            step_done_callback()
            return
        elif self.codec is SupportedCodec.PGS:
            if type(self.subfile) is not Pgs:
                self.subfile = Pgs(self.file_path, self.language_codes, self.temp_dir)
            self.file_path = self.subfile.to_srt(step_done_callback)
            self.codec = SupportedCodec.SRT
            self.subfile = None
        else:
            raise ValueError(f"Codec '{self.codec}' unsupported")

    def get_optimization_steps(self) -> int:
        if self.codec is SupportedCodec.SRT:
            return 1
        elif self.codec is SupportedCodec.PGS:
            if type(self.subfile) is not Pgs:
                self.subfile = Pgs(self.file_path, self.language_codes, self.temp_dir)
            return len(self.subfile.subtitles) + len(self.subfile.subtitles[:10]) * 5
        else:
            raise ValueError(f"Codec '{self.codec}' unsupported")

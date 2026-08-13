import os
import tempfile
from typing import Any, Callable
from optimizatron.file_wrappers.pgs import Pgs
from optimizatron.file_wrappers.ass import Ass
from optimizatron.file_wrappers.tx3g import Tx3g
from optimizatron.codecs import SubtitlesCodec


class Subtitles:
    def __init__(self, codec: SubtitlesCodec, file_path: str, temp_dir: tempfile.TemporaryDirectory, language: str = "UND", language_codes: list[str] | None = None, flag_default: bool = False, flag_forced: bool = False, flag_hearing_impaired: bool = False, flag_visual_impaired: bool = False, flag_original: bool = False):
        self.codec: SubtitlesCodec = codec
        self.file_path: str = file_path
        self.temp_dir: tempfile.TemporaryDirectory = temp_dir
        self.language: str = language.upper()
        self.language_codes: list[str] = [self.language] if language_codes is None else language_codes
        self.flag_default: bool = flag_default
        self.flag_forced: bool = flag_forced
        self.flag_hearing_impaired: bool = flag_hearing_impaired
        self.flag_visual_impaired: bool = flag_visual_impaired
        self.flag_original: bool = flag_original
        self.size = os.path.getsize(self.file_path)
        self.subfile: Any | None = None

    def optimize(self, increment_progress_bar: Callable[[], None]) -> None:
        # step_done_callback: à appeler à chaque itération achevée (nb d'itérations donné par get_optimization_steps)
        if self.codec is SubtitlesCodec.SRT:
            increment_progress_bar()
            return
        elif self.codec is SubtitlesCodec.PGS:
            if type(self.subfile) is not Pgs:
                self.subfile = Pgs(self.file_path, self.language_codes, self.temp_dir)
            self.file_path = self.subfile.to_srt(increment_progress_bar)
            self.codec = SubtitlesCodec.SRT
            self.subfile = None
        elif self.codec is SubtitlesCodec.ASS:
            if type(self.subfile) is not Ass:
                self.subfile = Ass(self.file_path, self.temp_dir)
            self.file_path = self.subfile.to_srt(increment_progress_bar)
            self.codec = SubtitlesCodec.SRT
            self.subfile = None
        elif self.codec is SubtitlesCodec.TX3G:
            if type(self.subfile) is not Tx3g:
                self.subfile = Tx3g(self.file_path, self.temp_dir)
            self.file_path = self.subfile.to_srt(increment_progress_bar)
            self.codec = SubtitlesCodec.SRT
            self.subfile = None
        else:
            raise ValueError(f"Codec '{self.codec}' unsupported")

    def get_optimization_steps(self) -> int:
        if self.codec is SubtitlesCodec.SRT:
            return 1
        elif self.codec is SubtitlesCodec.PGS:
            if type(self.subfile) is not Pgs:
                self.subfile = Pgs(self.file_path, self.language_codes, self.temp_dir)
            return len(self.subfile.subtitles) + len(self.subfile.subtitles[:10]) * 5
        elif self.codec is SubtitlesCodec.ASS:
            if type(self.subfile) is not Ass:
                self.subfile = Ass(self.file_path, self.temp_dir)
            return len(self.subfile.subtitles)
        elif self.codec is SubtitlesCodec.TX3G:
            if type(self.subfile) is not Tx3g:
                self.subfile = Tx3g(self.file_path, self.temp_dir)
            return len(self.subfile.subtitles)
        else:
            raise ValueError(f"Codec '{self.codec}' unsupported")

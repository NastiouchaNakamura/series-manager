from enum import StrEnum
import tempfile
from typing import Callable


class SupportedCodec(StrEnum):
    AC3 = "AC-3" # Optimized
    AAC = "AAC" # Optimized

class Audio:
    def __init__(self, codec: str, file_path: str, temp_dir: tempfile.TemporaryDirectory, language: str = "UND", flag_default: bool = False, flag_forced: bool = False, flag_hearing_impaired: bool = False, flag_visual_impaired: bool = False, flag_original: bool = False):
        if codec not in SupportedCodec:
            raise ValueError(f"Codec '{codec}' unsupported")
        
        self.codec: SupportedCodec = SupportedCodec(codec)
        self.file_path: str = file_path
        self.temp_dir: tempfile.TemporaryDirectory = temp_dir
        self.language: str = language.upper()
        self.flag_default: bool = flag_default
        self.flag_forced: bool = flag_forced
        self.flag_hearing_impaired: bool = flag_hearing_impaired
        self.flag_visual_impaired: bool = flag_visual_impaired
        self.flag_original: bool = flag_original

    def optimize(self, step_done_callback: Callable[[], None]) -> None:
        # step_done_callback: à appeler à chaque itération achevée (nb d'itérations donné par get_optimization_steps)
        if self.codec is SupportedCodec.AC3:
            step_done_callback()
            return
        elif self.codec is SupportedCodec.AAC:
            step_done_callback()
            return
        else:
            raise ValueError(f"Codec '{self.codec}' unsupported")

    def get_optimization_steps(self) -> int:
        if self.codec is SupportedCodec.AC3:
            return 1
        elif self.codec is SupportedCodec.AAC:
            return 1
        else:
            raise ValueError(f"Codec '{self.codec}' unsupported")

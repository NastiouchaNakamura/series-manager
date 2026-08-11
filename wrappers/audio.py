import tempfile


class Audio:
    def __init__(self, codec: str, file_path: str, temp_dir: tempfile.TemporaryDirectory, language: str = "UND", flag_default: bool = False, flag_forced: bool = False, flag_hearing_impaired: bool = False, flag_visual_impaired: bool = False, flag_original: bool = False):
        self.codec = codec
        self.file_path = file_path
        self.temp_dir = temp_dir
        self.language = language.upper()
        self.flag_default = flag_default
        self.flag_forced = flag_forced
        self.flag_hearing_impaired = flag_hearing_impaired
        self.flag_visual_impaired = flag_visual_impaired
        self.flag_original = flag_original
        if self.codec == "AC-3":
            self.video_tool = AudioToolAc3(self.file_path)
        elif self.codec == "AAC":
            self.video_tool = AudioToolAac(self.file_path)
        else:
            raise ValueError(f"Codec '{self.codec}' unsupported")

    def optimize(self) -> None:
        new_codec, new_file_path = self.video_tool.optimize(self.file_path)
        self.codec = new_codec
        self.file_path = new_file_path


class AudioToolAc3:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def optimize(self, file_path: str):
        return "AC-3", file_path


class AudioToolAac:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def optimize(self, file_path: str):
        return "AAC", file_path

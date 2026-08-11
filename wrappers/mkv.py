import pymkv
import tempfile
from tqdm import tqdm
from wrappers.audio import Audio
from wrappers.subtitles import Subtitles


MKVTOOLS_PATH = "/Applications/MKVToolNix.app/Contents/MacOS/"

def is_h265_mkv(file_path):
    mkv_file = pymkv.MKVFile(file_path, mkvmerge_path = f"{MKVTOOLS_PATH}/mkvmerge")
    is_h265 = False
    for track in mkv_file.tracks:
        if track.track_type == "video":
            if track.track_codec is None:
                raise ValueError("Video track codec is None")
            elif track.track_codec == "HEVC/H.265/MPEG-H":
                is_h265 = True
                break
    return is_h265


class Mkv:
    def __init__(self, title: str, year: int, original_language: str = "UND", temp_dir: tempfile.TemporaryDirectory | None = None):
        self.title: str = title
        self.year: int = year
        self.original_language: str = original_language
        self.temp_dir: tempfile.TemporaryDirectory = tempfile.TemporaryDirectory() if temp_dir is None else temp_dir
        self.video: pymkv.MKVTrack | None = None
        self.definition = "?"
        self.audios: list[Audio] = []
        self.subtitles: list[Subtitles] = []


    def load_mkv(self, file_path: str):
        mkv_file = pymkv.MKVFile(file_path, mkvmerge_path = f"{MKVTOOLS_PATH}/mkvmerge")
        for track in tqdm(mkv_file.tracks, unit = "tracks", desc = "Extracting tracks from MKV file"):
            track.mkvextract_path = (f"{MKVTOOLS_PATH}/mkvextract",)
            track.compression = True

            if track.track_type == "video":
                if track.track_codec is None:
                    raise ValueError("Video track codec is None")
                else:
                    self.video = track
                    self.video.track_name = f"{self.definition} - {track.track_codec}"
                    self.video.language = "UND"
                    self.video.compression = True
                    #TODO: Définition
                    self.definition = "1080p"

            elif track.track_type == "audio":
                if track.track_codec is None:
                    raise ValueError("Video track codec is None")
                elif track.language is None:
                    # Si pas de langue, doublage inutile, pas conservé.
                    continue
                else:
                    source_path = track.extract(f"{self.temp_dir.name}", silent = True)
                    self.audios.append(Audio(
                        track.track_codec,
                        source_path,
                        self.temp_dir,
                        language = track.language if track.language is not None else "UND",
                        flag_default = track.default_track if track.default_track is not None else False,
                        flag_forced = track.forced_track if track.forced_track is not None else False,
                        flag_hearing_impaired = track.flag_hearing_impaired if track.flag_hearing_impaired is not None else False,
                        flag_visual_impaired = track.flag_visual_impaired if track.flag_visual_impaired is not None else False,
                        flag_original = track.matches_language(self.original_language)
                    ))

            elif track.track_type == "subtitles":
                if track.track_codec is None:
                    raise ValueError("Video track codec is None")
                elif track.language is None:
                    # Si pas de langue, sous-titre inutile, pas conservé.
                    continue
                else:
                    source_path = track.extract(f"{self.temp_dir.name}", silent = True)
                    self.subtitles.append(Subtitles(
                        track.track_codec,
                        source_path,
                        self.temp_dir,
                        language = track.language.upper() if track.language is not None else "UND",
                        language_codes = list(pymkv.Languages.language_equivalents(track.language, mkvmerge_path = (f'{MKVTOOLS_PATH}/mkvmerge',))) if track.language is not None else [],
                        flag_default = track.default_track if track.default_track is not None else False,
                        flag_forced = track.forced_track if track.forced_track is not None else False,
                        flag_hearing_impaired = track.flag_hearing_impaired if track.flag_hearing_impaired is not None else False,
                        flag_visual_impaired = track.flag_visual_impaired if track.flag_visual_impaired is not None else False,
                        flag_original = track.matches_language(self.original_language)
                    ))

            else:
                print(track.track_codec, f"{track.track_type}")
                pass
        mkv_file.cleanup()


    def optimize(self):
        class callback_tqdm(tqdm):
            def step_done(self):
                self.update(1)
        
        # Audio
        for audio in self.audios:
            audio.optimize()

        # Subtitles
        total_steps = 0
        for subtitle in self.subtitles:
            total_steps += subtitle.get_optimization_steps()
        
        progress_bar = callback_tqdm(total = total_steps, unit = "steps", desc = "Optimizing subtitles tracks")
        
        for subtitle in self.subtitles:
            subtitle.optimize(step_done_callback = progress_bar.step_done)


    def export(self, output_dir_path: str):
        if not output_dir_path.endswith("/"):
            output_dir_path += "/"

        mkv_file = pymkv.MKVFile(title = self.title, mkvmerge_path = f"{MKVTOOLS_PATH}/mkvmerge")

        if self.video is None:
            raise ValueError("Need video track for export")
        else:
            mkv_file.add_track(self.video)

        for audio in self.audios:
            track_name = audio.language.upper()
            if audio.flag_original:
                track_name += " (VO)"
            if audio.flag_visual_impaired:
                track_name += " (AD)"
            mkv_file.add_track(pymkv.MKVTrack(
                track_name = f"{track_name} - {audio.codec}",
                file_path = audio.file_path,
                language = audio.language,
                default_track = audio.flag_default,
                forced_track = audio.flag_forced,
                flag_hearing_impaired = audio.flag_hearing_impaired,
                flag_visual_impaired = audio.flag_visual_impaired,
                flag_original = audio.flag_original,
                compression = True,
                mkvmerge_path = f"{MKVTOOLS_PATH}/mkvmerge",
                mkvextract_path = f"{MKVTOOLS_PATH}/mkvextract"
            ))

        for subtitle in self.subtitles:
            track_name = subtitle.language.upper()
            if subtitle.flag_original:
                track_name += " (VO)"
            if subtitle.flag_hearing_impaired:
                track_name += " (SME)"
            if subtitle.flag_forced:
                track_name += " (Forcés)"
            mkv_file.add_track(pymkv.MKVTrack(
                track_name = f"{subtitle.language} - {subtitle.codec}",
                file_path = subtitle.file_path,
                language = subtitle.language,
                default_track = subtitle.flag_default,
                forced_track = subtitle.flag_forced,
                flag_hearing_impaired = subtitle.flag_hearing_impaired,
                flag_visual_impaired = subtitle.flag_visual_impaired,
                flag_original = subtitle.flag_original,
                compression = True,
                mkvmerge_path = f"{MKVTOOLS_PATH}/mkvmerge",
                mkvextract_path = f"{MKVTOOLS_PATH}/mkvextract"
            ))

        class callback_tqdm(tqdm):
            def update_to(self, current):
                self.update(current - self.n)

        with callback_tqdm(total = 100, unit = "%", desc = "Muxing to output MKV file") as progress_bar:
            mkv_file.mux(f"{output_dir_path}{self.title} ({self.year}).mkv", silent = True, progress_handler = progress_bar.update_to)
        mkv_file.cleanup()

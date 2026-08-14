import platform
import shutil
import subprocess
import pymkv
import tempfile
from tqdm import tqdm
from time import time
from track_wrappers.audio import Audio
from track_wrappers.subtitles import Subtitles
from track_wrappers.video import Video
from track_wrappers.metadata import Metadata
from model.codecs import VideoCodec, AudioCodec, SubtitlesCodec


class Movie:
    def __init__(self, title: str, year: int, season: int | None = None, episode: int | None = None, original_language: str = "UND", temp_dir: tempfile.TemporaryDirectory | None = None, mkvtools_path: str = ""):
        if (season is None and episode is not None) or (season is not None and episode is None):
                raise ValueError("Season and episode must both be None or both be not None")
        
        self.is_series: bool = season is not None and episode is not None
        self.title: str = f"{title} ({year})" if not self.is_series else f"{title} - S{season:02d}E{episode:02d}"
        self.original_language: str = original_language.upper()
        self.temp_dir: tempfile.TemporaryDirectory = tempfile.TemporaryDirectory() if temp_dir is None else temp_dir
        self.mkvtools_path = mkvtools_path
        self.video: Video | None = None
        self.audios: list[Audio] = []
        self.subtitles: list[Subtitles] = []
        self.metadata: Metadata | None = None
        self.init_ts: float = time()


    def load_file(self, file_path: str) -> None:
        # Extraction des pistes du fichier source et instantiation des wrappers
        if file_path.endswith(".mkv") or file_path.endswith(".MKV"):
            self.extract_mkvtools(file_path)
        else:
            self.extract_ffmpeg(file_path)

        self.remove_useless_tracks()


    def remove_useless_tracks(self) -> None:
        # Traitement des pistes selon critères
        if len(self.audios) == 1 and self.audios[0].language == "UND":
            # S'il n'y a qu'un seul audio d'une langue inconnue, on suppose que
            # c'est la langue originale
            self.audios[0].language = self.original_language
        else:
            # Sinon, on supprime toutes les pistes de langues inconnues
            self.audios = [audio for audio in self.audios if audio.language != "UND"]

        # Sous-titres en langue inconnue inutiles
        to_remove = []
        for subtitle in self.subtitles:
            if subtitle.language == "UND":
                to_remove.append(subtitle)
        for subtitle in to_remove:
            self.subtitles.remove(subtitle)

        # Pour 2 subs identiques sauf le codec on enlève celui qui n'est pas
        # SRT, ou bien le plus lourd. C'est un ordre total donc pas de cycle.
        to_remove = []
        for subtitle_1 in self.subtitles:
            for subtitle_2 in self.subtitles:
                if subtitle_1 is not subtitle_2 \
                    and subtitle_1 not in to_remove and subtitle_2 not in to_remove \
                    and subtitle_1.language == subtitle_2.language \
                    and subtitle_1.flag_forced == subtitle_2.flag_forced \
                    and subtitle_1.flag_hearing_impaired == subtitle_2.flag_hearing_impaired \
                    and subtitle_1.flag_visual_impaired == subtitle_2.flag_visual_impaired:
                    if subtitle_1.codec is SubtitlesCodec.SRT:
                        to_remove.append(subtitle_2)
                    elif subtitle_2.codec is SubtitlesCodec.SRT:
                        to_remove.append(subtitle_1)
                    elif subtitle_1.size < subtitle_2.size:
                        to_remove.append(subtitle_2)
                    else:
                        to_remove.append(subtitle_1)
        for subtitle in to_remove:
            self.subtitles.remove(subtitle)
        

    def extract_ffmpeg(self, file_path: str) -> None:
        # Pré-traitement
        proc = subprocess.run(['ffprobe', "-v", "error", "-show_entries", "stream=index,codec_name,codec_type:stream_tags=language,title", "-of", "default=nokey=1", file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stream_blocs = proc.stdout.decode("utf-8").split("[/STREAM]")
        if stream_blocs[-1].strip() == "":
            stream_blocs.pop()

        # Traitement
        with ProgressBar("Extracting tracks using FFMPEG", len(stream_blocs), "tracks") as progress_bar:
            for stream_str in stream_blocs:
                if stream_str == "" or stream_str == "\n":
                    break

                if not stream_str.strip().startswith("[STREAM]"):
                    raise ValueError(f"Unreadable output for ffprobe command: {stream_str}")

                fields = stream_str.strip().split("\n")[1:] # '[STREAM]' n'est pas un champ
                index = int(fields[0])
                codec_name = fields[1]
                type = fields[2]
                language = fields[3].upper()
                title = fields[4] if len(fields) > 4 else ""

                if type == "video":
                    codec = VideoCodec.by_name(codec_name)
                    # Il est impossible d'extraire en standalone quasi tous les
                    # codec vidéo (tous sauf H.265 et encore), car entre autre
                    # les standalone ne sont pas reconnus par FFMPEG pour les
                    # fonctions utilisées dans ce code, mais aussi cela
                    # provoque d'autre problèmes au remuxage (perte de frames
                    # et autres bugs en tout genre). Donc on utilise le fichier
                    # d'origine comme source. On le copie pour décharger les
                    # échanges avec le NAS. En cas de longue conversion, cela
                    # permet la veille.
                    file_path = shutil.copyfile(file_path, f"{self.temp_dir.name}/{id(self)}_original.{file_path.split("/")[-1].split(".")[-1]}")
                    self.video = Video(codec, file_path, self.temp_dir)

                elif type == "audio":
                    codec = AudioCodec.by_name(codec_name)
                    path = f"{self.temp_dir.name}/{id(self)}_{index}{codec.file_extension}"
                    subprocess.run(["ffmpeg", "-i", file_path, "-map", f"0:{index}", "-c", codec.ffmpeg_encoder if codec.ffmpeg_encoder is not None else "copy", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self.audios.append(Audio(
                        codec,
                        path,
                        self.temp_dir,
                        language = language,
                        flag_default = language == "FRE",
                        flag_forced = False,
                        flag_hearing_impaired = False,
                        flag_visual_impaired = "AD" in title.upper() or "AUDIO DESCRIPTION" in title.upper() or "AUDIO-DESCRIPTION" in title.upper() or "AUDIODESCRIPTION" in title.upper(),
                        flag_original = language == self.original_language
                    ))

                elif type == "subtitle":
                    codec = SubtitlesCodec.by_name(codec_name)
                    path = f"{self.temp_dir.name}/{id(self)}_{index}{codec.file_extension}"
                    subprocess.run(["ffmpeg", "-i", file_path, "-map", f"0:{index}", "-c", codec.ffmpeg_encoder if codec.ffmpeg_encoder is not None else "copy", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self.subtitles.append(Subtitles(
                        codec,
                        path,
                        self.temp_dir,
                        language = language,
                        flag_default = False,
                        flag_forced = "FORCÉ" in title.upper() or "FORCED" in title.upper(),
                        flag_hearing_impaired = "CC" in title.upper() or "CLOSED CAPTIONS" in title.upper() or "SDH" in title.upper(),
                        flag_visual_impaired = False,
                        flag_original = language == self.original_language
                    ))

                else:
                    raise ValueError(f"Unknown stream type: {type}")

                progress_bar.increment()


    def extract_mkvtools(self, mkv_file_path: str) -> None:
        # Pré-traitement
        mkv_file = pymkv.MKVFile(mkv_file_path, mkvmerge_path = f"{self.mkvtools_path}mkvmerge")

        # Traitement
        with ProgressBar("Extracting tracks using MKVTools", len(mkv_file.tracks), "tracks") as progress_bar:
            for track in mkv_file.tracks:
                track.mkvextract_path = (f"{self.mkvtools_path}mkvextract",)
                track.compression = True

                if track.track_type == "video":
                    if track.track_codec is None:
                        raise ValueError("Video track codec is None")
                    codec = VideoCodec.by_name(track.track_codec)
                    # Il est impossible d'extraire en standalone quasi tous les
                    # codec vidéo (tous sauf H.265 et encore), car entre autre
                    # les standalone ne sont pas reconnus par FFMPEG pour les
                    # fonctions utilisées dans ce code, mais aussi cela
                    # provoque d'autre problèmes au remuxage (perte de frames
                    # et autres bugs en tout genre). Donc on utilise le fichier
                    # d'origine comme source. On le copie pour décharger les
                    # échanges avec le NAS. En cas de longue conversion, cela
                    # permet la veille.
                    file_path = shutil.copyfile(mkv_file_path, f"{self.temp_dir.name}/{id(self)}_original.mkv")
                    self.video = Video(codec, file_path, self.temp_dir)

                elif track.track_type == "audio":
                    if track.track_codec is None:
                        raise ValueError("Audio track codec is None")
                    codec = AudioCodec.by_name(track.track_codec)
                    source_path = track.extract(f"{self.temp_dir.name}", silent = True)
                    self.audios.append(Audio(
                        AudioCodec.by_name(track.track_codec),
                        source_path,
                        self.temp_dir,
                        language = track.language if track.language is not None else "UND",
                        flag_default = track.default_track if track.default_track is not None else track.language == "FRE",
                        flag_forced = False if track.track_name is None else "FORCÉ" in track.track_name.upper() or "FORCED" in track.track_name.upper(),
                        flag_hearing_impaired = False,
                        flag_visual_impaired = track.flag_visual_impaired if track.flag_visual_impaired is not None else False if track.track_name is None else "AD" in track.track_name.upper() or "AUDIO DESCRIPTION" in track.track_name.upper() or "AUDIO-DESCRIPTION" in track.track_name.upper() or "AUDIODESCRIPTION" in track.track_name.upper(),
                        flag_original = track.matches_language(self.original_language)
                    ))

                elif track.track_type == "subtitles":
                    if track.track_codec is None:
                        raise ValueError("Subtitles track codec is None")
                    if track.language is None:
                        raise ValueError("Subtitles track has no language")
                    codec = SubtitlesCodec.by_name(track.track_codec)
                    source_path = track.extract(f"{self.temp_dir.name}", silent = True)
                    self.subtitles.append(Subtitles(
                        SubtitlesCodec.by_name(track.track_codec),
                        source_path,
                        self.temp_dir,
                        language = track.language.upper(),
                        language_codes = list(pymkv.Languages.language_equivalents(track.language, mkvmerge_path = (f'{self.mkvtools_path}mkvmerge',))),
                        flag_default = track.default_track if track.default_track is not None else False,
                        flag_forced = False if track.track_name is None else "FORCÉ" in track.track_name.upper() or "FORCED" in track.track_name.upper(),
                        flag_hearing_impaired = track.flag_hearing_impaired if track.flag_hearing_impaired is not None else False if track.track_name is None else "CC" in track.track_name.upper() or "CLOSED CAPTIONS" in track.track_name.upper() or "SDH" in track.track_name.upper(),
                        flag_visual_impaired = False,
                        flag_original = track.matches_language(self.original_language)
                    ))

                else:
                    print(track.track_codec, f"{track.track_type}")
                    pass

                progress_bar.increment()
        
        mkv_file.cleanup()


    def optimize(self, force_av1: bool = False) -> None:
        # Video
        if self.video is not None:
            total_steps = self.video.get_optimization_steps()
            with ProgressBar(desc = "Optimizing video track", total = total_steps, unit = "steps") as progress_bar:
                self.video.optimize(increment_progress_bar = progress_bar.increment, force_av1 = force_av1)

        # Audio
        total_steps = sum(audio.get_optimization_steps() for audio in self.audios)
        if total_steps != 0:
            with ProgressBar(desc = "Optimizing audio tracks", total = total_steps, unit = "steps") as progress_bar:
                for audio in self.audios:
                    audio.optimize(increment_progress_bar = progress_bar.increment)

        # Subtitles
        total_steps = sum(subtitle.get_optimization_steps() for subtitle in self.subtitles)
        if total_steps != 0:
            with ProgressBar(desc = "Optimizing subtitles tracks", total = total_steps, unit = "steps") as progress_bar:
                for subtitle in self.subtitles:
                    subtitle.optimize(increment_progress_bar = progress_bar.increment)

        self.remove_useless_tracks()


    def make_metadata(self):
        if self.video is None:
            raise ValueError("Video track is None, can't make metadata from nothing")
        self.metadata = Metadata(self.title, {
            "title": self.title,
            "video_codec": self.video.codec.mkvtools_name,
            "metric": f"{round(self.video.metric, 2)} Go/h",
            "processing_server": platform.node(),
            "processing_duration": f"{round(time() - self.init_ts, 2)}",
            "processing_datetime": f"{round(time())}"
        }, "", self.temp_dir)

        self.metadata.metadatas["audio_track_count"] = f"{len(self.audios)}"
        for i, audio in enumerate(self.audios):
            self.metadata.metadatas[f"audio_track_{i + 1}_codec"] = audio.codec.mkvtools_name
            self.metadata.metadatas[f"audio_track_{i + 1}_language"] = audio.language

        self.metadata.metadatas["subtitle_track_count"] = f"{len(self.subtitles)}"
        for i, subtitle in enumerate(self.subtitles):
            self.metadata.metadatas[f"subtitle_track_{i + 1 + len(self.audios)}_codec"] = subtitle.codec.mkvtools_name
            self.metadata.metadatas[f"subtitle_track_{i + 1 + len(self.audios)}_language"] = subtitle.language


    def export(self, output_dir_path: str) -> None:
        if not output_dir_path.endswith("/"):
            output_dir_path += "/"

        mkv_file = pymkv.MKVFile(title = f"{self.title}", mkvmerge_path = f"{self.mkvtools_path}mkvmerge")

        if self.video is None:
            raise ValueError("Need video track for export")
        else:
            mkv_file.add_track(pymkv.MKVTrack(
                track_name = f"{self.video.definition} - {self.video.codec.mkvtools_name}",
                file_path = self.video.file_path,
                language = "UND",
                default_track = True,
                forced_track = True,
                flag_hearing_impaired = False,
                flag_visual_impaired = False,
                flag_original = True,
                compression = True,
                mkvmerge_path = f"{self.mkvtools_path}mkvmerge",
                mkvextract_path = f"{self.mkvtools_path}mkvextract"
            ))

        for audio in self.audios:
            track_name = audio.language.upper()
            if audio.flag_original: track_name += " (VO)"
            if audio.flag_visual_impaired: track_name += " (AD)"
            mkv_file.add_track(pymkv.MKVTrack(
                track_name = f"{track_name} - {audio.codec.mkvtools_name}",
                file_path = audio.file_path,
                language = audio.language,
                default_track = audio.flag_default,
                forced_track = audio.flag_forced,
                flag_hearing_impaired = audio.flag_hearing_impaired,
                flag_visual_impaired = audio.flag_visual_impaired,
                flag_original = audio.flag_original,
                compression = True,
                mkvmerge_path = f"{self.mkvtools_path}mkvmerge",
                mkvextract_path = f"{self.mkvtools_path}mkvextract"
            ))

        for subtitle in self.subtitles:
            track_name = subtitle.language.upper()
            if subtitle.flag_original: track_name += " (VO)"
            if subtitle.flag_hearing_impaired: track_name += " (SME)"
            if subtitle.flag_forced: track_name += " (Forcés)"
            mkv_file.add_track(pymkv.MKVTrack(
                track_name = f"{track_name} - {subtitle.codec.mkvtools_name}",
                file_path = subtitle.file_path,
                language = subtitle.language,
                default_track = subtitle.flag_default,
                forced_track = subtitle.flag_forced,
                flag_hearing_impaired = subtitle.flag_hearing_impaired,
                flag_visual_impaired = subtitle.flag_visual_impaired,
                flag_original = subtitle.flag_original,
                compression = True,
                mkvmerge_path = f"{self.mkvtools_path}mkvmerge",
                mkvextract_path = f"{self.mkvtools_path}mkvextract"
            ))

        if self.metadata is not None:
            metadata_path = self.metadata.make_file()
            mkv_file.add_attachment(pymkv.MKVAttachment(metadata_path, "Movie information", "Additionnal movie metadata and information."))

        with ProgressBar("Muxing to output MKV file", 100, "%") as progress_bar:
            mkv_file.mux(f"{output_dir_path}{self.title}.mkv", silent = True, progress_handler = progress_bar.update_to_n)

        mkv_file.cleanup()


class ProgressBar(tqdm):
    def __init__(self, desc: str, total: int, unit: str):
        super().__init__(total = total, desc = desc, unit = unit)
        
    def update_to_n(self, new_n: int) -> None:
        self.update(new_n - self.n)

    def increment(self, n: int = 1) -> None:
        self.update(n)

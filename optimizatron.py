import os
import re
import subprocess
from time import sleep
from tqdm import tqdm
from wrappers.mkv import Mkv, is_h265_mkv
import tempfile


INPUT_DIR = "/Users/anael/Downloads/Films/test_in/"
TEMP_DIR = "/Users/anael/Downloads/Films/temp/"
MOVIES_OUTPUT_DIR = "/Users/anael/Downloads/Films/test_out/"
SERIES_OUTPUT_DIR = "/Users/anael/Downloads/Films/test_out/"


def encode_to_h265_mkv(file_path: str, temp_dir_path: str) -> str:
    if not temp_dir_path.endswith("/"):
        temp_dir_path += "/"

    proc = subprocess.run(['ffprobe', "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    total_seconds = float(proc.stdout)
    class callback_tqdm(tqdm):
        def update_to(self, millis):
            self.update(millis - self.n)

    mkv_file_path = f"{temp_dir_path}h265.mkv"
    progress_bar = callback_tqdm(total = total_seconds, unit = "s", desc = "Encoding to H.265 MKV file")
    proc = subprocess.Popen(["ffmpeg", "-i", file_path, "-codec:v", "libx265", "-crf", "20", "-preset", "fast", mkv_file_path], stderr = subprocess.PIPE, stdout = subprocess.PIPE)
    if proc.stderr is None:
        raise ValueError("???")
    line = b""
    while proc.poll() is None:
        next_b = proc.stderr.read(1)
        if next_b == b"\r":
            finds = re.findall(r"time= ?(\d\d):(\d\d):(\d\d.\d\d)", line.decode("utf-8"))
            if len(finds) == 0:
                continue
            progress_bar.update_to(int(finds[0][0]) * 3600 + int(finds[0][1]) * 60 + float(f"{finds[0][2]}"))
            line = b""
            sleep(0.5)
        else:
            line += next_b
    progress_bar.close()
    proc.wait()
    return mkv_file_path


def load_and_optimize(file_path: str, output_dir: str, title: str, year: int, original_language: str, season: int | None = None, episode: int | None = None):
    # Vérification
    if (season is None and episode is not None) or (season is not None and episode is None):
        raise ValueError("Season and episode must both be None or both be not None")

    # Dossier temporaire
    temp_dir = tempfile.TemporaryDirectory(dir = TEMP_DIR)

    # Analyse de l'encodage
    encoding = file_path.split(".")[-1].upper()
    need_reencoding = not is_h265_mkv(file_path)
    if encoding == "MKV" and not need_reencoding:
        print(f" -- {title} ({year}){f' S{season:02d}E{episode:02d}' if season is not None and episode is not None else ''} - MKV (H.265) -- ")
    elif encoding == "MKV":
        print(f" -- {title} ({year}){f' S{season:02d}E{episode:02d}' if season is not None and episode is not None else ''} - MKV (not H.265) -- ")
    else:
        print(f" -- {title} ({year}){f' S{season:02d}E{episode:02d}' if season is not None and episode is not None else ''} - {encoding} -- ")

    if need_reencoding:
        file_path = encode_to_h265_mkv(file_path, temp_dir.name)

    # Manipulation de l'objet MKV
    mkv = Mkv(title, year, season, episode, original_language = original_language, temp_dir = temp_dir)
    mkv.load_mkv(file_path)
    # Add metadata
    mkv.optimize()
    mkv.export(output_dir)

    # Suppression du dossier temporaire
    temp_dir.cleanup()


def main():
    print(f"Scan of INPUT directory '{INPUT_DIR}'…")
    all_files = os.listdir(INPUT_DIR)
    movies_files = [file for file in all_files if os.path.isfile(f"{INPUT_DIR}{file}") and not file.startswith(".")]
    series_dirs = [file for file in all_files if os.path.isdir(f"{INPUT_DIR}{file}") and not file.startswith(".")]
    series_files = []
    for dir in series_dirs:
        series_files.extend([file for file in os.listdir(f"{INPUT_DIR}{dir}/") if os.path.isfile(f"{INPUT_DIR}{dir}/{file}") and not file.startswith(".")])
    print(f"Found {len(movies_files)} movie files and {len(series_files)} series files")

    # Séries
    for dir_name in series_dirs:
        finds = re.findall(r"(?P<title>.*) \((?P<year>\d\d\d\d)\) - (?P<original_language>...)", dir_name)
        if len(finds) == 0:
            continue
        title, year, original_language = finds[0]

        if not os.path.exists(f"{SERIES_OUTPUT_DIR}{title} ({year})"):
            os.mkdir(f"{SERIES_OUTPUT_DIR}{title} ({year})")

        # Chaque épisode
        for file_name in sorted([file for file in os.listdir(f"{INPUT_DIR}{dir_name}/") if os.path.isfile(f"{INPUT_DIR}{dir_name}/{file}") and not file.startswith(".")]):
            finds = re.findall(r"S(?P<season_no>\d\d)E(?P<episode_no>\d\d)", file_name)
            if len(finds) == 0:
                continue
            season_no, episode_no = map(int, finds[0])
            
            load_and_optimize(f"{INPUT_DIR}{dir_name}/{file_name}", f"{SERIES_OUTPUT_DIR}{title} ({year})/", title, year, original_language, season_no, episode_no)

    # Films
    for file_name in sorted(movies_files):
        finds = re.findall(r"(?P<title>.*) \((?P<year>\d\d\d\d)\) - (?P<original_language>...)", file_name)
        if len(finds) == 0:
            continue
        title, year, original_language = finds[0]
        
        load_and_optimize(f"{INPUT_DIR}{file_name}", f"{MOVIES_OUTPUT_DIR}", title, year, original_language, None, None)


if __name__ == "__main__":
    main()

import os
import re
import subprocess
from time import sleep
from tqdm import tqdm
from wrappers.mkv import Mkv, is_h265_mkv
import tempfile


INPUT_DIR = "/Users/anael/Downloads/Films/in/"
TEMP_DIR = "/Users/anael/Downloads/Films/temp/"
OUTPUT_DIR = "/Users/anael/Downloads/Films/out/"


def encode_to_h265_mkv(file_path: str, temp_dir: tempfile.TemporaryDirectory) -> str:
    proc = subprocess.run(['ffprobe', "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    total_seconds = float(proc.stdout)
    class callback_tqdm(tqdm):
        def update_to(self, millis):
            self.update(millis - self.n)

    mkv_file_path = f"{temp_dir.name}/h265.mkv"
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


def main():
    print(f"Scan of INPUT directory '{INPUT_DIR}'…")
    video_files = [file for file in os.listdir(INPUT_DIR) if os.path.isfile(f"{INPUT_DIR}{file}") and file.split(".")[-1].upper() in ["MKV", "MP4"]]
    print(f"Found {len(video_files)} valid video files")

    for file_name in video_files:
        # Dossier temporaire
        temp_dir = tempfile.TemporaryDirectory(dir = TEMP_DIR)

        # Lecture du nom de fichier
        finds = re.findall(r"(?P<title>.*) \((?P<year>\d\d\d\d)\) - (?P<original_language>...)", ''.join(file_name.split(".")[:-1]))
        if len(finds) == 0:
            continue

        movie_title, year, original_language = finds[0]

        # Analyse de l'encodage
        file_path = f"{INPUT_DIR}{file_name}"
        encoding = file_name.split(".")[-1].upper()
        need_reencoding = not is_h265_mkv(file_path)
        if encoding == "MKV" and not need_reencoding:
            print(f" -- {movie_title} ({year}) - MKV (H.265) -- ")
        elif encoding == "MKV":
            print(f" -- {movie_title} ({year}) - MKV (not H.265) -- ")
        else:
            print(f" -- {movie_title} ({year}) - {encoding} -- ")

        if need_reencoding:
            file_path = encode_to_h265_mkv(file_path, temp_dir)

        # Manipulation de l'objet MKV
        mkv = Mkv(movie_title, year, original_language = original_language, temp_dir = temp_dir)
        mkv.load_mkv(file_path)
        # Add metadata
        mkv.optimize()
        mkv.export(OUTPUT_DIR)

        # Suppression du dossier temporaire
        temp_dir.cleanup()


if __name__ == "__main__":
    main()

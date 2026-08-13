import os
import re
from optimizatron.movie import Movie
import tempfile


INPUT_DIR = "/Volumes/videos/Unformated/Export Ready/"
TEMP_DIR = "/Users/anael/Movies/Films/temp/"
MOVIES_OUTPUT_DIR = "/Volumes/videos/Movies/"
SERIES_OUTPUT_DIR = "/Volumes/videos/Series/"


def load_and_optimize(file_path: str, output_dir: str, title: str, year: int, original_language: str, season: int | None = None, episode: int | None = None):
    # Affichage
    print(f" -- {title} ({year}){f' S{season:02d}E{episode:02d}' if season is not None and episode is not None else ''} -- ")

    # Vérification
    if (season is None and episode is not None) or (season is not None and episode is None):
        raise ValueError("Season and episode must both be None or both be not None")

    # Dossier temporaire
    temp_dir = tempfile.TemporaryDirectory(dir = TEMP_DIR)

    # Manipulation de l'objet vidéo
    try:
        movie = Movie(title, year, season, episode, original_language = original_language, temp_dir = temp_dir)
        movie.load_file(file_path)
        movie.optimize()
        movie.export(output_dir)
    except Exception as e:
        print(f"An error occurred during process: {e}")
        if input("Display traceback? (y/n)") == "y":
            raise e

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

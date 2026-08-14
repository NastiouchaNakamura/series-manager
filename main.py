import re
import tempfile
import os
import argparse
from time import sleep
from processor import process


INPUT_DIR = "/Users/anael/Movies/Films/in/"
TEMP_DIR = "/Users/anael/Movies/Films/temp/"
MOVIES_OUTPUT_DIR = "/Users/anael/Movies/Films/out/"
SERIES_OUTPUT_DIR = "/Users/anael/Movies/Films/out/"

# ANSI color codes
RED = "\033[0;91m"
GREEN = "\033[0;92m"
YELLOW = "\033[1;93m"
BOLD = "\033[1m"
END = "\033[0m"

if __name__ == "__main__":
    try:
        # Parseur d'arguments
        parser = argparse.ArgumentParser(description = "Processes movies video files, transcoding tracks codecs if necessary")
        parser.add_argument("--input", help = "Path to the input directory", required = True)
        parser.add_argument("--movies-output", help = "Path to the movie output directory", required = True)
        parser.add_argument("--series-output", help = "Path to the series output directory", required = True)
        parser.add_argument("--temp", help = "Path to the temporary directory (in which temporary files and directories will be created)", required = False, default = ".")
        parser.add_argument("--force-av1", help = "Whether to force AV1 transcoding", choices = (0, 1), required = False, default = "0")

        # Récupération des répertoires
        args = parser.parse_args()

        input_dir: str = args.input
        if not input_dir.endswith("/"):
            input_dir += "/"

        temp_dir: str = args.temp
        if not temp_dir.endswith("/"):
            temp_dir += "/"

        movies_output_dir: str = args.movies_output
        if not movies_output_dir.endswith("/"):
            movies_output_dir += "/"

        series_output_dir: str = args.series_output
        if not series_output_dir.endswith("/"):
            series_output_dir += "/"

        force_av1 = args.force_av1 == "1"

        # Vérification des répertoires
        if not os.path.isdir(input_dir):
            raise IOError(f"Input directory path '{input_dir}' is not a directory")
        elif not os.access(input_dir, os.R_OK):
            raise IOError(f"Input directory '{input_dir}' is not readable")
        elif not os.path.isdir(temp_dir):
            raise IOError(f"Temporary directory path '{temp_dir}' is not a directory")
        elif not os.access(temp_dir, os.R_OK):
            raise IOError(f"Temporary directory '{temp_dir}' is not readable")
        elif not os.access(temp_dir, os.W_OK):
            raise IOError(f"Temporary directory '{temp_dir}' is not writable")
        elif not os.path.isdir(movies_output_dir):
            raise IOError(f"Movies output directory path '{movies_output_dir}' is not a directory")
        elif not os.access(movies_output_dir, os.W_OK):
            raise IOError(f"Movies output directory '{movies_output_dir}' is not writable")
        elif not os.path.isdir(series_output_dir):
            raise IOError(f"Movies output directory path '{series_output_dir}' is not a directory")
        elif not os.access(series_output_dir, os.W_OK):
            raise IOError(f"Movies output directory '{series_output_dir}' is not writable")

        # Message d'accueil !
        print(f"\n{BOLD}{YELLOW} ⊹₊ ˚‧︵‿₊୨ ᰔ ୧₊‿︵‧ ˚ ₊⊹ \nNastioucha Video Transcoder\nᓚ₍ ^. ̫ .^₎{END}\n")

        # Exécution de la boucle principale
        while True:
            print(f"Scan of input directory '{input_dir}'…")
            all_files = os.listdir(input_dir)
            movies_files = [file for file in all_files if os.path.isfile(f"{input_dir}{file}") and not file.startswith(".")]
            series_dirs = [file for file in all_files if os.path.isdir(f"{input_dir}{file}") and not file.startswith(".")]
            series_files = []
            for dir in series_dirs:
                series_files.extend([file for file in os.listdir(f"{input_dir}{dir}/") if os.path.isfile(f"{input_dir}{dir}/{file}") and not file.startswith(".")])
            print(f"Found {len(movies_files)} movie files and {len(series_files)} series files in input directory.")
        
            # Séries
            if len(series_dirs) != 0:
                for dir_name in series_dirs:
                    finds = re.findall(r"(?P<title>.*) \((?P<year>\d\d\d\d)\) - (?P<original_language>...)", dir_name)
                    if len(finds) == 0:
                        print(f"{RED}Badly named series: {dir_name}{END}")
                        continue
                    else:
                        title, year, original_language = finds[0]
                
                        if not os.path.exists(f"{series_output_dir}{title} ({year})"):
                            os.mkdir(f"{series_output_dir}{title} ({year})")
                
                        # Chaque épisode
                        for file_name in sorted([file for file in os.listdir(f"{input_dir}{dir_name}/") if os.path.isfile(f"{input_dir}{dir_name}/{file}") and not file.startswith(".")]):
                            finds = re.findall(r"S(?P<season_no>\d\d)E(?P<episode_no>\d\d)", file_name)
                            if len(finds) == 0:
                                print(f"{RED}Badly named episode (can't find season and episode numbers): {file_name}{END}")
                                continue
                            else:
                                season_no, episode_no = map(int, finds[0])
                                process(f"{input_dir}{dir_name}/{file_name}", f"{series_output_dir}{title} ({year})/", temp_dir, title, year, original_language, season_no, episode_no, force_av1 = force_av1)

            else:
                for file_name in movies_files:
                    finds = re.findall(r"(?P<title>.*) \((?P<year>\d\d\d\d)\) - (?P<original_language>...)", file_name)
                    if len(finds) == 0:
                        print(f"{RED}Badly named movie: {file_name}{END}")
                        continue
                    else:
                        title, year, original_language = finds[0]
                        process(f"{input_dir}{file_name}", movies_output_dir, temp_dir, title, year, original_language, None, None, force_av1 = force_av1)
            
            sleep(5)

    except KeyboardInterrupt:
        print("Video Transcoder interrupted.")

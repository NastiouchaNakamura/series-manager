import socket
import re
import os
import argparse
from time import sleep


# ANSI color codes
RED = "\033[0;91m"
GREEN = "\033[0;92m"
YELLOW = "\033[1;93m"
BOLD = "\033[1m"
END = "\033[0m"


def find_available_worker(workers_sockets: list[socket.socket]) -> socket.socket:
    while len(workers_sockets) != 0:
        for worker_socket in workers_sockets:
            worker_socket.send(b"CHECK\n")
            response = worker_socket.recv(1024)

            if response.startswith(b"STATUS"):
                keyword, state = map(lambda b: b.decode("UTF-8"), response.strip().split(b"\n"))

                if state == "IDLE":
                    return worker_socket
                elif state == "WORKING":
                    continue
                else:
                    ip, port = worker_socket.getpeername()
                    print(f"Worker {ip}:{port} did not recognize the CHECK message: {response}")
                    print(f"Closing connection from worker…")
                    worker_socket.close()
                    workers_sockets.remove(worker_socket)
                    continue

            elif len(response) == 0:
                ip, port = worker_socket.getpeername()
                print(f"Worker {ip}:{port} forcefully closed connection")
                print(f"Closing connection from worker…")
                worker_socket.close()
                workers_sockets.remove(worker_socket)
                continue
                
            else:
                ip, port = worker_socket.getpeername()
                print(f"Worker {ip}:{port} sent an unrecognized message: {response}")
                print(f"Closing connection from worker…")
                worker_socket.close()
                workers_sockets.remove(worker_socket)
                continue

        sleep(1)
    
    raise ValueError("There is no connected worker")

if __name__ == "__main__":
    # Parseur d'arguments
    parser = argparse.ArgumentParser(description = "Worker for processing movies video files that does what a boss tells it")
    parser.add_argument("--input", help = "Path to the input directory", required = True)
    parser.add_argument("--movies-output", help = "Path to the movie output directory", required = True)
    parser.add_argument("--series-output", help = "Path to the series output directory", required = True)
    parser.add_argument("--workers-addresses", help = "Path to the series output directory", required = True)
    parser.add_argument("--force-av1", help = "Whether to force AV1 transcoding", choices = ("0", "1"), required = False, default = "0")

    # Récupération des arguments
    args = parser.parse_args()

    input_dir: str = args.input
    if not input_dir.endswith("/"):
        input_dir += "/"

    movies_output_dir: str = args.movies_output
    if not movies_output_dir.endswith("/"):
        movies_output_dir += "/"

    series_output_dir: str = args.series_output
    if not series_output_dir.endswith("/"):
        series_output_dir += "/"

    workers_addresses_str: str = args.workers_addresses
    workers_addresses: list[tuple[str, int]] = []
    for i, addr in enumerate(workers_addresses_str.split(",")):
        if ":" not in addr:
            raise ValueError(f"'{addr}': Worker address must be IP address and port, i.e. '192.168.1.1:12345', separated by commas ','")
        else:
            ip, port = addr.split(":")
            workers_addresses.append((ip, int(port)))

    force_av1 = args.force_av1 == "1"

    # Vérification des répertoires
    if not os.path.isdir(input_dir):
        raise IOError(f"Input directory path '{input_dir}' is not a directory")
    elif not os.access(input_dir, os.R_OK):
        raise IOError(f"Input directory '{input_dir}' is not readable")
    elif not os.path.isdir(movies_output_dir):
        raise IOError(f"Movies output directory path '{movies_output_dir}' is not a directory")
    elif not os.access(movies_output_dir, os.W_OK):
        raise IOError(f"Movies output directory '{movies_output_dir}' is not writable")
    elif not os.path.isdir(series_output_dir):
        raise IOError(f"Movies output directory path '{series_output_dir}' is not a directory")
    elif not os.access(series_output_dir, os.W_OK):
        raise IOError(f"Movies output directory '{series_output_dir}' is not writable")
    
    # Message d'accueil !
    print(f"\n{BOLD}{YELLOW} ⊹₊ ˚‧︵‿₊୨ ᰔ ୧₊‿︵‧ ˚ ₊⊹ \nNastioucha Video Transcoder Boss\n≽(◉˕◉≼マ{END}\n")

    try:
        # Connexion aux workers
        workers_sockets: list[socket.socket] = []
        for (ip, port) in workers_addresses:
            worker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            worker_socket.connect((ip, port))
            workers_sockets.append(worker_socket)

        # Exécution de la boucle principale
        print(f"Scan of input directory '{input_dir}'…")
        all_files = os.listdir(input_dir)
        movies_files = [file for file in all_files if os.path.isfile(f"{input_dir}{file}") and not file.startswith(".") and not file.startswith("DONE - ")]
        series_dirs = [file for file in all_files if os.path.isdir(f"{input_dir}{file}") and not file.startswith(".") and not file.startswith("DONE - ")]
        series_files = []
        for dir in series_dirs:
            series_files.extend([file for file in os.listdir(f"{input_dir}{dir}/") if os.path.isfile(f"{input_dir}{dir}/{file}") and not file.startswith(".") and not file.startswith("DONE - ")])
        print(f"Found {len(movies_files)} movie files and {len(series_files)} series files in input directory.")
    
        # Séries
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
                for file_name in sorted([file for file in os.listdir(f"{input_dir}{dir_name}/") if os.path.isfile(f"{input_dir}{dir_name}/{file}") and not file.startswith(".") and not file.startswith("DONE - ")]):
                    finds = re.findall(r"S(?P<season_no>\d\d)E(?P<episode_no>\d\d)", file_name)
                    if len(finds) == 0:
                        print(f"{RED}Badly named episode (can't find season and episode numbers): {file_name}{END}")
                        continue
                    else:
                        season_no, episode_no = map(int, finds[0])
                        available_worker = find_available_worker(workers_sockets)
                        input_file_path = f"{input_dir}{dir_name}/{file_name}"
                        output_dir_path = f"{series_output_dir}{title} ({year})/"
                        available_worker.send(bytes(f"REQUEST\n{input_file_path}\n{output_dir_path}\n{title}\n{year}\n{original_language}\n{season_no}\n{episode_no}\n{force_av1}\n", encoding = "UTF-8"))
                        print(f"Sent process request for {title} ({year}) - S{season_no:0<2}E{episode_no:0<2} to worker at {available_worker.getpeername()[0]}:{available_worker.getpeername()[1]}")

        # Films
        for file_name in movies_files:
            finds = re.findall(r"(?P<title>.*) \((?P<year>\d\d\d\d)\) - (?P<original_language>...)", file_name)
            if len(finds) == 0:
                print(f"{RED}Badly named movie: {file_name}{END}")
                continue
            else:
                title, year, original_language = finds[0]
                available_worker = find_available_worker(workers_sockets)
                input_file_path = f"{input_dir}{file_name}"
                output_dir_path = movies_output_dir
                available_worker.send(bytes(f"REQUEST\n{input_file_path}\n{output_dir_path}\n{title}\n{year}\n{original_language}\n\n\n{force_av1}\n", encoding = "UTF-8"))
                print(f"Sent process request for {title} ({year}) to worker at {available_worker.getpeername()[0]}:{available_worker.getpeername()[1]}")

        # Fermeture des connexions
        for worker_socket in workers_sockets:
            worker_socket.close()


    except KeyboardInterrupt:
        print("Video Transcoder interrupted.")

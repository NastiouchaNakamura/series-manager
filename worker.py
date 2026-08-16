import socket
import os
import argparse
from threading import Thread
from processor import process


# ANSI color codes
RED = "\033[0;91m"
GREEN = "\033[0;92m"
YELLOW = "\033[1;93m"
BOLD = "\033[1m"
END = "\033[0m"

mkvtools_path = "/Applications/MKVToolNix.app/Contents/MacOS/"


if __name__ == "__main__":
    # Parseur d'arguments
    parser = argparse.ArgumentParser(description = "Worker for processing movies video files that does what a boss tells it")
    parser.add_argument("--port", help = "port number", type = int, required = True)
    parser.add_argument("--temp", help = "Path to the temporary directory (in which temporary files and directories will be created)", required = False, default = ".")
    parser.add_argument("--mkvtools-path", help = "Path to the directory where 'mkvmerge' and 'mkvextract' executables can be found", required = False, default = "")

    # Récupération des arguments
    args = parser.parse_args()

    temp_dir: str = args.temp
    if not temp_dir.endswith("/"):
        temp_dir += "/"

    port = int(args.port)
    if not (0 < port < 2 ** 16):
        raise ValueError(f"Invalid port {port}: must be in range 0 <= port <= 65535")

    mkvtools_path = args.mkvtools_path

    # Vérification des répertoires
    if not os.path.isdir(temp_dir):
        raise IOError(f"Temporary directory path '{temp_dir}' is not a directory")
    elif not os.access(temp_dir, os.R_OK):
        raise IOError(f"Temporary directory '{temp_dir}' is not readable")
    elif not os.access(temp_dir, os.W_OK):
        raise IOError(f"Temporary directory '{temp_dir}' is not writable")
    
    # Message d'accueil !
    print(f"\n{BOLD}{YELLOW} ⊹₊ ˚‧︵‿₊୨ ᰔ ୧₊‿︵‧ ˚ ₊⊹ \nNastioucha Video Transcoder Worker\n₍^ >⩊< ^₎Ⳋ{END}\n")

    # Création de la socket d'écoute
    worker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    worker_socket.bind(("", port))

    # Mise en écoute
    worker_socket.listen()
    print(f"Listening on port {port}…")

    process_thread: Thread = Thread()
    # Boucle principale
    boss_socket: socket.socket | None = None
    boss_address: tuple[str, int] | None = None
    try:
        while True:
            boss_socket, boss_address = worker_socket.accept()
            #print(f"Accepted connection from boss at {boss_address}")

            while True:
                # Réception des données
                # Elle se feront jamais + de 1024o
                # Format de requête : REQUEST \n input file path \n
                # output dir path \n title \n year \n original language \n
                # season \n episode \ force AV1
                # Format de check : CHECK \n
                # Les chemins devraient être sur des volumes accessibles.
                request = boss_socket.recv(1024)
                if request.startswith(b"REQUEST") and not process_thread.is_alive():
                    (keyword, file_path, output_dir_path, title, year,
                    original_language, season, episode, force_av1
                    ) = map(lambda b: b.decode("UTF-8"), request.strip().split(b"\n"))

                    year = int(year)
                    season = int(season) if season != "" else None
                    episode = int(episode) if episode != "" else None
                    force_av1 = force_av1.upper() in ["TRUE", "1", "YES", "Y"]
                    
                    #print(f"REQUEST to process {title} ({year}){f' - S{season:0<2}E{episode:0<2}' if season is not None else ''} at '{file_path}' into '{output_dir_path}'")
                    #print(f"Running thread…")
                    process_thread = Thread(target = process, args = (file_path, output_dir_path, temp_dir, title, year, original_language, season, episode, force_av1, mkvtools_path))
                    process_thread.start()

                elif request.startswith(b"REQUEST") and process_thread.is_alive():
                    #print(f"REQUEST while the worker is unavailable")
                    boss_socket.send(b"STATUS\nWORKING")

                elif request.startswith(b"CHECK") and not process_thread.is_alive():
                    #print(f"CHECK for availability: the worker is available!")
                    boss_socket.send(b"STATUS\nIDLE")

                elif request.startswith(b"CHECK") and process_thread.is_alive():
                    #print(f"CHECK for availability: the worker is not available!")
                    boss_socket.send(b"STATUS\nWORKING")

                elif len(request) == 0:
                    #print(f"Closed connection from boss")
                    break

                else:
                    print(f"Boss sent an unrecognized message: {request}")
                    boss_socket.send(b"STATUS\nDID NOT UNDERSTAND")

    except KeyboardInterrupt:
        worker_socket.close()
        if boss_socket is not None:
            print(f"Forcefully closed connection from boss at {boss_address}")
            boss_socket.close()
        print("Video Transcoder Worker interrupted.")

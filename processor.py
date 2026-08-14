from model.movie import Movie
import tempfile


def process(file_path: str, output_dir: str, temp_dir: str, title: str, year: int, original_language: str, season: int | None = None, episode: int | None = None) -> None:
    # Affichage
    print(f"\n -- {title} ({year}){f' S{season:02d}E{episode:02d}' if season is not None and episode is not None else ''} -- ")

    # Vérification
    if (season is None and episode is not None) or (season is not None and episode is None):
        raise ValueError("Season and episode must both be None or both be not None")

    # Dossier temporaire
    sub_temp_dir = tempfile.TemporaryDirectory(dir = temp_dir)

    # Manipulation de l'objet vidéo
    try:
        movie = Movie(title, year, season, episode, original_language = original_language, temp_dir = sub_temp_dir)
        movie.load_file(file_path)
        movie.optimize()
        movie.make_metadata()
        movie.export(output_dir)
    except Exception as e:
        print(f"An error occurred during process: {e}")
        if input("Display traceback? (y/n)") == "y":
            raise e

    # Suppression du dossier temporaire
    sub_temp_dir.cleanup()

import tempfile
from typing import Callable, Literal
from PIL import Image
import pytesseract
import datetime as dt


# Selon la norme VobSub (sous-titres DVD)
# vaguement définie… again

class VobSub:
    def __init__(self, idx_file_path: str, sub_file_path: str, language_codes: list[str], temp_dir: tempfile.TemporaryDirectory):
        self.idx_file_path: str = idx_file_path
        self.sub_file_path: str = sub_file_path
        self.language_codes: list[str] = language_codes
        self.temp_dir: tempfile.TemporaryDirectory = temp_dir
        self.subtitles: list[Subtitle] = []

        try:
            # Décodage
            with open(self.idx_file_path, mode = "r") as idx, open(self.sub_file_path, mode = "rb") as sub:
                block_size = 2048 # Fixe
                while True:
                    line = idx.readline()
                    if line == "":
                        # End of File
                        break

                    elif line == "\n":
                        # Ligne vide
                        continue

                    elif line.startswith("timestamp"):
                        timestamp_str, filepos_str = line.strip().split(", ")
                        hours, minutes, seconds, millis = timestamp_str[11:].split(":")
                        timestamp = dt.timedelta(hours = int(hours), minutes = int(minutes), seconds = int(seconds), milliseconds = int(millis * 10))
                        filepos = int(filepos_str[9:], base = 16)
                        sub_bytes = sub.read(block_size)

                        self.subtitles.append(Subtitle(timestamp, filepos, sub_bytes))

                    else:
                        # Autre info on s'en fiche
                        continue

        except Exception as ex:
            print("Failed to decode PGS file")
            raise ex

    def to_srt(self, step_done_callback: Callable[[], None]) -> str:
        # Déterminer le code langage
        intersect = set(pytesseract.get_languages()) & set(self.language_codes)
        if len(intersect) == 0:
            raise ValueError("MKV language (ISO 639-2/B standard) or any known equivalent are not recognized by Tesseract OCR")
        tess_language = intersect.pop()

        # Options Tesseract
        valid_chars = {
            "eng": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ,;.…?!-[]:“”‘’♪€$£&°ÄäÉéÑñÖöÜü",
            "fra": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ,;.…?!-[]:“”‘’«»♪€$£&°ÀàÂâÄäÇçÉéÈèÊêËëÎîÏïÑñÔôÖöŒœÙùÛûÜü",
            "spa": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ,;.…?!-[]:“”‘’♪€$£&°ÀàÂâÄäÇçÉéÈèÊêËëÎîÏïÑñÔôÖöŒœÙùÛûÜü",
            "ita": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ,;.…?!-[]:“”‘’♪€$£&°ÄäÉéÑñÖöÜü",
            "por": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ,;.…?!-[]:“”‘’♪€$£&°ÁáÀàÂâÄäÉéÊêÍíÑñÓóÔôÖöÕõÚúÜü",
            "deu": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ,;.…?!-[]:„“‚‘♪€$£&°ÄäÉéÑñÖößÜü",
        }

        if tess_language in valid_chars:
            options = f"-c tessedit_char_whitelist='{valid_chars[tess_language]}'"
        else:
            options = ""
        
        # Voir quel seuil donne la meilleure confiance sur les 10 premiers sous-titres
        tests = [
            { "threshold": 0., "mean_confidence": 0, "conf_of_found_words": [] },
            { "threshold": 0.5, "mean_confidence": 0, "conf_of_found_words": [] },
            { "threshold": 0.76, "mean_confidence": 0, "conf_of_found_words": [] },
            { "threshold": 0.88, "mean_confidence": 0, "conf_of_found_words": [] },
            { "threshold": 1., "mean_confidence": 0, "conf_of_found_words": [] }
        ]

        for test in tests:
            threshold = test["threshold"]
            for sub in self.subtitles[:10]:
                img = sub.get_image(alpha_threashold = threshold)
                data: list[int] = pytesseract.image_to_data(img, lang = tess_language, output_type = "dict", config = options)["conf"]
                test["conf_of_found_words"].extend(filter(lambda c: c != -1, data))
                step_done_callback()
            if len(test["conf_of_found_words"]) != 0:
                test["mean_confidence"] = sum(test["conf_of_found_words"]) / len(test["conf_of_found_words"])
        
        threshold = max(tests, key = lambda t: t["mean_confidence"])["threshold"]

        # Conversion
        srt_file_path = f"{self.temp_dir.name}/{id(self)}-{self.language_codes[0]}.srt"
        with open(srt_file_path, mode = "w") as srt:
            count = 1
            for sub in self.subtitles:
                img = sub.get_image(alpha_threashold = threshold)

                text = pytesseract.image_to_string(img, lang = tess_language, config = options).replace("\n", " ").strip()
                if text != "":
                    srt.write(f"{count}\n{str(dt.timedelta(seconds = sub.start_timestamp)).replace(".", ",")[:11]} --> {str(dt.timedelta(seconds = sub.end_timestamp)).replace(".", ",")[:11]}\n{text}\n\n")
                
                count += 1
                step_done_callback()

        return srt_file_path


class DisplaySet:
    def __init__(self, presentation_composition: PgsSegment, window_definitions: list[PgsSegment], palette_definitions: list[PgsSegment], object_definitions: list[PgsSegment]):
        self.presentation_composition: PgsSegment = presentation_composition
        self.window_definitions: list[PgsSegment] = window_definitions
        self.palette_definitions: list[PgsSegment] = palette_definitions
        self.object_definitions: list[PgsSegment] = object_definitions
        self.palette_entries = []
        for pal_def in self.palette_definitions:
            cursor = 2 # 2 premiers octets pour l'ID de palette et version, inutiles 
            while cursor < len(pal_def.content):
                self.palette_entries.append(PaletteEntry(
                    pal_def.content[cursor],
                    pal_def.content[cursor + 1],
                    pal_def.content[cursor + 2],
                    pal_def.content[cursor + 3],
                    pal_def.content[cursor + 4]
                ))
                cursor += 5

    def is_empty(self):
        return len(self.object_definitions) == 0


class Subtitle:
    def __init__(self, timestamp: dt.timedelta, filepos: int, sub_bytes: bytes):
        self.timestamp: dt.timedelta = timestamp
        self.filepos: int = filepos
        self.sub_bytes: bytes = sub_bytes
        self.text: str | None

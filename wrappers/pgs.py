import tempfile
from typing import Callable, Literal
from PIL import Image
import pytesseract
import datetime as dt


# Selon la norme Presentation Graphic Stream (PGS)
# définie dans le US Patent 'US20090185789A1'

class Pgs:
    def __init__(self, file_path: str, language_codes: list[str], temp_dir: tempfile.TemporaryDirectory):
        self.file_path: str = file_path
        self.language_codes: list[str] = language_codes
        self.temp_dir = temp_dir
        self.segments: list[PgsSegment] = []
        self.display_sets: list[DisplaySet] = []

        try:
            # Décodage
            with open(self.file_path, mode = "rb") as sup:
                while True:
                    magic_number = sup.read(2)
                    if magic_number == b"":
                        # End of File
                        break
                    if magic_number != b"\x50\x47":
                        raise ValueError(f"Incorrect magic number: {magic_number} (must be 0x5047 'PG')")
                    presentation_timestamp = int.from_bytes(sup.read(4)) / 90_000 # 90kHz
                    decoding_timestamp = int.from_bytes(sup.read(4)) / 90_000 # 90kHz
                    segment_type_flag = sup.read(1)
                    if segment_type_flag == b"\x14":
                        segment_type = "PDS"
                    elif segment_type_flag == b"\x15":
                        segment_type = "ODS"
                    elif segment_type_flag == b"\x16":
                        segment_type = "PCS"
                    elif segment_type_flag == b"\x17":
                        segment_type = "WDS"
                    elif segment_type_flag == b"\x80":
                        segment_type = "END"
                    else:
                        raise ValueError("Incorrect segment type flag")
                    segment_size = int.from_bytes(sup.read(2))
                    segment_content = sup.read(segment_size)

                    self.segments.append(PgsSegment(presentation_timestamp, decoding_timestamp, segment_type, segment_size, segment_content))

            # Recomposition
            presentation_composition = None
            window_definitions = []
            palette_definitions = []
            object_definitions = []
            for segment in self.segments:
                if presentation_composition is None:
                    if segment.type == "PCS":
                        presentation_composition = segment
                    else:
                        raise ValueError(f"Unexpected segment type {segment.type} outside display set")
                else:
                    if segment.type == "WDS":
                        window_definitions.append(segment)
                    elif segment.type == "PDS":
                        palette_definitions.append(segment)
                    elif segment.type == "ODS":
                        object_definitions.append(segment)
                    elif segment.type == "END":
                        self.display_sets.append(DisplaySet(presentation_composition, window_definitions, palette_definitions, object_definitions))
                        presentation_composition = None
                        window_definitions = []
                        palette_definitions = []
                        object_definitions = []
                    else:
                        raise ValueError(f"Unexpected segment type {segment.type} inside display set")

            self.display_sets.sort(key = lambda ds: ds.presentation_composition.presentation_timestamp)

            # Analyse (DS -> Subtitles)
            self.subtitles: list[Subtitle] = []
            for ds in self.display_sets:
                if len(self.subtitles) == 0 and ds.is_empty():
                    continue
                elif ds.is_empty():
                    self.subtitles[-1].end_timestamp = ds.presentation_composition.presentation_timestamp
                else:
                    for obj_segment in ds.object_definitions:
                        if len(self.subtitles) != 0 and self.subtitles[-1].end_timestamp == 0:
                            self.subtitles[-1].end_timestamp = obj_segment.presentation_timestamp
                        self.subtitles.append(Subtitle(obj_segment.presentation_timestamp, 0, ds.palette_entries, obj_segment.content))
            if len(self.subtitles) != 0 and self.subtitles[-1].end_timestamp == 0:
                self.subtitles[-1].end_timestamp = 10 # 10s arbitraire pour le dernier sous-titre si aucune indication de fin

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
                    srt.write(f"{count}\n{str(dt.timedelta(seconds = sub.start_timestamp)).replace(".", ",")[:11]} --> {str(dt.timedelta(seconds = sub.end_timestamp)).replace(".", ",")[:12]}\n{text}\n\n")
                
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


class PgsSegment:
    def __init__(self, presentation_timestamp: float, decoding_timestamp: float, type: Literal['PDS', 'ODS', 'PCS', 'WDS', 'END'], size: int, content: bytes):
        self.presentation_timestamp: float = presentation_timestamp
        self.decoding_timestamp: float = decoding_timestamp
        self.type: str = type
        self.size: int = size
        self.content = content


class Subtitle:
    def __init__(self, start_timestamp: float, end_timestamp: float, palette_entries: list[PaletteEntry], obj_content: bytes):
        self.start_timestamp: float = start_timestamp
        self.end_timestamp: float = end_timestamp
        self.palette_entries_dict: dict[int, PaletteEntry] = { entry.id: entry for entry in palette_entries }
        self.rle_length: int = int.from_bytes(obj_content[4:7])
        self.width: int = int.from_bytes(obj_content[7:9])
        self.height: int = int.from_bytes(obj_content[9:11])
        self.rle: bytes = obj_content[11:11+self.rle_length]

    def read_rle_bytes(self) -> list[list[int]]:
        # Selon l'US Patent US007912305B1 (2011)
        lines = [[]]
        cursor = 0
        while cursor < len(self.rle):
            if self.rle[cursor] != 0:
                lines[-1].append(self.rle[cursor])
                cursor += 1
            elif self.rle[cursor] == 0 and self.rle[cursor + 1] == 0:
                if cursor + 2 != len(self.rle):
                    lines.append([])
                cursor += 2
            elif self.rle[cursor] == 0 and self.rle[cursor + 1] < 64:
                lines[-1] += [0] * self.rle[cursor + 1]
                cursor += 2
            elif self.rle[cursor] == 0 and self.rle[cursor + 1] < 128:
                lines[-1] += [0] * ((self.rle[cursor + 1] - 64) * 256 + self.rle[cursor + 2])
                cursor += 3
            elif self.rle[cursor] == 0 and self.rle[cursor + 1] < 192:
                lines[-1] += [self.rle[cursor + 2]] * (self.rle[cursor + 1] - 128)
                cursor += 3
            elif self.rle[cursor] == 0 and self.rle[cursor + 1] < 256:
                lines[-1] += [self.rle[cursor + 3]] * ((self.rle[cursor + 1] - 192) * 256 + self.rle[cursor + 2])
                cursor += 4
            else:
                raise ValueError(f"Unexpected bytes {self.rle[cursor:cursor+4]}… in RLE decoding")

        return lines

    def get_image(self, alpha_threashold: float = 0.):
        lines = self.read_rle_bytes()
        img = Image.new("RGBA", (self.width + 60, self.height + 60)) # Marge supplémentaire
        min_i = self.width + 60
        min_j = self.height + 60
        max_i = 0
        max_j = 0
        for j in range(len(lines)):
            for i in range(len(lines[j])):
                if lines[j][i] == 255:
                    rgba = (0, 0, 0, 0)
                else:
                    palette_entry = self.palette_entries_dict[lines[j][i]]
                    rgba = (palette_entry.r, palette_entry.g, palette_entry.b, palette_entry.alpha)
                    if rgba[3] < alpha_threashold * 255:
                        rgba = (0, 0, 0, 0)
                    else:
                        if i - 30 < min_i:
                            min_i = i - 30
                        if i + 30 > max_i:
                            max_i = i + 30
                        if j - 30 < min_j:
                            min_j = j - 30
                        if j + 30 > max_j:
                            max_j = j + 30
                        rgba = (rgba[0] // 4, rgba[0] // 4, rgba[0] // 4, 255)
                img.putpixel((i + 30, j + 30), rgba)

        if min_i > max_i or min_j > max_j:
            # Probablement une image totalement vide
            return img
        else:
            # Optimiser l'OCR avec moins de pixels et quand même une marge
            return img.crop((min_i, min_j, max_i, max_j))


class PaletteEntry:
    def __init__(self, id: int, y: int, cr: int, cb: int, alpha: int):
        self.id: int = id
        self.y: int = y
        self.cr: int = cr
        self.cb: int = cb
        self.alpha = alpha

        #YCrCbA->RGBA
        delta = 128
        self.r = int(self.y + 1.403 * (self.cr - delta))
        self.g = int(self.y - 0.714 * (self.cr - delta) -  0.344 * (self.cb - delta))
        self.b = int(self.y + 1.773 * (self.cb - delta))


        


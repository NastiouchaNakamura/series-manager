import re
import tempfile
from typing import Callable
import datetime as dt


# Selon la norme MOV text
# Sous-titres internes à MP4
# Transcodés en SRT avec des artéfacts XML/HTML sur les textes

class Tx3g:
    def __init__(self, file_path: str, temp_dir: tempfile.TemporaryDirectory):
        self.file_path: str = file_path
        self.temp_dir: tempfile.TemporaryDirectory = temp_dir
        self.subtitles: list[Subtitle] = []

        try:
            # Décodage
            with open(self.file_path, mode = "r", encoding = "utf-8") as tx3g:
                agregated_lines = []
                while True:
                    line = tx3g.readline()
                    if bytes(line, encoding = "utf-8").startswith(b"\xef\xbb\xbf"): # Indicateur d'ordre des octets à ignorer
                        line = bytes(line, encoding = "utf-8")[3:].decode(encoding = "utf-8")

                    if (line == "\n" or line == ""):
                        if len(agregated_lines) != 0:
                            index = int(agregated_lines[0].strip())
                            if index != len(self.subtitles) + 1:
                                raise ValueError(f"Unexpected subtitle index in TG3X file read: {index} (previous subtitle index: {len(self.subtitles)})")
                            startStr, endStr = agregated_lines[1].strip().split(" --> ")
                            startHours, startMinutes, startSeconds = startStr.split(":")
                            endHours, endMinutes, endSeconds = endStr.split(":")
                            text = "".join(agregated_lines[2:]).strip()
                            self.subtitles.append(Subtitle(
                                dt.timedelta(hours = int(startHours), minutes = int(startMinutes), seconds = float(startSeconds.replace(",", "."))),
                                dt.timedelta(hours = int(endHours), minutes = int(endMinutes), seconds = float(endSeconds.replace(",", "."))),
                                text
                            ))
                            agregated_lines = []

                        if line == "":
                            break
        
                    else :
                        agregated_lines.append(line)

        except Exception as ex:
            print("Failed to decode TG3X file")
            raise ex

    def to_srt(self, step_done_callback: Callable[[], None]) -> str:
        # Conversion
        srt_file_path = f"{self.temp_dir.name}/{id(self)}.srt"
        with open(srt_file_path, mode = "w") as srt:
            count = 1
            for sub in self.subtitles:
                text_with_xml = sub.text
                text = re.sub(r"<.*?>", "", text_with_xml)
                srt.write(f"{count}\n{str(sub.start_timestamp).replace(".", ",")[:11]} --> {str(sub.end_timestamp).replace(".", ",")[:11]}\n{text}\n\n")
                
                count += 1
                step_done_callback()

        return srt_file_path


class Subtitle:
    def __init__(self, start_timestamp: dt.timedelta, end_timestamp: dt.timedelta, text: str):
        self.start_timestamp: dt.timedelta = start_timestamp
        self.end_timestamp: dt.timedelta = end_timestamp
        self.text: str = text

import tempfile
from typing import Callable
import datetime as dt
from enum import Enum


# Selon la norme Advanced SubStation Alpha (ASS/SSA)
# définie de manière assez décentralisée et vague sur le net

class Ass:
    def __init__(self, file_path: str, temp_dir: tempfile.TemporaryDirectory):
        self.file_path: str = file_path
        self.temp_dir: tempfile.TemporaryDirectory = temp_dir
        self.subtitles: list[Subtitle] = []

        try:
            # Décodage
            with open(self.file_path, mode = "r", encoding = "utf-8") as ass:
                class SectionState(Enum):
                    Nothing = 0
                    ScriptInfo = 1
                    Styles = 2
                    Events = 3
                    
                section = SectionState.Nothing
                startIndex, endIndex, textIndex = 1, 2, 9 # Pour la section Events uniquement si pas de format indiqué explicitement
                while True:
                    line = ass.readline()
                    if bytes(line, encoding = "utf-8").startswith(b"\xef\xbb\xbf"): # Indicateur d'ordre des octets à ignorer
                        line = bytes(line, encoding = "utf-8")[3:].decode(encoding = "utf-8")

                    if line == "":
                        break
                    elif line == "\n" or line.startswith(";"):
                        continue

                    elif line.strip() == "[Script Info]":
                        section = SectionState.ScriptInfo
                    elif line.strip() == "[V4+ Styles]" or line == "[V4 Styles]":
                        section = SectionState.Styles
                    elif line.strip() == "[Events]":
                        section = SectionState.Events

                    elif section == SectionState.ScriptInfo:
                        # On se fiche des infos pour notre usage ici.
                        pass
                    elif section == SectionState.Styles:
                        # On s'en fiche des styles pour notre usage ici.
                        pass
                    elif section == SectionState.Events:
                        if line.startswith("Format: "):
                            eventsFormat = list(map(lambda s: s.strip(), line[8:].strip().split(",")))
                            startIndex = eventsFormat.index("Start")
                            endIndex = eventsFormat.index("End")
                            textIndex = eventsFormat.index("Text")
                        if line.startswith("Dialogue: "):
                            fields = line[10:].strip().split(",")
                            startHours, startMinutes, startSeconds = fields[startIndex].split(":")
                            endHours, endMinutes, endSeconds = fields[endIndex].split(":")
                            text = fields[textIndex]
                            self.subtitles.append(Subtitle(
                                dt.timedelta(hours = int(startHours), minutes = int(startMinutes), seconds = float(startSeconds)),
                                dt.timedelta(hours = int(endHours), minutes = int(endMinutes), seconds = float(endSeconds)),
                                text
                            ))

                    else:
                        raise ValueError(f"Unexpected state in SSA/ASS file reading: {section}")

        except Exception as ex:
            print("Failed to decode SSA/ASS file")
            raise ex

    def to_srt(self, step_done_callback: Callable[[], None]) -> str:
        # Conversion
        srt_file_path = f"{self.temp_dir.name}/{id(self)}.srt"
        with open(srt_file_path, mode = "w") as srt:
            count = 1
            for sub in self.subtitles:
                srt.write(f"{count}\n{str(sub.start_timestamp).replace(".", ",")[:11]} --> {str(sub.end_timestamp).replace(".", ",")[:11]}\n{sub.text}\n\n")
                
                count += 1
                step_done_callback()

        return srt_file_path


class Subtitle:
    def __init__(self, start_timestamp: dt.timedelta, end_timestamp: dt.timedelta, text: str):
        self.start_timestamp: dt.timedelta = start_timestamp
        self.end_timestamp: dt.timedelta = end_timestamp
        self.text: str = text

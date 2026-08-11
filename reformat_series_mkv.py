import os
import re
import pymkv

SERIES_NAME = "Il était une fois… l'Homme"
ORIGINAL_LANGUAGE = "FRE"


INPUT_DIR = "/Users/anael/Downloads/Il Etait Une Fois L'homme.TRUEFRENCH.1080p.BDLight.x265-SAHKELPLAISIR/"
OUTPUT_DIR = "/Volumes/videos/Series/Il était une fois… l'Homme (1978)/"
REFORMAT_PATTERN = re.compile(r"Il")

def main():
    for file_name in os.listdir(INPUT_DIR):
        if not file_name.startswith(".") \
                and os.path.isfile(f"{INPUT_DIR}{file_name}") \
                and REFORMAT_PATTERN.match(file_name) \
                and file_name.endswith(".mkv"):
            
            finds = re.findall(r"S(?P<season_no>\d\d)E(?P<episode_no>\d\d)", file_name)
            if len(finds) == 0:
                continue

            season_no, episode_no = map(int, finds[0])

            mkv = pymkv.MKVFile(f"{INPUT_DIR}{file_name}", mkvmerge_path="/Applications/MKVToolNix.app/Contents/MacOS/mkvmerge")
            mkv.title = f"{SERIES_NAME} - S{str(season_no).zfill(2)}E{str(episode_no).zfill(2)}"
            for t in mkv.tracks:
                print(t.track_id)
                if t.language is None:
                    lang_str = "?"
                else:
                    lang_str = t.language.upper()

                if lang_str == ORIGINAL_LANGUAGE:
                    t.flag_original = True

                if t.track_type == "video":
                    if t.track_name is not None:
                        t.track_name = f"[{t.track_codec}] {t.track_name.strip()}"
                    
                elif t.track_type == "audio":
                    t.track_name = f"{lang_str}{' (VO)' if lang_str == ORIGINAL_LANGUAGE else ''}{' (AD)' if t.flag_visual_impaired else ''}"
                    
                elif t.track_type == "subtitles":
                    t.track_name = f"{lang_str}{' (VO)' if lang_str == ORIGINAL_LANGUAGE else ''}{' (SME)' if t.flag_hearing_impaired else ''}{' (Forcés)' if t.forced_track else ''}"

            mkv.mux(f"{OUTPUT_DIR}{mkv.title}.mkv")
            mkv.cleanup()

if __name__ == "__main__":
    main()

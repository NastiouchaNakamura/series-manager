import os
import pymkv


INPUT_DIR = "/Volumes/videos/Movies/"
OUTPUT_DIR = "/Volumes/videos/Movies/"

def main():
    for file_name in os.listdir(INPUT_DIR):
        if not file_name.startswith(".") \
                and os.path.isfile(f"{INPUT_DIR}{file_name}") \
                and file_name.endswith(".mkv"):

            movie_title = ''.join(file_name.split(".")[:-1])

            mkv = pymkv.MKVFile(f"{INPUT_DIR}{file_name}", mkvmerge_path="/Applications/MKVToolNix.app/Contents/MacOS/mkvmerge")
            mkv.title = f"{movie_title}"
            print(mkv.title)
            for t in mkv.tracks:
                t.compression = True

                if t.language is None:
                    lang_str = "?"
                else:
                    lang_str = t.language.upper()

                if t.track_type == "video":
                    if t.track_name is not None:
                        t.track_name = f"[{t.track_codec}] {t.track_name.strip()}"
                    else:
                        t.track_name = f"[{t.track_codec}] Original video track"
                    
                elif t.track_type == "audio":
                    t.track_name = f"{lang_str}{' (VO)' if lang_str == t.flag_original else ''}{' (AD)' if t.flag_visual_impaired else ''}"
                    
                elif t.track_type == "subtitles":
                    t.track_name = f"{lang_str}{' (VO)' if lang_str == t.flag_original else ''}{' (SME)' if t.flag_hearing_impaired else ''}{' (Forcés)' if t.forced_track else ''}"

                print(t.track_codec)
            continue
            mkv.mux(f"{OUTPUT_DIR}{mkv.title}.mkv")
            mkv.cleanup()

if __name__ == "__main__":
    main()

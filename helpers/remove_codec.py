import os
import pymkv

INPUT_DIR = "/Volumes/videos/Unformated/Chocola et Vanilla (2005) - JPN/"
OUTPUT_DIR = "/Volumes/videos/Unformated/Chocola et Vanilla (2005) - JPN - 2/"
CODEC_TO_REMOVE = "VobSub"

for file in os.listdir(INPUT_DIR):
    if file.startswith("."):
        continue

    else:
        mkv_file = pymkv.MKVFile(f"{INPUT_DIR}{file}", mkvmerge_path = "/Applications/MKVToolNix.app/Contents/MacOS/mkvmerge")

        while True:
            removed_nothing = True
            for i, track in enumerate(mkv_file.tracks):
                if track.track_codec == CODEC_TO_REMOVE:
                    mkv_file.remove_track(i)
                    removed_nothing = False
                    break

            if removed_nothing:
                break

        name_without_extension, _ = os.path.splitext(file)
        
        mkv_file.mux(f"{OUTPUT_DIR}{name_without_extension}_without_{CODEC_TO_REMOVE}.mkv")
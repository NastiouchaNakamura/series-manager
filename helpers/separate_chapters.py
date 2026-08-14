import os

import pymkv


def main():
    # mkv_file = pymkv.MKVFile(
    #     "/Volumes/videos/Unformated/Les.Shadoks.S04.COMPLETE.VFF.DVDRip.Vorbis-LOADiX.mkv",
    #     mkvmerge_path = "/Applications/MKVToolNix.app/Contents/MacOS/mkvmerge"
    # )

    # mkv_file.split_chapters()
    # mkv_file.mux("/Users/anael/Movies/Films/shadoks/output.mkv")

    for i, file in enumerate(sorted(file for file in os.listdir("/Users/anael/Movies/Films/shadoks/S1/") if not file.startswith(".")), start = 1):
        os.rename(f"/Users/anael/Movies/Films/shadoks/S1/{file}", f"/Users/anael/Movies/Films/shadoks/S1/Shadok_S01E{i:0>2}.mkv")

    #mkv_file.cleanup()

if __name__ == "__main__":
    main()

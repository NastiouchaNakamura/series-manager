import os
import pymkv

AV1_DIR = "/Volumes/videos/Unformated/out/Code Lyoko/"
MKV_DIR = "/Volumes/videos/Unformated/in/Code Lyoko (2003) - FRE/"
OUTPUT_DIR = "/Users/anael/Movies/Films/test_out/Code Lyoko (MKV+AV1)/"

for av1_file_name, mkv_file_name in zip(sorted(filter(lambda f: not f.startswith("."), os.listdir(AV1_DIR))), sorted(filter(lambda f: not f.startswith("."), os.listdir(MKV_DIR)))):
    av1_file = pymkv.MKVFile(f"{AV1_DIR}{av1_file_name}", mkvmerge_path = "/Applications/MKVToolNix.app/Contents/MacOS/mkvmerge")
    mkv_file = pymkv.MKVFile(f"{MKV_DIR}{mkv_file_name}", mkvmerge_path = "/Applications/MKVToolNix.app/Contents/MacOS/mkvmerge")
    mkv_file.remove_track(0)
    mkv_file.add_track(av1_file.tracks[0])
    mkv_file.move_track_front(len(av1_file.tracks) - 1)
    for track in mkv_file.tracks:
        track.compression = True
    #print([(track.track_id, track.track_codec) for track in av1_file.tracks])
    #print([(track.track_id, track.track_codec) for track in mkv_file.tracks])
    print(f"{av1_file_name} + {mkv_file_name}")
    mkv_file.mux(f"{OUTPUT_DIR}{mkv_file_name}.mkv", silent = True)
    av1_file.cleanup()
    mkv_file.cleanup()

import os
import re
import cv2

INPUT_DIR = "/Volumes/videos/Series/"


def main():
    read_count = 0

    for file_name in os.listdir(INPUT_DIR):
        read_count += 1

        if os.path.isdir(f"{INPUT_DIR}{file_name}"):
            #print(f"{file_name[:12]}: Directory (passed)")
            pass

        elif file_name.startswith("."):
            #print(f"{file_name[:12]}: Hidden file (passed)")
            pass

        elif file_name.lower().endswith(".mkv"):
            capture = cv2.VideoCapture(f"{INPUT_DIR}{file_name}")
            height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)

            if width >= 1920:
                print(f"{file_name[:12]}: MKV file - {int(width)}*{int(height)}")

        elif file_name.lower().endswith(".avi"):
            capture = cv2.VideoCapture(f"{INPUT_DIR}{file_name}")
            height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)

            if width >= 1920:
                print(f"{file_name[:12]}: AVI file - {int(width)}*{int(height)}")

        elif file_name.lower().endswith(".mp4"):
            capture = cv2.VideoCapture(f"{INPUT_DIR}{file_name}")
            height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)

            if width >= 1920:
                print(f"{file_name[:12]}: MP4 file - {int(width)}*{int(height)}")

        elif file_name.lower().endswith(".m4v"):
            #print(f"{file_name[:12]}: M4V file (passed)")
            pass

        elif file_name.lower().endswith(".divx"):
            capture = cv2.VideoCapture(f"{INPUT_DIR}{file_name}")
            height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)

            if width >= 1920:
                print(f"{file_name[:12]}: DIVX file - {int(width)}*{int(height)}")

        elif file_name.lower().endswith(".flv"):
            capture = cv2.VideoCapture(f"{INPUT_DIR}{file_name}")
            height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)

            if width >= 1920:
                print(f"{file_name[:12]}: FLV file - {int(width)}*{int(height)}")

        else:
            print(f"{file_name[:12]}: Unknown file format {file_name.split(".")[-1].upper()} (passed)")

    print(f"Done! {read_count} files read")


if __name__ == "__main__":
    main()

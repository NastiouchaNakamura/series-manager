import os
import subprocess


MOVIES_DIR = "/Volumes/videos/Movies/"
SERIES_DIR = "/Volumes/videos/Series/"

RED = "\033[0;91m"
GREEN = "\033[0;92m"
YELLOW = "\033[1;93m"
BOLD = "\033[1m"
END = "\033[0m"

def main():
    movies = []
    for file in os.listdir(MOVIES_DIR):
        if file.startswith("."):
            continue
        else:
            file_path = f"{MOVIES_DIR}{file}"
            codec, seconds = str(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name:format=duration", "-of", "default=noprint_wrappers=1:nokey=1",file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout, encoding = "UTF-8").split("\n")[:2]
            seconds = float(seconds)
            size = os.path.getsize(file_path)
            metric = round((size / 1e9) / (seconds / 3600), 2)

            movies.append({
                "title": file,
                "codec": codec,
                "size": size,
                "duration": seconds,
                "metric": metric
            })
        print(f"OK - {file}")

    series = []
    for dir in os.listdir(SERIES_DIR):
        if dir.startswith("."):
            continue
        else:
            episodes = []
            for file in os.listdir(f"{SERIES_DIR}{dir}/"):
                if file.startswith("."):
                    continue
                else:
                    file_path = f"{SERIES_DIR}{dir}/{file}"
                    #print(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout)
                    codec, seconds = str(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name:format=duration", "-of", "default=noprint_wrappers=1:nokey=1",file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout, encoding = "UTF-8").split("\n")[:2]
                    seconds = float(seconds)
                    size = os.path.getsize(file_path)
                    metric = round((size / 1e9) / (seconds / 3600), 2)
                    episodes.append({
                        "title": file,
                        "codec": codec,
                        "size": size,
                        "duration": seconds,
                        "metric": metric
                    })
                print(f"OK - {file}")

            seconds = sum(episode["duration"] for episode in episodes)
            size = sum(episode["size"] for episode in episodes)
            metric = round((size / 1e9) / (seconds / 3600), 2) if seconds != 0 else float("+inf")
            series.append({
                "title": dir,
                "codec": " - ".join(set(episode["codec"] for episode in episodes)),
                "size": seconds,
                "duration": size,
                "metric": metric
            })

    for movie in sorted(movies + series, key = lambda m: m["metric"]):
        print(f"{GREEN if movie['metric'] < 1.2 else YELLOW if movie['metric'] < 2 else RED}{movie['metric']:0<4} Go/h{END} {GREEN if movie['codec'] == 'av1' else YELLOW if movie['codec'] == 'hevc' else RED if movie['codec'] == 'h264' else ''}({movie['codec']:<4}){END} - {movie['title']}")

if __name__ == "__main__":
    main()

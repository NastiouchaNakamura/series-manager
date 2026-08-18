import os
import subprocess
import tqdm


MOVIES_DIR = "/Volumes/videos/Movies/"
SERIES_DIR = "/Volumes/videos/Series/"

RED = "\033[0;91m"
GREEN = "\033[0;92m"
YELLOW = "\033[1;93m"
BOLD = "\033[1m"
END = "\033[0m"

def main():
    total_files = len(os.listdir(MOVIES_DIR)) + sum(len(os.listdir(f"{SERIES_DIR}{dir}/")) for dir in os.listdir(SERIES_DIR) if not dir.startswith("."))
    progress_bar = tqdm.tqdm(total = total_files, unit = "file(s)")

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
        progress_bar.update()

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
                #print(f"OK - {file}")
                progress_bar.update()

            seconds = sum(episode["duration"] for episode in episodes)
            size = sum(episode["size"] for episode in episodes)
            metric = round((size / 1e9) / (seconds / 3600), 2) if seconds != 0 else float("+inf")
            series.append({
                "title": dir,
                "codec": " - ".join(set(episode["codec"] for episode in episodes)),
                "size": size,
                "duration": seconds,
                "metric": metric
            })

    progress_bar.close()

    for movie in sorted(movies + series, key = lambda m: m["metric"]):
        print(f"{GREEN if movie['metric'] < 1.2 else YELLOW if movie['metric'] < 2 else RED}{movie['metric']:0<4} Go/h{END} {GREEN if movie['codec'] == 'av1' else YELLOW if movie['codec'] == 'hevc' else RED if movie['codec'] == 'h264' else ''}({movie['codec']:<4}){END} - {round(movie['size'] / 1e9, 2)}Go/{int(movie['duration'] // 3600)}h{(int(movie['duration'] % 3600) // 60):0>2} - {movie['title']}")
    total_size = sum(movie["size"] for movie in movies + series)
    total_duration = sum(movie["duration"] for movie in movies + series)
    total_metric = round((total_size / 1e9) / (total_duration / 3600), 2)
    print(f"--> Total size of everything: {round(total_size / 1e9, 2)} Go")
    print(f"--> Total duration of everything: {int(total_duration // 3600)}h{(int(total_duration % 3600) // 60):0>2} ({total_duration} seconds)")
    print(f"--> Mean metric of everything: {total_metric} Go/h")

if __name__ == "__main__":
    main()

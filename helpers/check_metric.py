import os
import subprocess
import tqdm
import matplotlib.pyplot as plt


MOVIES_DIR = "/Volumes/videos/Movies/"
SERIES_DIR = "/Volumes/videos/Series/"

RED = "\033[0;91m"
GREEN = "\033[0;92m"
YELLOW = "\033[0;93m"
BOLD = "\033[1m"
END = "\033[0m"

def main():
    movies_count = len(os.listdir(MOVIES_DIR))
    episodes_count = sum(sum(len(os.listdir(f"{SERIES_DIR}{dir}/{season}/")) for season in os.listdir(f"{SERIES_DIR}{dir}/") if not season.startswith(".")) for dir in os.listdir(SERIES_DIR) if not dir.startswith("."))
    total_files = movies_count + episodes_count
    progress_bar = tqdm.tqdm(total = total_files, unit = "file(s)")

    movies = []
    for file in os.listdir(MOVIES_DIR):
        if os.path.isdir(f"{MOVIES_DIR}{file}") or file.startswith("."):
            progress_bar.update()
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
        if os.path.isfile(f"{SERIES_DIR}{dir}") or dir.startswith("."):
            progress_bar.update()
            continue
        else:
            episodes = []
            for season in os.listdir(f"{SERIES_DIR}{dir}/"):
                if os.path.isfile(f"{SERIES_DIR}{dir}/{season}") or season.startswith("."):
                    continue
                else:
                    for file in os.listdir(f"{SERIES_DIR}{dir}/{season}/"):
                        if os.path.isdir(f"{SERIES_DIR}{dir}/{season}/{file}") or file.startswith("."):
                            continue
                        else:
                            file_path = f"{SERIES_DIR}{dir}/{season}/{file}"
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

    shows = movies + series

    # Console Display
    shows.sort(key = lambda m: m["metric"])
    for show in shows:
        print(f"{GREEN if show['metric'] < 1.2 else YELLOW if show['metric'] < 2 else RED}{show['metric']:0<4} Go/h{END} {GREEN if show['codec'] == 'av1' else YELLOW if show['codec'] == 'hevc' else RED if show['codec'] == 'h264' else ''}({show['codec']:<4}){END} - {round(show['size'] / 1e9, 2)}Go/{int(show['duration'] // 3600)}h{(int(show['duration'] % 3600) // 60):0>2} - {show['title']}")
    total_size = sum(show["size"] for show in shows)
    total_duration = sum(show["duration"] for show in shows)
    total_metric = round((total_size / 1e9) / (total_duration / 3600), 2)
    print(f"--> Total size of everything: {round(total_size / 1e9, 2)} Go")
    print(f"--> Total duration of everything: {int(total_duration // 3600)}h{(int(total_duration % 3600) // 60):0>2} ({total_duration} seconds)")
    print(f"--> Mean metric of everything: {total_metric} Go/h")

    # Camembert
    shows.sort(key = lambda m: m["size"], reverse = True)
    fig, ax = plt.subplots()
    ax.pie(
        list(map(lambda m: m["size"], shows)),
        labels = [m["title"] if i < 30 else "" for i, m in enumerate(shows)],
        colors = [("#1aff1a" if i % 2 == 0 else "#00e600") if m["codec"] == "av1" else ("#ffff1a" if i % 2 == 0 else "#e5e600") if m["codec"] == "hevc" else ("#ff1a1a" if i % 2 == 0 else "#e60000") if m["codec"] == "h264" else ("#8c8c8c" if i % 2 == 0 else "#737373") for i, m in enumerate(shows)]
    )
    plt.show()

if __name__ == "__main__":
    main()

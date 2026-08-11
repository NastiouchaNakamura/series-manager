import os
import re
import pymkv

SERIES_ROOT = "/Volumes/videos/Series"
SHOW_EPISODES = True

class Season:
    def __init__(self, number: int):
        self.number: int = number
        self.episodes: dict[int, pymkv.MKVFile] = {}

    def get_episode_dub_languages(self, i):
        return sorted(map(lambda t: t.track_name if t.track_name is not None else '?', filter(lambda t: t.track_type == "audio", self.episodes[i].tracks)))

    def get_dub_languages(self):
        return sorted(set.intersection(*map(lambda mkv: set(map(lambda t: t.track_name if t.track_name is not None else "?", filter(lambda t: t.track_type == "audio", mkv.tracks))), self.episodes.values())))

    def get_episode_sub_languages(self, i):
        return sorted(map(lambda t: t.track_name if t.track_name is not None else '?', filter(lambda t: t.track_type == "subtitles", self.episodes[i].tracks)))

    def get_sub_languages(self):
        return sorted(set.intersection(*map(lambda mkv: set(map(lambda t: t.track_name if t.track_name is not None else "?", filter(lambda t: t.track_type == "subtitles", mkv.tracks))), self.episodes.values())))

for dir_name in os.listdir(SERIES_ROOT):
    if os.path.isfile(f"{SERIES_ROOT}/{dir_name}"):
        print(f"This is not a series directory: {dir_name}")
        continue

    match = re.fullmatch(r"(?P<name>.*) \((?P<year>\d*)\)", dir_name)
    if match is None:
        print(f"Bad name format for directory: {dir_name}")
        continue
    
    name, year_string = match.group("name", "year")
    year = int(year_string)

    seasons: list[Season] = []
    
    for file_name in os.listdir(f"{SERIES_ROOT}/{dir_name}"):
        if file_name.startswith("."):
            continue

        if os.path.isdir(f"{SERIES_ROOT}/{dir_name}/{file_name}"):
            print(f"→ This is not a file: {file_name}")
            continue

        if not file_name.endswith(".mkv"):
            print(f"→ Bad file format: {file_name}")
            continue
        
        match = re.fullmatch(r"(?P<ep_name>.*) - S(?P<season>\d\d)E(?P<episode>\d\d)\.mkv", file_name)
        if match is None:
            print(f"→ Bad name format for episode: {file_name}")
            continue

        episode_name, season_no_str, episode_no_str = match.group("ep_name", "season", "episode")
        season_no = int(season_no_str)
        episode_no = int(episode_no_str)

        if episode_name != name:
            print(f"→ Episode name is different of series name: {file_name}")
            continue

        if not any(season.number == season_no for season in seasons):
            seasons.append(Season(season_no))
    
        mkv = pymkv.MKVFile(f"{SERIES_ROOT}/{dir_name}/{file_name}", mkvmerge_path="/Applications/MKVToolNix.app/Contents/MacOS/mkvmerge")
        [season for season in seasons if season.number == season_no][0].episodes[episode_no] = mkv
    
    if len(seasons) > 0:
        print(f"{name} ({year}):")
        for season in sorted(seasons, key = lambda s: s.number):
            print(f"  ↪ Season {season.number} ({len(season.episodes)} episodes) | Dubs: {', '.join(sorted(season.get_dub_languages()))} | Subs: {', '.join(sorted(season.get_sub_languages()))}")
            if SHOW_EPISODES:
                for i, episode in sorted(season.episodes.items(), key = lambda it: it[0]):
                    print(f"    ↪ {episode.title} | Dubs: {', '.join(season.get_episode_dub_languages(i))} | Subs: {', '.join(season.get_episode_sub_languages(i))}")

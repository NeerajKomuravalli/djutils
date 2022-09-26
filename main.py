import pandas as pd
import sys
from get_song_meta_deta_from_beatport import get_meta_data_of_song
from generate_combinations import generate_combinations_for_row

if __name__ == "__main__":
    csv_path = sys.argv[1]
    df = pd.read_csv(csv_path)
    df_data = []
    for index, row in df.iterrows():
        print("Processing song no: ", index+1)
        url = row["Link"]
        song_metadata = get_meta_data_of_song(url)
        artists = song_metadata.get("artist", [])
        artist_names = [artist_metadata["name"]
                        for artist_metadata in artists]
        artists_str = ", ".join(artist_names)
        combinations = generate_combinations_for_row(
            song_metadata.get("title", {}).get("title", ""),
            song_metadata.get("title", {}).get("mixData", ""),
            artists_str
        )
        df_data.append([
            url,
            song_metadata.get("title", {}).get("title", ""),
            combinations,
            song_metadata.get("title", {}).get("mixData", ""),
            artists_str,
            song_metadata.get("bpm", ""),
            song_metadata.get("genre", ""),
            song_metadata.get("key", ""),
            row["Category"],
            row["DownloadPreference"],
            row["PersonalLikenessFactor"],
            row["VocalsPresent"],
            row["Notes"],
            row["Keywords"]
        ])
    songs_metadata_filled = pd.DataFrame(df_data)
    songs_metadata_filled.to_csv("songs_metadata_filled.csv", index=False)
    songs_metadata_filled.columns = [[
        "url",
        "title",
        "combinations",
        "mixMatadata",
        "artists",
        "bpm",
        "genre",
        "key",
        "category",
        "downloadPreference",
        "personalLikenessFactor",
        "vocalsPresent",
        "notes",
        "keywords"
    ]]
    songs_metadata_filled["downloadStatus"] = ""
    songs_metadata_filled["soulseekUser"] = ""
    songs_metadata_filled["soulseekFolder"] = ""
    songs_metadata_filled["fileType"] = ""
    songs_metadata_filled.to_csv("songs_metadata_filled.csv", index=False)

import pandas as pd
import requests
from bs4 import BeautifulSoup


def get_meta_data_of_song(url: str) -> dict:
    data = {}
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")

    # To get length, released, bpm, key, genre, and label
    job_elements = soup.find_all("ul", class_="interior-track-content-list")
    for job_element in job_elements:
        for data_suffix in ['length', 'released', 'bpm', 'key', 'genre', 'labels']:
            data_class = job_element.find(
                'li', class_="interior-track-content-item interior-track-"+data_suffix)
            value = data_class.find('span', class_="value").text.strip()
            data[data_suffix] = value

    # To get title of the song
    job_elements = soup.find_all("div", class_="interior-title")
    title_data = {}
    for job_element in job_elements:
        try:
            title_data['title'] = job_element.find("h1").text.strip()
        except:
            pass
        try:
            title_data["mixData"] = job_element.find(
                "h1", class_="remixed").text.strip()
        except:
            pass
    if title_data:
        data["title"] = title_data
    # To get artists
    job_elements = soup.find_all("div", class_="interior-track-content")
    class_data = "interior-track-artists"
    link_prefix = "https://www.beatport.com"
    for job_element in job_elements:
        artist_data = job_element.find("div", class_=class_data)
        artists = artist_data.find('span', class_="value")
        artists_ancor = artists.find_all('a')
        if len(artists_ancor):
            artists_list = []
            for a in artists_ancor:
                artist = {}
                artist['name'] = a.text.strip()
                artist['url'] = link_prefix + a["href"].strip()
                artists_list.append(artist)
            data["artist"] = artists_list
        else:
            data["artist"] = [artist_data.find(
                'span', class_="value").text.strip()]
    return data

import requests
from bs4 import BeautifulSoup


def parse_traxsource_url(url: str) -> dict:
    data = {}
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")

    # # parsing page head
    page_head = soup.find_all("div", class_="page-head")
    if len(page_head) > 1:
        raise ValueError(
            "More than one page heads observed but expected only one")
    # parsing title
    title = page_head[0].find_all("h1", class_="title")
    if len(title) > 1:
        raise ValueError("More than one title observed but expected only one")
    data["title"] = title[0].text.strip()
    # parsing mix information
    mix_data = page_head[0].find_all("h1", class_="version")
    if len(mix_data) > 1:
        raise ValueError("More than one mix information but expected only one")
    data["mixData"] = mix_data[0].text.strip()
    # get artist info
    artists = page_head[0].find_all("a", class_="com-artists")
    link_prefix = "https://www.traxsource.com"
    if len(artists):
        artists_list = []
        for a in artists:
            artist = {}
            artist['name'] = a.text.strip()
            artist['url'] = link_prefix + a["href"].strip()
            artists_list.append(artist)
        data["artist"] = artists_list

    # parsing table information
    table_data = soup.find_all("table", class_="tr-det-tbl horiz")
    print("size : ", len(table_data))
    print("table data : ", table_data)
    if len(table_data) != 1:
        raise ValueError("Table data different from expectation")
    column_names = []
    for row_index, row in enumerate(table_data[0].find_all("tr")):
        for col_index, col in enumerate(row.find_all("td")):
            if row_index == 0:
                column_names.append(col.text.strip())
            else:
                data[column_names[col_index]] = col.text.strip()
    return data


if __name__ == "__main__":
    url = "https://www.traxsource.com/track/10256773/e-da-veee-original-mix"
    data = parse_traxsource_url(url)
    print(data)

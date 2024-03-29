import requests
import xml.etree.ElementTree as ET
from watchlist.config import OMDB_KEY, TMDB_KEY, tmdb_headers

def get_OMDB(title, year):
    omdb_url = f"http://www.omdbapi.com/?apikey={OMDB_KEY}&t={title}&y={year}&r=json"
    omdb_response = requests.get(omdb_url)

    if omdb_response.status_code == 200:
        return omdb_response.json()
    else:
        print(f"Error accessing OMDB API: {omdb_response.status_code}")
        return None

def get_OMDB_from_id(id):
    omdb_url = f"http://www.omdbapi.com/?apikey={OMDB_KEY}&i={id}&r=json"
    omdb_response = requests.get(omdb_url)

    if omdb_response.status_code == 200:
        return omdb_response.json()
    else:
        print(f"Error accessing OMDB API: {omdb_response.status_code}")
        return None

def get_TMDB(omdb):
    imdb_id = omdb["imdbID"]
    type = omdb["Type"]

    # TV SERIES
    if type == "series":
        tmdb_find_url = f"https://api.themoviedb.org/3/find/{imdb_id}?api_key={TMDB_KEY}&external_source=imdb_id"
        tmdb_find_response = requests.get(tmdb_find_url)
        tmdb_id = tmdb_find_response.json()["tv_results"][0]["id"]
        tmdb_url = f"https://api.themoviedb.org/3/tv/{tmdb_id}?api_key={TMDB_KEY}&append_to_response=credits,keywords,videos,watch/providers"
    # MOVIE
    else:
        tmdb_url = f"https://api.themoviedb.org/3/movie/{imdb_id}?api_key={TMDB_KEY}&append_to_response=credits,keywords,videos,watch/providers"

    tmdb_response = requests.get(tmdb_url)
    if tmdb_response.status_code == 200:
        return tmdb_response.json()
    else:
        print(f"Error accessing TMDB API: {tmdb_response.status_code}")
        return None

def get_TMDB_from_id(id, type):
    # TV SERIES
    if type == "series":
        tmdb_url = f"https://api.themoviedb.org/3/tv/{id}?api_key={TMDB_KEY}&append_to_response=credits,keywords,videos,watch/providers"
    # MOVIE
    else:
        tmdb_url = f"https://api.themoviedb.org/3/movie/{id}?api_key={TMDB_KEY}&append_to_response=credits,keywords,videos,watch/providers"

    tmdb_response = requests.get(tmdb_url)
    if tmdb_response.status_code == 200:
        return tmdb_response.json()
    else:
        print(f"Error accessing TMDB API: {tmdb_response.status_code}")
        return None

def get_TMDB_posters_from_id(id, type):
    # TV SERIES
    if type == "series":
        tmdb_url = f"https://api.themoviedb.org/3/tv/{id}/images?include_image_language=en%2Cnull"
    # MOVIE
    else:
        tmdb_url = f"https://api.themoviedb.org/3/movie/{id}/images?include_image_language=en%2Cnull"
    tmdb_response = requests.get(tmdb_url, headers=tmdb_headers)
    if tmdb_response.status_code == 200:
        return tmdb_response.json()
    else:
        print(f"Error accessing TMDB API: {tmdb_response.status_code}")
        return None

def get_OMDB_xml(title, year):
    omdb_xml_url = f"http://www.omdbapi.com/?apikey={OMDB_KEY}&t={title}&y={year}&r=xml&tomatoes=true"
    response = requests.get(omdb_xml_url)

    if response.status_code == 200:
        return response.text
    else:
        print(f"Error accessing OMDB XML API: {response.status_code}")
        return None

def parse_OMDB_xml(xml_content):
    try:
        root = ET.fromstring(xml_content)
        movie_element = root.find(".//movie")
        tomato_meter = movie_element.get("tomatoMeter")
        tomato_user_meter = movie_element.get("tomatoUserMeter")
        return tomato_meter, tomato_user_meter
    except ET.ParseError as e:
        print(f"Error parsing OMDB XML: {e}")
        return None, None

def get_person_TMDB(tmdb_id):
    tmdb_url = f"https://api.themoviedb.org/3/person/{tmdb_id}?api_key={TMDB_KEY}&language=en-US"

    tmdb_response = requests.get(tmdb_url)
    if tmdb_response.status_code == 200:
        return tmdb_response.json()
    else:
        print(f"Error accessing TMDB API: {tmdb_response.status_code}")
        return None

def get_company_TMDB(id):
    tmdb_find_url = f"https://api.themoviedb.org/3/company/{id}?api_key={TMDB_KEY}"
    tmdb_find_response = requests.get(tmdb_find_url)

    if tmdb_find_response.status_code == 200:
        return tmdb_find_response.json()
    else:
        print(f"Error accessing TMDB API: {tmdb_find_response.status_code}")
        return None

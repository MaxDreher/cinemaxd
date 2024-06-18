import requests
import xmltodict
import json
from moviedb.config import TMDB_HEADERS, OMDB_KEY


def region_filter(data, region):
    if data.get('watch/providers'):
        data['watch/providers']['results'] = {region: data['watch/providers']['results'][region]} if region in data['watch/providers']['results'] else {}

    if data.get('release_dates'):
        data['release_dates']['results'] = [{region: item['release_dates']} for item in data['release_dates']['results'] if item['iso_3166_1'] == region]

    return data


class TMDB:
    BASE_URL = "https://api.themoviedb.org/3/"
    HEADERS = TMDB_HEADERS


    def __init__(self):
        self = self


    def _get(self, endpoint, filter=False):
        response = requests.get(f"{self.BASE_URL}{endpoint}", headers=self.HEADERS)
        response.raise_for_status()
        if filter:
            return region_filter(response.json(), "US")
        else:
            return response.json()
    

    def get_movie_details(self, movie_id, append_to_response=True):
        if append_to_response:
            return self._get(f"movie/{movie_id}?append_to_response=credits,keywords,images,videos,watch/providers,external_ids,release_dates", True)
        return self._get(f"movie/{movie_id}", True)
    

    def get_tv_details(self, tv_id, append_to_response=True):
        if append_to_response:
            return self._get(f"tv/{tv_id}?append_to_response=credits,keywords,images,videos,watch/providers,external_ids,release_dates", True)
        return self._get(f"movie/{tv_id}", True)
    

    def get_person_details(self, id):
        return self._get(f"person/{id}?language=en-US")
    

class OMDB:
    ROOT_URL = "http://www.omdbapi.com/"

    def __init__(self):
        self.api_key = OMDB_KEY
        self.url = f"{self.ROOT_URL}?apikey={OMDB_KEY}"
    
    def _get(self, url, type):
        try:
            if type not in ["json", "xml"]:
                raise ValueError("Type must be either 'movie' or 'series'")
            response = requests.get(url)
            response.raise_for_status()
            if type == "json":
                data = response.json()
                return data if data.get('Response') == 'True' else None
            else: 
                data = response.text
                converted_data = xmltodict.parse(data).get('root')
                return converted_data.get('movie') if converted_data.get('@response') == 'True' else None

        except requests.RequestException as e:
            print(f"An error occurred while fetching OMDB entity: {e}")
            return None

    def get_item(self, id, type):
        url = f"{self.url}&i={id}&r={type}{"&tomatoes=true" if type == "xml" else ""}"
        return(self._get(url, type))


class WIKIMEDIA:
    BASE_URL = "https://www.wikidata.org/w/api.php"

    def __init__(self):
        self = self

    def _get(self, id):
        params = {
            'action': 'wbgetentities',
            'ids': id,
            'format': 'json',
            'languages': 'en'
        }
        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()  # Raise an error for bad status codes
            data = response.json()
            return data.get('entities', {}).get(id, {})
        except requests.RequestException as e:
            print(f"An error occurred while fetching Wikidata entity: {e}")
            return None

    def get_item(self, id):
        return self._get(id)
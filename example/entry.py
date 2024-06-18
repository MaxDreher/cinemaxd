from moviedb.api import *
from django.utils import timezone
from moviedb.config import STREAMING_PROVIDERS, WIKIMEDIA_IDS, build_ratings, standardize
from datetime import date, datetime
from moviedb.scraper import *
from slugify import slugify
from iso639 import Lang
import time

class entry:

    def __init__(self, input_package):
        t1 = time.time()
        
        try:

            id = input_package.get('id', None)
            type = input_package.get('type', None)

            if type not in ["movie", "series"]:
                raise ValueError("Type must be either 'movie' or 'series'")
            
            self.tmdb_api = TMDB()
            self.wikimedia_api = WIKIMEDIA()
            self.omdb_api = OMDB()
            self.scraper = Scraper()
            self.image_url_root = "https://image.tmdb.org/t/p/original"
            self.type = type
            self.input = input_package
            self.data = self.tmdb_api.get_movie_details(id) if type == "movie" else self.tmdb_api.get_tv_details(id)
            self.streaming_providers = STREAMING_PROVIDERS
        
        except ValueError as e:
            print(f"Initialization error: {e}")
            raise

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise


    def _get_title(self):
        return f"{self.data.get('title' if self.type == 'movie' else 'name')}"


    def _get_slug(self, title):
        return slugify(f"{title}", replacements=[["'", ""], [".", ""]])


    def _get_trailer(self):
        trailers = [{'key': member.get("key"), 'name': member.get("name")} for member in self.data.get("videos", {}).get("results", []) if member.get('type') == 'Trailer']
        official_trailer = next((t['key'] for t in trailers if 'Official Trailer' in t.get('name', '')), None)
        if official_trailer:
            return official_trailer
        elif trailers:
            return trailers[0].get('key')
        return None


    def _get_release_date(self):
        return datetime.strptime(self.data.get("release_date" if self.type == "movie" else "first_air_date"), "%Y-%m-%d").date()


    def _get_decade(self, release_date):
        year = release_date.year
        decade = (year // 10) * 10
        return f"{decade}s"


    def _build_image_url(self, path):
        if path:
            return f"{self.image_url_root}{path}"
        return None


    def _get_cast(self, num):
        return [{'id': item.get('id'), 'role': item.get('character')} for item in self.data.get("credits", {}).get("cast", [])[:num]]


    def _get_directors(self):
        return [{'id': item.get('id'), 'name': item.get('name')} for item in self.data.get("credits", {}).get("crew", []) if item.get('job') == 'Director'] if self.type == "movie" else [{'id': item.get('id')} for item in self.data.get("created_by", [])]


    def _get_crew(self, job):
        return [{'id': item.get('id'), 'name': item.get('name')} for item in self.data.get("credits", {}).get("crew", []) if item.get('job') == job]


    def _get_production_companies(self, num):
        return [{'id': item.get('id'), 'name': item.get('name'), 'logo': self._build_image_url(item.get('logo_path'))} for item in self.data.get("production_companies", [])[:num]]


    def _get_genres(self):
        return [{'id': item.get('id'), 'name': item.get('name')} for item in self.data.get('genres', [])]


    def _get_providers(self):
        all_providers = self.data.get('watch/providers', {}).get('results', {}).get('US', {}).get('flatrate', []) + self.data.get('watch/providers', {}).get('results', {}).get('US', {}).get('ads', [])
        return [{'id': item.get('provider_id'), 'name': item.get('provider_name')} for item in all_providers if item.get('provider_name') in self.streaming_providers]


    def _get_keywords(self):
        return [{'id': item.get('id'), 'name': item.get('name')} for item in self.data.get("keywords", {}).get("keywords", [])]


    def _get_external_ids(self):

        def get_ids_from_tmdb(self):
            TMDB = str(self.data.get('id', None))
            IMDB = self.data.get('external_ids').get('imdb_id')
            Wikidata = self.data.get('external_ids').get('wikidata_id')
            
            external_ids = [
                {
                    'name': 'TMDB',
                    'id': TMDB,
                    'url': f'https://www.themoviedb.org/{self.type if self.type == 'movie' else 'tv'}/{TMDB}'
                },
            ]

            if IMDB:
                external_ids.append(
                    {
                        'name': 'IMDB',
                        'id': IMDB,
                        'url': f'https://www.imdb.com/title/{IMDB}/'
                    }
                )

            if Wikidata:
                external_ids.append(
                    {
                        'name': 'Wikidata',
                        'id': Wikidata,
                        'url': f'https://www.wikidata.org/wiki/{Wikidata}'
                    }
                )
            
            return external_ids

        def get_all_ids(self):
            ids = get_ids_from_tmdb(self)
            if ids[-1].get('name') == 'Wikidata':
                wikidata = self.wikimedia_api.get_item(ids[-1].get('id')).get('claims')
                if wikidata:
                    for item in WIKIMEDIA_IDS:
                        try:
                            external_id = wikidata.get(item.get('id'))[0].get('mainsnak').get('datavalue').get('value')
                            if external_id:
                                name = item.get('name')
                                ids.append(
                                    {
                                        'name': name,
                                        'id': external_id,
                                        'url': f"{item.get('url_root')}{f"{self.type}/" if name == "TheTVDB" else ""}{external_id}"
                                    }
                                )
                        except: 
                            continue
            return ids
        
        return get_all_ids(self)
    

    def _get_ratings(self, external_ids):

        t1 = time.time()
        imdb_id = next((item['id'] for item in external_ids if item['name'] == "IMDB"), None)
        omdb_data = self.omdb_api.get_item(imdb_id, "xml") if imdb_id else None

        def scrape_data(site):
            print(f"Falling back to web scraping for {site} ratings.")
            url = next((item['url'] for item in external_ids if item['name'] == site), None)
            return self.scraper.get_ratings(site, url) if url else None


        def get_imdb():
            site = "IMDB"
            if omdb_data:
                imdb = omdb_data.get('@imdbRating')
                if imdb and (imdb != 'N/A'):
                    return build_ratings(site, [imdb])
                else:
                    return scrape_data(site)
            else:
                return scrape_data(site)


        def get_tomatoes():
            site = "Rotten Tomatoes"
            if omdb_data:
                tomatometer = omdb_data.get('@tomatoMeter')
                usermeter = omdb_data.get('@tomatoUserMeter')
                if (tomatometer and usermeter) and (tomatometer != 'N/A' and usermeter != 'N/A'):
                    return build_ratings(site, [tomatometer, usermeter])
                else:
                    return scrape_data(site)
            else:
                return scrape_data(site)


        def get_letterboxd():
            site = "Letterboxd"
            return scrape_data(site)


        def get_metacritic():
            site = "Metacritic"
            if omdb_data:
                metascore = omdb_data.get('@metascore')
                if metascore and (metascore != 'N/A'):
                    return build_ratings(site, [metascore])
                else:
                    return scrape_data(site)
            else:
                return scrape_data(site)


        score = self.data.get('vote_average')
        ratings = [
            {
                "name": "TMDB",
                "value": score,
                "standardized": standardize(score, 10)
            }
        ]


        rating_functions = {
            "IMDB": get_imdb(),
            "Metacritic": get_metacritic(),
            "Rotten Tomatoes": get_tomatoes(),
            "Letterboxd": get_letterboxd(),
        }


        for site, scores in rating_functions.items():
            if scores:
                ratings += scores


        return ratings


    def _get_average_critical(self, ratings):
        if ratings:
            total = sum(item.get('standardized', 0) for item in ratings)
            return round(total / len(ratings), 2)
        return None


    def _get_languages(self):
        return [{'iso_639_1': item.get('iso_639_1'), 'name': item.get('english_name')} for item in self.data.get("spoken_languages", [])]


    def _get_countries(self):
        return [{'iso_3166_1': item.get('iso_3166_1'), 'name': item.get('name')} for item in self.data.get("production_countries", [])]


    def _get_bechdel(self, wikidata_id):        
        if wikidata_id:
            wikidata = self.wikimedia_api.get_item(wikidata_id).get('claims')
            if wikidata:
                assesment = wikidata.get('P5021', None)
                if assesment:
                    try:
                        bechdel_item = next((item for item in assesment if item.get('mainsnak').get('datavalue').get('value').get('id') == "Q4165246"), None)
                        qualifier = bechdel_item.get('qualifiers').get('P9259')[0]
                        if qualifier.get('property') == 'P9259':
                            value = qualifier.get('datavalue').get('value').get('id')
                            if value == 'Q105773168':
                                return True
                            elif value == 'Q105773155':
                                return False
                            else:
                                return None
                    except:
                        return None

        return None


    def _get_franchise(self, wikidata_id):        
        if wikidata_id:
            wikidata = self.wikimedia_api.get_item(wikidata_id).get('claims')
            if wikidata:
                franchise = wikidata.get('P8345', None)
                if franchise:
                    try:
                        franchise_id = franchise[0].get('mainsnak').get('datavalue').get('value').get('id')
                        franchise_data = self.wikimedia_api.get_item(franchise_id)
                        if franchise_data:
                            label = franchise_data.get('labels').get('en').get('value')
                            return label
                    except:
                        return None
        return None


    def parse_data(self):
        t1 = time.time()

        title = self._get_title()
        release_date = self._get_release_date()
        year = release_date.year

        external_ids = self._get_external_ids()
        wikidata_id = next((item['id'] for item in external_ids if item['name'] == "Wikidata"), None)

        ratings = self._get_ratings(external_ids)


        tags = self.input.get('tags', None)
        tags = (tags.split(',') if tags != "" else None) if tags else None

        rating = self.input.get('rating', None)

        elo = (float(rating) * 200 + 900) if rating else None

        common_fields = {
            'date': self.input.get('date', None),
            'favorite': self.input.get('favorite', None),
            'rating': rating,
            'elo': elo,
            'review': self.input.get('review', None),
            'theaters': self.input.get('theaters', None),
            'service': self.input.get('service', None),
            'seen': self.input.get('seen', None),
            'timesSeen': self.input.get('timesSeen', None),
            'datetime_added': timezone.now(),

            'TMDB_ID': self.data.get('id', None),
            'title': title,
            'year': year,
            'type': self.type,
            'slug': self._get_slug(title),
            'releaseDate': release_date,
            'decade': self._get_decade(release_date),
            'status': self.data.get('status', None),
            'posterLink': self._build_image_url(self.data.get('poster_path')),
            'bgLink': self._build_image_url(self.data.get('backdrop_path')),
            'trailerLink': self._get_trailer(),
            'plot': self.data.get('overview', None),
            'tagline': self.data.get('tagline', None),
            'original_language': Lang(self.data.get('original_language')).name,
            'bechdel': self._get_bechdel(wikidata_id),
            'franchise': self._get_franchise(wikidata_id),

            'many-to-many': {
                'tags': tags,
                'cast': self._get_cast(10),
                'directors': self._get_directors(),
                'production_companies': self._get_production_companies(10),
                'genres': self._get_genres(),
                'providers': self._get_providers(),
                'keywords': self._get_keywords(),
                'external_ids': external_ids,
                'ratings': ratings,
                'languages': self._get_languages(),
                'countries': self._get_countries(),
            },

            'avg_critical_rating': self._get_average_critical(ratings),
        }


        if self.type == 'movie':
            specific_fields = {
                'runtime': self.data.get('runtime', None),
                'budget': self.data.get('budget', None),
                'revenue': self.data.get('revenue', None)
            }


        elif self.type == 'series':
            specific_fields = {
                'episodes': self.data.get('number_of_episodes', 0),
                'seasons': self.data.get('number_of_seasons', 0)
            }

        print(f"Parsing took {time.time() - t1}s")
        return {**common_fields, **specific_fields}

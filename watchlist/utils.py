import os
import json
import time
import logging
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from slugify import slugify
from datetime import datetime
from watchlist.models import *
from watchlist.api_calls import *  
import concurrent.futures
from django.utils import timezone
from django.db import transaction, IntegrityError
from functools import partial

# ===============================================
# DATA RETRIVAL GETTERS
# ===============================================
'''
Getters to be used in the database update functions
'''
# -----------------------------------------------
# CAST INFORMATION AND PROCESSING
# -----------------------------------------------
    
def get_cast(tmdb_data, num):
    """
    Get a list of cast IDs and corresponding roles based on TMDB data.

    Args:
    - tmdb_data (dict): The TMDB data containing information about the cast.
    - num (int): Number of cast members to retrieve.

    Returns:
    - tuple: A tuple containing lists of cast IDs and roles.
    """
    cast_ids = [entry["id"] for entry in tmdb_data.get("credits", {}).get("cast", [])[:num]]
    roles = [entry["character"] for entry in tmdb_data.get("credits", {}).get("cast", [])[:num]]
    return cast_ids or None, roles or None

def process_actor(actor_id):
    """
    Process actor information retrieved from TMDB and save it to the database.

    Args:
    - actor_id (int): The TMDB ID of the actor.

    Returns:
    - Actor: An instance of the Actor model.
    """
    # Retrieve actor information from TMDB
    actor_tmdb = get_person_TMDB(actor_id)

    # Specify the fields to retrieve from actor_tmdb
    actor_data = {
        'TMDB_ID': actor_tmdb.get("id"),
        'IMDB_ID': actor_tmdb.get("imdb_id"),
        'name': actor_tmdb.get("name"),
        'gender': actor_tmdb.get("gender"),
        'bio': actor_tmdb.get("biography"),
        'birthday': actor_tmdb.get("birthday"),
        'imgLink': actor_tmdb.get("profile_path"),
    }

    # Create an Actor instance
    actor = Actor(**actor_data)

    try:
        # Save the actor to the database using a context manager
        with transaction.atomic(using='library_db'):
            actor.save()
    except IntegrityError:
        # Handle integrity errors (e.g., if actor with the same ID already exists)
        pass
    except Exception as e:
        # Handle other exceptions
        print(f"Error processing actor: {e}")

    return actor

# -----------------------------------------------
# DIRECTOR INFORMATION AND PROCESSING
# -----------------------------------------------

def get_directors(tmdb_data, type, num):
    """
    Get a list of director IDs based on TMDB data.

    Args:
    - tmdb_data (dict): The TMDB data containing information about the content.
    - type (str): Type of content, either 'movie' or 'series'.
    - num (int): Max number of directors to retrieve.

    Returns:
    - list: A list of director IDs.
    """

    if type == 'series':
        # For TV series, extract creator IDs
        directors = [creator["id"] for creator in tmdb_data.get("created_by", [])[:num]]
    else:
        # For movies, extract director IDs from the crew
        directors = [member["id"] for member in tmdb_data.get("credits", {}).get("crew", []) if member.get('job') == 'Director'][:num]

    return directors

def process_director(director_id):
    """
    Process director information and save it to the database.

    Parameters:
    - TMDB_KEY (str): The TMDB API key.
    - direc_id (int): The TMDB ID of the director.

    Returns:
    - Director: The Director instance created and saved.
    """
    # Retrieve director information from TMDB
    director_tmdb = get_person_TMDB(director_id)

    # Specify the fields to retrieve from direc_tmdb
    director_data = {
        'TMDB_ID': director_tmdb.get("id"),
        'IMDB_ID': director_tmdb.get("imdb_id"),
        'name': director_tmdb.get("name"),
        'gender': director_tmdb.get("gender"),
        'bio': director_tmdb.get("biography"),
        'birthday': director_tmdb.get("birthday"),
        'imgLink': director_tmdb.get("profile_path"),
    }

    # Create a Director instance
    director = Director(**director_data)

    try:
        # Save the director to the database using a context manager
        with transaction.atomic(using='library_db'):
            director.save()
    except IntegrityError:
        # Handle integrity errors (e.g., if director with the same ID already exists)
        pass
    except Exception as e:
        # Handle other exceptions
        print(f"Error processing director: {e}")

    return director

# -----------------------------------------------
# PRODUCTION COMPANY INFORMATION AND PROCESSING
# -----------------------------------------------

def get_prod_companies(tmdb_data, num):
    """
    Extract production company IDs from TMDB data.

    Parameters:
    - tmdbData (dict): The TMDB data containing information about the movie or series.
    - num (int): The number of production companies to retrieve.

    Returns:
    - list or None: A list of production company IDs or None if no data is available.
    """
    # Extract production company IDs using list comprehension
    prodCompanies = [entity["id"] for entity in tmdb_data.get("production_companies", [])[:num]]

    # Return the list of production company IDs or None if the list is empty
    return prodCompanies or None

def process_prod_company(company_id):
    """
    Process production company data and save it to the database.

    Parameters:
    - company_id (int): The id of the production company.

    Returns:
    - ProdCompany: The ProdCompany instance created and saved to the database.
    """
    # Retrieve production company information from TMDB
    company_tmdb = get_company_TMDB(company_id)

    # Specify the fields to retrieve from comp_tmdb
    company_data = {
        'id': company_tmdb.get("id"),
        'name': company_tmdb.get("name"),
        'logo': company_tmdb.get("logo_path"),
    }

    # Create a ProdCompany instance
    company = ProdCompany(**company_data)

    try:
        # Save the production company to the database using a context manager
        with transaction.atomic(using='library_db'):
            company.save()
    except IntegrityError:
        # Handle integrity errors (e.g., if company with the same ID already exists)
        pass
    except Exception as e:
        # Handle other exceptions
        print(f"Error processing production company: {e}")

    return company

# -----------------------------------------------
# OTHER M2M GETTERS
# -----------------------------------------------

def get_genres(tmdb_data):
    """
    Retrieve all genre information from TMDB data.

    Parameters:
    - tmdbData (dict): The TMDB data containing genre information.

    Returns:
    - list: A list of lists, where each inner list contains genre ID and name.
    """
    # Using list comprehension to create a list of lists containing genre ID and name
    genres = [[entity["id"], entity["name"]]for entity in tmdb_data.get("genres", [])] or None
    return genres

def get_keywords(tmdb_data):
    """
    Retrieve all genre information from TMDB data.

    Parameters:
    - tmdbData (dict): The TMDB data containing genre information.

    Returns:
    - list: A list of lists, where each inner list contains genre ID and name.
    """
    # Using list comprehension to create a list of lists containing genre ID and name
    keywords = [[entity["id"], entity["name"]]for entity in tmdb_data.get("keywords", {}).get("keywords", [])] or None
    return keywords

def get_providers(tmdb_data):
    """
    Retrieve streaming providers for a specific region (US).

    Args:
    - tmdb (dict): The TMDB API response containing information about streaming providers.
    - preferred_providers (List[str]): List of preferred streaming providers.

    Returns:
    - List[Union[int, str]]: A list of streaming providers, each represented by a list containing
      the provider ID (int) and provider name (str). Returns None if no valid providers are found.
    """
    try:
        # Extract information about flatrate and ads providers from the TMDB API response
        providers = tmdb_data.get('watch/providers', {}).get('results', {}).get('US', {}).get('flatrate', [])
        ads_providers = tmdb_data.get('watch/providers', {}).get('results', {}).get('US', {}).get('ads', [])
    except Exception as error:
        # Print or log the specific exception for debugging
        print(f"An error occurred: {error}")
        return None

    # Use the provided preferred providers or a default list
    preferred_providers = [
        "Netflix", "Hulu", "Max", "Disney Plus", "Apple TV Plus",
        "Amazon Prime Video", "Peacock Premium", "Paramount Plus",
        "Paramount+ Amazon Channel", "Tubi TV", "Freevee", "TNT", "TBS", 
        "AMC+", "AMC", "AMC+ Amazon Channel", "AMC Plus Apple TV Channel ", "AMC+ Roku Premium Channel", 
        "MGM Plus", "Starz"
    ]

    amc_clones = ["AMC", "AMC+ Amazon Channel", "AMC Plus Apple TV Channel ", "AMC+ Roku Premium Channel"]

    streaming = []

    def process_providers(provider_list):
        nonlocal streaming
        # Iterate through the list of providers and extract relevant information
        for provider in provider_list:
            try:
                if provider['provider_name'] in preferred_providers:
                    if provider['provider_name'] in amc_clones:
                        streaming.append([526, "AMC+"])
                    else:
                        streaming.append([provider['provider_id'], provider['provider_name']])
            except Exception as provider_error:
                # Print or log the specific exception for debugging
                print(f"An error occurred while processing providers: {provider_error}")
                # Break the loop if an error occurs while processing providers
                break

    # Process both flatrate and ads providers
    process_providers(providers)
    process_providers(ads_providers)

    # Return the list of streaming providers or None if no valid providers are found
    return streaming if streaming else None

def get_awards(title, year):
    with open('./watchlist/the_oscar_award.json') as f, open('./watchlist/the_oscar_map.json') as g:
        data = json.load(f)
        map = json.load(g)
        return [{'year': item.get('year_film'), 'award': map[(item.get('category'))], 'win': item.get('winner')} for item in data if (item.get('film') == title and item.get('year_film') == year)]

# -----------------------------------------------
# STATIC VALUE GETTERS
# -----------------------------------------------

def get_trailer(tmdb_data):
    """
    Retrieves the official trailer key from TMDB data.

    Parameters:
    - tmdb_data (dict): The TMDB data containing information about videos.

    Returns:
    - str or None: The key of the official trailer if found, otherwise, None.
    """
    trailers = [{'key': member.get("key"), 'name': member.get("name")} for member in tmdb_data.get("videos", {}).get("results", []) if member.get('type') == 'Trailer']
    official_trailer = next((t['key'] for t in trailers if 'Official Trailer' in t.get('name', '')), None)
    if official_trailer:
        return official_trailer
    elif trailers:
        return trailers[0].get('key')

    return None

def get_runtime(tmdb_data, type):
    """
    Retrieve the runtime of a movie from TMDB data.

    Args:
    - tmdbData (dict): The TMDB API response containing information about a movie.
    - type (str): The type of content (e.g., "movie" or "series").

    Returns:
    - int or None: The runtime of the movie in minutes if it's a movie, or None for other types.
    """
    if type == "movie":
        # Use get() to avoid KeyError if "runtime" is not present in tmdbData
        return tmdb_data.get("runtime")
    else:
        return None

def get_seasons(tmdb_data, type):
    """
    Retrieve the number of seasons from TMDB data for a series.

    Args:
    - tmdbData (dict): The TMDB API response containing information about a series.
    - type (str): The type of content (e.g., "movie" or "series").

    Returns:
    - int or None: The number of seasons for the series if it's a series, or None for other types.
    """
    if type == "series":
        # Use get() to avoid KeyError if "number_of_seasons" is not present in tmdbData
        return tmdb_data.get("number_of_seasons")
    else:
        return None

def get_episodes(tmdb_data, type):
    """
    Retrieve the number of episodes from TMDB data for a series.

    Args:
    - tmdbData (dict): The TMDB API response containing information about a series.
    - type (str): The type of content (e.g., "movie" or "series").

    Returns:
    - int or None: The number of episodes for the series if it's a series, or None for other types.
    """
    if type == "series":
        # Use get() to avoid KeyError if "number_of_episodes" is not present in tmdbData
        return tmdb_data.get("number_of_episodes")
    else:
        return None

def get_release_date(tmdb_data, type):
    """
    Retrieve the release date from TMDB data for a movie or series.

    Args:
    - tmdbData (dict): The TMDB API response containing information about a movie or series.
    - type (str): The type of content (e.g., "movie" or "series").

    Returns:
    - str or None: The release date for the movie or series, or None if the date is not available.
    """
    if type == "movie":
        return tmdb_data.get("release_date")
    elif type == "series":
        return tmdb_data.get("first_air_date")
    else:
        return None

def getDecade(date_str):
    """
    Get the decade from a given date string.

    Args:
    - date_str (str): A date string in the format '%Y-%m-%d'.

    Returns:
    - str: The decade string (e.g., "2020s").
    """
    year = datetime.strptime(date_str, "%Y-%m-%d").year
    decade = (year // 10) * 10
    return f"{decade}s"

# -----------------------------------------------
# ADDITIONAL REVIEW SCORE GETTERS
# -----------------------------------------------

def fetch_html_content(url):
    """
    Fetches HTML content from a given URL.

    Parameters:
    - url (str): The URL to fetch HTML content from.

    Returns:
    - str: The HTML content if successful, None otherwise.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Failed to fetch the URL: {url}. Error: {e}")
        return None

def extract_letterboxd_rating(html):
    """
    Extracts the Letterboxd rating from HTML content.

    Parameters:
    - html (str): The HTML content to extract rating from.

    Returns:
    - str or None: The extracted rating value or None if not found.
    """
    json_start_index = html.find('{"image":"')
    json_end_index = html.find('/* ]]> */', json_start_index)
    
    if json_start_index != -1 and json_end_index != -1:
        json_string = html[json_start_index:json_end_index]
        json_data = json.loads(json_string)

        return json_data.get('aggregateRating', {}).get('ratingValue')

    return None

def get_letterboxd(title, year, type):
    """
    Retrieves the Letterboxd rating for a given title, year, and type.

    Parameters:
    - title (str): The title of the movie or series.
    - year (int): The release year of the movie.
    - type (str): The type of the content, either "movie" or "series".

    Returns:
    - str or None: The Letterboxd rating if available, None otherwise.
    """
    if type == "series":
        return None

    base_url = "https://letterboxd.com/film/"
    slugged_title_year = slugify(f"{title}-{year}")
    slugged_title = slugify(title)

    urls_to_try = [f"{base_url}{slugged_title_year}/", f"{base_url}{slugged_title}/"]

    for url in urls_to_try:
        html_content = fetch_html_content(url)
        if html_content:
            rating = extract_letterboxd_rating(html_content)
            if rating:
                return rating

    return None

def get_rotten_tomatoes(title, year):
    """
    Retrieves Rotten Tomatoes information for a given title and year.

    Parameters:
    - title (str): The title of the movie or series.
    - year (int): The release year of the content.

    Returns:
    - tuple or None: A tuple containing Rotten Tomatoes score and URL if available,
                    or None if information is not found.
    """
    omdb_xml_content = get_OMDB_xml(title, year)

    if omdb_xml_content:
        return parse_OMDB_xml(omdb_xml_content)
    else:
        return None, None

# ===============================================
# DATABASE UPDATE FUNCTIONS
# ===============================================
'''
Database update functions.
'''

def make_api_calls_and_update_database(title, year, rating, review, theaters, favorite, date_watched=None, service=None):
    start_time = time.time()

    try:
        omdb = get_OMDB(title, year)
        tmdb = get_TMDB(omdb)

        type = omdb["Type"]
        rt_critic, rt_user = get_rotten_tomatoes(title, year) if year < 2022 else (None, None)
        viewing_date = date_watched if date_watched is not None else None
        streaming_service = service if service and service != "" else None
        release_date = get_release_date(tmdb, type)
        IMDB = float(omdb["imdbRating"]) if omdb["imdbRating"] != "N/A" else None
        TMDB = float(tmdb["vote_average"]) if tmdb["vote_average"] != "N/A" else None
        MC = int(omdb["Metascore"]) if omdb["Metascore"] != 'N/A' else None
        RTCritic = int(rt_critic) if rt_critic and rt_critic != "N/A" else None
        RTUser = int(rt_user) if rt_user and rt_user != "N/A" else None
        LBXD = get_letterboxd(title, year, type)

        rating_fields = [IMDB, TMDB, MC, RTCritic, RTUser, LBXD]
        rating_score_maps = [10, 10, 1, 1, 1, 20]
        ratings = [field * rating_score for (field, rating_score) in zip(rating_fields, rating_score_maps) if field is not None and rating_score is not None]
        avg_critical_rating = round((sum(ratings) / 20) / len(ratings), 2) if ratings else None

        with transaction.atomic():
            movie = Movie(
                TMDB_ID=tmdb["id"],
                IMDB_ID=omdb["imdbID"],
                type=type,
                status=tmdb["status"],
                title=title,
                year=year,
                rating=rating,
                review=review if review != "" else None,
                date=viewing_date,
                datetime_added=timezone.now(),
                timesSeen=1,
                seasonsSeen=None,
                episodesSeen=None,
                posterLink=f"https://image.tmdb.org/t/p/original{tmdb['poster_path']}",
                bgLink=f"https://image.tmdb.org/t/p/original{tmdb['backdrop_path']}",
                trailerLink=f"https://youtube.com/embed/{get_trailer(tmdb)}",
                plot=omdb["Plot"],
                tagline=tmdb["tagline"],
                releaseDate=release_date,
                decade=getDecade(release_date),
                MPA=omdb["Rated"],
                runtime=get_runtime(tmdb, type),
                seasons=get_seasons(tmdb, type),
                episodes=get_episodes(tmdb, type),
                languages=omdb["Language"],
                countrys=omdb["Country"],
                IMDB=IMDB,
                TMDB=TMDB,
                MC=MC,
                RTCritic=RTCritic,
                RTUser=RTUser,
                LBXD=LBXD,
                avg_critical_rating=avg_critical_rating,
                service=streaming_service,
                theaters=theaters,
                favorite=favorite,
                elo = (rating * 200 + 900) if rating is not None else 900,
                eloMatches = 0
            )
            movie.save(using='library_db')

            try:
                watchlist_movie = WatchlistMovie.objects.get(pk=tmdb["id"])
                watchlist_movie.delete()
            except WatchlistMovie.DoesNotExist:
                pass

    except Exception as e:
        logging.error(f"Error updating database for {title}: {e}")
        return

    cast, roles = get_cast(tmdb, num=10)
    if cast:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            actors = list(executor.map(process_actor, cast))

        for actor, role in zip(actors, roles):
            MovieActor.objects.create(movie=movie, actor=actor, role=role)

    direc = get_directors(tmdb, type, num=10)
    if direc:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            directors = list(executor.map(process_director, direc))

        for director in directors:
            movie.director.add(director)

    companies = get_prod_companies(tmdb, num=10)
    if companies:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            prod_companies = list(executor.map(process_prod_company, companies))

        for company in prod_companies:
            movie.prodCompany.add(company)

    genres = get_genres(tmdb)
    if genres:
        for g in genres:
            gen = Genre(id=g[0], name=g[1])
            try:
                gen.save(using='library_db')
            except IntegrityError:
                pass
            movie.genres.add(gen)

    keywords = get_keywords(tmdb)
    if keywords:
        for k in keywords:
            key = Keyword(id=k[0], name=k[1])
            try:
                key.save(using='library_db')
            except IntegrityError:
                pass
            movie.keywords.add(key)

    awards = get_awards(title, year)
    if awards:
        for a in awards:
            awd = Award(name=a['award'], year=a['year'])
            try:
                awd.save(using='library_db')
            except:
                awd = Award.objects.get(name=a['award'], year=a['year'])
            MovieAward.objects.create(movie=movie, award=awd, winner=a['win'])

    print(f"{title} added in {time.time() - start_time} seconds.")

def make_api_calls_and_update_watchlist(title, year, favorite, tags, date_watched=None):
    start_time = time.time()

    try:
        omdb = get_OMDB(title, year)
        tmdb = get_TMDB(omdb)
        type = omdb["Type"]
        rt_critic, rt_user = get_rotten_tomatoes(title, year) if year < 2022 else (None, None)
        viewing_date = date_watched if date_watched is not None else None
        release_date = get_release_date(tmdb, type)
        
        IMDB = float(omdb["imdbRating"]) if omdb["imdbRating"] != "N/A" else None
        TMDB = float(tmdb["vote_average"]) if tmdb["vote_average"] != "N/A" else None
        MC = int(omdb["Metascore"]) if omdb["Metascore"] != 'N/A' else None
        RTCritic = int(rt_critic) if rt_critic and rt_critic != "N/A" else None
        RTUser = int(rt_user) if rt_user and rt_user != "N/A" else None
        LBXD = get_letterboxd(title, year, type)

        rating_fields = [IMDB, TMDB, MC, RTCritic, RTUser, LBXD]
        rating_score_maps = [10, 10, 1, 1, 1, 20]
        ratings = [field * rating_score for (field, rating_score) in zip(rating_fields, rating_score_maps) if field is not None]
        avg_critical_rating = round((sum(ratings) / 20) / len(ratings), 2) if ratings else None

        with transaction.atomic():
            movie = WatchlistMovie(
                TMDB_ID=tmdb["id"],
                IMDB_ID=omdb["imdbID"],
                type=type,
                status=tmdb["status"],
                title=title,
                year=year,
                date=viewing_date,
                reason=None,
                posterLink=f"https://image.tmdb.org/t/p/original{tmdb['poster_path']}",
                bgLink=f"https://image.tmdb.org/t/p/original{tmdb['backdrop_path']}",
                trailerLink=f"https://youtube.com/embed/{get_trailer(tmdb)}",
                plot=omdb["Plot"],
                tagline=tmdb["tagline"],
                releaseDate=release_date,
                decade=getDecade(release_date),
                MPA=omdb["Rated"],
                runtime=get_runtime(tmdb, type),
                seasons=get_seasons(tmdb, type),
                episodes=get_episodes(tmdb, type),
                languages=omdb["Language"],  # Langs csv
                countrys=omdb["Country"],  # Countries csv
                IMDB=IMDB,
                TMDB=TMDB,
                MC=MC,
                RTCritic=RTCritic,
                RTUser=RTUser,
                LBXD=LBXD,
                favorite=favorite,
                avg_critical_rating=avg_critical_rating,
            )
            movie.save(using='library_db')

    except Exception as e:
        logging.error(f"Error updating database for {title}: {e}")
        return

    # Update the database
    movie.save(using='library_db')

    cast, roles = get_cast(tmdb, num=10)
    if cast:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Use executor.map to process each actor_id concurrently
            actors = list(executor.map(process_actor, cast))

        for actor, role in zip(actors, roles):
            WatchlistActor.objects.create(movie=movie, actor=actor, role=role)

    direc = get_directors(tmdb, type, num=10)
    if direc:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            directors = list(executor.map(process_director, direc))

        for director in directors:
            movie.director.add(director)

    companies = get_prod_companies(tmdb, num=10)
    if companies:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            prod_companies = list(executor.map(process_prod_company, companies))

        for company in prod_companies:
            movie.prodCompany.add(company)

    genres = get_genres(tmdb)
    if genres:
        for g in genres:
            gen = Genre(id=g[0], name=g[1])
            try:
                gen.save(using='library_db')
            except IntegrityError:
                pass
            movie.genres.add(gen)

    keywords = get_keywords(tmdb)
    if keywords:
        for k in keywords:
            key = Keyword(id=k[0], name=k[1])
            try:
                key.save(using='library_db')
            except IntegrityError:
                pass
            movie.keywords.add(key)

    providers = get_providers(tmdb)
    if providers:
        for p in providers:
            prov = Provider(id=p[0], name=p[1])
            try:
                prov.save(using='library_db')
            except IntegrityError:
                pass
            movie.provider.add(prov)

    awards = get_awards(title, year)
    if awards:
        for a in awards:
            awd = Award(name=a['award'], year=a['year'])
            try:
                awd.save(using='library_db')
            except:
                awd = Award.objects.get(name=a['award'], year=a['year'])
            WatchlistAward.objects.create(movie=movie, award=awd, winner=a['win'])

    if tags:
        data = tags.split(',')
        for t in data:
            tag = Tag(name=t)
            try:
                tag.save(using='library_db')
            except:
                tag = Tag.objects.get(name=t)
            WatchlistTag.objects.create(movie=movie, tag=tag)

    print(f"{title} added in {time.time() - start_time} seconds.")

def make_api_calls_and_update_database_from_id(id, rating, review, theaters, date_Watched=None, service=None):
    t1 = time.time()
    load_dotenv()
    OMDB_KEY = os.getenv("OMDB_KEY")
    TMDB_KEY = os.getenv("TMDB_KEY")

    omdb = get_OMDB_from_id(OMDB_KEY, id)
    tmdb = get_TMDB(TMDB_KEY, omdb)
    title=omdb["Title"]
    year=omdb["Year"]
    type = omdb["Type"]
    viewingDate = date_Watched if date_Watched is not None else None
    streaming_service = service if service is not None and service != "" else None
    releaseDate = getReleaseDate(tmdb, type)
    num = 10  # Number of Cast, Directors, and Production Companies to pull.
    
    try:
        with transaction.atomic():
            movie = Movie(
                TMDB_ID=tmdb["id"],
                IMDB_ID=omdb["imdbID"],
                type=type,
                title=title,
                year=year,
                rating=rating,
                review=review if (review != "") else None,
                date=viewingDate,
                datetime_added = datetime.now(),
                timesSeen=1,
                posterLink=omdb["Poster"],
                plot=omdb["Plot"],
                tagline=tmdb["tagline"],
                releaseDate=releaseDate,
                decade=getDecade(releaseDate),
                MPA=omdb["Rated"],
                runtime=getRuntime(tmdb,type),
                seasons = getSeasons(tmdb,type),
                episodes = getEpisodes(tmdb,type), 
                languages = omdb["Language"],
                countrys = omdb["Country"], 
                IMDB = float(omdb["imdbRating"]) if omdb["imdbRating"] != "N/A" else None,
                TMDB = float(tmdb["vote_average"]) if tmdb["vote_average"] != "N/A" else None,
                MC = int(omdb["Metascore"]) if omdb["Metascore"] !='N/A' else None, 
                RTCritic = None,
                RTUser = None, 
                LBXD = get_letterboxd(title, year, type), 
                service = streaming_service if streaming_service != "" else None,
                theaters = theaters
            )
            movie.save(using='library_db')
            try:
                watchlist_movie = WatchlistMovie.objects.get(pk=tmdb["id"])
                watchlist_movie.delete()
            except:
                pass
    except Exception as e:
        logging.error(f"Error updating database for {title}: {e}")
        return

    cast = getCast(tmdb, num)
    if cast:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Use executor.map to process each actor_id concurrently
            actors = list(executor.map(partial(process_actor, TMDB_KEY), cast))

        for actor in actors:
            movie.cast.add(actor)
    else:
        pass

    direc = getDirectors(omdb, tmdb, type, num)
    if direc:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            directors = list(executor.map(partial(process_director, TMDB_KEY), direc))

        for director in directors:
            movie.director.add(director)
    else:
        # Handle the case when direc is empty
        pass

    companies = getProdCompanies(tmdb, num)
    if companies:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            prod_companies = list(executor.map(partial(process_prod_company, TMDB_KEY), companies))

        for company in prod_companies:
            movie.prodCompany.add(company)
    else:
        # Handle the case when companies is empty
        pass

    genres = getGenres(tmdb,num)
    if genres:
        for g in genres:
            gen = Genre(id=g[0], name=g[1])
            try:
                gen.save(using='library_db')
            except:
                None
            movie.genres.add(gen)
    else:
        None
    
    print(f"{title} added in {time.time() - t1} seconds.")

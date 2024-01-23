import os
import json
import time
import logging
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from slugify import slugify
from datetime import datetime
from watchlist.models import Movie, Actor, MovieActor, Director, Genre, ProdCompany, Provider, WatchlistMovie, WatchlistActor
from watchlist.api_calls import *  
import concurrent.futures
from django.db import transaction
from functools import partial

# GETTERS
def getRottenTomatoes(title, year):
    load_dotenv()
    OMDB_KEY = os.getenv("OMDB_KEY")
    omdb_xml_content = get_OMDB_xml(OMDB_KEY, title, year)

    if omdb_xml_content:
        return parse_OMDB_xml(omdb_xml_content)
    else:
        return None, None

def getCast(tmdbData, num):
    cast = [tmdbData["credits"]["cast"][i]["id"] for i in range(num) if i < len(tmdbData["credits"]["cast"])] or None
    roles = [tmdbData["credits"]["cast"][i]["character"] for i in range(num) if i < len(tmdbData["credits"]["cast"])] or None
    return cast, roles

def getDirectors(omdbData, tmdbData, type, num):
    if (type == 'series'): 
        direc = [tmdbData["created_by"][i]["id"] for i in range(num) if i < len(tmdbData["created_by"])] or None
    else: 
        direc = []
        for member in tmdbData["credits"]["crew"]:
            if member['job'] == 'Director':
                direc.append(member["id"])
    return direc

def getProdCompanies(tmdbData, num):
    prodCompanies = [tmdbData["production_companies"][i]["id"] for i in range(num) if i < len(tmdbData["production_companies"])] or None
    return prodCompanies

def getGenres(tmdbData, num):
    cast = [[tmdbData["genres"][i]["id"], tmdbData["genres"][i]["name"]] for i in range(num) if i < len(tmdbData["genres"])] or None
    return cast

def getRuntime(tmdbData, type):
    if (type == "movie"): return tmdbData["runtime"]
    else: return None

def getSeasons(tmdbData, type):
    if (type == "series"): return tmdbData["number_of_seasons"]
    else: return None

def getEpisodes(tmdbData, type):
    if (type == "series"): return tmdbData["number_of_episodes"]
    else: return None

def getReleaseDate(tmdbData, type):
    if (type == "movie"): return tmdbData["release_date"]
    else: return tmdbData["first_air_date"]

def getDecade(date_str):
    year = datetime.strptime(date_str, "%Y-%m-%d").year
    decade = (year // 10) * 10
    return f"{decade}s"

def convert_to_slug(input_string):
    return slugify(input_string)

def extract_letterboxd(url_val):
    url = "https://letterboxd.com/film/" + url_val + "/"

    # Fetch the HTML content of the page
    response = requests.get(url)

    if response.status_code == 200:
        html = response.text

        # Search for the JSON data within the <script> tag
        json_start_index = html.find('{"image":"')
        json_end_index = html.find('/* ]]> */', json_start_index)
        
        if json_start_index != -1 and json_end_index != -1:
            json_string = html[json_start_index:json_end_index]
            json_data = json.loads(json_string)

            if json_data and json_data.get('aggregateRating') and json_data['aggregateRating'].get('ratingValue'):
                rating_value = json_data['aggregateRating']['ratingValue']
                return rating_value
            else:
                print("Rating Value not found in JSON data.")
        else:
            print("JSON data not found in the HTML content.")
    else:
        print(f"Failed to fetch the URL. Response code: {response.status_code}")

def get_letterboxd(title, year, type):
    if type == "series":
        return None

    try:
        rating = extract_letterboxd(convert_to_slug(title))
        if not rating:
            raise ValueError("Icky Bad!")
        return rating
    except ValueError:
        try:
            rating = extract_letterboxd(convert_to_slug(f"{title}-{year}"))
            if not rating:
                raise ValueError("Icky Bad!")
            return rating
        except ValueError:
            return None

def getProviders(tmdb):
    try:
        providers = tmdb.get('watch/providers', {}).get('results', {}).get('US', {}).get('flatrate', [])
        ads_providers = tmdb.get('watch/providers', {}).get('results', {}).get('US', {}).get('ads', [])
    except Exception as e:
        return None

    my_providers = [
        "Netflix", "Hulu", "Max", "Disney Plus", "Apple TV Plus",
        "Amazon Prime Video", "Peacock Premium", "Paramount Plus",
        "Paramount+ Amazon Channel", "Tubi TV", "Freevee", "TNT", "TBS"
    ]

    streaming = []

    def process_providers(provider_list):
        nonlocal streaming
        for provider in provider_list:
            try:
                if provider['provider_name'] in my_providers:
                    streaming.append([provider['provider_id'], provider['provider_name']])
            except Exception as e:
                break

    process_providers(providers)
    process_providers(ads_providers)

    return streaming if streaming else None

# PROCESS FUNCTIONS
def process_actor(TMDB_KEY, actor_id):
    actor_tmdb = get_person_TMDB(TMDB_KEY, actor_id)
    actor = Actor(
        TMDB_ID=actor_tmdb["id"],
        IMDB_ID=actor_tmdb["imdb_id"],
        name=actor_tmdb["name"],
        bio=actor_tmdb["biography"],
        birthday=actor_tmdb["birthday"],
        imgLink=actor_tmdb["profile_path"]
    )
    try:
        actor.save(using='library_db')
    except:
        pass
    return actor

def process_director(TMDB_KEY, direc_id):
    direc_tmdb = get_person_TMDB(TMDB_KEY, direc_id)
    director = Director(
        TMDB_ID=direc_tmdb["id"],
        IMDB_ID=direc_tmdb["imdb_id"],
        name=direc_tmdb["name"],
        bio=direc_tmdb["biography"],
        birthday=direc_tmdb["birthday"],
        imgLink=direc_tmdb["profile_path"]
    )
    try:
        director.save(using='library_db')
    except:
        pass
    return director

def process_prod_company(TMDB_KEY, comp):
    comp_tmdb = get_company_TMDB(TMDB_KEY, comp)
    company = ProdCompany(
        id=comp_tmdb["id"],
        name=comp_tmdb["name"],
        logo=comp_tmdb["logo_path"]
    )
    try:
        company.save(using='library_db')
    except:
        pass
    return company
    
# DATABASE UPDATES
def make_api_calls_and_update_database(title, year, rating, review, theaters, date_Watched=None, service=None):
    t1 = time.time()
    load_dotenv()
    OMDB_KEY = os.getenv("OMDB_KEY")
    TMDB_KEY = os.getenv("TMDB_KEY")

    omdb = get_OMDB(OMDB_KEY, title, year)
    tmdb = get_TMDB(TMDB_KEY, omdb)
    type = omdb["Type"]
    rtCritic, rtUser = getRottenTomatoes(title, year) if year < 2022 else (None, None)
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
                RTCritic = int(rtCritic) if (rtCritic != "N/A" and rtCritic is not None) else None, 
                RTUser = int(rtUser) if (rtCritic != "N/A" and rtUser is not None) else None, 
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

    cast, roles = getCast(tmdb, num)
    if cast:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Use executor.map to process each actor_id concurrently
            actors = list(executor.map(partial(process_actor, TMDB_KEY), cast))

        for actor, role in zip(actors, roles):
            print(actor.name, role)
            MovieActor.objects.create(movie=movie, actor=actor, role=role)
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

def make_api_calls_and_update_watchlist(title, year, reason, date_Watched=None):
    t1 = time.time()
    load_dotenv()
    OMDB_KEY = os.getenv("OMDB_KEY")
    TMDB_KEY = os.getenv("TMDB_KEY")

    omdb = get_OMDB(OMDB_KEY, title, year)
    tmdb = get_TMDB(TMDB_KEY, omdb)
    type = omdb["Type"]
    rtCritic, rtUser = getRottenTomatoes(title, year) if year < 2022 else (None, None)
    viewingDate = date_Watched if date_Watched is not None else None
    releaseDate = getReleaseDate(tmdb, type)
    num = 10 # Number of Cast, Directors, and Production Companies to pull.

    try:
        with transaction.atomic():
            movie = WatchlistMovie(
                TMDB_ID=tmdb["id"],
                IMDB_ID=omdb["imdbID"],
                type=type,
                title=title,
                date = viewingDate,
                year=year,
                reason=reason,
                posterLink=omdb["Poster"],
                plot=omdb["Plot"],
                tagline=tmdb["tagline"],
                releaseDate=releaseDate,
                decade=getDecade(releaseDate),
                MPA=omdb["Rated"],
                runtime=getRuntime(tmdb,type),
                seasons = getSeasons(tmdb,type), # Seasons
                episodes = getEpisodes(tmdb,type), # Episodes
                languages = omdb["Language"], # Langs csv
                countrys = omdb["Country"], # Countries csv
                IMDB = float(omdb["imdbRating"]) if omdb["imdbRating"] != "N/A" else None, # IMDB Score
                TMDB = float(tmdb["vote_average"]) if tmdb["vote_average"] != "N/A" else None, # TMDB Score
                MC = int(omdb["Metascore"]) if omdb["Metascore"] !='N/A' else None, # Metascore
                RTCritic = int(rtCritic) if (rtCritic != "N/A" and rtCritic is not None) else None, # RottenTomatoes Score
                RTUser = int(rtUser) if (rtCritic != "N/A" and rtUser is not None) else None, # RottenTomatores Userscore
                LBXD = get_letterboxd(title, year, type) # Letterboxd Score
            )
            movie.save(using='library_db')
    except Exception as e:
        logging.error(f"Error updating database for {title}: {e}")
        return

    # Update the database
    movie.save(using='library_db')

    cast, roles = getCast(tmdb, num)
    if cast:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Use executor.map to process each actor_id concurrently
            actors = list(executor.map(partial(process_actor, TMDB_KEY), cast))

        for actor, role in zip(actors, roles):
            print(actor.name, role)
            WatchlistActor.objects.create(movie=movie, actor=actor, role=role)
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
    
    providers = getProviders(tmdb)
    if providers:
        for p in providers:
            prov = Provider(id=p[0],name=p[1])
            try:
                prov.save(using='library_db')
            except:
                None
            movie.provider.add(prov)
    else:
        None

    print(f"{title} : added in  {time.time()-t1} seconds.")

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

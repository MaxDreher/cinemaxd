import sys
sys.path.append(r"D:\Users\Max\MovieSite")

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MovieSite.settings')
django.setup()

import time
import random
from watchlist.models import *
from watchlist.api_calls import *  
from watchlist.utils import get_trailer, get_keywords
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from api_calls import get_TMDB_from_id
from utils import get_awards


# Manual Poster Entry Link
"https://a.ltrbxd.com/resized/alternative-poster/7/3/1/2/2/2/p/8y7tqHjwN2HPdQewW83euyj1os0-0-500-0-750-crop.jpg"
# or 
key = "alternative-poster/7/3/1/2/2/2/p/8y7tqHjwN2HPdQewW83euyj1os0"
link = f"https://a.ltrbxd.com/resized/{key}-0-500-0-750-crop.jpg"

# Manual Movie Deletion given List of IDs
def deleteMovie(list):
    for item in list:
        try:
            movie = Movie.objects.get(pk=item)
        except:
            movie = WatchlistMovie.objects.get(pk=item)
        movie.delete()

# deleteMovie([226979])

keys = [88728]
for key in keys:
    item = Movie.objects.get(pk=key)
    item.date=None
    item.save()

def createTags():
    for movie in WatchlistMovie.objects.all():
        if movie.reason:
            tags = movie.reason.split(', ')
            for t in tags:
                tag = Tag(name=t)
                try:
                    tag.save(using='library_db')
                except:
                    tag = Tag.objects.get(name=t)
                WatchlistTag.objects.create(movie=movie, tag=tag)

# --------------------------------------------
#             Garbage Functions
# --------------------------------------------


def movieOscars():
    d = MovieAward.objects.all()
    d.delete()

    for movie in Movie.objects.all():
        print(f"{movie.title} {movie.year}")
        awards = get_awards(movie.title, movie.year)
        if awards:
            for a in awards:
                awd = Award(name=a['award'], year=a['year'])
                try:
                    awd.save(using='library_db')
                except:
                    awd = Award.objects.get(name=a['award'], year=a['year'])
                MovieAward.objects.create(movie=movie, award=awd, winner=a['win'])


def watchlistOscars():
    d = WatchlistAward.objects.all()
    d.delete()

    for movie in WatchlistMovie.objects.all():
        print(f"{movie.title} {movie.year}")
        awards = get_awards(movie.title, movie.year)
        if awards:
            for a in awards:
                awd = Award(name=a['award'], year=a['year'])
                try:
                    awd.save(using='library_db')
                except:
                    awd = Award.objects.get(name=a['award'], year=a['year'])
                WatchlistAward.objects.create(movie=movie, award=awd, winner=a['win'])


def customPoster(id, link):
    movie = Movie.objects.get(pk=id)
    movie.posterLink = link
    movie.save()


# (200, 900) as defaults for scale of (1000, 1100, 1200, 1300, 1400, 1500, ...)
def defaultElo(scalingFactor, default):
    for movie in Movie.objects.filter(rating__isnull=False):
        movie.elo = (movie.rating * scalingFactor) + default
        # movie.elo = round(movie.elo, 2)
        print(f"{movie.title} ({movie.year}): {movie.elo}")
        movie.save()


def random_elo_match(movies, k, num):
    while num > 0:
        random_movies = random.sample(list(movies), 2)
        
        print(f"{random_movies[0].title} {random_movies[0].elo} vs. {random_movies[1].title} {random_movies[1].elo}")
        
        p1 = 1.0 / (1 + 10 ** ((random_movies[1].elo - random_movies[0].elo) / 400))
        p2 = 1.0 - p1
        
        response = input("1 or 2: ")
        
        if response == '1':
            update_elo(random_movies[0], random_movies[1], k, p1, p2)
        elif response == '2':
            update_elo(random_movies[1], random_movies[0], k, p2, p1)
        num = num - 1


def update_elo(winner, loser, k, pw, pl):
    winner.elo += round(k * (1 - pw), 2)
    loser.elo += round(k * (0 - pl), 2)
    
    print(f"{winner.title} {winner.elo} vs. {loser.title} {loser.elo}")
    
    winner.save()
    loser.save()


def correct_embed():
    for mov in Movie.objects.all():
        if "/watch/" in mov.trailerLink:
            new_url = mov.trailerLink.replace("/watch/", "/embed/")
            print(new_url)
            mov.trailerLink = new_url
            mov.save()
        else:
            print("The URL format is not as expected.")


def updateWatchlistPosterTrailer():
    t1 = time.time()
    for mov in WatchlistMovie.objects.all():
        tmdb = get_TMDB_from_id(mov.TMDB_ID, mov.type)
        omdb = get_OMDB_from_id(mov.IMDB_ID)
        mov.posterLink = omdb['Poster']
        print(f"{mov.title} {mov.year}")
        mov.status = tmdb['status']
        mov.bgLink = f"https://image.tmdb.org/t/p/original{tmdb['backdrop_path']}"
        mov.trailerLink = f"https://youtube.com/embed/{get_trailer(tmdb)}"
        mov.save()
    print(f"Completed Watchlog update in {time.time()-t1} seconds")


def updateWatchlogKeywords():
    t1 = time.time()
    for mov in Movie.objects.all():
        print(f"{mov.title} at {time.time()-t1} seconds.")
        tmdb = get_TMDB_from_id(mov.TMDB_ID, mov.type)
        # omdb = get_OMDB(mov.IMDB_ID)
        # mov.posterLink = omdb['Poster']
        keywords = get_keywords(tmdb)
        if keywords:
            for k in keywords:
                print(k[1])
                key = Keyword(id=k[0], name=k[1])
                try:
                    key.save(using='library_db')
                except IntegrityError:
                    print('failed')
                    pass
                mov.keywords.add(key)
        mov.save()
    print(f"Completed Watchlog update in {time.time()-t1} seconds")


def delete_movie_actors_with_null_role():
    movie_actors_to_delete = MovieActor.objects.filter(role__isnull=True)
    movie_actors_to_delete.delete()

def delete_watchlist_actors_with_null_role():
    movie_actors_to_delete = WatchlistActor.objects.filter(role__isnull=True)
    movie_actors_to_delete.delete()
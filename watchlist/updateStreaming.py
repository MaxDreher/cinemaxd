import sys
sys.path.append(r"D:\Users\Max\MovieSite")

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MovieSite.settings')
django.setup()

from watchlist.models import WatchlistMovie, WatchlistProvider, Provider
from api_calls import get_TMDB_from_id
from utils import getProviders
from dotenv import load_dotenv
import time
import concurrent.futures

def main():
    def updateStreaming(movie):
        print(f"Updating Streaming for {movie.title} {movie.year}")
        load_dotenv()
        TMDB_KEY = os.getenv("TMDB_KEY")
        tmdb = get_TMDB_from_id(TMDB_KEY, movie.TMDB_ID, movie.type)

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

    t1 = time.time()
    movies = WatchlistMovie.objects.all()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(updateStreaming, movies)

    print(f"Time to Update Streaming Services: {time.time()-t1}")

main()
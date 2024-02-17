import sys
sys.path.append(r"D:\Users\Max\MovieSite")
# sys.path.append(r"C:\Users\maxan\moviesite")

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MovieSite.settings')
django.setup()

from watchlist.models import WatchlistMovie, WatchlistProvider, Provider
from api_calls import get_TMDB_from_id
from utils import get_providers
from dotenv import load_dotenv
import time
import concurrent.futures

def main():
    def updateStreaming(movies):
        for movie in movies:
            print(f"Updating Streaming for {movie.title} {movie.year}")
            tmdb = get_TMDB_from_id(movie.TMDB_ID, movie.type)

            providers = get_providers(tmdb)
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

    # Specify the batch size for fetching movie details
    batch_size = 5
    movies = WatchlistMovie.objects.all()
    t1 = time.time()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for i in range(0, len(movies), batch_size):
            movie_batch = movies[i:i + batch_size]
            executor.submit(updateStreaming, movie_batch)

    print(f"Time to Update Streaming Services: {time.time()-t1}")

main()
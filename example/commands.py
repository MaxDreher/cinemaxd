from django.db import transaction
from django.db.models import Count, F, Q

from moviedb.models import Movie, Provider
from moviedb.api_calls import get_TMDB_from_id
# from moviedb.utils import get_providers, recreate_movie, recreate_cast
from moviedb.entry import *
from datetime import date
import os
import datetime
import time

                    
def update_streaming():

    updated = [f"Update Log for {datetime.date.today()}"]

    def updateStreaming(movie):
        e = entry({'id': movie.TMDB_ID, 'type': movie.type})
        providers = e._get_providers()
        length_providers = len(providers) if providers is not None else 0

        current_providers = set(movie.provider.values_list('id', flat=True))
        new_providers = set(p.get('id') for p in providers) if providers else set()

        if current_providers != new_providers:

            favs = ["\033[34m", "\033[0m"] if movie.favorite else ["", ""]
            print(f"{favs[0]}Updated Streaming for {movie.title} ({movie.year}): ({len(current_providers)}) -> ({length_providers}){favs[1]}")
            updated.append(f"Updated Streaming for {movie.title} ({movie.year}): ({len(current_providers)}) -> ({length_providers})")

            movie.provider.clear()
            if providers:
                with transaction.atomic(using='library_db'):
                    for p in providers:
                        try:
                            # Try to get the provider by ID and name
                            provider = Provider.objects.get(pk=p.get('id'), name=p.get('name'))
                            movie.provider.add(provider)

                        except Provider.DoesNotExist:
                            # If the provider does not exist, create and add it
                            prov = Provider(id=p[0], name=p[1])
                            prov.save(using="library_db")
                            movie.provider.add(prov)

    movies = Movie.objects.filter(seen=False).annotate(count=Count('movieprovider'))

    t1 = time.time()
    for movie in movies:
        updateStreaming(movie)

    file_name = "updateLog.txt"
    file_path = os.path.join("moviedb", "data", "logs", file_name)

    closing_statement = f"Time to Update Streaming Services: {time.time() - t1}"
    updated.append(closing_statement)

    with open(file_path, "w") as x:
        for item in updated:
            x.write(f"{item}\n")

    print(closing_statement)


def update_unreleased():
    updated = [f"Update Log for {datetime.date.today()}"]

    t1 = time.time()

    movies = Movie.objects.filter(date__lt=F('releaseDate'))
    for movie in movies:
        updated.append(recreate_movie(movie))

    file_name = "unreleasedLog.txt"
    file_path = os.path.join("moviedb", "data", "logs", file_name)

    closing_statement = f"Time to Update Unreleased Films: {time.time() - t1}"
    updated.append(closing_statement)

    with open(file_path, "w") as x:
        for item in updated:
            x.write(f"{item}\n")


def update_cast():
    updated = [f"Update Log for {datetime.date.today()}"]

    t1 = time.time()

    start_date = date(2024, 3, 28)
    end_date = date(2024, 4, 8)

    movies = Movie.objects.filter(
        Q(date__lt=start_date) | Q(date__gt=end_date) | Q(date__isnull=True) | Q(seen=False)
    )
    
    i = 1
    for movie in movies:
        print(f"{i}: {movie.title} ({movie.year})")
        updated.append(recreate_cast(movie))
        i += 1

    file_name = "castLog.txt"
    file_path = os.path.join("moviedb", "data", "logs", file_name)

    closing_statement = f"Time to Update Casts for all Films: {time.time() - t1}"
    updated.append(closing_statement)

    with open(file_path, "w") as x:
        for item in updated:
            x.write(f"{item}\n")

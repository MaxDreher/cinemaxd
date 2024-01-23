from django.db.models import Prefetch, Case, When, IntegerField, Avg, Count, Min, Sum, Q, Func
from .models import *

def navbar_data(request):
    # Fetch data from your model or other source
    movie_total = Movie.objects.filter(type="movie").count()
    series_total = Movie.objects.filter(type="series").count()
    total_time = Movie.objects.aggregate(Sum("runtime"))
    total_episodes = Movie.objects.aggregate(Sum("episodes"))
    total_seasons = Movie.objects.aggregate(Sum("seasons"))
    watchlist_total = WatchlistMovie.objects.all().count()

    return {'movie_total': movie_total,
            'series_total': series_total,
            'total_time': total_time,
            'total_episodes': total_episodes,
            'total_seasons': total_seasons,
            'watchlist_total': watchlist_total
            }

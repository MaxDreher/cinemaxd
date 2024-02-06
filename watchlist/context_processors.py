from django.db.models import Prefetch, Case, When, IntegerField, Avg, Count, Min, Sum, Q, Func
from .models import *

def navbar_data(request):
    navigation_links = [
        ('dashboard', 'bi-grid-3x3-gap-fill', 'DASHBOARD'),
        ('watchlog', 'bi-collection-play-fill', 'WATCHLOG'),
        ('watchlist', 'bi-eye-fill', 'WATCHLIST'),
        ('rankings', 'bi-list-columns-reverse', 'RANKINGS'),
        ('elo', 'bi-calculator', 'ELO'),
    ]
    
    stat_data = [
        ('total_movies', 'movies', Movie.objects.filter(type="movie").count()),
        ('total_series', 'series', Movie.objects.filter(type="series").count()),
        ('total_runtime', 'mins', Movie.objects.aggregate(Sum("runtime"))['runtime__sum']),
        ('total_episodes', 'episodes', Movie.objects.aggregate(Sum("episodes"))['episodes__sum']),
        ('total_seasons', 'seasons', Movie.objects.aggregate(Sum("seasons"))['seasons__sum']),
        ('watchlist_total', 'to watch', WatchlistMovie.objects.all().count()),
    ]

    return {'navigation_links': navigation_links,
            'stat_data': stat_data,
            }

from django.db.models import Prefetch, Case, When, IntegerField, Avg, Count, Min, Sum, Q, Func
from .models import *

def navbar_data(request):
    # Fetch data from your model or other source
    movie_total = Movie.objects.filter(type="movie").count()
    series_total = Movie.objects.filter(type="series").count()

    return {'movie_total': movie_total,
            'series_total': series_total
            }

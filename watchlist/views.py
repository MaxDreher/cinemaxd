from django.http import JsonResponse
from django.db.models import Prefetch, Case, When, IntegerField, Avg, Count, Min, Sum, Q, Func
from django.db.models.functions import ExtractWeekDay
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from .forms import MovieForm, WatchlistForm, RankingForm
from django.conf import settings
from .models import *
from datetime import *
import json 
import random
import os
from dotenv import load_dotenv
from .api_calls import get_OMDB, get_TMDB
from .utils import make_api_calls_and_update_database, make_api_calls_and_update_watchlist  # Create this function
from .viewUtils import *
class Round(Func):
    function = 'ROUND'
    template = '%(function)s(%(expressions)s, 2)'

# ACTIVE:

def get_random_movies(request):
    idlist = [i.TMDB_ID for i in WatchlistMovie.objects.filter(provider__isnull=False)]
    rand_ids = random.sample(idlist, 5)
    rand_movies = [WatchlistMovie.objects.get(pk=i) for i in rand_ids]
    context = {
        'random': rand_movies,
        'url_start': 'https://www.themoviedb.org/t/p/w90_and_h90_face',
    }
    return render(request, 'watchlist/randomMovies.html', context)

    return

def get_movie_info(request):
    # Get movie name and year from the request
    title = request.GET.get('id_title')
    year = request.GET.get('id_year')

    omdb = get_OMDB(title, year)
    tmdb = get_TMDB(omdb)
    

    # Process the API response (replace this with your actual response processing)
    poster_url = f"https://image.tmdb.org/t/p/original{tmdb['poster_path']}"

    return JsonResponse({'poster_url': poster_url})

def sidebar_ajax(request, movie_id):
    try:
        movie = Movie.objects.get(pk=movie_id)
    except:
        movie = WatchlistMovie.objects.get(pk=movie_id)
    context = {
        'movie': movie,
        'url_start': 'https://www.themoviedb.org/t/p/w90_and_h90_face',
    }
    return render(request, 'watchlist/offcanvas_movie.html', context)

def elo_matchup(request):
    winner = Movie.objects.get(pk=request.GET.get('id_winner'))
    loser = Movie.objects.get(pk=request.GET.get('id_loser'))

    p1 = 1.0 / (1 + 10 ** ((winner.elo - loser.elo) / 400))
    p2 = 1.0 - p1

    winner.elo += round(64 * (1 - p2), 2)
    loser.elo += round(64 * (0 - p1), 2)
    winner.eloMatches += 1
    loser.eloMatches += 1
    winner.save()
    loser.save()

    movies = Movie.objects.filter(rating__isnull=False)
    matches = movies.aggregate((Sum('eloMatches'))).get('eloMatches__sum') // 2
    context = {
        'movies': random.sample(list(movies), 2),
        'matches': matches
    }
    return render(request, 'watchlist/eloMatchup.html', context)

@csrf_exempt  # Use this decorator for simplicity; you might want to use a proper csrf token setup in production
def save_poster_link(request):
    if request.method == 'POST':
        movie_id = request.POST.get('movieId')
        poster_link = request.POST.get('posterLink')
        movie = Movie.objects.get(pk=movie_id)
        movie.posterLink = poster_link
        movie.save()
        return JsonResponse({'message': 'Link saved successfully'})

    return JsonResponse({'message': 'Invalid request method'}, status=400)

class WatchlogView(View):
    template_name = 'watchlist/watchlog.html'

    def get(self, request):
        data = Movie.objects.all()
        form = MovieForm()
        context = {
            'data': data,
            'form': form,
            'url_start': 'https://www.themoviedb.org/t/p/w90_and_h90_face',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = MovieForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            year = form.cleaned_data['year']
            rating = form.cleaned_data['rating']
            review = form.cleaned_data['review']
            date_watched = form.cleaned_data['date_watched']
            service = form.cleaned_data['service']
            theaters = form.cleaned_data['theaters']
            cleaned = {
                'title': title,
                'year': year,
                'rating': rating,
                'review': review,
                'date': date_watched,
                'service': service,
                'theaters': theaters
            }
            try:
                update_object = Movie.objects.get(title=title, year=year)
                for key, value in cleaned.items():
                    if value != "" and value is not None and value != False:
                        if getattr(update_object, key) != value:
                            setattr(update_object, key, value)
                update_object.save()
            except Movie.DoesNotExist:
                make_api_calls_and_update_database(title, year, rating, review, theaters, date_watched, service)

            # Fetch the updated data after saving
            data = Movie.objects.all()
            title_year = f'<span><i class="bi bi-check-circle-fill"></i>&nbsp;&nbsp;{title} ({year}) has been successfully added!<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></span>'
            # Render the table HTML using Django template
            response_data = {
                'title_year': title_year,
                'table_html': render_to_string('watchlist/watchlog-table.html', {'data': data})
            }

            return JsonResponse(response_data)
        else:
            print(form.errors)
        
        data = Movie.objects.all()
        context = {
            'data': data,
            'form': form,
        }
        return render(request, self.template_name, context)

class WatchlistView(View):
    template_name = 'watchlist/watchlist.html'

    def get(self, request):
        data = WatchlistMovie.objects.all()
        form = WatchlistForm()
        context = {
            'data': data,
            'form': form,
            'url_start': 'https://www.themoviedb.org/t/p/w90_and_h90_face',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        form = WatchlistForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            year = form.cleaned_data['year']
            date_added = form.cleaned_data['date_added']
            reason = form.cleaned_data['reason']

            cleaned = {
                'title': title,
                'year': year,
                'date': date_added,
                'reason': reason,
            }

            try:
                update_object = WatchlistMovie.objects.get(title=title, year=year)
                for key, value in cleaned.items():
                    if getattr(update_object, key) != value:
                        setattr(update_object, key, value)
                update_object.save()
            except WatchlistMovie.DoesNotExist:
                make_api_calls_and_update_watchlist(title, year, reason, date_added)
            data = WatchlistMovie.objects.all()
            title_year = f'<span><i class="bi bi-check-circle-fill"></i>&nbsp;&nbsp;{title} ({year}) has been successfully added!<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></span>'
            response_data = {
                'title_year': title_year,
                'table_html': render_to_string('watchlist/watchlist-table.html', {'data': data})
            }
            return JsonResponse(response_data)
        else:
            print(form.errors)
        
        data = WatchlistMovie.objects.all()
        context = {
            'data': data,
            'form': form,
        }
        return render(request, self.template_name, context)

class RankingsView(View):
    template_name = 'watchlist/rankings.html'

    def get(self, request):
        movies = get_list_in_order(1)  
        startDate = date(2023, 8, 15)
        today = date.today()

        newest = movies.order_by('-datetime_added').first()

        form = RankingForm()
        context = {
            'data': movies,
            'form': form,
            'stats': get_stats(movies, startDate, today),
            'longest_days': get_longest_days(movies, 5),
            'latest': newest,
            'start': startDate,
            'end': today,
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request):
        form = RankingForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            year = form.cleaned_data['year']

            every_night_list = List.objects.get(pk=1)
            movie = Movie.objects.get(title=title, year=year)
            MovieList.objects.create(list=every_night_list, movie=movie, order=0)

            return redirect('rankings')  # Redirect to the same page after adding a movie

@csrf_exempt   
def update_order(request):
    if request.method == 'POST':
        movie_ids = request.POST.getlist('movie_ids[]')
        list_id = request.POST.get('list_id')
        # Check for empty values
        if not list_id or not movie_ids:
            return JsonResponse({'status': 'error', 'message': 'Invalid list_id or movie_ids'}, status=400)

        try:
            for order, movie_id in enumerate(movie_ids, start=1):
                list_movie_order = MovieList.objects.get(list_id=list_id, movie_id=movie_id)
                list_movie_order.order = order
                list_movie_order.save()

            return JsonResponse({'status': 'success'})
        except MovieList.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Movie or list not found'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

class DashboardView(View):
    def get(self, request):
        movies = Movie.objects.all()
        today = date.today()

        context = {
            'newest': movies.order_by('-datetime_added').first(),
            'today': today,
            'week': get_week_info(movies, today), # from viewUtils
            'month': get_month_info(movies, today), # from viewUtils
            'year': get_year_info(movies, today), # from viewUtils
            'heatmap': get_heatmap_data(movies, today), # from viewUtils
            'year_count_data': get_year_count_data(movies, today), # from viewUtils,
            'country_data': get_country_data(), # from viewUtils,
            'keyword_data': get_keyword_data(), # from viewUtils
            'ratings_data': get_rating_distribution(movies), # from viewUtils
            'weekday_distribution': get_weekday_distribution(movies), # from viewUtils
            'on_this_day': on_this_day(today), # from viewUtils
            'streak': get_streak(today), # from viewUtils
            'random': get_random_on_streaming(), # from viewUtils
            'actors': get_top_actors(movies, 10, 4), # from viewUtils
            'directors': get_top_directors(movies, 10, 3), # from viewUtils
            'url_start': 'https://www.themoviedb.org/t/p/w90_and_h90_face',
        }
        return render(request, 'watchlist/dashboard.html', context)

class EloView(View):
    def get(self, request):
        movies = Movie.objects.filter(rating__isnull=False)
        matches = movies.aggregate((Sum('eloMatches'))).get('eloMatches__sum') // 2

        context = {
            'movies': random.sample(list(movies), 2),
            'matches': matches
        }
        return render(request, 'watchlist/elo.html', context)

from django.http import JsonResponse
from django.db.models import Prefetch, Case, When, IntegerField, Avg, Count, Min, Sum
from django.shortcuts import render, redirect
from django.core import serializers
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from .forms import MovieForm, WatchlistForm, RankingForm
from django.conf import settings
from .models import *
import datetime

from .api_calls import get_OMDB
from .utils import make_api_calls_and_update_database, make_api_calls_and_update_watchlist  # Create this function

# DISCONTINUED:
class AddMovieView(View):
    def get(self, request):
        form = MovieForm()
        return render(request, 'watchlist/add_movie.html', {'form': form})

    def post(self, request):
        form = MovieForm(request.POST)
        if form.is_valid():
            # Get form data
            title = form.cleaned_data['title']
            year = form.cleaned_data['year']
            rating = form.cleaned_data['rating']
            review = form.cleaned_data['review']
            date_watched = form.cleaned_data['date_watched']

            # Make API calls and update the database
            make_api_calls_and_update_database(title, year, rating, review, date_watched)

            return redirect('add_movie')  # Redirect to the movie list page or any other page

        return render(request, 'watchlist/add_movie.html', {'form': form})

class AddWatchlistView(View):
    def get(self, request):
        return render(request, 'watchlist/add_watchlist.html')


# ACTIVE:
class WatchlogView(View):
    template_name = 'watchlist/watchlog.html'

    def get(self, request):
        data = Movie.objects.all()
        form = MovieForm()
        context = {
            'data': data,
            'form': form,
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

            make_api_calls_and_update_database(title, year, rating, review, theaters, date_watched, service)

            return redirect('watchlog')  # Redirect to the same page after adding a movie
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
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        form = WatchlistForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            year = form.cleaned_data['year']
            date_added = form.cleaned_data['date_added']
            reason = form.cleaned_data['reason']

            make_api_calls_and_update_watchlist(title, year, reason, date_added)

            return redirect('watchlist')  # Redirect to the same page after adding a movie
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
        movie_lists = MovieList.objects.all()
        movie_ids = [movie_list.movie.TMDB_ID for movie_list in movie_lists]
        ordering = Case(*[When(TMDB_ID=movie_id, then=pos) for pos, movie_id in enumerate(movie_ids)], output_field=IntegerField())
        movies_in_order = Movie.objects.filter(TMDB_ID__in=movie_ids).order_by(ordering)
        common_date = movies_in_order.exclude(date__isnull=True).values('date').annotate(num_movies=Count('TMDB_ID')).order_by('-num_movies')[0]['date']
        common_date_movies = movies_in_order.filter(date=common_date)
        print(common_date_movies)
        newest = movies_in_order.latest("date")
        avg = movies_in_order.aggregate((Avg('rating')))
        runtime = movies_in_order.aggregate((Sum('runtime')))
        print(common_date)
        total = (len(movies_in_order))
        day1 = datetime.date(2023, 8, 15)
        dayNow = datetime.date.today()

        form = RankingForm()
        context = {
            'data': movies_in_order,
            'form': form,
            'total': total,
            'days': (dayNow - day1).days,
            'newest': newest,
            'start': day1,
            'end': dayNow,
            'avg': round(avg['rating__avg'], 2),
            'runtime': runtime,
            'busiestDay': common_date,
            'busiestMovies': common_date_movies
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


# EMPTY TEMPLATES:
class DashboardView(View):
    def get(self, request):
        return render(request, 'watchlist/dashboard.html')
    
class EloView(View):
    def get(self, request):
        return render(request, 'watchlist/elo.html')

class EditMovieView(View):
    def get(self, request):
        return render(request, 'watchlist/edit_movie.html')

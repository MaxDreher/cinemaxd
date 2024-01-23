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
import datetime
import json 
import random
import os
from dotenv import load_dotenv
from .api_calls import get_OMDB
from .utils import make_api_calls_and_update_database, make_api_calls_and_update_watchlist  # Create this function

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

    load_dotenv()
    OMDB_KEY = os.getenv("OMDB_KEY")
    omdb = get_OMDB(OMDB_KEY, title, year)

    # Process the API response (replace this with your actual response processing)
    poster_url = omdb["Poster"]

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
        movie_lists = MovieList.objects.all()
        movie_ids = [movie_list.movie.TMDB_ID for movie_list in movie_lists]
        ordering = Case(*[When(TMDB_ID=movie_id, then=pos) for pos, movie_id in enumerate(movie_ids)], output_field=IntegerField())
        movies_in_order = Movie.objects.filter(TMDB_ID__in=movie_ids).order_by(ordering)
        common_date = movies_in_order.exclude(date__isnull=True).values('date').annotate(num_movies=Count('TMDB_ID')).order_by('-num_movies')[0]['date']
        common_date_movies = movies_in_order.filter(date=common_date)
        newest = movies_in_order.latest('datetime_added')
        avg = movies_in_order.aggregate((Avg('rating')))
        runtime = movies_in_order.aggregate((Sum('runtime')))
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

class DashboardView(View):
    def get(self, request):
        # CONSTANTS
        movies = Movie.objects.all()
        today = datetime.date.today()
        this_year = today.year
        this_month = today.strftime("%B")

        # RECENT MOVIE DATA
        newest = movies.order_by('-datetime_added').first()
        # WEEK
        weekMovies = movies.filter(date__range=[today-datetime.timedelta(days=7), today])
        weeklyRatingCounts = weekMovies.values('rating').annotate(count=Count('TMDB_ID')).order_by('-rating')
        weeklyRatingsList = [obj['rating'] for obj in weeklyRatingCounts]
        weeklyCountList = [obj['count'] for obj in weeklyRatingCounts]
        weekSorted = weekMovies.order_by('-rating', '-date')
        week_data = [weekSorted.first(), len(weekSorted), weekSorted.aggregate(avg=Round(Avg('rating')))]
        # MONTH
        monthMovies = movies.filter(date__month=today.month, date__year=today.year)
        monthlyRatingCounts = monthMovies.values('rating').annotate(count=Count('TMDB_ID')).order_by('-rating')
        monthlyRatingsList = [obj['rating'] for obj in monthlyRatingCounts]
        monthlyCountList = [obj['count'] for obj in monthlyRatingCounts]
        monthSorted = monthMovies.order_by('-rating', 'date')
        month_data = [monthSorted.first(), len(monthSorted), monthSorted.aggregate(avg=Round(Avg('rating')))]
        top_ever_month = movies.filter(releaseDate__month=today.month).order_by('-rating').first()
        # YEAR
        yearMovies = movies.filter(date__year=today.year)
        yearlyRatingCounts = yearMovies.values('rating').annotate(count=Count('TMDB_ID')).order_by('-rating')
        yearlyRatingsList = [obj['rating'] for obj in yearlyRatingCounts]
        yearlyCountList = [obj['count'] for obj in yearlyRatingCounts]
        yearSorted = yearMovies.order_by('-rating', 'date')
        year_data = [yearSorted.first(), len(yearSorted), yearSorted.aggregate(avg=Round(Avg('rating')))]
        most_recent_5 = movies.order_by('-rating', '-date').first()
        most_recent_release = movies.order_by('-releaseDate').first()

        # MOVIES SEEN BY YEAR DATA
        years = list(range(this_year - 99, this_year + 1))
        movie_counts = [movies.filter(year=year).count() for year in years]

        # HEATMAP DATA
        dateStart = today - datetime.timedelta(weeks=6, days=today.weekday())
        dateEnd = today + datetime.timedelta(days=(6 - today.weekday()))
        last_15_weeks = movies.filter(date__range=[dateStart, dateEnd]).values('date').annotate(count=Count('TMDB_ID'))

        weekday_lists = [[] for _ in range(7)]

        for entry in last_15_weeks:
            date = entry['date']
            weekday = date.weekday()  # 0 for Monday, 1 for Tuesday, ..., 6 for Sunday
            count = entry['count']

            # Create a dictionary with the required format
            day_dict = {'x': len(weekday_lists[weekday]) + 1, 'y': count, 'date': date.strftime('%m/%d/%Y')}
            weekday_lists[weekday].append(day_dict)

        start_date = dateStart
        end_date = dateEnd
        current_date = start_date
        while current_date <= end_date:
            weekday = current_date.weekday()
            if not any(day['date'] == current_date.strftime('%m/%d/%Y') for day in weekday_lists[weekday]):
                # Add a dictionary with count 0 for missing dates
                day_dict = {'x': '', 'y': 0, 'date': current_date.strftime('%m/%d/%Y')}
                weekday_lists[weekday].append(day_dict)
            current_date += datetime.timedelta(days=1)

        # Sort each list by 'date'
        for weekday_list in weekday_lists:
            weekday_list.sort(key=lambda x: datetime.datetime.strptime(x['date'], '%m/%d/%Y'))

        # Assign x-values based on the sorted order
        for weekday_list in weekday_lists:
            for index, entry in enumerate(weekday_list):
                entry['x'] = index + 1

        # RANDOM LIST (WIP)
        idlist = [i.TMDB_ID for i in WatchlistMovie.objects.filter(provider__isnull=False)]
        rand_ids = random.sample(idlist, 5)
        rand_movies = [WatchlistMovie.objects.get(pk=i) for i in rand_ids]

        actorObjects = Actor.objects.annotate(
            movie_count=Count('movieactor'),
            nonnull_count=Count('movieactor', filter=Q(movieactor__movie__rating__isnull=False), distinct=True),
            avg_rating=Round(Avg('movieactor__movie__rating'))
        ).order_by('-movie_count')

        actors = actorObjects[:15]
        top_15_actors = actorObjects.filter(nonnull_count__gte=4).order_by('-avg_rating')[:15]
        bot_15_actors = actorObjects.filter(nonnull_count__gte=4).order_by('avg_rating')[:15]

        directorObjects = Director.objects.annotate(
            movie_count=Count('moviedirector'),
            nonnull_count=Count('moviedirector', filter=Q(moviedirector__movie__rating__isnull=False)),
            avg_rating=Round(Avg('moviedirector__movie__rating'))
        ).order_by('-movie_count')

        directors = directorObjects[:15]
        top_15_directors = directorObjects.filter(nonnull_count__gte=3).order_by('-avg_rating')[:15]
        bot_15_directors = directorObjects.filter(nonnull_count__gte=3).order_by('avg_rating')[:15]

        today = datetime.date.today()
        start_of_week = today - datetime.timedelta(days=today.weekday())
        end_of_week = start_of_week + datetime.timedelta(days=6)

        # Query to get count and average rating for each day of the week
        weekly_stats = Movie.objects.exclude(date__isnull=True).annotate(
            weekday=ExtractWeekDay('date')
        ).values('weekday').annotate(
            count=Count('TMDB_ID'),
            avg_rating=Round(Avg('rating'))
        ).order_by('weekday')
        counts_list = [item['count'] for item in weekly_stats]
        avg_ratings_list = [item['avg_rating'] for item in weekly_stats]

        year_ranges = [
            (this_year - 99, this_year - 75),
            (this_year - 74, this_year - 50),
            (this_year - 49, this_year - 25),
            (this_year - 24, this_year),
        ]

        context = {
            'years1': json.dumps(years[0:25]),
            'movie_counts1': json.dumps(movie_counts[0:25]),
            'years2': json.dumps(years[25:50]),
            'movie_counts2': json.dumps(movie_counts[25:50]),
            'years3': json.dumps(years[50:75]),
            'movie_counts3': json.dumps(movie_counts[50:75]),
            'years4': json.dumps(years[75:100]),
            'movie_counts4': json.dumps(movie_counts[75:100]),
            'newest': newest,
            'month_today': this_month,
            'year_today': this_year,
            'date_today': datetime.date.today(),
            'top_this_week': week_data[0],
            'week_total': week_data[1],
            'week_avg': week_data[2],
            'weeklyRatingsList': weeklyRatingsList,
            'weeklyCountList': weeklyCountList,
            'top_this_month': month_data[0],
            'month_total': month_data[1],
            'month_avg': month_data[2],
            'alltime_month': top_ever_month,
            'monthlyRatingsList': monthlyRatingsList,
            'monthlyCountList': monthlyCountList,
            'top_this_year': year_data[0],
            'year_total': year_data[1],
            'year_avg': year_data[2],
            'yearlyRatingsList': yearlyRatingsList,
            'yearlyCountList': yearlyCountList,
            'most_recent_release': most_recent_release,
            'last_5': most_recent_5,
            'monday': weekday_lists[0],
            'tuesday': weekday_lists[1],
            'wednesday': weekday_lists[2],
            'thursday': weekday_lists[3],
            'friday': weekday_lists[4],
            'saturday': weekday_lists[5],
            'sunday': weekday_lists[6],
            'random': rand_movies,
            'actors': actors,
            'actor_avg': top_15_actors,
            'actor_bad_avg': bot_15_actors,
            'directors': directors,
            'director_avg': top_15_directors,
            'director_bad_avg': bot_15_directors,
            'url_start': 'https://www.themoviedb.org/t/p/w90_and_h90_face',
            'weekday_counts': counts_list,
            'weekday_avg': avg_ratings_list,
            'year_ranges': year_ranges
        }
        return render(request, 'watchlist/dashboard.html', context)

# EMPTY TEMPLATES   
class EloView(View):
    def get(self, request):
        return render(request, 'watchlist/elo.html')

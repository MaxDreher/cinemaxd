import sys
sys.path.append(r"D:\Users\Max\MovieSite")

import os
import django
from collections import Counter
import pycountry
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MovieSite.settings')
django.setup()

# from django.http import JsonResponse
from django.db.models import Prefetch, Case, When, IntegerField, Avg, Count, Min, Sum, Q, Func
from django.db.models.functions import ExtractWeekDay
# from django.shortcuts import render, redirect
# from django.template.loader import render_to_string
from watchlist.models import *
from datetime import *
import math
# import json 
# import random
# import os
# from dotenv import load_dotenv
# from .api_calls import get_OMDB, get_TMDB
# from .utils import make_api_calls_and_update_database, make_api_calls_and_update_watchlist  # Create this function

class Round(Func):
    function = 'ROUND'
    template = '%(function)s(%(expressions)s, 2)'

def get_top_actors(movies, num, non_null):
    actors = Actor.objects.filter(movie__in=(movies))
    by_count_actors = actors.annotate(
        movie_count=Count('movieactor'),
        nonnull_count=Count('movieactor', filter=Q(movieactor__movie__rating__isnull=False), distinct=True),
        avg_rating=Round(Avg('movieactor__movie__rating'))
    ).order_by('-movie_count')
    by_rating_actors = by_count_actors.filter(nonnull_count__gte=non_null).order_by('-avg_rating')
    
    return {
        'by_count': [{'actor': actor, 'movie': actor.movie_set.order_by('-rating').first()} for actor in by_count_actors[:num]],
        'best_by_rating': [{'actor': actor, 'movie': actor.movie_set.order_by('-rating').first()} for actor in by_rating_actors[:num]],
        'worst_by_rating': [{'actor': actor, 'movie': actor.movie_set.filter(rating__isnull=False).order_by('rating').first()} for actor in by_rating_actors.reverse()[:num]],
    }

def get_top_directors(movies, num, non_null):
    directors = Director.objects.filter(movie__in=(movies))
    by_count_directors = directors.annotate(
        movie_count=Count('moviedirector'),
        nonnull_count=Count('moviedirector', filter=Q(moviedirector__movie__rating__isnull=False), distinct=True),
        avg_rating=Round(Avg('moviedirector__movie__rating'))
    ).order_by('-movie_count')
    by_rating_directors = by_count_directors.filter(nonnull_count__gte=non_null).order_by('-avg_rating')
    
    return {
        'by_count': [{'director': director, 'movie': director.movie_set.order_by('-rating').first()} for director in by_count_directors[:num]],
        'best_by_rating': [{'director': director, 'movie': director.movie_set.order_by('-rating').first()} for director in by_rating_directors[:num]],
        'worst_by_rating': [{'director': director, 'movie': director.movie_set.filter(rating__isnull=False).order_by('rating').first()} for director in by_rating_directors.reverse()[:num]],
    }

def get_week_info(movies, today):
    # Filter movies for the last 7 days
    start_date = today - timedelta(days=7)
    movies_week = movies.filter(date__range=[start_date, today]).order_by('-datetime_added')

    # Get weekly rating counts
    # movies_rating_count = movies_week.values('rating').annotate(count=Count('TMDB_ID')).order_by('-rating')

    # Create lists of ratings and counts
    # ratings_list = [obj['rating'] for obj in movies_rating_count]
    # count_list = [obj['count'] for obj in movies_rating_count]

    # Get movies for the week, sorted by rating and date
    movies_sorted = movies_week.order_by('-rating', 'date')
    # Get additional information (first movie, count of movies, average rating)
    highest_rated = movies_sorted.first()
    lowest_rated = movies_sorted.last()
    highest_critical = movies_week.order_by('-avg_critical_rating').first()
    movie_count = len(movies_sorted)
    average_rating = movies_sorted.aggregate(avg=Round(Avg('rating')))
    average_critical = movies_sorted.aggregate(avg=Round(Avg('avg_critical_rating')))
    total_runtime = movies_sorted.aggregate(sum=Sum('runtime')).get('sum') if (movies_sorted.aggregate(sum=Sum('runtime')).get('sum')) else 0
    actors = get_top_actors(movies_week, 4, 0)
    directors = get_top_directors(movies_week, 4, 0)
    return {
        'start_date': start_date,
        'end_date': today,
        # 'ratings_list': ratings_list,
        # 'count_list': count_list,
        'movies': movies_week,
        'highest_critical': highest_critical,
        'highest_rated': highest_rated,
        'lowest_rated': lowest_rated,
        'movie_count': movie_count,
        'average_rating': average_rating,
        'average_critical': average_critical,
        'total_runtime': f"{total_runtime//60}hr{total_runtime%60}min",
        'actors_by_count': actors.get('by_count'),
        'actors_by_rating': actors.get('by_rating'),
        'directors_by_count': directors.get('by_count'),
        'directors_by_rating': directors.get('by_rating'),
    }

def get_month_info(movies, today):
    year = today.year
    month = today.month
    movies_month = movies.filter(date__month=month, date__year=year)
    movies_alltime_month = movies.filter(releaseDate__month=month).order_by('-rating')[:10]

    # movies_rating_count = movies_month.values('rating').annotate(count=Count('TMDB_ID')).order_by('-rating')

    # ratings_list = [obj['rating'] for obj in movies_rating_count]
    # count_list = [obj['count'] for obj in movies_rating_count]

    movies_sorted = movies_month.order_by('-rating', 'date')

    highest_rated = movies_sorted.first()
    lowest_rated = movies_sorted.last()
    highest_critical = movies_month.order_by('-avg_critical_rating').first()
    movie_count = len(movies_sorted)
    average_rating = movies_sorted.aggregate(avg=Round(Avg('rating')))
    average_critical = movies_sorted.aggregate(avg=Round(Avg('avg_critical_rating')))
    total_runtime = movies_sorted.aggregate(sum=Sum('runtime')).get('sum') if (movies_sorted.aggregate(sum=Sum('runtime')).get('sum')) else 0
    actors = get_top_actors(movies_month, 4, 0)
    directors = get_top_directors(movies_month, 4, 0)
    return {
        'month': today.strftime("%B"),
        'year': year,
        # 'ratings_list': ratings_list,
        # 'count_list': count_list,
        'movies': movies_alltime_month,
        'highest_critical': highest_critical,
        'highest_rated': highest_rated,
        'lowest_rated': lowest_rated,
        'movie_count': movie_count,
        'average_rating': average_rating,
        'average_critical': average_critical,
        'total_runtime': f"{total_runtime//60}hr{total_runtime%60}min",
        'actors_by_count': actors.get('by_count'),
        'actors_by_rating': actors.get('by_rating'),
        'directors_by_count': directors.get('by_count'),
        'directors_by_rating': directors.get('by_rating'),
    }

def get_year_info(movies, today):
    year = today.year
    movies_year = movies.filter(date__year=year)
    movies_released_year = movies.filter(releaseDate__year=year).order_by('-rating')[:10]

    # movies_rating_count = movies_year.values('rating').annotate(count=Count('TMDB_ID')).order_by('-rating')

    # ratings_list = [obj['rating'] for obj in movies_rating_count]
    # count_list = [obj['count'] for obj in movies_rating_count]

    movies_sorted = movies_year.order_by('-rating', 'date')

    highest_rated = movies_sorted.first()
    lowest_rated = movies_sorted.last()
    highest_critical = movies_year.order_by('-avg_critical_rating').first()
    movie_count = len(movies_sorted)
    average_rating = movies_sorted.aggregate(avg=Round(Avg('rating')))
    average_critical = movies_sorted.aggregate(avg=Round(Avg('avg_critical_rating')))
    total_runtime = movies_sorted.aggregate(sum=Sum('runtime')).get('sum') if (movies_sorted.aggregate(sum=Sum('runtime')).get('sum')) else 0
    actors = get_top_actors(movies_year, 4, 0)
    directors = get_top_directors(movies_year, 4, 0)
    return {
        'year': year,
        'movies': movies_released_year,
        'highest_critical': highest_critical,
        'highest_rated': highest_rated,
        'lowest_rated': lowest_rated,
        'movie_count': movie_count,
        'average_rating': average_rating,
        'average_critical': average_critical,
        'total_runtime': f"{total_runtime//60}hr{total_runtime%60}min",
        'actors_by_count': actors.get('by_count'),
        'actors_by_rating': actors.get('by_rating'),
        'directors_by_count': directors.get('by_count'),
        'directors_by_rating': directors.get('by_rating'),
    }

def get_heatmap_data(movies, today):
    dateStart = today - timedelta(weeks=6, days=today.weekday())
    dateEnd = today + timedelta(days=(6 - today.weekday()))

    movie_data = (movies.filter(date__range=[dateStart, dateEnd]).values('date').annotate(count=Count('TMDB_ID')))

    weekday_lists = [[] for _ in range(7)]
    for entry in movie_data:
        date = entry['date']
        list_of_movies = movies.filter(date=date)
        str = ["\n"+item.title for item in list_of_movies]
        weekday = date.weekday()
        week = 6 - ((dateEnd - date).days // 7)
        count = entry['count']
        day_dict = {'week': week, 'weekday': date.strftime("%A"), 'value': count, 'date':date.strftime('%m/%d/%Y'), 'movies': str}
        weekday_lists[weekday].append(day_dict)
    
    return [day_dict for weekday_list in weekday_lists for day_dict in weekday_list]

def get_year_count_data(movies, today):
    year = today.year
    years = list(range(year - 99, year + 1))
    def getMovies(movies, year):
        list_of_movies = movies.filter(year=year)
        return ["\n"+item.title for item in list_of_movies]
    movie_counts = [{'year': str(year), 'value': movies.filter(year=year).count(), 'movies': getMovies(movies, year)} for year in years]
    return movie_counts

def get_rating_distribution(movies):
    movies_rating_count = movies.filter(rating__isnull=False).values('rating').annotate(count=Count('TMDB_ID')).order_by('-rating')
    return [{'rating': item['rating'], 'value': item['count'], 'latest': movies.filter(rating=item['rating']).order_by('-date').first().title} for item in movies_rating_count]

def get_weekday_distribution(movies):
    dayKey = {1: 'Sunday', 2: 'Monday', 3: 'Tuesday', 4: 'Wednesday', 5: 'Thursday', 6: 'Friday', 7: 'Saturday'}
    weekly_stats = movies.exclude(date__isnull=True).annotate(
        weekday=ExtractWeekDay('date')).values('weekday').annotate(
        count=Count('TMDB_ID'),avg_rating=Round(Avg('rating'))
    ).order_by('weekday')
    return [{'weekday': dayKey[item['weekday']], 'rating': item['avg_rating'], 'count': item['count']} for item in weekly_stats]

def get_keyword_data():
    keywords = Keyword.objects.all().annotate(count=Count('movie')).order_by('-count')
    return[{'tag': item.name, 'weight': item.count} for item in keywords[3:33]]

def standardize_country_name(country_name):
    # You can extend this mapping as needed
    country_name_mapping = {
        'USA': 'United States',
        'US': 'United States',
        # Add more mappings as needed
    }
    return country_name_mapping.get(country_name, country_name)

def get_country_code(country_name):
    try:
        # Handle specific cases
        if country_name == "Czech Republic":
            return "Czechia"
        elif country_name == "South Korea":
            return "Korea, Republic of"
        elif country_name == "Taiwan":
            return "Taiwan (Province of China)"

        country = pycountry.countries.get(name=country_name)
        if country:
            return country.alpha_2
    except AttributeError:
        pass

    # Handle cases where the country name is not found
    return None

def get_country_data():
    queryset = Movie.objects.all().values('countrys')
    countries_list = [standardize_country_name(country.strip()) for entry in queryset for country in entry['countrys'].split(',')]

    # Count occurrences using Counter
    country_counts = Counter(countries_list)

    # Convert Counter to a list of tuples (country, count)
    countries_with_counts = list(country_counts.items())
    data = [{'id': get_country_code(item[0]), 'name': item[0], 'value': math.log(item[1]), 'count': item[1]} for item in countries_with_counts]
    return data

def on_this_day(today):
    seed = today.toordinal()
    random.seed(seed)
    movies = Movie.objects.all()
    random_index = random.randint(0, movies.count() - 1)
    random_movie = movies[random_index]
    random.seed

    released_today_watchlist = WatchlistMovie.objects.filter(releaseDate__month=today.month, releaseDate__day=today.day).order_by('date').first() or None
    released_today_watchlog = Movie.objects.filter(releaseDate__month=today.month, releaseDate__day=today.day).order_by('-rating').first() or None
    actor_born_today = Actor.objects.filter(birthday__month=today.month, birthday__day=today.day).first() or None
    director_born_today = Director.objects.filter(birthday__month=today.month, birthday__day=today.day).first() or None
    data =  {
        'released_today_watchlist': {'movie': released_today_watchlist},
        'released_today_watchlog': {'movie': released_today_watchlog},
        'actor_born_today': {'movie': (actor_born_today.watchlistmovie_set.first() or actor_born_today.movie_set.first()) if (actor_born_today) else None, 'actor': actor_born_today},
        'director_born_today': {'movie': (director_born_today.watchlistmovie_set.first() or director_born_today.movie_set.first()) if (director_born_today) else None or None, 'director': director_born_today},
        'random_movie': {'movie': random_movie},
    }
    return [value for value in data.values() if value['movie'] is not None]




    # if releasedTodayWatchlist:
    #     print(f"Watchlist Movie Released on this day in {releasedTodayWatchlist.releaseDate.year}... {releasedTodayWatchlist.title} ({releasedTodayWatchlist.year}), {releasedTodayWatchlist.releaseDate}")
    # if releasedTodayMovie:
    #     print(f"Watchlog Movie Released on this day in {releasedTodayMovie.releaseDate.year}... {releasedTodayMovie.title} ({releasedTodayMovie.year}), {releasedTodayMovie.releaseDate}")
    # if seenTodayMovie:
    #     print(f"Watchlog Movie Seen on this day in {seenTodayMovie.date.year}... {seenTodayMovie.title} ({seenTodayMovie.year}), {seenTodayMovie.date}")
    # if actorMovieToday:
    #     if actorMovieToday.watchlistmovie_set.first():
    #         print(f"Actor {actorMovieToday.name} born on this day in {actorMovieToday.birthday.year}. They appear in {actorMovieToday.watchlistmovie_set.first().title}")
    #     if actorMovieToday.movie_set.first():
    #         print(f"Actor {actorMovieToday.name} born on this day in {actorMovieToday.birthday.year}. They appear in {actorMovieToday.movie_set.first().title}")
    # if directorMovieToday:
    #     if directorMovieToday.watchlistmovie_set.first():
    #         print(f"Director {directorMovieToday.name} born on this day in {directorMovieToday.birthday.year}. They directed {directorMovieToday.watchlistmovie_set.first().title}")
    #     if directorMovieToday.movie_set.first():
    #         print(f"Director {directorMovieToday.name} born on this day in {directorMovieToday.birthday.year}. They directed {directorMovieToday.movie_set.first().title}")

def get_streak(today):
    # Retrieve all records sorted by date
    records = Movie.objects.filter(date__isnull=False).order_by('-date')

    current_streak = 0
    temp_streak = 0
    longest_streak = 0
    # previous_date = today-timedelta(days=1)
    # print(previous_date)
    previous_date = today
    if (records[0].date == today):
        current_streak += 1

    for record in records:
        if previous_date:
            delta = previous_date - record.date
            days_difference = delta.days
            if days_difference > 1:
                break
            elif days_difference == 0:
                continue
            else:
                current_streak += 1

        previous_date = record.date

    previous_date = None
    for record in records:
        # Calculate the difference in days
        if previous_date:
            delta = previous_date - record.date
            days_difference = delta.days
            if days_difference > 1:
                temp_streak = 0
            elif days_difference == 0:
                continue
            else:
                temp_streak += 1

            # Update the longest streak
            longest_streak = max(longest_streak, temp_streak)

        # Update previous date for the next iteration
        previous_date = record.date

    return {
        'current': current_streak,
        'longest': longest_streak,
    }

def get_random_on_streaming():
    idlist = [i.TMDB_ID for i in WatchlistMovie.objects.filter(provider__isnull=False)]
    rand_ids = random.sample(idlist, 5)
    return [WatchlistMovie.objects.get(pk=i) for i in rand_ids]

def get_list_in_order(id):
    movie_list = MovieList.objects.filter(list_id=id)
    movie_ids = [item.movie_id for item in movie_list]
    ordering = Case(*[When(TMDB_ID=movie_id, then=pos) for pos, movie_id in enumerate(movie_ids)], output_field=IntegerField())
    return Movie.objects.filter(TMDB_ID__in=movie_ids).order_by(ordering)

def get_longest_days(movies, num):
    common_date = movies.exclude(date__isnull=True).values('date').annotate(count=Count('TMDB_ID')).annotate(time=Sum('runtime')).order_by('-count', '-time')[:num]
    return [{'date': item['date'], 'count': item['count'], 'time': (f"{item['time']//60}hr{int(item['time']%60)}min"), 'movies': movies.filter(date=item['date'])} for item in common_date]
    # common_date_movies = movies_in_order.filter(date=common_date)

def get_stats(movies, start, end):
    total_days = (end - start).days
    movie_count = len(movies)
    total_runtime = movies.aggregate(sum=Sum('runtime')).get('sum') if (movies.aggregate(sum=Sum('runtime')).get('sum')) else 0
    return {
        'movie_count': movie_count,
        'average_rating': movies.aggregate(avg=Round(Avg('rating'))),
        'average_critical': movies.aggregate(avg=Round(Avg('avg_critical_rating'))),
        'days_runtime': f"~{round(total_runtime/60/24,2)} days",
        'total_runtime': f"{total_runtime//60}hr{total_runtime%60}min",
        'total_days': total_days,
        'gap': movie_count - total_days
    }

top_10 = ["La La Land",
          "Good Will Hunting",
          "Spotlight",
          "Knives Out",
          "Arrival",
          "The Nice Guys",
          "The Mitchells vs. The Machines",
          "Oppenheimer",
          "Catch Me If You Can",
          "Prisoners",
        ]
import sys
sys.path.append(r"D:\Users\Max\MovieSite")

import os
import django
from collections import Counter
import pycountry
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MovieSite.settings')
django.setup()

from watchlist.api_calls import get_TMDB_posters_from_id
from django.db.models import Case, When, IntegerField, Avg, Count, Min, Sum, Q, Func
from django.db.models.functions import ExtractWeekDay
from django.core.exceptions import ObjectDoesNotExist
from watchlist.models import *
from datetime import *
import math
import json

class Round(Func):
    function = 'ROUND'
    template = '%(function)s(%(expressions)s, 2)'

def get_top_actors(movies, num, non_null):
    actors = Actor.objects.filter(movie__in=(movies))
    by_count_actors = actors.annotate(
        movie_count=Count('movieactor'),
        nonnull_count=Count('movieactor', filter=Q(movieactor__movie__rating__isnull=False), distinct=True),
        avg_rating=Round(Avg('movieactor__movie__rating'))
    ).order_by('-movie_count', '-avg_rating')
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
    ).order_by('-movie_count', '-avg_rating')
    by_rating_directors = by_count_directors.filter(nonnull_count__gte=non_null).order_by('-avg_rating')
    
    return {
        'by_count': [{'director': director, 'movie': director.movie_set.order_by('-rating').first()} for director in by_count_directors[:num]],
        'best_by_rating': [{'director': director, 'movie': director.movie_set.order_by('-rating').first()} for director in by_rating_directors[:num]],
        'worst_by_rating': [{'director': director, 'movie': director.movie_set.filter(rating__isnull=False).order_by('rating').first()} for director in by_rating_directors.reverse()[:num]],
    }


def get_week_info(movies, today):
    start_date = today - timedelta(days=7)
    movies_week = movies.filter(date__range=[start_date, today]).order_by('-datetime_added')
    movies_sorted = movies_week.order_by('-rating', 'date')
    highest_rated = movies_sorted.first()
    lowest_rated = movies_sorted.last()
    highest_critical = movies_week.order_by('-avg_critical_rating').first()
    movie_count = len(movies_sorted)
    average_rating = movies_sorted.aggregate(avg=Round(Avg('rating')))
    average_critical = movies_sorted.aggregate(avg=Round(Avg('avg_critical_rating')))
    total_runtime = movies_sorted.aggregate(sum=Sum('runtime')).get('sum') if (movies_sorted.aggregate(sum=Sum('runtime')).get('sum')) else 0
    actors = get_top_actors(movies_week, 3, 0)
    directors = get_top_directors(movies_week, 3, 0)
    return {
        'title': 'week',
        'start_date': start_date,
        'end_date': today,
        'span': f"{start_date.strftime("%b. %d, %Y")} - {today.strftime("%b. %d, %Y")}",
        'badge': 'bi-calendar3-week',
        'movies': movies_week,
        'highest_critical': highest_critical,
        'highest_rated': highest_rated,
        'lowest_rated': lowest_rated,
        'movie_count': movie_count,
        'average_rating': average_rating,
        'average_critical': average_critical,
        'total_runtime': total_runtime,
        'actors_by_count': actors.get('by_count'),
        'actors_by_rating': actors.get('by_rating'),
        'directors_by_count': directors.get('by_count'),
        'directors_by_rating': directors.get('by_rating'),
        'carousel_title': 'All Movies Seen This Week',
        'use_releases': False,
        'award_highest': {'text': 'Highest Rated Movie Seen This Week', 'color': 'green', 'icon': 'bi-award-fill'},
        'award_critical': {'text': 'Highest Critically-Rated Movie Seen This Week', 'color': 'gold', 'icon': 'bi-trophy-fill'},
        'award_lowest': {'text': 'Lowest Rated Movie Seen This Week', 'color': 'red', 'icon': 'bi-hand-thumbs-down-fill'},
    }


def get_last_12_months(today):
    last_12_months = []

    for i in range(12):
        current_month = today - timedelta(days=today.day-1)
        last_12_months.append(current_month)
        today = current_month - timedelta(days=current_month.day)

    return last_12_months


def get_month_info(movies, today):
    month_dict = []
    months = get_last_12_months(today)
    for date in months:
        month = date.month
        year = date.year
        movies_month = movies.filter(date__month=month, date__year=year)
        movies_alltime_month = movies.filter(releaseDate__month=month).order_by('-rating')[:10]

        movies_sorted = movies_month.order_by('-rating', 'date')

        highest_rated = movies_sorted.first()
        lowest_rated = movies_sorted.last()
        highest_critical = movies_month.order_by('-avg_critical_rating').first()
        movie_count = len(movies_sorted)
        average_rating = movies_sorted.aggregate(avg=Round(Avg('rating')))
        average_critical = movies_sorted.aggregate(avg=Round(Avg('avg_critical_rating')))
        total_runtime = movies_sorted.aggregate(sum=Sum('runtime')).get('sum') if (movies_sorted.aggregate(sum=Sum('runtime')).get('sum')) else 0
        actors = get_top_actors(movies_month, 3, 0)
        directors = get_top_directors(movies_month, 3, 0)
        span = f"{date.strftime("%B")} {year}"
        month_dict.append({
        'title': date.strftime("%B"),
        'title_alltime': f"{date.strftime("%B")}-alltime",
        'month': date.strftime("%B"),
        'year': year,
        'span': span,
        'movies': movies_month.order_by('-rating', 'date')[:10],
        'movies_alltime': movies_alltime_month,
        'highest_critical': highest_critical,
        'highest_rated': highest_rated,
        'lowest_rated': lowest_rated,
        'movie_count': movie_count,
        'average_rating': average_rating,
        'average_critical': average_critical,
        'total_runtime': total_runtime,
        'actors_by_count': actors.get('by_count'),
        'actors_by_rating': actors.get('by_rating'),
        'directors_by_count': directors.get('by_count'),
        'directors_by_rating': directors.get('by_rating'),
        'carousel_title': f'My Top 10 Movies Seen in {span}',
        'carousel_title_alltime': f'My Top 10 Movies Released in {date.strftime("%B")} (All-Time)',
        'award_highest': {'text': f'Highest Rated Movie Seen in {span}', 'color': 'green', 'icon': 'bi-award-fill'},
        'award_critical': {'text': f'Highest Critically-Rated Movie Seen in {span}', 'color': 'gold', 'icon': 'bi-trophy-fill'},
        'award_lowest': {'text': f'Lowest Rated Movie Seen in {span}', 'color': 'red', 'icon': 'bi-hand-thumbs-down-fill'},
    })
    return month_dict
        

def get_year_info(movies, today):
    year_dict = []
    current_year = today.year
    for year in range(current_year, 2022, -1):
        movies_year = movies.filter(date__year=year)
        movies_released_year = movies.filter(releaseDate__year=year).order_by('-rating')[:10]
        movies_sorted = movies_year.order_by('-rating', 'date')
        highest_rated = movies_sorted.first()
        lowest_rated = movies_sorted.last()
        highest_critical = movies_year.order_by('-avg_critical_rating').first()
        movie_count = len(movies_sorted)
        average_rating = movies_sorted.aggregate(avg=Round(Avg('rating')))
        average_critical = movies_sorted.aggregate(avg=Round(Avg('avg_critical_rating')))
        total_runtime = movies_sorted.aggregate(sum=Sum('runtime')).get('sum') if (movies_sorted.aggregate(sum=Sum('runtime')).get('sum')) else 0
        actors = get_top_actors(movies_year, 3, 0)
        directors = get_top_directors(movies_year, 3, 0)
        year_dict.append({
            'title': year,
            'title_alltime': f"{year}-alltime",
            'year': year,
            'span': year,
            'movies': movies_year.order_by('-rating')[:10],
            'movies_alltime': movies_released_year,
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
            'carousel_title': f'My Top 10 Movies Seen in {year}',
            'carousel_title_alltime': f'My Top 10 Movies Released in {year}',
            'award_highest': {'text': f'Highest Rated Movie Seen in {year}', 'color': 'green', 'icon': 'bi-award-fill'},
            'award_critical': {'text': f'Highest Critically-Rated Movie Seen in {year}', 'color': 'gold', 'icon': 'bi-trophy-fill'},
            'award_lowest': {'text': f'Lowest Rated Movie Seen in {year}', 'color': 'red', 'icon': 'bi-hand-thumbs-down-fill'},
        })
    return year_dict


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


# def on_this_day_new(today):
#     seed = today.toordinal()
#     random.seed(seed)
#     movies = Movie.objects.all()
#     random_index = random.randint(0, movies.count() - 1)
#     random_movie = movies[random_index]
#     random.seed

#     released_today_watchlist = WatchlistMovie.objects.filter(releaseDate__month=today.month, releaseDate__day=today.day).order_by('date')[:3]
#     released_today_watchlog = Movie.objects.filter(releaseDate__month=today.month, releaseDate__day=today.day).order_by('-rating')[:3]
#     actor_born_today_list = Actor.objects.filter(birthday__month=today.month, birthday__day=today.day)[:3]
#     actor_born_today = [actor.watchlistmovie_set.first() or actor.movie_set.first() for actor in actor_born_today_list]
#     director_born_today_list = Director.objects.filter(birthday__month=today.month, birthday__day=today.day)[:3]
#     director_born_today = [actor.watchlistmovie_set.first() or actor.movie_set.first() for actor in director_born_today_list]
#     return {
#         'released_today_watchlist': released_today_watchlist,
#         'released_today_watchlog': released_today_watchlog,
#         'actor_born_today': actor_born_today,
#         'director_born_today': director_born_today,
#         'random_movie': random_movie,
#         'length': len(released_today_watchlist) + len(released_today_watchlog) + len(actor_born_today) + len(director_born_today) + 1,
#     }


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


def get_streak(today):
    # Retrieve all records sorted by date
    records = Movie.objects.filter(date__isnull=False).order_by('-date')

    current_streak = 0
    temp_streak = 0
    longest_streak = 0
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
    if (records[0].date == today):
        temp_streak += 1
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


def get_streaming(movies):
    movies_rating_count = movies.filter(service__isnull=False).values('service').annotate(count=Count('TMDB_ID')).order_by('-count')
    return [{'name': item['service'], 'value': item['count'], 'image': f"/static/watchlist/images/{item['service']}.png", 'latest': movies.filter(service=item['service']).order_by('-date').first().title} for item in movies_rating_count]


def get_oscars_year(movies, year, award):
    with open('./watchlist/the_oscar_award.json') as f, open('./watchlist/the_oscar_map.json') as g:
            data = json.load(f)
            map = json.load(g)
            
            noms = [{'title': item.get('film'), 'year': item.get('year_film'), 'win': item.get('winner'), 'seen': False} for item in data if (item.get('year_film') == year) and (map[(item.get('category'))] == award) ]
            seen = 0
            winner_seen = False
            for item in noms:
                try:
                    if (item['year'] == 2020):
                        movie = movies.get(title__iexact=item['title'])
                    else:
                        movie = movies.get(title__iexact=item['title'], year=item['year'])
                    item['seen'] = True
                    if item['win']:
                        winner_seen = True
                    seen += 1
                except ObjectDoesNotExist:
                    pass
            return {'seen': seen, 'total': len(noms), 'winner_seen': winner_seen, 'year': year, 'award': award, 'movies': noms}


def get_oscars_range(movies, year_start, year_end, award):
    return [get_oscars_year(movies, year, award) for year in range(year_end, year_start, -1) ]


def get_top_studios(movies, num):
    studios = ProdCompany.objects.filter(movie__in=(movies))
    by_count_studios = studios.annotate(
        movie_count=Count('moviecompany'),
        avg_rating=Round(Avg('moviecompany__movie__rating'))
    ).order_by('-movie_count', '-avg_rating')

    return [{'name': company.name, 'value': company.movie_count, 'logo': company.logo, 'movie': company.movie_set.order_by('-date').first()} for company in by_count_studios[:num]]    


def get_posters(movie):
    tmdb = get_TMDB_posters_from_id(movie.TMDB_ID, movie.type)
    url_start = 'https://www.themoviedb.org/t/p/original'
    return [f"{url_start}{url['file_path']}" for url in tmdb['posters']]


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
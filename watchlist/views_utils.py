from collections import Counter
from moviedb.api_calls import get_TMDB_posters_from_id
from django.db.models import Case, When, IntegerField, Avg, Count, Min, Sum, Q, Func, F, Window, When, Value, IntegerField, CharField, FloatField, ExpressionWrapper, fields
from django.db.models.functions import ExtractWeekDay, Rank, Round, ExtractHour, ExtractMinute, ExtractSecond
from django.core.exceptions import ObjectDoesNotExist
from moviedb.models import *
from datetime import *
from time import strptime
from collections import defaultdict
from math import sin, cos, atan2, pi, fabs

from .config import get_elo_movies, STREAMING_PROVIDERS
from .forms import RankingForm

import random, json
import numpy as np

# ===============================================
# GENERAL UTILITIES
# ===============================================


# Generates a list of datetime objects representing the first day of each of the last 12 months
def get_last_12_months(today):
    last_12_months = []

    # Iterate through the last 12 months
    for i in range(12):
        # Get the first day of the current month
        current_month = today.replace(day=1)
        # Add the current month to the list
        last_12_months.append(current_month)
        # Move to the first day of the previous month
        today = current_month - timedelta(days=current_month.day)

    return last_12_months


def get_posters(movie):
    tmdb = get_TMDB_posters_from_id(movie.TMDB_ID, movie.type)
    url_start = 'https://www.themoviedb.org/t/p/original'
    return [f"{url_start}{url['file_path']}" for url in tmdb['posters']]


def get_streamers():
    return STREAMING_PROVIDERS

# ===============================================
# OSCARS DATA UTILITIES
# ===============================================


def get_oscars_year(movies, year, award):
    oscar_data = Oscar.objects.filter(year_ceremony=(year + 1), category=award)
    noms = [{'title': item.film_title, 'year': year, 'win': item.winner, 'seen': False} for item in oscar_data]
    seen = 0
    winner_seen = False
    for item in noms:
        try:
            if year == 2020:
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


def get_all_oscars_year(movies, year):
    with open('./the_oscar_award.json') as f, open('./the_oscar_map.json') as g:
        data = json.load(f)
        map = json.load(g)
        
        noms = [{'title': item.get('film'), 'year': item.get('year_film')} for item in data if (item.get('year_film') == year)]
        counts = Counter((nom['title'], nom['year']) for nom in noms)
    
        # Create a list with unique items and their counts
        unique_noms = [{'title': title, 'year': year, 'count': count} for (title, year), count in counts.items()]
        return sorted(unique_noms, key=lambda x: x['count'], reverse=True)


# ===============================================
# ELO DATA UTILITIES
# ===============================================

def get_top_and_bottom_elo(movies, num):
    return {
        'highest': movies.order_by('-elo')[:num],
        'lowest': movies.order_by('elo')[:num]
    }


def convert_to_stars(value):
    if value <= 1000:
        return round(0.0 + ((value / 1000) * 0.50),2)
    elif 1000 < value < 2000:
        range_start = (value - 1000) // 100 * 0.5
        return round((range_start + ((value - 1000) % 100 / 100) * 0.49) + 0.50,2)
    else:
        return round(5.0 + ((value / 2000) * 0.50),2)


def get_biggest_elo_diff(movies, num):
    items = []
    for movie in movies:
        estimate = convert_to_stars(movie.elo)
        items.append({
            'movie': movie,
            'rating': movie.rating,
            'estimate': estimate,
            'diff': round(fabs(estimate - movie.rating),2)
        })
    return sorted(items, key=lambda x: x['diff'], reverse=True)


# ===============================================
# Used in New Dashboard
# ===============================================

# Get data for the streaming service chart
def get_streaming(seen):
    movies_rating_count = seen.filter(service__isnull=False).values('service').annotate(count=Count('TMDB_ID')).order_by('-count')
    return [{'name': item['service'], 'value': item['count'], 'image': f"/static/images/{item['service']}.png", 'latest': seen.filter(service=item['service']).order_by('-date').first().title} for item in movies_rating_count]


# Get the highest rated film from a queryset
def get_best(seen):
    return seen.order_by('-rating', '-elo', 'date').first()


# Get the lowest rated film from a queryset
def get_worst(seen):
    return seen.order_by('rating', 'elo', 'date').first()


# Get the highest critically rated film from a queryset
def get_crit_best(seen):
    return seen.order_by('-avg_critical_rating', '-elo', 'date').first()


# Get top actors based on their movie count, average rating, and filter by non-null ratings.
def get_top_actors(movies, num, non_null):
    actors = Actor.objects.filter(movie__in=movies)

    # Annotate actors with movie count, non-null movie count, and average rating
    annotated_actors = actors.annotate(
        movie_count=Count('movieactor', filter=Q(movieactor__movie__seen=True)),
        nonnull_count=Count('movieactor', filter=Q(movieactor__movie__rating__isnull=False), distinct=True),
        avg_rating=(Avg('movieactor__movie__rating'))
    )

    # Order actors by movie count and average rating
    by_count_actors = annotated_actors.order_by('-movie_count', '-avg_rating')
    by_rating_actors = by_count_actors.filter(nonnull_count__gte=non_null).order_by('-avg_rating')

    # Retrieve top actors for each category
    top_by_count = [{'person': actor, 'movie': actor.movie_set.order_by('-rating').first()} for actor in by_count_actors[:num]]
    top_by_rating = [{'person': actor, 'movie': actor.movie_set.order_by('-rating').first()} for actor in by_rating_actors[:num]]
    bottom_by_rating = [{'person': actor, 'movie': actor.movie_set.filter(rating__isnull=False).order_by('rating').first()} for actor in by_rating_actors.reverse()[:num]]

    return {
        'by_count': top_by_count,
        'best_by_rating': top_by_rating,
        'worst_by_rating': bottom_by_rating,
    }


# Get top directors based on movie count and average rating.
def get_top_directors(movies, num, non_null):
    directors = Director.objects.filter(movie__in=movies)
    
    # Annotate directors with movie count, non-null rating count, and average rating
    by_count_directors = directors.annotate(
        movie_count=Count('moviedirector', filter=Q(moviedirector__movie__seen=True)),
        nonnull_count=Count('moviedirector', filter=Q(moviedirector__movie__rating__isnull=False), distinct=True),
        avg_rating=(Avg('moviedirector__movie__rating'))
    ).order_by('-movie_count', '-avg_rating')
    
    # Filter directors based on non-null rating count and order by average rating
    by_rating_directors = by_count_directors.filter(nonnull_count__gte=non_null).order_by('-avg_rating')
    
    return {
        'by_count': [{'person': director, 'movie': director.movie_set.order_by('-rating').first()} for director in by_count_directors[:num]],
        'best_by_rating': [{'person': director, 'movie': director.movie_set.order_by('-rating').first()} for director in by_rating_directors[:num]],
        'worst_by_rating': [{'person': director, 'movie': director.movie_set.filter(rating__isnull=False).order_by('rating').first()} for director in by_rating_directors.reverse()[:num]],
    }


# Get top tags based on a certain set of movies
def get_top_tags(movies):
    tags = Tag.objects.filter(movie__in=movies)

    # Annotate actors with movie count, non-null movie count, and average rating
    annotated_tags = tags.annotate(
        count=Count('movietag', filter=Q(movietag__movie__seen=True)),
        avg_rating=(Avg('movietag__movie__rating'))
    ).order_by('-count')

    return annotated_tags


# Calculate various statistics about a list of movies within a given time range
def get_stats(movies, start, end):
    total_days = (end - start).days
    movie_count = movies.count()
    
    # Calculate total runtime of all movies
    total_runtime = movies.aggregate(sum=Sum('runtime')).get('sum') or 0
    
    # Calculate average rating and average critical rating
    avg_rating = round(movies.aggregate(avg=(Avg('rating')))['avg'],2)
    avg_critical = round(movies.aggregate(avg=(Avg('avg_critical_rating')))['avg'],2)

    return {
        'movie_count': movie_count,
        'average_rating': avg_rating,
        'average_critical': avg_critical,
        'days_runtime': f"~{round(total_runtime / 60 / 24, 2)} days",
        'total_runtime': total_runtime,
        'total_days': total_days,
        'gap': movie_count - total_days
    }


# ===============================================
# BUNDLERS
# ===============================================


# Context Data Bundled Function for Dashboard/Home
def fetch_home():
    today = date.today()
    seen = Movie.objects.filter(seen=True)
    unseen = Movie.objects.filter(seen=False)


    def get_major_statistics(seen):
        streak_start_date = date(2023, 8, 15)
        birthday = date(2002, 7, 15)

        days_streak = (today - streak_start_date).days
        days_prior = (streak_start_date - birthday).days

        total_movies = seen.filter(type="movie")
        num_total_movies = total_movies.count()

        since_streak = total_movies.filter(date__gte=date(2023, 8, 15))
        num_since_streak = since_streak.count()

        before_stream = (num_total_movies - num_since_streak)
        overtake = (before_stream - num_since_streak)

        avg_since = round(num_since_streak / days_streak, 2)
        projected_days = int(overtake // avg_since)
        projected_date = today + timedelta(days=projected_days)

        stat_data = [
            ('total_movies', 'movies total', num_total_movies),
            ('before_stream', 'movies before 8/15/2023', before_stream),
            ('avg', 'avg. movies per day before 8/15/2023', round((before_stream) / days_prior, 2)),
            ('since_streak', 'movies since 8/15/2023', num_since_streak),
            ('avg', 'avg. movies per day since 8/15/2023', avg_since),
            ('overtake', 'movies to overtake', overtake),
            ('projected_date', f'expected date to overtake ({projected_days} days)', projected_date),
        ]

        return stat_data


    def get_heatmap_data(seen):
        start_date = today - timedelta(weeks=20, days=today.weekday())
        end_date = today + timedelta(days=(6 - today.weekday()))

        movie_data = (seen.filter(date__range=[start_date, end_date]).values('date').annotate(count=Count('TMDB_ID')))
        weekday_lists = [[] for _ in range(7)]
        for entry in movie_data:
            date = entry['date']
            list_of_movies = seen.filter(date=date)
            str = ["\n"+item.title for item in list_of_movies]
            weekday = date.weekday()
            week = 20 - ((end_date - date).days // 7)
            count = entry['count']
            day_dict = {'week': week, 'weekday': date.strftime("%A"), 'value': count, 'date':date.strftime('%m/%d/%Y'), 'movies': str}
            weekday_lists[weekday].append(day_dict)
        
        return [day_dict for weekday_list in weekday_lists for day_dict in weekday_list]


    def get_streak(seen):
        # Retrieve all records sorted by date
        records = seen.filter(date__isnull=False).order_by('-date')

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


    def get_year_count_data(seen):
        year = today.year
        years = list(range(year - 99, year + 1))
        movie_counts = []

        for year in years:
            # Query the movies for the current year and annotate the count and average rating
            list_of_movies = seen.filter(year=year).order_by('-date')
            data = list_of_movies.aggregate(count=Count('TMDB_ID'), avg_rating=Round(Avg('rating')))

            # Get the first movie by date in descending order
            first_movie = list_of_movies.first()

            # Append the data to the result list
            movie_counts.append({
                'year': str(year),
                'value': data['count'] if data['count'] else 0,
                'movie': first_movie.title if first_movie else 'None',
                'rating': str(data['avg_rating']) if data['avg_rating'] else 'None',
            })

        return movie_counts

    

    def get_random_on_streaming(unseen, num):
        idlist = [i.TMDB_ID for i in unseen.filter(provider__isnull=False)]
        rand_ids = random.sample(idlist, num)
        return [Movie.objects.get(pk=i) for i in rand_ids]


    return {
        'newest': seen.order_by('-date', '-datetime_added')[:5],
        'stats': get_major_statistics(seen),
        'heatmap': get_heatmap_data(seen),
        'streak': get_streak(seen),
        'year_count_data': get_year_count_data(seen),
        'elo_movies': get_elo_movies(),
        'streaming_bubbles': get_streaming(seen),
        'random': get_random_on_streaming(unseen, 10)
    }


# Context Data Bundled Function for Dashboard/Analytics
def fetch_analytics(anomalies, table_length):
    today = date.today()
    seen = Movie.objects.filter(seen=True)

    # Get x of the rating anomalies for the header
    def get_anomalies(seen, num):
        movies = seen.filter(elo__isnull=False, rating__isnull=False)
        items = []
        for movie in movies:
            estimate = convert_to_stars(movie.elo)
            items.append({
                'movie': movie,
                'rating': movie.rating,
                'estimate': estimate,
                'diff': round(fabs(estimate - movie.rating),2)
            })
        return sorted(items, key=lambda x: x['diff'], reverse=True)[:num]


    # Data for the Elo / Critical Rating differential table
    def get_elo_differential_table(seen):
        differentials = []
        movies = seen.filter(elo__isnull=False)
        ratings = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]

        for item in ratings:
            movies_with_rating = movies.filter(rating=item)
            count = len(movies_with_rating)

            if count >= 50:
                elo = (item * 200 + 900)
                avg = round(movies_with_rating.aggregate(Avg('elo')).get('elo__avg'),2)
                critical_avg = round(movies_with_rating.aggregate(Avg('avg_critical_rating')).get('avg_critical_rating__avg'),2)
                diff = round(avg - elo, 2)
                differentials.append({'rating': item, 'movies': count, 'elo': elo, 'avg': avg, 'diff': diff, 'critical_avg': critical_avg})

        return differentials


    # Data for User Rating & Critical Rating series of the Ratings chart
    def get_avgrating_distribution(seen):
        # Define the rounding to the nearest 0.5
        round_to_half = ExpressionWrapper(Round(F('rating') * 2) / 2, output_field=FloatField())
        round_to_half_avg = ExpressionWrapper(Round(F('avg_critical_rating') * 2) / 2, output_field=FloatField())

        # Query to count and round 'rating'
        rating_distribution = (
            seen.filter(rating__isnull=False)
            .annotate(rounded_rating=round_to_half)
            .values('rounded_rating')
            .annotate(count=Count('TMDB_ID'))
            .order_by('rounded_rating')
        )

        # Query to count and round 'avg_critical_rating'
        avg_rating_distribution = (
            seen.filter(avg_critical_rating__isnull=False)
            .annotate(rounded_rating=round_to_half_avg)
            .values('rounded_rating')
            .annotate(count=Count('TMDB_ID'))
            .order_by('rounded_rating')
        )

        # Create a dictionary to combine both distributions
        combined_results = defaultdict(lambda: {'rating_count': 0, 'avg_rating_count': 0})
        
        # Fill the dictionary with rating_distribution results
        for item in rating_distribution:
            combined_results[item['rounded_rating']]['rating_count'] = item['count']

        # Fill the dictionary with avg_rating_distribution results
        for item in avg_rating_distribution:
            combined_results[item['rounded_rating']]['avg_rating_count'] = item['count']

        # Convert dictionary to sorted list of results
        combined_list = [
            {'rating': rating, 'rating_count': data['rating_count'], 'avg_rating_count': data['avg_rating_count'], 'latest': Movie.objects.filter(rating=rating).order_by('-date').first().title}
            for rating, data in sorted(combined_results.items())
        ]

        return combined_list


    # Data for Elo chart
    def get_elorating_distribution(seen):
        min_value = 1000
        max_value = 2600
        step = 50

        buckets = [(i, i + step) for i in range(min_value, max_value, step)]

        elo_case = Case(
            *[When(elo__range=(low, high), then=Value(f'{low}-{high}')) for low, high in buckets],
            default=Value('0-1000'),  # Default case for ratings above the highest bucket
            output_field=CharField()
        )
        movies = seen.filter(elo__isnull=False)
        movies_with_buckets = movies.annotate(bucket=elo_case)

        # Aggregate counts for each bucket
        bucket_counts = movies_with_buckets.values('bucket').annotate(count=Count('TMDB_ID')).order_by('-bucket')
        return [{'rating': item['bucket'], 'value': item['count'], 'label': item['bucket'].split('-')[0]} for item in bucket_counts]


    # Data for Timing chart
    def get_time_data(seen):

        # Format hours for the Axis labels
        def format_hours(hour):
            hour = ((hour % 24)) % 24
            am = hour < 12
            return f"{(hour % 12) if (hour % 12) != 0 else 12}{"am" if am else "pm"}"

        # Format hours for the chart tooltips
        def format_hours_label(hour):
            hour = ((hour % 24)) % 24
            hour_initial = hour % 24
            am_initial = hour < 12
            hour_second = (hour + 1) % 24
            am_second = hour_second < 7
            if hour == 0: return "12:00am - 1:00am"
            return f"{hour_initial % 12 if hour_initial % 12 != 0 else 12 }:00{"am" if am_initial else "pm"} - {hour_second % 12 if hour_second % 12 != 0 else 12}:00{"am" if am_second else "pm"}"

        movies = seen.filter(datetime_added__isnull=False, date__isnull=False)
        movies_with_hrs = movies.annotate(hour=ExtractHour(F('datetime_added')))
        times = movies_with_hrs.values('hour').annotate(hour_count=Count('TMDB_ID'))
        
        return [{'hour': format_hours(item['hour']), 'value': item['hour_count'], 'label': format_hours_label(item['hour']), 'latest': movies_with_hrs.filter(hour=item['hour']).order_by('-date').first().title} for item in times]


    # Fetch the middle analytics statbar.
    def get_analytics_stats(seen):

        # Get the avereage time from a set of movies
        def get_average_time(movies):
            # Fetch the time components and convert to radians
            times_annotated = movies.annotate(
                hour=ExtractHour(F('datetime_added')),
                minute=ExtractMinute(F('datetime_added')),
                second=ExtractSecond(F('datetime_added'))
            )

            times = times_annotated.values_list('hour', 'minute', 'second')

            sin_sum = 0
            cos_sum = 0
            count = 0

            # Convert each time to an angle and sum up sines and cosines
            for hour, minute, second in times:
                # Convert time to total seconds since midnight
                total_seconds = (((hour % 24)) % 24) * 3600 + minute * 60 + second
                # Convert seconds to angle in radians
                angle = (total_seconds / 86400) * (2 * pi)
                sin_sum += sin(angle)
                cos_sum += cos(angle)
                count += 1

            if count == 0:
                return None

            # Calculate average angle
            mean_angle = atan2(sin_sum / count, cos_sum / count)
            if mean_angle < 0:
                mean_angle += 2 * pi

            # Convert back to seconds and then to time
            mean_seconds = mean_angle * (86400 / (2 * pi))
            hours, remainder = divmod(int(mean_seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            mean_time = time(hour=hours % 12 if hours % 12 != 0 else 12, minute=minutes, second=seconds)

            return f"{mean_time}{"am" if hours < 6 else "pm"}"

        # Get the average runtime from a set of movies
        def get_average_length(movies):
            return round(movies.aggregate(Avg('runtime'))['runtime__avg'], 2)


        average_user_rating = round(seen.filter(rating__isnull=False).aggregate(avg=Avg('rating'))['avg'],2)
        average_time = get_average_time(seen.filter(datetime_added__isnull=False, date__isnull=False))
        average_length = get_average_length(seen.filter(runtime__isnull=False, runtime__gte=60))
        average_critical_rating = round(seen.filter(rating__isnull=False).aggregate(avg=Avg('avg_critical_rating'))['avg'],2)
        average_predicted_rating = convert_elo_to_stars(round(seen.filter(rating__isnull=False).aggregate(avg=Avg('elo'))['avg'],2))
        # adding more options will populate the HTML row automatically
        return [
            ('average_rating', 'avg. user rating', f"★ {average_user_rating}"),
            ('average_critical_rating', 'avg. critical rating', f"★ {average_critical_rating}"),
            ('average_predicted_rating', 'avg. predicted rating by elo', f"★ {average_predicted_rating}"),
            ('average_length', 'average feature film length', f"{int(average_length // 60)}hr {int(average_length % 60)}min"),
            ('average_time', 'avg. time of entry', average_time),
        ]


    # Data for the scatter plot of Ratings vs Avg. Ratings
    def get_scatter_years(seen):
        movies = seen.filter(rating__isnull=False)
        movies_rating = movies.values('year').annotate(average_rating=Avg('rating')).order_by('year')
        movies_avg_rating = movies.values('year').annotate(average_rating=Avg('avg_critical_rating')).order_by('year')
        # Assuming movies_rating and movies_avg_rating are already fetched from Django ORM and are lists of dictionaries

        # Extract year and average ratings for both datasets
        years = np.array([item['year'] for item in movies_rating])
        ratings = np.array([item['average_rating'] for item in movies_rating])
        avg_ratings = np.array([item['average_rating'] for item in movies_avg_rating])

        # Calculate linear regression (trend line) for ratings
        m_rating, b_rating = np.polyfit(years, ratings, 1)
        m_avg_rating, b_avg_rating = np.polyfit(years, avg_ratings, 1)

        # Start and end year
        start_year = min(years)
        end_year = max(years)

        # Coordinates for the trend line of normal ratings
        start_rating = m_rating * start_year + b_rating
        end_rating = m_rating * end_year + b_rating

        # Coordinates for the trend line of average critical ratings
        start_avg_rating = m_avg_rating * start_year + b_avg_rating
        end_avg_rating = m_avg_rating * end_year + b_avg_rating

        # Build the return array, integrating the trend line data
        return_data = [
            {
                'year': str(movies_rating[i]['year']),
                'ay': round(movies_rating[i]['average_rating'], 2),
                'by': round(movies_avg_rating[i]['average_rating'], 2),
            } for i in range(len(movies_rating))
        ]

        trend_rating = [{'x': start_year, 'y': round(start_rating, 2)}, {'x': end_year, 'y': round(end_rating, 2)}]
        trend_avg = [{'x': start_year, 'y': round(start_avg_rating, 2)}, {'x': end_year, 'y': round(end_avg_rating, 2)}]

        return return_data, trend_rating, trend_avg


    # Data for the analytics tables 
    def get_analytics_tables(seen, table_length):
        
        # Mapping function to solve USA/US discrepencies
        def standardize_country_name(country_name):
            country_name_mapping = {
                'USA': 'United States',
                'US': 'United States',
            }
            return country_name_mapping.get(country_name, country_name)


        # Get the table data for Production Companies
        def get_top_studios_table(seen, num):
            studios = ProdCompany.objects.filter(movie__in=(seen))
            by_count_studios = studios.annotate(
                movie_count=Count('moviecompany'),
                avg_rating=Round(Avg('moviecompany__movie__rating'))
            ).order_by('-movie_count', '-avg_rating')

            return [{'name': company.name, 'value': company.movie_count} for company in by_count_studios[:num]]    


        # Get the table data for Countries
        def get_countries_table(seen, num):
            countries = Country.objects.filter(movie__in=(seen))
            by_count = countries.annotate(
                movie_count=Count('moviecountry'),
                avg_rating=Round(Avg('moviecountry__movie__rating'))
            ).order_by('-movie_count', '-avg_rating')

            data = [{'name': item.name, 'value': item.movie_count} for item in by_count[:num]]
            return data


        # Get the table data for Languages
        def get_languages_table(seen, num):
            countries = Language.objects.filter(movie__in=(seen))
            by_count = countries.annotate(
                movie_count=Count('movielanguage'),
                avg_rating=Round(Avg('movielanguage__movie__rating'))
            ).order_by('-movie_count', '-avg_rating')

            data = [{'name': item.name, 'value': item.movie_count} for item in by_count[:num]]
            return data


        # Get the table data for Streaming Services
        def get_services_table(seen, num):
            movies_count = seen.filter(service__isnull=False).values('service').annotate(count=Count('TMDB_ID')).order_by('-count')
            return [{'name': item['service'], 'value': item['count']} for item in movies_count[:num]]    

        return [
            {
                'items': get_top_studios_table(seen, table_length),
                'title': f"Top {table_length} Companies",
                'key': 'companies_table'
            },
            # {
            #     'items': get_countries_table(seen, table_length),
            #     'title': f"Top {table_length} Countries",
            #     'key': 'countries_table'
            # },
            {
                'items': get_languages_table(seen, table_length),
                'title': f"Top {table_length} Languages",
                'key': 'languages_table'
            },
            {
                'items': get_services_table(seen, table_length),
                'title': f"Top {table_length} Streaming Services",
                'key': 'streaning_table'
            }
        ]


    def get_secondary_tables(seen, table_length):
        seen = Movie.objects.filter(seen=True)
        # Get the table data for Streaming Services
        def get_genres_table(seen, num):
            genres = Genre.objects.filter(movie__in=(seen))
            by_count_genres = genres.annotate(
                movie_count=Count('moviegenre'),
                avg_rating=Round(Avg('moviegenre__movie__rating'))
            ).order_by('-movie_count', '-avg_rating')

            return [{'name': genre.name, 'value': genre.movie_count} for genre in by_count_genres[:num]]    

        def get_keyword_table(seen, num):
            genres = Keyword.objects.filter(movie__in=(seen))
            by_count_keywords = genres.annotate(
                movie_count=Count('moviekeyword'),
                avg_rating=Round(Avg('moviekeyword__movie__rating'))
            ).order_by('-movie_count', '-avg_rating')

            return [{'name': keyword.name, 'value': keyword.movie_count} for keyword in by_count_keywords[:num]]    

        return [
            {
                'items': get_genres_table(seen, table_length),
                'title': f"Top {table_length} Genres",
                'key': 'genres_table'
            },
            {
                'items': get_keyword_table(seen, table_length),
                'title': f"Top {table_length} Keywords",
                'key': 'keywords_table'
            },
        ]


    # Convert an elo score to stars
    def convert_elo_to_stars(value):
        if value <= 1000:
            return round(0.0 + ((value / 1000) * 0.50),2)
        elif 1000 < value < 2000:
            range_start = (value - 1000) // 100 * 0.5
            return round((range_start + ((value - 1000) % 100 / 100) * 0.49) + 0.50,2)
        else:
            return round(5.0 + ((value / 2000) * 0.50),2)


    # Get data filtered by each weekday
    def get_weekday_data(seen):
        dayKey = {1: 'Sunday', 2: 'Monday', 3: 'Tuesday', 4: 'Wednesday', 5: 'Thursday', 6: 'Friday', 7: 'Saturday'}

        weekly_stats = seen.filter(date__isnull=False).annotate(weekday=ExtractWeekDay('date'))
        
        data = weekly_stats.values('weekday').annotate(count=Count('TMDB_ID'),avg_rating=Avg('rating')).order_by('weekday')

        return [{'weekday': dayKey[item['weekday']], 'rating': round(item['avg_rating'],2), 'count': item['count'], 'latest': weekly_stats.filter(weekday=item['weekday']).order_by('-date').first()} for item in data]


    # Get Avg Ratings by Streaming Service
    def get_streaming_ratings(seen):
        movies_rating_count = seen.filter(rating__isnull=False, service__isnull=False).values('service').annotate(avg=Avg('rating'), count=Count('TMDB_ID')).order_by('-avg')
        return [{'name': item['service'], 'value': round(item['avg'],2), 'icon': f"/static/images/{item['service']}.png", 'count': item['count']} for item in movies_rating_count if item['count'] > 6]



    def get_longest_days(movies, num):
        common_date = movies.exclude(date__isnull=True).values('date').annotate(count=Count('TMDB_ID')).annotate(time=Sum('runtime')).order_by('-time')[:num]
        return [{'date': item['date'], 'count': item['count'], 'time': item['time'], 'movies': movies.filter(date=item['date'])} for item in common_date]



    # Fetch the touple from the get_scatter_years() function so they can be keyed
    scatter_data, scatter_line_1, scatter_line_2 = get_scatter_years(seen)

    return {
        'anomalies': get_anomalies(seen, anomalies),
        'elo_stats': get_elo_differential_table(seen),
        'ratings_chart_data': get_avgrating_distribution(seen),
        'elo_chart_data': get_elorating_distribution(seen),
        'time_chart_data': get_time_data(seen),
        'stats': get_analytics_stats(seen),
        'scatter_data': scatter_data,
        'scatter_line_1': scatter_line_1,
        'scatter_line_2': scatter_line_2,
        'tables': get_analytics_tables(seen, table_length),
        'tables2': get_secondary_tables(seen, table_length),
        'weekday_data': get_weekday_data(seen),
        'streaming_data': get_streaming_ratings(seen),
        'oscars_data': get_oscars_range(seen, 1927, today.year - 1, "Best Picture"),
        'tags': get_top_tags(seen),
        'animated_data': get_oscars_range(Movie.objects.all(), 2000, date.today().year - 1, "Best Animated Feature"),
        'longest_days': get_longest_days(seen, 10)
    }


# Context Data Bundled Function for Dashboard/P
def fetch_people(non_null, num):
    today = date.today()
    seen = Movie.objects.filter(seen=True)
    actors = get_top_actors(seen, num, non_null)
    directors = get_top_directors(seen, num, non_null)

    # Fetch the middle people statbar.
    def get_actor_stats(seen):
        total_movies = seen.count()

        actors = Actor.objects.annotate(seen_count=Count('movieactor__movie', filter=Q(movieactor__movie__seen=True)))

        actors_seen = actors.filter(seen_count__gte=1).count()
        actors_seen_3 = actors.filter(seen_count__gte=3).count()
        actors_seen_5 = actors.filter(seen_count__gte=5).count()
        actors_seen_10 = actors.filter(seen_count__gte=10).count()
        actors_seen_20 = actors.filter(seen_count__gte=20).count()

        avg_distinct = round((actors_seen/total_movies),2)

        return [
            ('actors_seen', 'distinct actors seen', f"{actors_seen}"),
            ('actors_seen_3', 'actors seen in 3+ projects', f"{actors_seen_3}"),
            ('actors_seen_5', 'actors seen in 5+ projects', f"{actors_seen_5}"),
            ('actors_seen_10', 'actors seen in 10+ projects', f"{actors_seen_10}"),
            ('actors_seen_20', 'actors seen in 20+ projects', f"{actors_seen_20}"),
            ('avg_distinct', 'avg. distinct actors per film', f"{avg_distinct}"),
        ]

    # Fetch the middle people statbar.
    def get_director_stats(seen):
        total_movies = seen.count()

        directors = Director.objects.annotate(seen_count=Count('moviedirector__movie', filter=Q(moviedirector__movie__seen=True)))

        directors_seen = directors.filter(seen_count__gte=1).count()
        directors_seen_3 = directors.filter(seen_count__gte=3).count()
        directors_seen_5 = directors.filter(seen_count__gte=5).count()
        directors_seen_10 = directors.filter(seen_count__gte=10).count()
        directors_seen_20 = directors.filter(seen_count__gte=20).count()

        avg_distinct = round((directors_seen/total_movies),2)

        return [
            ('directors_seen', 'distinct directors seen', f"{directors_seen}"),
            ('directors_seen_3', 'directors seen in 3+ projects', f"{directors_seen_3}"),
            ('directors_seen_5', 'directors seen in 5+ projects', f"{directors_seen_5}"),
            ('directors_seen_10', 'directors seen in 10+ projects', f"{directors_seen_10}"),
            ('directors_seen_20', 'directors seen in 20+ projects', f"{directors_seen_20}"),
            ('avg_distinct_d', 'avg. distinct directors per film', f"{avg_distinct}"),
        ]



    return {
        'actors': actors,
        'directors': directors,
        'oscars_best_actor': get_oscars_range(seen, 1927, today.year - 1, "Best Actor"),
        'oscars_best_actress': get_oscars_range(seen, 1927, today.year - 1, "Best Actress"),
        'oscars_director': get_oscars_range(seen, 1927, today.year - 1, "Best Director"),
        'stats': get_actor_stats(seen),
        'stats_director': get_director_stats(seen)
    }


# Context Data Bundled Function for Dashboard/On-This-Day
def fetch_on_this_day():
    today = date.today()
    # today = date(2024,4,22)
    movies = Movie.objects.all()
    seen = movies.filter(seen=True)
    unseen = movies.filter(seen=False)

    # Boolean check to see if a Movie exists released on this day
    def movie_released(movies):
        return movies.filter(releaseDate__month=today.month, releaseDate__day=today.day).first() != None

    # Get a 'movie of the day' for the header. 
    # Use a seeded random movie if none released today
    def get_movie_of_the_day(movies):
        if movie_released(movies):
            return movies.filter(releaseDate__month=today.month, releaseDate__day=today.day).order_by('seen', '-releaseDate')
        else:
            seed = today.toordinal()
            seeded_random = random.Random(seed)
            return [movies[seeded_random.randint(0, movies.count() - 1)]]


    def get_old_suggestion(unseen):
        movie =  unseen.order_by('date').first()
        days = (today - movie.date).days
        return {'movie': movie, 'text': f"{days} days on the watchlist"}


    def get_actor_birthdays():
        actors =  Actor.objects.filter(birthday__month=today.month, birthday__day=today.day, movieactor__isnull=False).annotate(num_movies=Count('movieactor'))
        return actors.order_by('-num_movies')


    def get_director_birthdays():
        actors =  Director.objects.filter(birthday__month=today.month, birthday__day=today.day).annotate(num_movies=Count('moviedirector'))
        return actors.order_by('-num_movies')


    def get_seen_on(seen):
        return seen.filter(date__month=today.month, date__day=today.day)
    

    def get_unseen_on(unseen):
        return unseen.filter(date__month=today.month, date__day=today.day)

    return {
        'movie_released': movie_released(movies),
        'movie_of_the_day': get_movie_of_the_day(movies),
        'clearout': get_old_suggestion(unseen),
        'birthday_actors': get_actor_birthdays(),
        'birthday_directors': get_director_birthdays(),
        'day': today.day,
        'month': today.strftime("%B"),
        'seen_today': get_seen_on(seen),
        'added_today': get_unseen_on(unseen),
    }


# Context Data Bundled Function for Dashboard/Week
def fetch_this_week():
    today = date.today()
    start_date = today - timedelta(days=7)
    seen = Movie.objects.filter(seen=True, date__range=[start_date, today]).order_by('-date','-datetime_added')

    actors = get_top_actors(seen, 3, 0)
    directors = get_top_directors(seen, 3, 0)

    released = []
    for day in (today - timedelta(days=n) for n in range(0, 6)):
        released.extend([item for item in(Movie.objects.filter(releaseDate__month=day.month, releaseDate__day=day.day, seen=False).order_by('date'))])

    return {
        'banner': get_best(seen),
        'movies': seen,
        'worst': get_worst(seen),
        'avg_best': get_crit_best(seen),
        'dates': {
            "start": start_date,
            "end": today,
            "range": f"{start_date.strftime("%b. %d, %Y")} - {today.strftime("%b. %d, %Y")}"
        },
        'stats': get_stats(seen, start_date, today),
        'streaming_bubbles': get_streaming(seen),
        'tags': get_top_tags(seen),
        'actors': actors.get('by_count'),
        'directors': directors.get('by_count'),
        'released': released,
    }


# Fetch data for a month given the month and year
def fetch_month(month, year):
    today = date.today()
    start_date = today - timedelta(days=today.day)
    month_int = strptime(month, '%B').tm_mon
    seen = Movie.objects.filter(seen=True, date__month=month_int, date__year=year).order_by('-datetime_added')
    released = Movie.objects.filter(releaseDate__month=month_int)

    actors = get_top_actors(seen, 3, 0)
    directors = get_top_directors(seen, 3, 0)

    return {
        'month': month.title(),
        'monthyear': f"{month.title()} {year}",
        'banner': get_best(seen),
        'released': released.order_by('-rating', '-elo', 'date')[:10],
        'stats': get_stats(seen, start_date, today),
        'streaming_bubbles': get_streaming(seen),
        'tags': get_top_tags(seen),
        'movies': seen.order_by('-rating', '-elo', 'date')[:10],
        'worst': get_worst(seen),
        'avg_best': get_crit_best(seen),
        'actors': actors.get('by_count'),
        'directors': directors.get('by_count'),
    }


# Fetch data for a month given the month and year
def fetch_year(year):
    today = date.today()
    start_date = date(year,1,1)
    seen = Movie.objects.filter(seen=True, date__year=year).order_by('-datetime_added')
    released = Movie.objects.filter(releaseDate__year=year)

    actors = get_top_actors(seen, 3, 0)
    directors = get_top_directors(seen, 3, 0)

    return {
        'year': year,
        'banner': get_best(seen),
        'released': released.order_by('-rating', '-elo', 'date')[:10],
        'stats': get_stats(seen, start_date, today),
        'streaming_bubbles': get_streaming(seen),
        'tags': get_top_tags(seen),
        'movies': seen.order_by('-rating', '-elo', 'date')[:10],
        'worst': get_worst(seen),
        'avg_best': get_crit_best(seen),
        'actors': actors.get('by_count'),
        'directors': directors.get('by_count'),
    }


# Fetch data for a rankings given the list_id
def fetch_rankings(list_id):

    def get_list_in_order(id):
        movie_list = MovieList.objects.filter(list_id=id)
        movie_ids = [item.movie_id for item in movie_list]
        ordering = Case(*[When(TMDB_ID=movie_id, then=pos) for pos, movie_id in enumerate(movie_ids)], output_field=IntegerField())
        movies = Movie.objects.filter(TMDB_ID__in=movie_ids).order_by(ordering)
        ret = movies.annotate(rank=Window(expression=Rank(), order_by=(ordering)), elo_rank=Window(expression=Rank(), order_by=F('elo').desc()), critical_rank=Window(expression=Rank(), order_by=F('avg_critical_rating').desc()))
        ret = ret.annotate(avg_rank=((F('rank') + (F('elo_rank')*0.75) + (F('critical_rank')*0.25) / 3.0)))
        for item in ret:
            item.avg_rank = round(item.avg_rank,2)
        return ret

    movies = get_list_in_order(list_id)
    startDate = date(2023, 8, 15)
    today = date.today()

    newest = movies.order_by('-date', '-datetime_added').first()

    list_instance = List.objects.get(pk=list_id)
    movies_not_in_list = Movie.objects.exclude(list=list_instance).filter(date__gt=date(2023, 8, 15), seen=True).order_by('-date')
    choices = [(item.title, f"{item.title} ({item.year})") for item in movies_not_in_list]
    form = RankingForm(choices=choices)
    
    return {
        'data': movies,
        'form': form,
        'stats': get_stats(movies, startDate, today),
        'not_in_list': movies_not_in_list,
        'latest': newest,
        'start': startDate,
        'end': today,
    }

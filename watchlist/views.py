from django.http import JsonResponse
from django.db.models import Prefetch, Case, When, IntegerField, Avg, Count, Min, Sum, Q, Func
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views import View
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.conf import settings
from .models import *
import time as t
from datetime import *
import random
from .api_calls import get_OMDB, get_TMDB, find_TMDB
from .utils import make_api_calls_and_update_database, make_api_calls_and_update_watchlist, download_csv  # Create this function
from .views_utils import *
from .config import initial_data, elo_match, get_elo_movies, get_elo_selective

class Round(Func):
    function = 'ROUND'
    template = '%(function)s(%(expressions)s, 2)'

"""
Universal non-paged functions.

These views can be processed from any page on the server, and return a non-static page element,
such as a modal or a sidebar element.

"""

# Get a sidebar element describing a film given its ID.
def sidebar_ajax(request, movie_id):
    movie = Movie.objects.get(pk=movie_id)
    cast = [{'actor': item.actor, 'role': item.role, 'seen': item.actor.movie_set.filter(seen=True), 'unseen': item.actor.movie_set.filter(seen=False)} for item in movie.movieactor_set.all()]
    directors = [{'director': item.director, 'seen': item.director.movie_set.filter(seen=True), 'unseen': item.director.movie_set.filter(seen=False)} for item in movie.moviedirector_set.all()]

    context = {
        'movie': movie,
        'directors': directors,
        'cast': cast,
        'url_start': 'https://www.themoviedb.org/t/p/w90_and_h90_face',
    }
    return render(request, 'offcanvas/offcanvas_movie.html', context)


# Get a sidebard element describing a person given their ID.
def sidebar_actor_ajax(request, actor_id):
    actor = Actor.objects.filter(pk=actor_id).annotate(
        movie_count=Count('movieactor', filter=Q(movieactor__movie__seen=True)),
        unseen_count=Count('movieactor', filter=Q(movieactor__movie__seen=False)),
        nonnull_count=Count('movieactor', filter=Q(movieactor__movie__rating__isnull=False), distinct=True),
        avg_rating=Round(Avg('movieactor__movie__rating', filter=Q(movieactor__movie__seen=True)))
    ).first()

    director = Director.objects.filter(pk=actor_id).annotate(
        movie_count=Count('moviedirector', filter=Q(moviedirector__movie__seen=True)),
        unseen_count=Count('moviedirector', filter=Q(moviedirector__movie__seen=False)),
        nonnull_count=Count('moviedirector', filter=Q(moviedirector__movie__rating__isnull=False), distinct=True),
        avg_rating=Round(Avg('moviedirector__movie__rating', filter=Q(moviedirector__movie__seen=True)))
    ).first()


    person = actor if actor else director
    movie = person.movie_set.order_by('?').first() if person.movie_set.first() else person.unseen_set.order_by('?').first()


    context = {
        'person': person,
        'actor': actor,
        'seen_actor': actor.movie_count if actor else None,
        'unseen_actor': actor.unseen_count if actor else None,
        'watchlog_actor': actor.movie_set.filter(seen=True) if actor else None,
        'watchlist_actor': actor.movie_set.filter(seen=False) if actor else None,
        'director': director,
        'seen_director': director.movie_count if director else None,
        'unseen_director': director.unseen_count if director else None,
        'watchlog_director': director.movie_set.filter(seen=True) if director else None,
        'watchlist_director': director.movie_set.filter(seen=False) if director else None,
        'movie': movie,
    }
    return render(request, 'offcanvas/offcanvas_actor.html', context)


# Get the custom posters modal for a film given its ID.
def modal_ajax(request, movie_id):
    movie = Movie.objects.get(pk=movie_id)
    
    context = {
        'movie': movie,
        'posters': get_posters(movie),
    }
    return render(request, 'modals/modal_posters.html', context)


# Get the YouTube trailer modal for a film given its ID.
def yt_player(request, movie_id):
    
    context = {
        'url': f'https://youtube.com/embed/{movie_id}',
    }
    return render(request, 'modals/modal_yt.html', context)


# Get the edit form modal for a film given its ID.
def edit_ajax(request, movie_id):
    movie = Movie.objects.get(pk=movie_id)

    context = {
        'movie': movie,
        'streamers': get_streamers(),
    }
    return render(request, 'modals/modal_edit.html', context)


# Get the Elo matchup modal for a film given its ID.
def elo_modal(request, movie_id):
    movie = Movie.objects.get(pk=movie_id)
    
    context = {
        'movie': movie,
        'movies': get_elo_selective(movie),
    }
    return render(request, 'modals/modal_elo.html', context)


"""
Update functions

These functions update an element, usually from a form or modal.

Many of these functions are written to be CSRF exept, as of 6/17/2024

"""

# Update a movie's poster, from the Poster Modal
@csrf_exempt
def poster_update(request):
    if request.method == 'POST':
        t1 = t.time()
        id = request.POST.get('movie')
        url = request.POST.get('poster')

        movie = Movie.objects.get(pk=id)
        
        movie.posterLink = url
        movie.save()
        print(f"{movie.title} poster updated in {t.time()-t1} seconds.")
        return JsonResponse({'message': 'Link saved successfully'})
    return JsonResponse({'message': 'Invalid request method'}, status=400)


# Update a movie's favorite bool from the Movie Sidebar.
@csrf_exempt
def update_favorite(request):
    if request.method == 'POST':
        movie_id = request.POST.get('movieId')
        favorite = request.POST.get('favorite')

        movie = Movie.objects.get(pk=movie_id)

        movie.favorite = favorite
        movie.save()
        return JsonResponse({'message': 'Favorite updated successfully'})

    return JsonResponse({'message': 'Invalid request method'}, status=400)


# Update a movie's IncludeElo bool from the Movie Sidebar.
@csrf_exempt
def update_include(request):
    movie_id = request.POST.get('movieId')
    include = request.POST.get('favorite')

    movie = Movie.objects.get(pk=movie_id)
    movie.eloInclude = include
    movie.save()

    return JsonResponse({'message': 'Include updated successfully'})


# Update a movie's attributes from the Update Movie Modal.
def movie_update(request):
    if request.method == 'POST':
        t1 = t.time()

        id = request.POST.get('movie')
        rating = request.POST.get('rating')
        date = request.POST.get('date')
        service = request.POST.get('service')
        tags = request.POST.get('tags')
        review = request.POST.get('review')

        movie = Movie.objects.get(TMDB_ID=id)

        movie.rating = rating if rating else None
        movie.date = date if date else None
        movie.service = service if service else None
        movie.review = review if review != "" else None if review else None

        existing_tags = MovieTag.objects.filter(movie=movie)

        if tags:
            tag_names = tags.split(',')
            if len(tag_names) != len(existing_tags):
                existing_tags.delete()
            for tag_name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                MovieTag.objects.get_or_create(movie=movie, tag=tag)
        elif existing_tags:
            existing_tags.delete()

        movie.save()

        print(f"{movie.title} updated in {t.time()-t1} seconds.")
        return JsonResponse({'message': 'Movie saved successfully'})
    return JsonResponse({'message': 'Invalid request method'}, status=400)


"""
Table Pages

These views are used on the Watchlog and Watchlist pages

"""

# Make an API call to get a list of movies from TMDB given a changing query.
def get_suggestions(request):
    query = request.GET.get('query')

    tmdb = find_TMDB(query)
    results = [
        {
            'id': item.get('id'), 
            'type': item.get('media_type') if item.get('media_type') == 'movie' else 'series',
            'title':item.get('title') if item.get('title') else item.get('name'), 
            'year': datetime.strptime(item.get("release_date" if item.get('media_type') == "movie" else "first_air_date"), "%Y-%m-%d").date().year if item.get('release_date') or item.get('first_air_date') else None,
            'poster_url': f"https://image.tmdb.org/t/p/original{item.get('poster_path')}"
        } 
        for item in tmdb.get('results')[:10] if item.get('media_type') != "person"
    ]
    
    return JsonResponse({'results': results})


# Defines the Watchlog page
class WatchlogView(View):
    template_name = 'watchlog.html'

    def get(self, request):
        data = Movie.objects.filter(seen=True)
        context = {
            'data': data,
            'date': date.today(),
            'streamers': get_streamers(),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        try:
            id = request.POST.get('movieid')
            type = request.POST.get('movietype')
            date = request.POST.get('date')
            rating = request.POST.get('rating')
            review = request.POST.get('review')
            service = request.POST.get('service')

            data = {
                'id': id,
                'type': type,
                'date': date if date else None,
                'rating': rating if rating else None,
                'review': review if review and review != "" else None,
                'service': service if service else None,
                'favorite': request.POST.get('favorite'),
                'theaters': request.POST.get('theaters'),
                'tags': request.POST.get('tags'),
                'elo': (float(rating) * 200 + 900) if rating else 900,
                'seen': True,
                'timesSeen': 1,
            }

            make_api_calls_and_update_database(data)

            data = Movie.objects.filter(seen=True)

            movie = Movie.objects.get(pk=id)

            title_year = f'{movie.title} ({movie.year})'
            response_data = {
                'title_year': title_year,
                'table_html': render_to_string('tables/watchlog-table.html', {'data': data}),
            }
            return JsonResponse(response_data)
        except Exception as e:
            print(f"Exception: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# Defines the Watchlist page
class WatchlistView(View):
    template_name = 'watchlist.html'

    def get(self, request):
        data = Movie.objects.filter(seen=False)
        context = {
            'data': data,
            'date': date.today(),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        try:
            id = request.POST.get('movieid')
            type = request.POST.get('movietype')

            data = {
                'id': id,
                'type': type,
                'date': request.POST.get('date'),
                'favorite': request.POST.get('favorite'),
                'tags': request.POST.get('tags'),
                'seen': False,
                'timesSeen': 0,
            }

            make_api_calls_and_update_watchlist(data)
            data = Movie.objects.filter(seen=False)

            movie = Movie.objects.get(pk=id)

            title_year = f'{movie.title} ({movie.year})'
            response_data = {
                'title_year': title_year,
                'table_html': render_to_string('tables/watchlist-table.html', {'data': data})
            }
            return JsonResponse(response_data)
        except Exception as e:
            print(f"Exception: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


"""
Rankings Pages

These views are used on the Rankings page

In theory, these pages can be lightly modified or used currently for other List-based pages.

"""

# Update the order of a list as it's changed via drag-and-drop elements on the Rankings page.
@csrf_exempt
def update_order(request):
    movie_ids = request.POST.getlist('movie_ids[]')
    list_id = request.POST.get('list_id')
    
    # Check for empty values
    if not list_id or not movie_ids:
        return JsonResponse({'status': 'error', 'message': 'Invalid list_id or movie_ids'}, status=400)

    try:
        with transaction.atomic():
            movie_list_objects = MovieList.objects.filter(list_id=list_id, movie_id__in=movie_ids).select_for_update()

            movie_list_dict = {str(obj.movie_id): obj for obj in movie_list_objects}

            for order, movie_id in enumerate(movie_ids, start=1):
                movie_list_dict[str(movie_id)].order = order

            MovieList.objects.bulk_update(movie_list_dict.values(), ['order'])

        return JsonResponse({'status': 'success'})
    except MovieList.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Movie or list not found'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# Process the submission of a new movie to a list.
def rankings_submit(request):
    try:
        id = request.POST.get('movieId')
        movie = Movie.objects.get(TMDB_ID=id)
        list_instance = List.objects.get(pk=1)
        MovieList.objects.create(list=list_instance, movie=movie, order=0)
    except:
        None

    context = {**initial_data(), **fetch_rankings(1)}
    return render(request, "rankings.html", context)


# Defines the Rankings page.
class RankingsView(View):
    def get(self, request):
        context = {**initial_data(), **fetch_rankings(1)}
        return render(request, "rankings.html", context)


"""
Rankings Pages

These views are used on the Rankings page

In theory, these pages can be lightly modified or used currently for other List-based pages.

"""

# Defines the base Dashboard page.
class DashboardView(View):
    def get(self, request):
        context = {**initial_data()}
        return render(request, 'dashboard.html', context)


# Defines the Dashboard/home page
def dashboard_home(request):
    context = {**fetch_home()}
    return render(request, 'dashboard/home.html', context)


# Defines the Dashboard/analytics page
def dashboard_analytics(request):
    context = {**fetch_analytics(10,5)}
    return render(request, 'dashboard/analytics.html', context)


# Defines the Dashboard/people page
def dashboard_people(request):
    context = {**fetch_people(4,10)}
    return render(request, 'dashboard/people.html', context)


# Defines the Dashboard/on_this_day page
def dashboard_on_this_day(request):
    context = {**fetch_on_this_day()}
    return render(request, 'dashboard/on_this_day.html', context)


# Defines the Dashboard/week page
def dashboard_this_week(request):
    context = {**initial_data(), **fetch_this_week()}
    return render(request, 'dashboard/this_week.html', context)


# Defines the Dashboard/month pages
def dashboard_month(request, month, year):
    context = {**fetch_month(month, year)}
    return render(request, 'dashboard/month.html', context)


# Defines the Dashboard/year page
def dashboard_year(request, year):
    context = {**initial_data(), **fetch_year(year)}
    return render(request, 'dashboard/year.html', context)


"""
Rankings Pages

These views are used on the Rankings page

In theory, these pages can be lightly modified or used currently for other List-based pages.

"""

# Defines the Elo page
class EloView(View):
    def get(self, request):
        movies = Movie.objects.filter(rating__isnull=False)
        matches = movies.aggregate((Sum('eloMatches'))).get('eloMatches__sum') // 2
        startDate = date(2024, 1, 29)
        today = date.today()
        gap5 = get_biggest_elo_diff(Movie.objects.filter(elo__isnull=False, rating__isnull=False), 1)[:10]


        context = {
            'movies': get_elo_movies(),
            'matches': matches,
            'start': startDate,
            'end': today,
            'gap5': gap5,
        }
        return render(request, 'elo.html', context)


# Process an Elo matchup from the Elo page and return its template
def elo_matchup(request):
    winner = Movie.objects.get(pk=request.GET.get('id_winner'))
    loser = Movie.objects.get(pk=request.GET.get('id_loser'))

    elo_match(winner, loser)

    movies = Movie.objects.filter(rating__isnull=False)
    matches = movies.aggregate((Sum('eloMatches'))).get('eloMatches__sum') // 2
    random.seed()

    startDate = date(2024, 1, 29)
    today = date.today()
    gap5 = get_biggest_elo_diff(Movie.objects.filter(elo__isnull=False, rating__isnull=False), 1)[:10]

    context = {
        'movies': get_elo_movies(),
        'matches': matches,
        'start': startDate,
        'end': today,
        'gap5': gap5
    }
    return render(request, 'components/elo/eloMatchup.html', context)


# Process an Elo matchup from the Dashboard Mini Player and return its template
def mini_elo_matchup(request):
    winner = Movie.objects.get(pk=request.GET.get('id_winner'))
    loser = Movie.objects.get(pk=request.GET.get('id_loser'))
    elo_match(winner, loser)

    context = {
        'movies': get_elo_movies(),
    }
    return render(request, 'components/elo/small-elo-match.html', context)


# Process an Elo matchup from the Elo Modal and return its template
def elo_modal_matchup(request, movie_id):
    winner = Movie.objects.get(pk=request.GET.get('id_winner'))
    loser = Movie.objects.get(pk=request.GET.get('id_loser'))

    elo_match(winner, loser)

    movie = Movie.objects.get(pk=movie_id)

    context = {
        'movies': get_elo_selective(movie),
    }
    return render(request, 'components/elo/modal-elo-match.html', context)



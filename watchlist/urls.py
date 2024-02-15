from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from .views import *

urlpatterns = [
    path('', RedirectView.as_view(url='watchlist/dashboard/', permanent=False)),
    path('sidebar_ajax/<int:movie_id>/', sidebar_ajax, name='sidebar_ajax'),
    path('sidebar_actor_ajax/<int:actor_id>/', sidebar_actor_ajax, name='sidebar_actor_ajax'),
    path('get_random_movies/', get_random_movies, name='get_random_movies'),
    path('get_movie_info/', get_movie_info, name='get_movie_info'),
    path('elo_matchup/', elo_matchup, name='elo_matchup'),
    path('save_poster_link/', save_poster_link, name='save_poster_link'),
    path('watchlist/dashboard/', DashboardView.as_view(), name='dashboard'),
    path('watchlist/watchlog/', WatchlogView.as_view(), name='watchlog'),
    path('watchlist/watchlist/', WatchlistView.as_view(), name='watchlist'),
    path('watchlist/rankings/', RankingsView.as_view(), name='rankings'),
    path('watchlist/elo/', EloView.as_view(), name='elo'),
    path('watchlist/update_order/', update_order, name='update_order'),
    # Add other URLs for watchlog, watchlist, rankings, elo, etc.
]

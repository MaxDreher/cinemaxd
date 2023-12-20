from django.contrib import admin
from django.urls import path, include
from .views import DashboardView, AddMovieView, WatchlogView,WatchlistView,RankingsView,EloView,AddWatchlistView,EditMovieView, update_order

urlpatterns = [
    path('watchlist/dashboard/', DashboardView.as_view(), name='dashboard'),
    path('watchlist/add_movie/', AddMovieView.as_view(), name='add_movie'),
    path('watchlist/watchlog/', WatchlogView.as_view(), name='watchlog'),
    path('watchlist/watchlist/', WatchlistView.as_view(), name='watchlist'),
    path('watchlist/rankings/', RankingsView.as_view(), name='rankings'),
    path('watchlist/elo/', RankingsView.as_view(), name='elo'),
    path('watchlist/add_watchlist/', AddWatchlistView.as_view(), name='add_watchlist'),
    path('watchlist/edit_movie/', EditMovieView.as_view(), name='edit_movie'),
    path('watchlist/update_order/', update_order, name='update_order'),
    # Add other URLs for watchlog, watchlist, rankings, elo, etc.
]

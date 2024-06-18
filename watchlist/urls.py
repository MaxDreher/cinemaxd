from django.contrib import admin
from django.urls import path, re_path, include
from django.views.generic import RedirectView
from datetime import date
from .views import *

urlpatterns = [
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),

    path('sidebar_ajax/<int:movie_id>/', sidebar_ajax, name='sidebar_ajax'),
    path('sidebar_actor_ajax/<int:actor_id>/', sidebar_actor_ajax, name='sidebar_actor_ajax'),

    path('modal_ajax/<int:movie_id>/', modal_ajax, name='modal_ajax'),
    path('yt_player/<str:movie_id>/', yt_player, name='yt_player'),
    path('edit_ajax/<int:movie_id>/', edit_ajax, name='edit_ajax'),

    path('elo_modal/<int:movie_id>/', elo_modal, name='elo_modal'),
    path('elo_modal_matchup/<int:movie_id>/', elo_modal_matchup, name='elo_modal_matchup'),


    path('poster_update/', poster_update, name='poster_update'),
    path('movie_update/', movie_update, name='movie_update'),
    path('update_favorite/', update_favorite, name='update_favorite'),
    path('update_include/', update_include, name='update_include'),

    path('get_suggestions/', get_suggestions, name='get_suggestions'),

    path('elo_matchup/', elo_matchup, name='elo_matchup'),
    path('mini_elo_matchup/', mini_elo_matchup, name='mini_elo_matchup'),

    path('rankings_submit/', rankings_submit, name='rankings_submit'),

    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    path('dashboard/home/', dashboard_home, name='dashboard_home'),
    path('dashboard/analytics/', dashboard_analytics, name='dashboard_analytics'),
    path('dashboard/people/', dashboard_people, name='dashboard_people'),
    path('dashboard/on_this_day/', dashboard_on_this_day, name='dashboard_on_this_day'),
    path('dashboard/this_week/', dashboard_this_week, name='dashboard_this_week'),
    path('dashboard/month/', RedirectView.as_view(url=f'/dashboard/month/{date.today().strftime("%B").lower()}/{date.today().strftime("%Y")}', permanent=False)),
    path('dashboard/month/<str:month>/<int:year>', dashboard_month, name='dashboard_month'),
    path('dashboard/year/', RedirectView.as_view(url=f'/dashboard/year/{date.today().strftime("%Y").lower()}', permanent=False)),
    path('dashboard/year/<int:year>', dashboard_year, name='dashboard_year'),
    path('dashboard/<anything>/', RedirectView.as_view(url='/dashboard/', permanent=False)),

    path('rankings/', RankingsView.as_view(), name='rankings'),
    path('watchlog/', WatchlogView.as_view(), name='watchlog'),
    path('watchlist/', WatchlistView.as_view(), name='watchlist'),
    path('elo/', EloView.as_view(), name='elo'),
    path('update_order/', update_order, name='update_order'),
]

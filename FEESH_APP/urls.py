from django.contrib import admin
from django.urls import include, path, re_path
from . import views 
urlpatterns = [
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path('restart/', views.restart, name='restart'),
    path("",views.index, name="index"),
    path('click_atom/', views.click_atom, name='click_atom'),
    path("game-broken/", views.game_broken, name="game_broken"),
    path("auto_clicker_tick/", views.auto_clicker_tick, name="auto_clicker_tick")
]
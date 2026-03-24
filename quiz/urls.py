from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("jogo/", views.jogo, name="jogo"),
]
from django.urls import path
from .views import login_view

urlpatterns = [
    path('login/', login_view, name='login'),
]
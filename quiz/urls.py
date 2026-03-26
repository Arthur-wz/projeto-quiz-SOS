from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('criar-usuario/', views.criar_usuario, name='criar_usuario'),
    path('jogo/', views.jogo, name='jogo'),
]
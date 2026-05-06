from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("criar-usuario/", views.criar_usuario, name="criar_usuario"),
    path("ranking/", views.ranking, name="ranking"),
    path("temas/", views.temas, name="temas"),
    path("temas/<slug:slug>/ativar/", views.ativar_tema, name="ativar_tema"),
    path("iniciar-partida/", views.iniciar_partida, name="iniciar_partida"),
    path("jogo/iniciar/", views.iniciar_partida, name="iniciar_jogo"),
    path("continuar-partida/", views.continuar_partida, name="continuar_partida"),
    path("reiniciar-partida/", views.reiniciar_partida, name="reiniciar_partida"),
    path("jogo/", views.jogo, name="jogo"),
    path("resultado/", views.resultado, name="resultado"),
]

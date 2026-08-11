from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("criar-usuario/", views.criar_usuario, name="criar_usuario"),
    path("ranking/", views.ranking, name="ranking"),
    path("kahoot/", views.kahoot_inicio, name="kahoot_inicio"),
    path("kahoot/criar/", views.criar_sala_kahoot, name="criar_sala_kahoot"),
    path("kahoot/entrar/", views.entrar_sala_kahoot, name="entrar_sala_kahoot"),
    path("kahoot/sala/<str:codigo>/", views.sala_kahoot, name="sala_kahoot"),
    path("kahoot/sala/<str:codigo>/editar/", views.editar_sala_kahoot, name="editar_sala_kahoot"),
    path("kahoot/sala/<str:codigo>/excluir/", views.excluir_sala_kahoot, name="excluir_sala_kahoot"),
    path(
        "kahoot/sala/<str:codigo>/perguntas/",
        views.gerenciar_perguntas_kahoot,
        name="gerenciar_perguntas_kahoot",
    ),
    path(
        "kahoot/sala/<str:codigo>/perguntas/criar/",
        views.criar_pergunta_personalizada_kahoot,
        name="criar_pergunta_personalizada_kahoot",
    ),
    path(
        "kahoot/sala/<str:codigo>/perguntas/<int:pergunta_id>/excluir/",
        views.excluir_pergunta_personalizada_kahoot,
        name="excluir_pergunta_personalizada_kahoot",
    ),
    path("kahoot/sala/<str:codigo>/iniciar/", views.iniciar_sala_kahoot, name="iniciar_sala_kahoot"),
    path("kahoot/sala/<str:codigo>/avancar/", views.avancar_rodada_kahoot, name="avancar_rodada_kahoot"),
    path("kahoot/sala/<str:codigo>/responder/", views.responder_kahoot, name="responder_kahoot"),
    path("temas/", views.temas, name="temas"),
    path("temas/<slug:slug>/ativar/", views.ativar_tema, name="ativar_tema"),
    path("iniciar-partida/", views.iniciar_partida, name="iniciar_partida"),
    path("jogo/iniciar/", views.iniciar_partida, name="iniciar_jogo"),
    path("continuar-partida/", views.continuar_partida, name="continuar_partida"),
    path("reiniciar-partida/", views.reiniciar_partida, name="reiniciar_partida"),
    path("jogo/", views.jogo, name="jogo"),
    path("resultado/", views.resultado, name="resultado"),
]

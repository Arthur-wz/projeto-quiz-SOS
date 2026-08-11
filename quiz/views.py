import random
from datetime import datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from django.conf import settings

from .models import (
    Partida,
    PerguntaSalaKahoot,
    ParticipanteSalaKahoot,
    PerfilUsuario,
    Pergunta,
    RespostaPartida,
    RespostaSalaKahoot,
    SalaKahoot,
)
from .themes import DEFAULT_THEME_SLUG, listar_temas, obter_tema_por_slug

QUIZ_SESSION_KEY = "quiz_state"
TOTAL_PERGUNTAS = 20
PONTOS_POR_PERGUNTA = 10
PONTOS_COM_AJUDA = 5
HELP_SKIP = "skip"
HELP_ELIMINATE = "eliminate"
RANKING_LIMIT = 10
KAHOOT_MIN_PERGUNTAS = 5
KAHOOT_PONTOS_BASE = 1000


def home(request):
    state = request.session.get(QUIZ_SESSION_KEY, {})
    answered_count = state.get("answered_count", 0)
    queue = state.get("queue", [])

    context = {
        "total_cadastradas": Pergunta.objects.count(),
        "total_perguntas": TOTAL_PERGUNTAS,
        "partida_em_andamento": bool(queue) and answered_count < TOTAL_PERGUNTAS,
        "partida_finalizada": bool(state) and answered_count >= TOTAL_PERGUNTAS,
        "pontuacao_atual": state.get("score", 0),
        "kahoot_disponivel": request.user.is_authenticated,
        "usuario_logado": request.user if request.user.is_authenticated else None,
    }
    return render(request, "home.html", context)


def login_view(request):
    erro = None

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            messages.success(request, f"Login efetuado com sucesso. Bem-vindo, {user.username}.")
            return redirect("home")

        erro = "Usuario ou senha invalidos."

    context = {
        "erro": erro,
        "google_login_configured": _google_login_esta_configurado(),
        "google_login_url": _obter_url_login_google(),
    }
    return render(request, "login.html", context)


def criar_usuario(request):
    erro = None
    sucesso = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        confirmar = request.POST.get("confirmar", "").strip()

        if not username or not password or not confirmar:
            erro = "Preencha todos os campos."
        elif password != confirmar:
            erro = "As senhas nao coincidem."
        elif User.objects.filter(username=username).exists():
            erro = "Esse usuario ja existe."
        else:
            User.objects.create_user(username=username, password=password)
            sucesso = "Usuario criado com sucesso!"

    return render(request, "criar_usuario.html", {"erro": erro, "sucesso": sucesso})


@require_POST
def iniciar_partida(request):
    ids = list(Pergunta.objects.values_list("id", flat=True))

    if len(ids) < TOTAL_PERGUNTAS:
        messages.error(
            request,
            f"Cadastre pelo menos {TOTAL_PERGUNTAS} perguntas para iniciar uma partida completa.",
        )
        return redirect("home")

    _encerrar_partida_anterior(request)

    random.shuffle(ids)
    partida = Partida.objects.create(
        usuario=request.user if request.user.is_authenticated else None,
        total_perguntas=TOTAL_PERGUNTAS,
    )

    request.session[QUIZ_SESSION_KEY] = {
        "queue": ids[:TOTAL_PERGUNTAS],
        "answered_count": 0,
        "score": 0,
        "correct_count": 0,
        "used_skip": False,
        "used_eliminate": False,
        "current_is_halved": False,
        "current_help_types": [],
        "eliminated_options": [],
        "history": [],
        "partida_id": partida.id,
    }
    return redirect("jogo")


def continuar_partida(request):
    state = request.session.get(QUIZ_SESSION_KEY)
    if not state:
        messages.info(request, "Inicie uma nova partida para continuar.")
        return redirect("home")

    if state.get("answered_count", 0) >= TOTAL_PERGUNTAS or not state.get("queue"):
        return redirect("resultado")

    return redirect("jogo")


def ranking(request):
    inicio_semana = _inicio_semana_atual()
    inicio_mes = _inicio_mes_atual()

    context = {
        "ranking_semanal": _montar_ranking(inicio_semana),
        "ranking_mensal": _montar_ranking(inicio_mes),
        "inicio_semana": timezone.localtime(inicio_semana).date(),
        "inicio_mes": timezone.localtime(inicio_mes).date(),
        "auto_refresh_ms": 5000,
    }
    return render(request, "ranking.html", context)


def kahoot_inicio(request):
    if not request.user.is_authenticated:
        messages.info(request, "Faca login para acessar o modo Kahoot.")
        return redirect("login")

    salas = SalaKahoot.objects.filter(anfitriao=request.user)[:10]
    participacoes = ParticipanteSalaKahoot.objects.filter(usuario=request.user).select_related("sala")[:10]
    context = {
        "salas_criadas": salas,
        "participacoes": participacoes,
        "total_perguntas": Pergunta.objects.count(),
        "minimo_perguntas": KAHOOT_MIN_PERGUNTAS,
    }
    return render(request, "kahoot_inicio.html", context)


@require_POST
def criar_sala_kahoot(request):
    if not request.user.is_authenticated:
        messages.info(request, "Faca login para acessar o modo Kahoot.")
        return redirect("login")

    total_perguntas = Pergunta.objects.count()
    if total_perguntas < KAHOOT_MIN_PERGUNTAS:
        messages.error(
            request,
            f"Cadastre pelo menos {KAHOOT_MIN_PERGUNTAS} perguntas para criar uma sala Kahoot.",
        )
        return redirect("kahoot_inicio")

    titulo = request.POST.get("titulo", "").strip() or "Sala Kahoot"
    try:
        rodadas = int(request.POST.get("total_rodadas", "10"))
    except ValueError:
        rodadas = 10
    try:
        tempo = int(request.POST.get("tempo_por_rodada", "20"))
    except ValueError:
        tempo = 20

    rodadas = max(KAHOOT_MIN_PERGUNTAS, min(rodadas, min(20, total_perguntas)))
    tempo = max(10, min(tempo, 60))

    sala = SalaKahoot.objects.create(
        anfitriao=request.user,
        codigo=_gerar_codigo_sala_kahoot(),
        titulo=titulo,
        total_rodadas=rodadas,
        tempo_por_rodada=tempo,
    )
    ParticipanteSalaKahoot.objects.get_or_create(
        sala=sala,
        usuario=request.user,
        defaults={"apelido": request.user.username},
    )
    messages.success(request, f"Sala {sala.codigo} criada com sucesso.")
    return redirect("sala_kahoot", codigo=sala.codigo)


@require_POST
def entrar_sala_kahoot(request):
    if not request.user.is_authenticated:
        messages.info(request, "Faca login para acessar o modo Kahoot.")
        return redirect("login")

    codigo = request.POST.get("codigo", "").strip().upper()
    if not codigo:
        messages.warning(request, "Informe o codigo da sala.")
        return redirect("kahoot_inicio")

    sala = SalaKahoot.objects.filter(codigo=codigo).first()
    if not sala:
        messages.error(request, "Sala nao encontrada.")
        return redirect("kahoot_inicio")

    ParticipanteSalaKahoot.objects.get_or_create(
        sala=sala,
        usuario=request.user,
        defaults={"apelido": request.user.username},
    )
    messages.success(request, f"Voce entrou na sala {sala.codigo}.")
    return redirect("sala_kahoot", codigo=sala.codigo)


def sala_kahoot(request, codigo):
    if not request.user.is_authenticated:
        messages.info(request, "Faca login para acessar o modo Kahoot.")
        return redirect("login")

    sala = get_object_or_404(
        SalaKahoot.objects.select_related("anfitriao", "pergunta_atual"),
        codigo=codigo.upper(),
    )
    participante = ParticipanteSalaKahoot.objects.filter(sala=sala, usuario=request.user).first()
    if not participante:
        messages.info(request, "Entre na sala para acompanhar este modo Kahoot.")
        return redirect("kahoot_inicio")

    ranking = list(sala.participantes.select_related("usuario").order_by("-pontuacao_total", "-respostas_certas", "apelido"))
    tempo_restante = _tempo_restante_kahoot(sala)
    resposta_atual = None
    if sala.rodada_atual and participante:
        resposta_atual = RespostaSalaKahoot.objects.filter(
            participante=participante,
            rodada=sala.rodada_atual,
        ).first()

    context = {
        "sala": sala,
        "participante": participante,
        "eh_anfitriao": sala.anfitriao_id == request.user.id,
        "ranking": ranking,
        "tempo_restante": tempo_restante,
        "pergunta_atual": sala.pergunta_personalizada_atual or sala.pergunta_atual,
        "resposta_atual": resposta_atual,
        "rodada_fechada": sala.status != SalaKahoot.STATUS_EM_ANDAMENTO or tempo_restante == 0,
        "auto_refresh_ms": 3000 if sala.status != SalaKahoot.STATUS_FINALIZADA else 0,
        "total_perguntas_personalizadas": sala.perguntas_personalizadas.count(),
    }
    return render(request, "kahoot_sala.html", context)


def editar_sala_kahoot(request, codigo):
    if not request.user.is_authenticated:
        messages.info(request, "Faca login para acessar o modo Kahoot.")
        return redirect("login")

    sala = get_object_or_404(SalaKahoot, codigo=codigo.upper(), anfitriao=request.user)
    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip() or sala.titulo
        try:
            rodadas = int(request.POST.get("total_rodadas", sala.total_rodadas))
        except ValueError:
            rodadas = sala.total_rodadas
        try:
            tempo = int(request.POST.get("tempo_por_rodada", sala.tempo_por_rodada))
        except ValueError:
            tempo = sala.tempo_por_rodada

        total_disponivel = sala.perguntas_personalizadas.count() or Pergunta.objects.count()
        rodadas = max(1, min(rodadas, max(total_disponivel, 1)))
        tempo = max(10, min(tempo, 60))

        sala.titulo = titulo
        sala.total_rodadas = rodadas
        sala.tempo_por_rodada = tempo
        sala.save(update_fields=["titulo", "total_rodadas", "tempo_por_rodada", "atualizada_em"])
        messages.success(request, "Sala atualizada com sucesso.")
        return redirect("sala_kahoot", codigo=sala.codigo)

    context = {"sala": sala}
    return render(request, "kahoot_editar_sala.html", context)


@require_POST
def excluir_sala_kahoot(request, codigo):
    if not request.user.is_authenticated:
        messages.info(request, "Faca login para acessar o modo Kahoot.")
        return redirect("login")

    sala = get_object_or_404(SalaKahoot, codigo=codigo.upper(), anfitriao=request.user)
    sala.delete()
    messages.success(request, "Sala excluida com sucesso.")
    return redirect("kahoot_inicio")


@require_POST
def criar_pergunta_personalizada_kahoot(request, codigo):
    if not request.user.is_authenticated:
        messages.info(request, "Faca login para acessar o modo Kahoot.")
        return redirect("login")

    sala = get_object_or_404(SalaKahoot, codigo=codigo.upper(), anfitriao=request.user)
    ordem = sala.perguntas_personalizadas.count() + 1
    pergunta = request.POST.get("pergunta", "").strip()
    alternativa_a = request.POST.get("alternativa_a", "").strip()
    alternativa_b = request.POST.get("alternativa_b", "").strip()
    alternativa_c = request.POST.get("alternativa_c", "").strip()
    alternativa_d = request.POST.get("alternativa_d", "").strip()
    alternativa_e = request.POST.get("alternativa_e", "").strip()
    resposta_correta = request.POST.get("resposta_correta", "").strip().upper()
    materia = request.POST.get("materia", "").strip() or "Sala"
    serie = request.POST.get("serie", "").strip() or "Personalizada"

    campos = [pergunta, alternativa_a, alternativa_b, alternativa_c, alternativa_d, alternativa_e]
    if not all(campos) or resposta_correta not in dict(Pergunta.OPCOES_RESPOSTA):
        messages.error(request, "Preencha a pergunta, as 5 alternativas e a resposta correta.")
        return redirect("gerenciar_perguntas_kahoot", codigo=sala.codigo)

    PerguntaSalaKahoot.objects.create(
        sala=sala,
        pergunta=pergunta,
        alternativa_a=alternativa_a,
        alternativa_b=alternativa_b,
        alternativa_c=alternativa_c,
        alternativa_d=alternativa_d,
        alternativa_e=alternativa_e,
        resposta_correta=resposta_correta,
        materia=materia,
        serie=serie,
        ordem=ordem,
    )
    messages.success(request, "Pergunta personalizada criada com sucesso.")
    return redirect("gerenciar_perguntas_kahoot", codigo=sala.codigo)


def gerenciar_perguntas_kahoot(request, codigo):
    if not request.user.is_authenticated:
        messages.info(request, "Faca login para acessar o modo Kahoot.")
        return redirect("login")

    sala = get_object_or_404(SalaKahoot, codigo=codigo.upper(), anfitriao=request.user)
    context = {"sala": sala, "perguntas": sala.perguntas_personalizadas.all()}
    return render(request, "kahoot_perguntas.html", context)


@require_POST
def excluir_pergunta_personalizada_kahoot(request, codigo, pergunta_id):
    if not request.user.is_authenticated:
        messages.info(request, "Faca login para acessar o modo Kahoot.")
        return redirect("login")

    sala = get_object_or_404(SalaKahoot, codigo=codigo.upper(), anfitriao=request.user)
    pergunta = get_object_or_404(PerguntaSalaKahoot, pk=pergunta_id, sala=sala)
    pergunta.delete()

    for indice, item in enumerate(sala.perguntas_personalizadas.all(), start=1):
        if item.ordem != indice:
            item.ordem = indice
            item.save(update_fields=["ordem"])

    messages.success(request, "Pergunta removida com sucesso.")
    return redirect("gerenciar_perguntas_kahoot", codigo=sala.codigo)


@require_POST
def iniciar_sala_kahoot(request, codigo):
    if not request.user.is_authenticated:
        messages.info(request, "Faca login para acessar o modo Kahoot.")
        return redirect("login")

    sala = get_object_or_404(SalaKahoot, codigo=codigo.upper())
    if sala.anfitriao_id != request.user.id:
        messages.error(request, "Apenas o anfitriao pode iniciar a sala.")
        return redirect("sala_kahoot", codigo=sala.codigo)

    if sala.status != SalaKahoot.STATUS_AGUARDANDO:
        messages.info(request, "Essa sala ja foi iniciada.")
        return redirect("sala_kahoot", codigo=sala.codigo)

    if sala.participantes.count() < 1:
        messages.warning(request, "A sala precisa ter pelo menos um participante.")
        return redirect("sala_kahoot", codigo=sala.codigo)

    if sala.perguntas_personalizadas.exists():
        if sala.perguntas_personalizadas.count() < sala.total_rodadas:
            messages.warning(request, "Crie perguntas personalizadas suficientes para a quantidade de rodadas.")
            return redirect("gerenciar_perguntas_kahoot", codigo=sala.codigo)
        perguntas_ids = list(sala.perguntas_personalizadas.values_list("id", flat=True))
    else:
        if Pergunta.objects.count() < sala.total_rodadas:
            messages.warning(request, "Nao existem perguntas suficientes no banco para iniciar essa sala.")
            return redirect("sala_kahoot", codigo=sala.codigo)
        perguntas_ids = list(Pergunta.objects.values_list("id", flat=True))
    random.shuffle(perguntas_ids)
    perguntas_ids = perguntas_ids[: sala.total_rodadas]

    sala.perguntas_sorteadas = perguntas_ids
    sala.status = SalaKahoot.STATUS_EM_ANDAMENTO
    _definir_rodada_kahoot(sala, 1)
    messages.success(request, "Modo Kahoot iniciado.")
    return redirect("sala_kahoot", codigo=sala.codigo)


@require_POST
def avancar_rodada_kahoot(request, codigo):
    if not request.user.is_authenticated:
        messages.info(request, "Faca login para acessar o modo Kahoot.")
        return redirect("login")

    sala = get_object_or_404(SalaKahoot, codigo=codigo.upper())
    if sala.anfitriao_id != request.user.id:
        messages.error(request, "Apenas o anfitriao pode avancar a rodada.")
        return redirect("sala_kahoot", codigo=sala.codigo)

    if sala.status != SalaKahoot.STATUS_EM_ANDAMENTO:
        messages.info(request, "A sala ja foi encerrada.")
        return redirect("sala_kahoot", codigo=sala.codigo)

    proxima_rodada = sala.rodada_atual + 1
    if proxima_rodada > sala.total_rodadas or proxima_rodada > len(sala.perguntas_sorteadas or []):
        sala.status = SalaKahoot.STATUS_FINALIZADA
        sala.pergunta_atual = None
        sala.pergunta_personalizada_atual = None
        sala.pergunta_iniciada_em = None
        sala.encerrada_em = timezone.now()
        sala.save(
            update_fields=[
                "status",
                "pergunta_atual",
                "pergunta_personalizada_atual",
                "pergunta_iniciada_em",
                "encerrada_em",
                "atualizada_em",
            ]
        )
        messages.success(request, "Sala finalizada. Ranking final disponivel.")
        return redirect("sala_kahoot", codigo=sala.codigo)

    _definir_rodada_kahoot(sala, proxima_rodada)
    messages.success(request, f"Rodada {proxima_rodada} iniciada.")
    return redirect("sala_kahoot", codigo=sala.codigo)


@require_POST
def responder_kahoot(request, codigo):
    if not request.user.is_authenticated:
        messages.info(request, "Faca login para acessar o modo Kahoot.")
        return redirect("login")

    sala = get_object_or_404(
        SalaKahoot.objects.select_related("pergunta_atual", "pergunta_personalizada_atual"),
        codigo=codigo.upper(),
    )
    participante = ParticipanteSalaKahoot.objects.filter(sala=sala, usuario=request.user).first()
    if not participante:
        messages.error(request, "Voce nao esta participando dessa sala.")
        return redirect("kahoot_inicio")

    pergunta_ativa = sala.pergunta_personalizada_atual or sala.pergunta_atual
    if sala.status != SalaKahoot.STATUS_EM_ANDAMENTO or not pergunta_ativa:
        messages.warning(request, "Nao ha rodada ativa para responder.")
        return redirect("sala_kahoot", codigo=sala.codigo)

    if _tempo_restante_kahoot(sala) <= 0:
        messages.warning(request, "O tempo dessa rodada acabou.")
        return redirect("sala_kahoot", codigo=sala.codigo)

    resposta = request.POST.get("answer", "").upper()
    if resposta not in dict(Pergunta.OPCOES_RESPOSTA):
        messages.warning(request, "Escolha uma alternativa valida.")
        return redirect("sala_kahoot", codigo=sala.codigo)

    resposta_existente = RespostaSalaKahoot.objects.filter(
        participante=participante,
        rodada=sala.rodada_atual,
    ).first()
    if resposta_existente:
        messages.info(request, "Voce ja respondeu esta rodada.")
        return redirect("sala_kahoot", codigo=sala.codigo)

    correta = pergunta_ativa.resposta_correta.upper()
    acertou = resposta == correta
    pontos = _calcular_pontos_kahoot(sala, acertou)

    RespostaSalaKahoot.objects.create(
        participante=participante,
        sala=sala,
        pergunta=sala.pergunta_atual,
        rodada=sala.rodada_atual,
        resposta_marcada=resposta,
        resposta_correta=correta,
        acertou=acertou,
        pontos_recebidos=pontos,
    )

    participante.pontuacao_total += pontos
    participante.respostas_certas += int(acertou)
    participante.save(update_fields=["pontuacao_total", "respostas_certas"])

    if acertou:
        messages.success(request, f"Resposta registrada. +{pontos} pontos.")
    else:
        messages.error(request, "Resposta registrada, mas estava incorreta.")
    return redirect("sala_kahoot", codigo=sala.codigo)


def temas(request):
    tema_ativo_slug = DEFAULT_THEME_SLUG
    temas_liberados = set()

    if request.user.is_authenticated:
        perfil = _obter_perfil_usuario(request.user)
        perfil.sincronizar_temas_gratuitos()
        temas_liberados = set(perfil.listar_temas_liberados())
        tema_ativo_slug = perfil.tema_ativo

    catalogo_temas = []
    for tema in listar_temas():
        liberado = tema.slug in temas_liberados or not tema.premium
        catalogo_temas.append(
            {
                "tema": tema,
                "liberado": liberado,
                "ativo": tema.slug == tema_ativo_slug,
            }
        )

    context = {"catalogo_temas": catalogo_temas}
    return render(request, "temas.html", context)


@require_POST
def ativar_tema(request, slug):
    if not request.user.is_authenticated:
        messages.info(request, "Faca login para escolher um tema personalizado.")
        return redirect("login")

    tema = obter_tema_por_slug(slug)
    if not tema:
        messages.error(request, "Tema nao encontrado.")
        return redirect("temas")

    perfil = _obter_perfil_usuario(request.user)
    perfil.sincronizar_temas_gratuitos()

    if not perfil.tema_esta_liberado(slug):
        messages.warning(request, "Esse tema ainda nao esta liberado para a sua conta.")
        return redirect("temas")

    perfil.ativar_tema(slug)
    messages.success(request, f"Tema {tema.nome} ativado com sucesso.")
    return redirect("temas")


@require_POST
def reiniciar_partida(request):
    _encerrar_partida_anterior(request, abandonada=True)
    request.session.pop(QUIZ_SESSION_KEY, None)
    messages.info(request, "A partida atual foi encerrada. Voce pode comecar outra quando quiser.")
    return redirect("home")


def jogo(request):
    state = request.session.get(QUIZ_SESSION_KEY)
    if not state:
        messages.info(request, "Inicie uma nova partida para comecar o quiz.")
        return redirect("home")

    queue = state.get("queue", [])
    if not queue:
        return redirect("resultado")

    pergunta = get_object_or_404(Pergunta, pk=queue[0])

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "answer":
            return _responder(request, state, pergunta)
        if action == "skip":
            return _pular(request, state)
        if action == "eliminate":
            return _eliminar_duas(request, state, pergunta)

        messages.warning(request, "Acao invalida para esta partida.")
        return redirect("jogo")

    return render(request, "jogo.html", _montar_contexto_jogo(state, pergunta))


def resultado(request):
    state = request.session.get(QUIZ_SESSION_KEY)
    if not state:
        messages.info(request, "Inicie uma nova partida para ver seu resultado.")
        return redirect("home")

    if state.get("answered_count", 0) < TOTAL_PERGUNTAS and state.get("queue"):
        return redirect("jogo")

    partida = _sincronizar_partida(request, finalizada=True)
    context = {
        "partida": partida,
        "pontuacao": state.get("score", 0),
        "acertos": state.get("correct_count", 0),
        "erros": state.get("answered_count", 0) - state.get("correct_count", 0),
        "total_perguntas": TOTAL_PERGUNTAS,
        "pontuacao_maxima": TOTAL_PERGUNTAS * PONTOS_POR_PERGUNTA,
        "pulo_usado": state.get("used_skip", False),
        "eliminar_usado": state.get("used_eliminate", False),
        "historico": state.get("history", []),
    }
    return render(request, "resultado.html", context)


def _responder(request, state, pergunta):
    resposta = request.POST.get("answer", "").upper()
    resposta_correta = pergunta.resposta_correta.upper()

    if resposta not in dict(Pergunta.OPCOES_RESPOSTA):
        messages.warning(request, "Escolha uma alternativa valida para continuar.")
        return redirect("jogo")
    if resposta in set(state.get("eliminated_options", [])):
        messages.warning(request, "Essa alternativa foi eliminada pela ajuda.")
        return redirect("jogo")

    numero_pergunta = state.get("answered_count", 0) + 1
    ajuda_tags = list(state.get("current_help_types", []))
    valor_pergunta = PONTOS_COM_AJUDA if state.get("current_is_halved") else PONTOS_POR_PERGUNTA
    acertou = resposta == resposta_correta
    pontos_recebidos = valor_pergunta if acertou else 0

    state["score"] = state.get("score", 0) + pontos_recebidos
    state["correct_count"] = state.get("correct_count", 0) + int(acertou)
    state["answered_count"] = numero_pergunta
    state.setdefault("history", []).append(
        {
            "numero": numero_pergunta,
            "pergunta": pergunta.pergunta,
            "materia": pergunta.materia,
            "serie": pergunta.serie,
            "resposta_marcada": resposta,
            "resposta_correta": resposta_correta,
            "acertou": acertou,
            "pontos": pontos_recebidos,
            "valor": valor_pergunta,
            "ajudas": ajuda_tags,
        }
    )

    _registrar_resposta_no_banco(
        request,
        state=state,
        pergunta=pergunta,
        numero_pergunta=numero_pergunta,
        resposta=resposta,
        resposta_correta=resposta_correta,
        acertou=acertou,
        ajuda_tags=ajuda_tags,
        valor_pergunta=valor_pergunta,
        pontos_recebidos=pontos_recebidos,
    )

    state["queue"] = state.get("queue", [])[1:]
    state["current_is_halved"] = False
    state["current_help_types"] = []
    state["eliminated_options"] = []
    request.session[QUIZ_SESSION_KEY] = state

    if acertou:
        if ajuda_tags:
            messages.success(request, f"Resposta certa com ajuda! +{valor_pergunta} pontos.")
        else:
            messages.success(request, f"Resposta certa! +{pontos_recebidos} pontos.")
    else:
        messages.error(request, f"Resposta errada. A correta era {resposta_correta}.")

    if state["answered_count"] >= TOTAL_PERGUNTAS or not state["queue"]:
        _sincronizar_partida(request, finalizada=True)
        return redirect("resultado")

    _sincronizar_partida(request)
    return redirect("jogo")


def _pular(request, state):
    if state.get("used_skip"):
        messages.warning(request, "Voce ja usou o pular nesta partida.")
        return redirect("jogo")

    queue = state.get("queue", [])
    if len(queue) < 2:
        messages.warning(request, "Nao ha outra pergunta disponivel para trocar agora.")
        return redirect("jogo")

    primeira = queue.pop(0)
    queue.append(primeira)

    state["queue"] = queue
    state["used_skip"] = True
    state["current_is_halved"] = True
    state["current_help_types"] = _adicionar_ajuda(state.get("current_help_types", []), HELP_SKIP)
    state["eliminated_options"] = []
    request.session[QUIZ_SESSION_KEY] = state

    _sincronizar_partida(request)
    messages.info(request, "Pergunta pulada. A nova pergunta desta rodada vale 5 pontos.")
    return redirect("jogo")


def _eliminar_duas(request, state, pergunta):
    if state.get("used_eliminate"):
        messages.warning(request, "Voce ja usou o eliminar 2 nesta partida.")
        return redirect("jogo")

    resposta_correta = pergunta.resposta_correta.upper()
    alternativas_erradas = [label for label, _ in pergunta.alternativas() if label != resposta_correta]

    state["used_eliminate"] = True
    state["current_is_halved"] = True
    state["current_help_types"] = _adicionar_ajuda(
        state.get("current_help_types", []),
        HELP_ELIMINATE,
    )
    state["eliminated_options"] = random.sample(alternativas_erradas, 2)
    request.session[QUIZ_SESSION_KEY] = state

    _sincronizar_partida(request)
    messages.info(request, "Duas alternativas erradas foram eliminadas. Esta pergunta agora vale 5 pontos.")
    return redirect("jogo")


def _montar_contexto_jogo(state, pergunta):
    eliminadas = set(state.get("eliminated_options", []))
    respondidas = state.get("answered_count", 0)
    numero_pergunta = respondidas + 1

    opcoes = [
        {"label": label, "texto": texto}
        for label, texto in pergunta.alternativas()
        if label not in eliminadas
    ]

    return {
        "pergunta": pergunta,
        "opcoes": opcoes,
        "numero_pergunta": numero_pergunta,
        "total_perguntas": TOTAL_PERGUNTAS,
        "pontuacao": state.get("score", 0),
        "valor_pergunta": PONTOS_COM_AJUDA if state.get("current_is_halved") else PONTOS_POR_PERGUNTA,
        "pulo_disponivel": not state.get("used_skip"),
        "eliminar_disponivel": not state.get("used_eliminate"),
        "restantes": TOTAL_PERGUNTAS - respondidas,
        "ajuda_ativa": state.get("current_is_halved", False),
        "progresso": int((respondidas / TOTAL_PERGUNTAS) * 100),
    }


def _registrar_resposta_no_banco(
    request,
    *,
    state,
    pergunta,
    numero_pergunta,
    resposta,
    resposta_correta,
    acertou,
    ajuda_tags,
    valor_pergunta,
    pontos_recebidos,
):
    partida = _obter_partida_da_sessao(request, state)
    if not partida:
        return

    RespostaPartida.objects.update_or_create(
        partida=partida,
        numero_pergunta=numero_pergunta,
        defaults={
            "pergunta": pergunta,
            "pergunta_texto": pergunta.pergunta,
            "materia": pergunta.materia,
            "serie": pergunta.serie,
            "resposta_marcada": resposta,
            "resposta_correta": resposta_correta,
            "acertou": acertou,
            "ajuda_utilizada": bool(ajuda_tags),
            "ajudas_utilizadas": ",".join(ajuda_tags),
            "valor_pergunta": valor_pergunta,
            "pontos_recebidos": pontos_recebidos,
        },
    )


def _sincronizar_partida(request, finalizada=False, abandonada=False):
    state = request.session.get(QUIZ_SESSION_KEY, {})
    partida = _obter_partida_da_sessao(request, state)
    if not partida:
        return None

    partida.usuario = request.user if request.user.is_authenticated else partida.usuario
    partida.total_perguntas = TOTAL_PERGUNTAS
    partida.pontuacao_total = state.get("score", 0)
    partida.acertos = state.get("correct_count", 0)
    partida.erros = state.get("answered_count", 0) - state.get("correct_count", 0)
    partida.pulo_usado = state.get("used_skip", False)
    partida.eliminar_usado = state.get("used_eliminate", False)

    if finalizada:
        partida.status = Partida.STATUS_FINALIZADA
        partida.encerrada_em = timezone.now()
    elif abandonada:
        partida.status = Partida.STATUS_ABANDONADA
        partida.encerrada_em = timezone.now()
    else:
        partida.status = Partida.STATUS_EM_ANDAMENTO
        partida.encerrada_em = None

    partida.save()
    return partida


def _encerrar_partida_anterior(request, abandonada=False):
    state = request.session.get(QUIZ_SESSION_KEY)
    if not state:
        return

    answered_count = state.get("answered_count", 0)
    queue = state.get("queue", [])

    if answered_count >= TOTAL_PERGUNTAS or not queue:
        _sincronizar_partida(request, finalizada=True)
        return

    if abandonada or answered_count or queue:
        _sincronizar_partida(request, abandonada=True)


def _obter_partida_da_sessao(request, state):
    partida_id = state.get("partida_id")
    if not partida_id:
        return None

    try:
        return Partida.objects.get(pk=partida_id)
    except Partida.DoesNotExist:
        messages.warning(request, "A partida atual nao foi encontrada. Comece outra para continuar.")
        return None


def _adicionar_ajuda(ajudas_atuais, nova_ajuda):
    if nova_ajuda in ajudas_atuais:
        return list(ajudas_atuais)
    return [*ajudas_atuais, nova_ajuda]


def _montar_ranking(inicio_periodo):
    ranking = list(
        Partida.objects.filter(
            status=Partida.STATUS_FINALIZADA,
            usuario__isnull=False,
            encerrada_em__gte=inicio_periodo,
        )
        .values("usuario_id", "usuario__username")
        .annotate(
            total_pontos=Sum("pontuacao_total"),
            total_acertos=Sum("acertos"),
            partidas_jogadas=Count("id"),
        )
        .order_by("-total_pontos", "-total_acertos", "-partidas_jogadas", "usuario__username")[
            :RANKING_LIMIT
        ]
    )

    for posicao, item in enumerate(ranking, start=1):
        item["posicao"] = posicao

    return ranking


def _inicio_semana_atual():
    hoje = timezone.localdate()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    return _inicio_do_dia(inicio_semana)


def _inicio_mes_atual():
    hoje = timezone.localdate()
    return _inicio_do_dia(hoje.replace(day=1))


def _inicio_do_dia(data):
    fuso = timezone.get_current_timezone()
    return timezone.make_aware(datetime.combine(data, time.min), fuso)


def _google_login_esta_configurado():
    google_settings = getattr(settings, "SOCIALACCOUNT_PROVIDERS", {}).get("google", {})
    app_settings = google_settings.get("APP", {})
    return bool(app_settings.get("client_id") and app_settings.get("secret"))


def _obter_url_login_google():
    try:
        return reverse("google_login")
    except NoReverseMatch:
        return None


def _obter_perfil_usuario(usuario):
    perfil, _ = PerfilUsuario.objects.get_or_create(
        usuario=usuario,
        defaults={
            "temas_liberados": [],
        },
    )
    return perfil


def _gerar_codigo_sala_kahoot():
    while True:
        codigo = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=6))
        if not SalaKahoot.objects.filter(codigo=codigo).exists():
            return codigo


def _definir_rodada_kahoot(sala, rodada):
    pergunta_id = (sala.perguntas_sorteadas or [])[rodada - 1]
    sala.pergunta_personalizada_atual = None
    sala.pergunta_atual = None
    sala.rodada_atual = rodada
    if sala.perguntas_personalizadas.filter(pk=pergunta_id).exists():
        sala.pergunta_personalizada_atual_id = pergunta_id
    else:
        sala.pergunta_atual_id = pergunta_id
    sala.pergunta_iniciada_em = timezone.now()
    sala.save(
        update_fields=[
            "rodada_atual",
            "pergunta_atual",
            "pergunta_personalizada_atual",
            "pergunta_iniciada_em",
            "status",
            "perguntas_sorteadas",
            "atualizada_em",
        ]
    )


def _tempo_restante_kahoot(sala):
    if not sala.pergunta_iniciada_em or sala.status != SalaKahoot.STATUS_EM_ANDAMENTO:
        return 0
    tempo_decorrido = int((timezone.now() - sala.pergunta_iniciada_em).total_seconds())
    return max(0, sala.tempo_por_rodada - tempo_decorrido)


def _calcular_pontos_kahoot(sala, acertou):
    if not acertou:
        return 0
    tempo_restante = _tempo_restante_kahoot(sala)
    bonus = int((tempo_restante / max(sala.tempo_por_rodada, 1)) * 500)
    return KAHOOT_PONTOS_BASE + bonus

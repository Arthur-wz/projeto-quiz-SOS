import random

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Pergunta

QUIZ_SESSION_KEY = "quiz_state"
TOTAL_PERGUNTAS = 20
PONTOS_POR_PERGUNTA = 10
PONTOS_COM_AJUDA = 5


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("jogo")

        return render(request, "login.html", {"erro": "Usuario ou senha invalidos"})

    return render(request, "login.html")


def criar_usuario(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        confirmar_password = request.POST.get("confirmar_password", "")

        if not username or not password or not confirmar_password:
            return render(request, "criar_usuario.html", {"erro": "Preencha todos os campos."})
        if password != confirmar_password:
            return render(request, "criar_usuario.html", {"erro": "As senhas nao coincidem."})
        if User.objects.filter(username=username).exists():
            return render(request, "criar_usuario.html", {"erro": "Esse nome de usuario ja existe."})

        User.objects.create_user(username=username, password=password)
        return redirect("login")

    return render(request, "criar_usuario.html")


def home(request):
    state = request.session.get(QUIZ_SESSION_KEY, {})
    partida_em_andamento = bool(state.get("queue")) and state.get("answered_count", 0) < TOTAL_PERGUNTAS
    partida_finalizada = state.get("answered_count", 0) >= TOTAL_PERGUNTAS

    context = {
        "total_cadastradas": Pergunta.objects.count(),
        "total_perguntas": TOTAL_PERGUNTAS,
        "partida_em_andamento": partida_em_andamento,
        "partida_finalizada": partida_finalizada,
    }
    return render(request, "home.html", context)


@require_POST
def iniciar_jogo(request):
    ids = list(Pergunta.objects.values_list("id", flat=True))

    if len(ids) < TOTAL_PERGUNTAS:
        messages.error(
            request,
            f"Cadastre pelo menos {TOTAL_PERGUNTAS} perguntas para iniciar uma partida completa.",
        )
        return redirect("home")

    random.shuffle(ids)
    request.session[QUIZ_SESSION_KEY] = {
        "queue": ids[:TOTAL_PERGUNTAS],
        "answered_count": 0,
        "score": 0,
        "correct_count": 0,
        "used_skip": False,
        "used_eliminate": False,
        "current_is_halved": False,
        "eliminated_options": [],
        "history": [],
    }
    return redirect("jogo")


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

    context = _montar_contexto_jogo(state, pergunta)
    return render(request, "jogo.html", context)


def resultado(request):
    state = request.session.get(QUIZ_SESSION_KEY)
    if not state:
        messages.info(request, "Inicie uma nova partida para ver seu resultado.")
        return redirect("home")

    if state.get("answered_count", 0) < TOTAL_PERGUNTAS and state.get("queue"):
        return redirect("jogo")

    context = {
        "pontuacao": state.get("score", 0),
        "acertos": state.get("correct_count", 0),
        "erros": TOTAL_PERGUNTAS - state.get("correct_count", 0),
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

    if resposta not in {"A", "B", "C", "D", "E"}:
        messages.warning(request, "Escolha uma alternativa valida para continuar.")
        return redirect("jogo")
    if resposta in set(state.get("eliminated_options", [])):
        messages.warning(request, "Essa alternativa foi eliminada pela ajuda.")
        return redirect("jogo")

    valor_pergunta = PONTOS_COM_AJUDA if state.get("current_is_halved") else PONTOS_POR_PERGUNTA
    acertou = resposta == resposta_correta
    pontos_recebidos = valor_pergunta if acertou else 0

    state["score"] = state.get("score", 0) + pontos_recebidos
    state["correct_count"] = state.get("correct_count", 0) + int(acertou)
    state["answered_count"] = state.get("answered_count", 0) + 1
    state["history"] = state.get("history", [])
    state["history"].append(
        {
            "numero": state["answered_count"],
            "pergunta": pergunta.pergunta,
            "materia": pergunta.materia,
            "resposta_marcada": resposta,
            "resposta_correta": resposta_correta,
            "acertou": acertou,
            "pontos": pontos_recebidos,
        }
    )
    state["queue"] = state.get("queue", [])[1:]
    state["current_is_halved"] = False
    state["eliminated_options"] = []

    request.session[QUIZ_SESSION_KEY] = state

    if acertou:
        messages.success(request, f"Resposta certa! +{pontos_recebidos} pontos.")
    else:
        messages.error(request, f"Resposta errada. A correta era {resposta_correta}.")

    if state["answered_count"] >= TOTAL_PERGUNTAS or not state["queue"]:
        return redirect("resultado")
    return redirect("jogo")


def _pular(request, state):
    if state.get("used_skip"):
        messages.warning(request, "Voce ja usou o pulo nesta partida.")
        return redirect("jogo")

    queue = state.get("queue", [])
    if len(queue) < 2:
        messages.warning(request, "Nao ha outra pergunta disponivel para trocar neste momento.")
        return redirect("jogo")

    primeira_pergunta = queue.pop(0)
    queue.append(primeira_pergunta)
    state["queue"] = queue
    state["used_skip"] = True
    state["current_is_halved"] = True
    state["eliminated_options"] = []
    request.session[QUIZ_SESSION_KEY] = state

    messages.info(request, "Pergunta pulada. A nova pergunta desta rodada vale 5 pontos.")
    return redirect("jogo")


def _eliminar_duas(request, state, pergunta):
    if state.get("used_eliminate"):
        messages.warning(request, "Voce ja usou a ajuda de eliminar 2 nesta partida.")
        return redirect("jogo")

    resposta_correta = pergunta.resposta_correta.upper()
    alternativas_erradas = [label for label, _ in pergunta.alternativas() if label != resposta_correta]

    state["used_eliminate"] = True
    state["current_is_halved"] = True
    state["eliminated_options"] = random.sample(alternativas_erradas, 2)
    request.session[QUIZ_SESSION_KEY] = state

    messages.info(request, "Duas alternativas erradas foram eliminadas. Esta pergunta agora vale 5 pontos.")
    return redirect("jogo")


def _montar_contexto_jogo(state, pergunta):
    eliminadas = set(state.get("eliminated_options", []))
    opcoes = [
        {"label": label, "texto": texto, "eliminada": label in eliminadas}
        for label, texto in pergunta.alternativas()
    ]

    return {
        "pergunta": pergunta,
        "opcoes": opcoes,
        "numero_pergunta": state.get("answered_count", 0) + 1,
        "total_perguntas": TOTAL_PERGUNTAS,
        "pontuacao": state.get("score", 0),
        "valor_pergunta": PONTOS_COM_AJUDA if state.get("current_is_halved") else PONTOS_POR_PERGUNTA,
        "pulo_disponivel": not state.get("used_skip"),
        "eliminar_disponivel": not state.get("used_eliminate"),
        "restantes": TOTAL_PERGUNTAS - state.get("answered_count", 0),
        "ajuda_ativa": state.get("current_is_halved", False),
    }

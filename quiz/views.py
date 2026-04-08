import random

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Partida, Pergunta, RespostaPartida

QUIZ_SESSION_KEY = "quiz_state"
TOTAL_PERGUNTAS = 20
PONTOS_POR_PERGUNTA = 10
PONTOS_COM_AJUDA = 5
HELP_SKIP = "skip"
HELP_ELIMINATE = "eliminate"


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
            return redirect("home")

        erro = "Usuario ou senha invalidos."

    return render(request, "login.html", {"erro": erro})


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

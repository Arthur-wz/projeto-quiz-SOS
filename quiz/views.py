from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.http import HttpResponse
from .models import Pergunta
import random

TOTAL_PERGUNTAS = 5


def home(request):
    tem_partida = 'perguntas_ids' in request.session and 'indice_atual' in request.session
    return render(request, 'home.html', {'tem_partida': tem_partida})


def login_view(request):
    erro = None

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect('home')
        else:
            erro = 'Usuário ou senha inválidos.'

    return render(request, 'login.html', {'erro': erro})


def criar_usuario(request):
    erro = None
    sucesso = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        confirmar = request.POST.get('confirmar', '').strip()

        if not username or not password or not confirmar:
            erro = 'Preencha todos os campos.'
        elif password != confirmar:
            erro = 'As senhas não coincidem.'
        elif User.objects.filter(username=username).exists():
            erro = 'Esse usuário já existe.'
        else:
            User.objects.create_user(username=username, password=password)
            sucesso = 'Usuário criado com sucesso!'

    return render(request, 'criar_usuario.html', {'erro': erro, 'sucesso': sucesso})


def iniciar_partida(request):
    perguntas = list(Pergunta.objects.all())

    if len(perguntas) < TOTAL_PERGUNTAS:
        return HttpResponse('Cadastre pelo menos 5 perguntas no admin.')

    selecionadas = random.sample(perguntas, TOTAL_PERGUNTAS)

    request.session['perguntas_ids'] = [p.id for p in selecionadas]
    request.session['indice_atual'] = 0
    request.session['pontuacao'] = 0

    return redirect('jogo')


def continuar_partida(request):
    if 'perguntas_ids' not in request.session:
        return redirect('home')

    return redirect('jogo')


def reiniciar_partida(request):
    for chave in ['perguntas_ids', 'indice_atual', 'pontuacao']:
        if chave in request.session:
            del request.session[chave]

    return redirect('home')


def jogo(request):
    perguntas_ids = request.session.get('perguntas_ids')
    indice_atual = request.session.get('indice_atual', 0)
    pontuacao = request.session.get('pontuacao', 0)

    if not perguntas_ids:
        return redirect('home')

    if indice_atual >= len(perguntas_ids):
        return redirect('resultado')

    try:
        pergunta = Pergunta.objects.get(id=perguntas_ids[indice_atual])
    except Pergunta.DoesNotExist:
        return HttpResponse('Pergunta não encontrada.')

    if request.method == 'POST':
        resposta = request.POST.get('resposta')

        if resposta == pergunta.resposta_correta:
            request.session['pontuacao'] = pontuacao + 1

        request.session['indice_atual'] = indice_atual + 1

        if request.session['indice_atual'] >= len(perguntas_ids):
            return redirect('resultado')

        return redirect('jogo')

    contexto = {
        'pergunta': pergunta,
        'numero_pergunta': indice_atual + 1,
        'total_perguntas': len(perguntas_ids),
        'pontuacao': pontuacao,
    }
    return render(request, 'jogo.html', contexto)


def resultado(request):
    pontuacao = request.session.get('pontuacao', 0)
    total = len(request.session.get('perguntas_ids', []))

    contexto = {
        'pontuacao': pontuacao,
        'total': total
    }
    return render(request, 'resultado.html', contexto)
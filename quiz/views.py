from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Pergunta
import random


def home(request):
    return render(request, 'home.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/jogo/')
        else:
            return render(request, 'login.html', {
                'erro': 'Usuário ou senha inválidos'
            })

    return render(request, 'login.html')


def criar_usuario(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirmar_password = request.POST.get('confirmar_password')

        if not username or not password or not confirmar_password:
            return render(request, 'criar_usuario.html', {
                'erro': 'Preencha todos os campos.'
            })

        if password != confirmar_password:
            return render(request, 'criar_usuario.html', {
                'erro': 'As senhas não coincidem.'
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'criar_usuario.html', {
                'erro': 'Esse nome de usuário já existe.'
            })

        User.objects.create_user(username=username, password=password)

        return redirect('/login/')

    return render(request, 'criar_usuario.html')


@login_required
def jogo(request):
    perguntas = list(Pergunta.objects.all())

    if not perguntas:
        return render(request, 'jogo.html', {'pergunta': None})

    if 'pontos' not in request.session:
        request.session['pontos'] = 0

    if request.method == 'POST':
        resposta = request.POST.get('resposta')
        pergunta_id = request.session.get('pergunta_id')

        if pergunta_id:
            try:
                pergunta_anterior = Pergunta.objects.get(id=pergunta_id)

                if resposta == pergunta_anterior.resposta_correta:
                    request.session['pontos'] += 1
            except Pergunta.DoesNotExist:
                pass

    pergunta = random.choice(perguntas)
    request.session['pergunta_id'] = pergunta.id

    return render(request, 'jogo.html', {'pergunta': pergunta})
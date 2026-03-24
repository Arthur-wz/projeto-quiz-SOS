from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import Pergunta
import random


def home(request):
    return render(request, "home.html")


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/jogo/')
        else:
            return render(request, 'login.html', {'erro': 'Usuário ou senha inválidos'})

    return render(request, 'login.html')


@login_required
def jogo(request):
    perguntas = list(Pergunta.objects.all())

    if not perguntas:
        return render(request, "jogo.html", {"pergunta": None})

    pergunta = random.choice(perguntas)

    return render(request, "jogo.html", {"pergunta": pergunta})
@login_required
def jogo(request):
    perguntas = list(Pergunta.objects.all())

    if 'pontos' not in request.session:
        request.session['pontos'] = 0

    if request.method == 'POST':
        resposta = request.POST.get('resposta')

        pergunta_id = request.session.get('pergunta_id')
        pergunta = Pergunta.objects.get(id=pergunta_id)

        if resposta == pergunta.resposta_correta:
            request.session['pontos'] += 1

    pergunta = random.choice(perguntas)
    request.session['pergunta_id'] = pergunta.id

    return render(request, "jogo.html", {"pergunta": pergunta})
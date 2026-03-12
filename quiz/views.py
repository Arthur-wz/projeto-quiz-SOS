from django.shortcuts import render
from .models import Pergunta
import random

def home(request):
    return render(request, "home.html")

def jogo(request):

    perguntas = list(Pergunta.objects.all())

    pergunta = random.choice(perguntas)

    return render(request, "jogo.html", {"pergunta": pergunta})
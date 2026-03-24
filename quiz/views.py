from django.shortcuts import render
from django.http import HttpResponse
from .models import Pergunta
import random

def home(request):
    return render(request, 'home.html')

def jogo(request):
    perguntas = list(Pergunta.objects.all())

    if not perguntas:
        return HttpResponse('Nenhuma pergunta cadastrada ainda.')

    pergunta = random.choice(perguntas)

    return render(request, 'jogo.html', {'pergunta': pergunta})
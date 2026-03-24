from django.contrib import admin
from .models import Pergunta

@admin.register(Pergunta)
class PerguntaAdmin(admin.ModelAdmin):
    list_display = ('id', 'pergunta', 'resposta_correta')
    search_fields = ('pergunta',)
    list_filter = ('resposta_correta',)
from django.contrib import admin

from .models import Partida, Pergunta, RespostaPartida


@admin.register(Pergunta)
class PerguntaAdmin(admin.ModelAdmin):
    list_display = ("pergunta_resumida", "materia", "serie", "resposta_correta")
    list_filter = ("materia", "serie")
    search_fields = ("pergunta", "materia", "serie")
    fieldsets = (
        ("Pergunta", {"fields": ("pergunta", "materia", "serie", "resposta_correta")}),
        (
            "Alternativas",
            {
                "fields": (
                    "alternativa_a",
                    "alternativa_b",
                    "alternativa_c",
                    "alternativa_d",
                    "alternativa_e",
                )
            },
        ),
    )

    @admin.display(description="Pergunta")
    def pergunta_resumida(self, obj):
        return f"{obj.pergunta[:60]}..." if len(obj.pergunta) > 60 else obj.pergunta


class RespostaPartidaInline(admin.TabularInline):
    model = RespostaPartida
    extra = 0
    can_delete = False
    fields = (
        "numero_pergunta",
        "materia",
        "serie",
        "resposta_marcada",
        "resposta_correta",
        "acertou",
        "ajuda_utilizada",
        "ajudas_utilizadas",
        "valor_pergunta",
        "pontos_recebidos",
    )
    readonly_fields = fields
    ordering = ("numero_pergunta",)


@admin.register(Partida)
class PartidaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "usuario",
        "modo",
        "status",
        "pontuacao_total",
        "acertos",
        "erros",
        "iniciada_em",
        "encerrada_em",
    )
    list_filter = ("status", "modo", "pulo_usado", "eliminar_usado", "iniciada_em")
    search_fields = ("usuario__username",)
    readonly_fields = (
        "usuario",
        "modo",
        "status",
        "total_perguntas",
        "pontuacao_total",
        "acertos",
        "erros",
        "pulo_usado",
        "eliminar_usado",
        "iniciada_em",
        "encerrada_em",
    )
    inlines = (RespostaPartidaInline,)


@admin.register(RespostaPartida)
class RespostaPartidaAdmin(admin.ModelAdmin):
    list_display = (
        "partida",
        "numero_pergunta",
        "materia",
        "serie",
        "resposta_marcada",
        "resposta_correta",
        "acertou",
        "pontos_recebidos",
    )
    list_filter = ("acertou", "ajuda_utilizada", "materia", "serie")
    search_fields = ("pergunta_texto", "partida__usuario__username")
    readonly_fields = (
        "partida",
        "pergunta",
        "numero_pergunta",
        "pergunta_texto",
        "materia",
        "serie",
        "resposta_marcada",
        "resposta_correta",
        "acertou",
        "ajuda_utilizada",
        "ajudas_utilizadas",
        "valor_pergunta",
        "pontos_recebidos",
        "respondida_em",
    )

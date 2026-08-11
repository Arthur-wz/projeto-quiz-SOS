from django.contrib import admin

from .models import (
    Partida,
    ParticipanteSalaKahoot,
    PerfilUsuario,
    Pergunta,
    RespostaPartida,
    RespostaSalaKahoot,
    SalaKahoot,
)


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


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "tema_ativo", "temas_liberados_resumo")
    search_fields = ("usuario__username", "tema_ativo")

    @admin.display(description="Temas liberados")
    def temas_liberados_resumo(self, obj):
        return ", ".join(obj.listar_temas_liberados())


class ParticipanteSalaKahootInline(admin.TabularInline):
    model = ParticipanteSalaKahoot
    extra = 0
    fields = ("usuario", "apelido", "pontuacao_total", "respostas_certas", "entrou_em")
    readonly_fields = fields


class RespostaSalaKahootInline(admin.TabularInline):
    model = RespostaSalaKahoot
    extra = 0
    fields = (
        "participante",
        "rodada",
        "pergunta",
        "resposta_marcada",
        "resposta_correta",
        "acertou",
        "pontos_recebidos",
        "respondida_em",
    )
    readonly_fields = fields


@admin.register(SalaKahoot)
class SalaKahootAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "titulo",
        "anfitriao",
        "status",
        "rodada_atual",
        "total_rodadas",
        "tempo_por_rodada",
        "criada_em",
    )
    list_filter = ("status", "tempo_por_rodada", "criada_em")
    search_fields = ("codigo", "titulo", "anfitriao__username")
    readonly_fields = ("codigo", "criada_em", "atualizada_em", "encerrada_em")
    inlines = (ParticipanteSalaKahootInline, RespostaSalaKahootInline)


@admin.register(ParticipanteSalaKahoot)
class ParticipanteSalaKahootAdmin(admin.ModelAdmin):
    list_display = ("apelido", "sala", "usuario", "pontuacao_total", "respostas_certas", "entrou_em")
    list_filter = ("sala", "entrou_em")
    search_fields = ("apelido", "usuario__username", "sala__codigo")
    readonly_fields = ("entrou_em",)


@admin.register(RespostaSalaKahoot)
class RespostaSalaKahootAdmin(admin.ModelAdmin):
    list_display = (
        "sala",
        "participante",
        "rodada",
        "resposta_marcada",
        "resposta_correta",
        "acertou",
        "pontos_recebidos",
        "respondida_em",
    )
    list_filter = ("sala", "acertou", "rodada")
    search_fields = ("participante__apelido", "participante__usuario__username", "sala__codigo")
    readonly_fields = ("respondida_em",)

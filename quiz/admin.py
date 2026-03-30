from django.contrib import admin

from .models import Pergunta


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

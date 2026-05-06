from .models import PerfilUsuario
from .themes import DEFAULT_THEME_SLUG, listar_slugs_temas_gratuitos, montar_css_tema, obter_tema


def theme_context(request):
    tema = obter_tema(DEFAULT_THEME_SLUG)

    if request.user.is_authenticated:
        perfil, _ = PerfilUsuario.objects.get_or_create(
            usuario=request.user,
            defaults={
                "tema_ativo": DEFAULT_THEME_SLUG,
                "temas_liberados": listar_slugs_temas_gratuitos(),
            },
        )
        perfil.sincronizar_temas_gratuitos()

        if perfil.tema_esta_liberado(perfil.tema_ativo):
            tema = obter_tema(perfil.tema_ativo)
        else:
            perfil.tema_ativo = DEFAULT_THEME_SLUG
            perfil.save(update_fields=["tema_ativo"])

    return {
        "tema_visual_atual": tema,
        "tema_css_inline": montar_css_tema(tema),
    }

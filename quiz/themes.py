from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeDefinition:
    slug: str
    nome: str
    descricao: str
    premium: bool
    resumo: str
    preview_cores: tuple[str, str, str]
    css_vars: dict[str, str]


THEME_CATALOG = (
    ThemeDefinition(
        slug="classico-sos",
        nome="Classico SOS",
        descricao="O visual original do projeto, com azul de programa e dourado de destaque.",
        premium=False,
        resumo="Equilibrado, legivel e pronto para qualquer partida.",
        preview_cores=("#39c2ff", "#ffdb7e", "#071833"),
        css_vars={
            "bg-deep": "#04122c",
            "bg-panel": "rgba(4, 17, 43, 0.86)",
            "bg-panel-strong": "rgba(6, 22, 54, 0.96)",
            "line-soft": "rgba(158, 201, 255, 0.22)",
            "text-main": "#f4f7ff",
            "text-soft": "#b7c6e6",
            "gold": "#f8bf4b",
            "gold-strong": "#ffdb7e",
            "blue-bright": "#39c2ff",
            "blue-deep": "#123c90",
            "red-accent": "#ff5b68",
            "green-accent": "#4dd0a0",
            "shadow-panel": "0 24px 60px rgba(0, 0, 0, 0.35)",
            "page-background": "radial-gradient(circle at top, rgba(35, 92, 183, 0.32), transparent 35%), linear-gradient(180deg, #071833 0%, #040b18 100%)",
            "page-shell-before-bg": "rgba(57, 194, 255, 0.24)",
            "page-shell-after-bg": "rgba(248, 191, 75, 0.16)",
            "hero-overlay-background": "linear-gradient(180deg, rgba(3, 10, 22, 0.32) 0%, rgba(2, 8, 20, 0.86) 100%), radial-gradient(circle at center, rgba(38, 98, 209, 0.18) 0%, transparent 40%)",
            "bg-soft": "rgba(8, 18, 38, 0.42)",
            "border-soft": "rgba(255, 255, 255, 0.12)",
            "accent": "#ffbb24",
            "input-bg": "rgba(255, 255, 255, 0.10)",
            "shadow": "0 20px 60px rgba(0, 0, 0, 0.35)",
            "auth-background": "radial-gradient(circle at top left, rgba(255, 187, 36, 0.12), transparent 30%), radial-gradient(circle at bottom right, rgba(82, 135, 255, 0.12), transparent 28%), linear-gradient(135deg, #000814, #001133 55%, #071b36)",
            "auth-overlay": "rgba(0, 0, 0, 0.18)",
        },
    ),
    ThemeDefinition(
        slug="oceano-vivo",
        nome="Oceano Vivo",
        descricao="Uma leitura mais fresca, com aqua, verde-agua e brilho mais esportivo.",
        premium=False,
        resumo="Leve e vibrante para quem quer um quiz mais energico.",
        preview_cores=("#5ce1e6", "#7ef7c9", "#032533"),
        css_vars={
            "bg-deep": "#032533",
            "bg-panel": "rgba(4, 39, 55, 0.82)",
            "bg-panel-strong": "rgba(5, 53, 74, 0.95)",
            "line-soft": "rgba(133, 240, 232, 0.2)",
            "text-main": "#ecfffb",
            "text-soft": "#9fded8",
            "gold": "#7ef7c9",
            "gold-strong": "#c6ffe7",
            "blue-bright": "#5ce1e6",
            "blue-deep": "#187e95",
            "red-accent": "#ff8364",
            "green-accent": "#9dffb0",
            "shadow-panel": "0 24px 60px rgba(1, 18, 25, 0.42)",
            "page-background": "radial-gradient(circle at top, rgba(92, 225, 230, 0.3), transparent 35%), linear-gradient(180deg, #073142 0%, #02131d 100%)",
            "page-shell-before-bg": "rgba(92, 225, 230, 0.24)",
            "page-shell-after-bg": "rgba(126, 247, 201, 0.18)",
            "hero-overlay-background": "linear-gradient(180deg, rgba(3, 21, 28, 0.26) 0%, rgba(2, 18, 24, 0.88) 100%), radial-gradient(circle at center, rgba(92, 225, 230, 0.14) 0%, transparent 40%)",
            "bg-soft": "rgba(5, 33, 46, 0.48)",
            "border-soft": "rgba(174, 255, 245, 0.16)",
            "accent": "#7ef7c9",
            "input-bg": "rgba(230, 255, 252, 0.08)",
            "shadow": "0 20px 60px rgba(1, 18, 25, 0.38)",
            "auth-background": "radial-gradient(circle at top left, rgba(126, 247, 201, 0.12), transparent 30%), radial-gradient(circle at bottom right, rgba(92, 225, 230, 0.14), transparent 28%), linear-gradient(135deg, #041a24, #083245 55%, #0a485e)",
            "auth-overlay": "rgba(1, 15, 20, 0.2)",
        },
    ),
    ThemeDefinition(
        slug="solar-premium",
        nome="Solar Premium",
        descricao="Um tema intenso, com calor de palco, vermelho rubi e reflexos dourados.",
        premium=False,
        resumo="Uma opcao mais dramatica para quem quer um visual marcante.",
        preview_cores=("#ff8966", "#ffd76d", "#2b0713"),
        css_vars={
            "bg-deep": "#2b0713",
            "bg-panel": "rgba(47, 9, 24, 0.84)",
            "bg-panel-strong": "rgba(66, 14, 32, 0.96)",
            "line-soft": "rgba(255, 183, 128, 0.2)",
            "text-main": "#fff4ef",
            "text-soft": "#efc2b1",
            "gold": "#ff9b54",
            "gold-strong": "#ffd76d",
            "blue-bright": "#ff8966",
            "blue-deep": "#b03e3e",
            "red-accent": "#ff667f",
            "green-accent": "#ffd76d",
            "shadow-panel": "0 26px 65px rgba(26, 3, 10, 0.48)",
            "page-background": "radial-gradient(circle at top, rgba(255, 137, 102, 0.28), transparent 36%), linear-gradient(180deg, #531321 0%, #18040c 100%)",
            "page-shell-before-bg": "rgba(255, 137, 102, 0.24)",
            "page-shell-after-bg": "rgba(255, 215, 109, 0.16)",
            "hero-overlay-background": "linear-gradient(180deg, rgba(29, 5, 12, 0.26) 0%, rgba(17, 3, 8, 0.88) 100%), radial-gradient(circle at center, rgba(255, 155, 84, 0.18) 0%, transparent 40%)",
            "bg-soft": "rgba(39, 10, 20, 0.5)",
            "border-soft": "rgba(255, 220, 176, 0.14)",
            "accent": "#ff9b54",
            "input-bg": "rgba(255, 244, 239, 0.08)",
            "shadow": "0 20px 60px rgba(22, 4, 10, 0.42)",
            "auth-background": "radial-gradient(circle at top left, rgba(255, 155, 84, 0.12), transparent 30%), radial-gradient(circle at bottom right, rgba(255, 102, 127, 0.14), transparent 28%), linear-gradient(135deg, #22040e, #4e1422 55%, #7b2b20)",
            "auth-overlay": "rgba(18, 3, 8, 0.2)",
        },
    ),
)

DEFAULT_THEME_SLUG = "classico-sos"
THEMES_BY_SLUG = {tema.slug: tema for tema in THEME_CATALOG}


def listar_temas():
    return list(THEME_CATALOG)


def listar_slugs_temas_gratuitos():
    return [tema.slug for tema in THEME_CATALOG if not tema.premium]


def obter_tema_por_slug(slug):
    return THEMES_BY_SLUG.get(slug)


def obter_tema(slug=None):
    return obter_tema_por_slug(slug) or THEMES_BY_SLUG[DEFAULT_THEME_SLUG]


def montar_css_tema(tema):
    linhas = [":root {"]
    for nome, valor in tema.css_vars.items():
        linhas.append(f"  --{nome}: {valor};")
    linhas.append("}")
    return "\n".join(linhas)

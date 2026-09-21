import uuid

from django.conf import settings
from django.db import models

from .themes import DEFAULT_THEME_SLUG, listar_slugs_temas_gratuitos, obter_tema_por_slug


def gerar_external_reference():
    return str(uuid.uuid4())


class Pergunta(models.Model):
    OPCOES_RESPOSTA = [(letra, letra) for letra in "ABCDE"]

    pergunta = models.TextField()
    alternativa_a = models.CharField(max_length=200)
    alternativa_b = models.CharField(max_length=200)
    alternativa_c = models.CharField(max_length=200)
    alternativa_d = models.CharField(max_length=200)
    alternativa_e = models.CharField(max_length=200)
    resposta_correta = models.CharField(max_length=1, choices=OPCOES_RESPOSTA)
    serie = models.CharField(max_length=50)
    materia = models.CharField(max_length=50)

    def __str__(self):
        return self.pergunta

    def alternativas(self):
        return [
            ("A", self.alternativa_a),
            ("B", self.alternativa_b),
            ("C", self.alternativa_c),
            ("D", self.alternativa_d),
            ("E", self.alternativa_e),
        ]


class Partida(models.Model):
    STATUS_EM_ANDAMENTO = "em_andamento"
    STATUS_FINALIZADA = "finalizada"
    STATUS_ABANDONADA = "abandonada"
    STATUS_CHOICES = [
        (STATUS_EM_ANDAMENTO, "Em andamento"),
        (STATUS_FINALIZADA, "Finalizada"),
        (STATUS_ABANDONADA, "Abandonada"),
    ]

    MODO_SOLO = "solo"
    MODO_CHOICES = [
        (MODO_SOLO, "Solo"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="partidas_quiz",
    )
    modo = models.CharField(max_length=20, choices=MODO_CHOICES, default=MODO_SOLO)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_EM_ANDAMENTO)
    total_perguntas = models.PositiveSmallIntegerField(default=20)
    pontuacao_total = models.PositiveIntegerField(default=0)
    acertos = models.PositiveSmallIntegerField(default=0)
    erros = models.PositiveSmallIntegerField(default=0)
    pulo_usado = models.BooleanField(default=False)
    eliminar_usado = models.BooleanField(default=False)
    iniciada_em = models.DateTimeField(auto_now_add=True)
    encerrada_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-iniciada_em"]

    def __str__(self):
        dono = self.usuario.username if self.usuario else "anonimo"
        return f"Partida #{self.pk} - {dono} - {self.status}"


class RespostaPartida(models.Model):
    OPCOES_RESPOSTA = Pergunta.OPCOES_RESPOSTA

    partida = models.ForeignKey(Partida, on_delete=models.CASCADE, related_name="respostas")
    pergunta = models.ForeignKey(
        Pergunta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="respostas_partida",
    )
    numero_pergunta = models.PositiveSmallIntegerField()
    pergunta_texto = models.TextField()
    materia = models.CharField(max_length=50)
    serie = models.CharField(max_length=50)
    resposta_marcada = models.CharField(max_length=1, choices=OPCOES_RESPOSTA)
    resposta_correta = models.CharField(max_length=1, choices=OPCOES_RESPOSTA)
    acertou = models.BooleanField(default=False)
    ajuda_utilizada = models.BooleanField(default=False)
    ajudas_utilizadas = models.CharField(max_length=50, blank=True)
    valor_pergunta = models.PositiveSmallIntegerField(default=10)
    pontos_recebidos = models.PositiveSmallIntegerField(default=0)
    respondida_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["numero_pergunta", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["partida", "numero_pergunta"],
                name="unique_resposta_por_ordem_na_partida",
            )
        ]

    def __str__(self):
        return f"Resposta #{self.numero_pergunta} da partida {self.partida_id}"


class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_quiz",
    )
    tema_ativo = models.CharField(max_length=50, default=DEFAULT_THEME_SLUG)
    temas_liberados = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfis de usuario"

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

    def listar_temas_liberados(self):
        slugs = list(self.temas_liberados or [])

        for slug in listar_slugs_temas_gratuitos():
            if slug not in slugs:
                slugs.append(slug)

        validos = []
        for slug in slugs:
            if obter_tema_por_slug(slug) and slug not in validos:
                validos.append(slug)

        return validos

    def sincronizar_temas_gratuitos(self):
        temas_liberados = self.listar_temas_liberados()
        alterado = temas_liberados != (self.temas_liberados or [])

        if self.tema_ativo not in temas_liberados:
            self.tema_ativo = DEFAULT_THEME_SLUG
            alterado = True

        if alterado:
            self.temas_liberados = temas_liberados
            self.save(update_fields=["tema_ativo", "temas_liberados"])

    def tema_esta_liberado(self, slug):
        return slug in self.listar_temas_liberados()

    def liberar_tema(self, slug):
        if not obter_tema_por_slug(slug):
            return False

        temas_liberados = self.listar_temas_liberados()
        if slug not in temas_liberados:
            temas_liberados.append(slug)
            self.temas_liberados = temas_liberados
            self.save(update_fields=["temas_liberados"])

        return True

    def ativar_tema(self, slug):
        if not self.tema_esta_liberado(slug):
            return False

        if self.tema_ativo != slug:
            self.tema_ativo = slug
            self.save(update_fields=["tema_ativo"])

        return True


class SalaKahoot(models.Model):
    STATUS_AGUARDANDO = "aguardando"
    STATUS_EM_ANDAMENTO = "em_andamento"
    STATUS_FINALIZADA = "finalizada"
    STATUS_CHOICES = [
        (STATUS_AGUARDANDO, "Aguardando"),
        (STATUS_EM_ANDAMENTO, "Em andamento"),
        (STATUS_FINALIZADA, "Finalizada"),
    ]

    anfitriao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="salas_kahoot_criadas",
    )
    codigo = models.CharField(max_length=8, unique=True)
    titulo = models.CharField(max_length=120, default="Sala Kahoot")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_AGUARDANDO)
    total_rodadas = models.PositiveSmallIntegerField(default=10)
    rodada_atual = models.PositiveSmallIntegerField(default=0)
    tempo_por_rodada = models.PositiveSmallIntegerField(default=20)
    pergunta_atual = models.ForeignKey(
        Pergunta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="salas_kahoot_ativas",
    )
    pergunta_personalizada_atual = models.ForeignKey(
        "PerguntaSalaKahoot",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="salas_kahoot_ativas",
    )
    pergunta_iniciada_em = models.DateTimeField(null=True, blank=True)
    perguntas_sorteadas = models.JSONField(default=list, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)
    encerrada_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-criada_em"]
        verbose_name = "Sala Kahoot"
        verbose_name_plural = "Salas Kahoot"

    def __str__(self):
        return f"{self.codigo} - {self.titulo}"

    def usa_perguntas_personalizadas(self):
        return self.perguntas_personalizadas.exists()


class ParticipanteSalaKahoot(models.Model):
    sala = models.ForeignKey(SalaKahoot, on_delete=models.CASCADE, related_name="participantes")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="participacoes_kahoot",
    )
    apelido = models.CharField(max_length=80)
    pontuacao_total = models.PositiveIntegerField(default=0)
    respostas_certas = models.PositiveSmallIntegerField(default=0)
    entrou_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-pontuacao_total", "-respostas_certas", "apelido"]
        constraints = [
            models.UniqueConstraint(fields=["sala", "usuario"], name="unique_usuario_por_sala_kahoot")
        ]
        verbose_name = "Participante da sala Kahoot"
        verbose_name_plural = "Participantes das salas Kahoot"

    def __str__(self):
        return f"{self.apelido} em {self.sala.codigo}"


class RespostaSalaKahoot(models.Model):
    participante = models.ForeignKey(
        ParticipanteSalaKahoot,
        on_delete=models.CASCADE,
        related_name="respostas",
    )
    sala = models.ForeignKey(SalaKahoot, on_delete=models.CASCADE, related_name="respostas")
    pergunta = models.ForeignKey(
        Pergunta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="respostas_kahoot",
    )
    rodada = models.PositiveSmallIntegerField()
    resposta_marcada = models.CharField(max_length=1, choices=Pergunta.OPCOES_RESPOSTA)
    resposta_correta = models.CharField(max_length=1, choices=Pergunta.OPCOES_RESPOSTA)
    acertou = models.BooleanField(default=False)
    pontos_recebidos = models.PositiveIntegerField(default=0)
    respondida_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["rodada", "respondida_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["participante", "rodada"],
                name="unique_resposta_por_participante_e_rodada_kahoot",
            )
        ]
        verbose_name = "Resposta da sala Kahoot"
        verbose_name_plural = "Respostas das salas Kahoot"

    def __str__(self):
        return f"Rodada {self.rodada} - {self.participante.apelido}"


class PerguntaSalaKahoot(models.Model):
    OPCOES_RESPOSTA = Pergunta.OPCOES_RESPOSTA

    sala = models.ForeignKey(
        SalaKahoot,
        on_delete=models.CASCADE,
        related_name="perguntas_personalizadas",
    )
    pergunta = models.TextField()
    alternativa_a = models.CharField(max_length=200)
    alternativa_b = models.CharField(max_length=200)
    alternativa_c = models.CharField(max_length=200)
    alternativa_d = models.CharField(max_length=200)
    alternativa_e = models.CharField(max_length=200)
    resposta_correta = models.CharField(max_length=1, choices=OPCOES_RESPOSTA)
    serie = models.CharField(max_length=50, default="Personalizada")
    materia = models.CharField(max_length=50, default="Sala")
    ordem = models.PositiveSmallIntegerField(default=1)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ordem", "id"]
        verbose_name = "Pergunta personalizada da sala Kahoot"
        verbose_name_plural = "Perguntas personalizadas das salas Kahoot"

    def __str__(self):
        return f"{self.sala.codigo} - {self.pergunta[:60]}"

    def alternativas(self):
        return [
            ("A", self.alternativa_a),
            ("B", self.alternativa_b),
            ("C", self.alternativa_c),
            ("D", self.alternativa_d),
            ("E", self.alternativa_e),
        ]

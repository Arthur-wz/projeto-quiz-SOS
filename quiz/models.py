from django.conf import settings
from django.db import models


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

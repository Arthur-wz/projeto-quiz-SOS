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

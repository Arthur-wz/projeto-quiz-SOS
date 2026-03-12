from django.db import models

class Pergunta(models.Model):
    pergunta = models.TextField()

    alternativa_a = models.CharField(max_length=200)
    alternativa_b = models.CharField(max_length=200)
    alternativa_c = models.CharField(max_length=200)
    alternativa_d = models.CharField(max_length=200)

    resposta_correta = models.CharField(max_length=1)

    serie = models.CharField(max_length=50)
    materia = models.CharField(max_length=50)

    def __str__(self):
        return self.pergunta

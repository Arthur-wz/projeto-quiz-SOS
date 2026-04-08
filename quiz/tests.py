from django.test import TestCase
from django.urls import reverse

from .models import Partida, Pergunta, RespostaPartida
from .views import QUIZ_SESSION_KEY, TOTAL_PERGUNTAS


class QuizFlowTests(TestCase):
    def criar_perguntas(self, total=TOTAL_PERGUNTAS):
        for indice in range(total):
            Pergunta.objects.create(
                pergunta=f"Pergunta {indice + 1}?",
                alternativa_a="Opcao A",
                alternativa_b="Opcao B",
                alternativa_c="Opcao C",
                alternativa_d="Opcao D",
                alternativa_e="Opcao E",
                resposta_correta="A",
                serie="1 ano",
                materia="Matematica",
            )

    def iniciar_partida(self):
        return self.client.post(reverse("iniciar_jogo"))

    def test_nao_inicia_partida_sem_20_perguntas(self):
        self.criar_perguntas(total=19)

        response = self.iniciar_partida()

        self.assertRedirects(response, reverse("home"))
        self.assertNotIn(QUIZ_SESSION_KEY, self.client.session)

    def test_resposta_correta_soma_10_pontos(self):
        self.criar_perguntas()
        self.iniciar_partida()

        response = self.client.post(reverse("jogo"), {"action": "answer", "answer": "A"})

        self.assertRedirects(response, reverse("jogo"))
        session = self.client.session[QUIZ_SESSION_KEY]
        self.assertEqual(session["score"], 10)
        self.assertEqual(session["answered_count"], 1)
        self.assertEqual(session["correct_count"], 1)
        partida = Partida.objects.get(pk=session["partida_id"])
        resposta = RespostaPartida.objects.get(partida=partida, numero_pergunta=1)
        self.assertEqual(partida.pontuacao_total, 10)
        self.assertEqual(partida.acertos, 1)
        self.assertTrue(resposta.acertou)
        self.assertEqual(resposta.pontos_recebidos, 10)

    def test_eliminar_duas_marca_pergunta_com_meia_pontuacao(self):
        self.criar_perguntas()
        self.iniciar_partida()

        response = self.client.post(reverse("jogo"), {"action": "eliminate"})

        self.assertRedirects(response, reverse("jogo"))
        session = self.client.session[QUIZ_SESSION_KEY]
        self.assertTrue(session["used_eliminate"])
        self.assertTrue(session["current_is_halved"])
        self.assertEqual(len(session["eliminated_options"]), 2)

        resposta = self.client.post(reverse("jogo"), {"action": "answer", "answer": "A"})

        self.assertRedirects(resposta, reverse("jogo"))
        session = self.client.session[QUIZ_SESSION_KEY]
        self.assertEqual(session["score"], 5)
        self.assertEqual(session["answered_count"], 1)
        partida = Partida.objects.get(pk=session["partida_id"])
        resposta_db = RespostaPartida.objects.get(partida=partida, numero_pergunta=1)
        self.assertTrue(resposta_db.ajuda_utilizada)
        self.assertEqual(resposta_db.ajudas_utilizadas, "eliminate")
        self.assertEqual(resposta_db.valor_pergunta, 5)

    def test_pular_rotaciona_fila_e_marca_meia_pontuacao(self):
        self.criar_perguntas()
        self.iniciar_partida()

        session = self.client.session[QUIZ_SESSION_KEY]
        primeira = session["queue"][0]
        segunda = session["queue"][1]

        response = self.client.post(reverse("jogo"), {"action": "skip"})

        self.assertRedirects(response, reverse("jogo"))
        session = self.client.session[QUIZ_SESSION_KEY]
        self.assertTrue(session["used_skip"])
        self.assertTrue(session["current_is_halved"])
        self.assertEqual(session["queue"][0], segunda)
        self.assertEqual(session["queue"][-1], primeira)
        partida = Partida.objects.get(pk=session["partida_id"])
        self.assertTrue(partida.pulo_usado)

    def test_partida_completa_redireciona_para_resultado(self):
        self.criar_perguntas()
        self.iniciar_partida()

        for _ in range(TOTAL_PERGUNTAS):
            response = self.client.post(reverse("jogo"), {"action": "answer", "answer": "A"})

        self.assertRedirects(response, reverse("resultado"))
        session = self.client.session[QUIZ_SESSION_KEY]
        self.assertEqual(session["score"], TOTAL_PERGUNTAS * 10)
        self.assertEqual(session["answered_count"], TOTAL_PERGUNTAS)
        self.assertEqual(session["correct_count"], TOTAL_PERGUNTAS)
        partida = Partida.objects.get(pk=session["partida_id"])
        self.assertEqual(partida.status, Partida.STATUS_FINALIZADA)
        self.assertEqual(partida.pontuacao_total, TOTAL_PERGUNTAS * 10)
        self.assertEqual(partida.acertos, TOTAL_PERGUNTAS)
        self.assertEqual(partida.erros, 0)
        self.assertEqual(partida.respostas.count(), TOTAL_PERGUNTAS)

    def test_nova_partida_abandona_partida_anterior(self):
        self.criar_perguntas(total=TOTAL_PERGUNTAS + 5)
        self.iniciar_partida()

        primeira_partida_id = self.client.session[QUIZ_SESSION_KEY]["partida_id"]
        response = self.iniciar_partida()

        self.assertRedirects(response, reverse("jogo"))
        primeira_partida = Partida.objects.get(pk=primeira_partida_id)
        self.assertEqual(primeira_partida.status, Partida.STATUS_ABANDONADA)

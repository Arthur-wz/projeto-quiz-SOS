from datetime import datetime, time, timedelta

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    Partida,
    ParticipanteSalaKahoot,
    PerfilUsuario,
    Pergunta,
    PerguntaSalaKahoot,
    RespostaPartida,
    SalaKahoot,
)
from .themes import DEFAULT_THEME_SLUG
from .views import QUIZ_RECENT_IDS_SESSION_KEY, QUIZ_SESSION_KEY, TOTAL_PERGUNTAS


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
        return self.client.post(reverse("iniciar_partida"))

    def criar_partida_finalizada(self, *, usuario, pontuacao, acertos, encerrada_em):
        partida = Partida.objects.create(
            usuario=usuario,
            status=Partida.STATUS_FINALIZADA,
            total_perguntas=TOTAL_PERGUNTAS,
            pontuacao_total=pontuacao,
            acertos=acertos,
            erros=TOTAL_PERGUNTAS - acertos,
        )
        Partida.objects.filter(pk=partida.pk).update(encerrada_em=encerrada_em)
        partida.refresh_from_db()
        return partida

    def test_nao_inicia_partida_sem_20_perguntas(self):
        self.criar_perguntas(total=19)

        response = self.iniciar_partida()

        self.assertRedirects(response, reverse("home"))
        self.assertNotIn(QUIZ_SESSION_KEY, self.client.session)
        self.assertEqual(Partida.objects.count(), 0)

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

    def test_mensagem_de_acerto_com_ajuda_mostra_5_pontos(self):
        self.criar_perguntas()
        self.iniciar_partida()

        self.client.post(reverse("jogo"), {"action": "eliminate"})
        response = self.client.post(
            reverse("jogo"),
            {"action": "answer", "answer": "A"},
            follow=True,
        )

        self.assertContains(response, "Resposta certa com ajuda! +5 pontos.")

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

    def test_nova_partida_prioriza_perguntas_ainda_nao_usadas_recentemente(self):
        self.criar_perguntas(total=TOTAL_PERGUNTAS + 5)
        perguntas = list(Pergunta.objects.values("id", "pergunta").order_by("id"))
        recentes = [item["pergunta"].strip().casefold() for item in perguntas[:TOTAL_PERGUNTAS]]
        restantes = {item["id"] for item in perguntas[TOTAL_PERGUNTAS:]}
        session = self.client.session
        session[QUIZ_RECENT_IDS_SESSION_KEY] = recentes
        session.save()

        response = self.iniciar_partida()

        self.assertRedirects(response, reverse("jogo"))
        fila = self.client.session[QUIZ_SESSION_KEY]["queue"]
        self.assertEqual(set(fila[:5]), restantes)

    def test_partida_nao_repite_texto_quando_existem_ids_duplicados_da_mesma_pergunta(self):
        for indice in range(TOTAL_PERGUNTAS):
            texto = f"Pergunta unica {indice + 1}?"
            for repeticao in range(3):
                Pergunta.objects.create(
                    pergunta=texto,
                    alternativa_a=f"Opcao A {repeticao}",
                    alternativa_b=f"Opcao B {repeticao}",
                    alternativa_c=f"Opcao C {repeticao}",
                    alternativa_d=f"Opcao D {repeticao}",
                    alternativa_e=f"Opcao E {repeticao}",
                    resposta_correta="A",
                    serie="1 ano",
                    materia="Matematica",
                )

        response = self.iniciar_partida()

        self.assertRedirects(response, reverse("jogo"))
        fila = self.client.session[QUIZ_SESSION_KEY]["queue"]
        textos = list(Pergunta.objects.filter(id__in=fila).values_list("pergunta", flat=True))
        self.assertEqual(len(textos), TOTAL_PERGUNTAS)
        self.assertEqual(len(set(textos)), TOTAL_PERGUNTAS)

    def test_ranking_agrega_pontos_semanal_e_mensal(self):
        agora_local = timezone.localtime()
        inicio_semana = agora_local.date() - timedelta(days=agora_local.weekday())
        inicio_mes = agora_local.date().replace(day=1)
        fuso = timezone.get_current_timezone()

        def aware(data):
            return timezone.make_aware(datetime.combine(data, time(hour=10)), fuso)

        alice = User.objects.create_user(username="alice", password="senha123")
        bruno = User.objects.create_user(username="bruno", password="senha123")
        carla = User.objects.create_user(username="carla", password="senha123")

        self.criar_partida_finalizada(
            usuario=alice,
            pontuacao=80,
            acertos=8,
            encerrada_em=aware(inicio_semana),
        )
        self.criar_partida_finalizada(
            usuario=alice,
            pontuacao=30,
            acertos=3,
            encerrada_em=aware(inicio_semana + timedelta(days=1)),
        )
        self.criar_partida_finalizada(
            usuario=bruno,
            pontuacao=90,
            acertos=9,
            encerrada_em=aware(inicio_mes),
        )
        self.criar_partida_finalizada(
            usuario=carla,
            pontuacao=120,
            acertos=12,
            encerrada_em=aware(inicio_mes - timedelta(days=1)),
        )

        response = self.client.get(reverse("ranking"))

        self.assertEqual(response.status_code, 200)

        ranking_semanal = response.context["ranking_semanal"]
        ranking_mensal = response.context["ranking_mensal"]

        self.assertEqual([item["usuario__username"] for item in ranking_semanal], ["alice"])
        self.assertEqual(ranking_semanal[0]["total_pontos"], 110)
        self.assertEqual(ranking_semanal[0]["partidas_jogadas"], 2)

        self.assertEqual(
            [item["usuario__username"] for item in ranking_mensal],
            ["alice", "bruno"],
        )
        self.assertEqual(ranking_mensal[0]["total_pontos"], 110)
        self.assertEqual(ranking_mensal[1]["total_pontos"], 90)

    def test_ranking_ignora_partidas_anonimas_ou_nao_finalizadas(self):
        agora = timezone.now()
        usuario = User.objects.create_user(username="ranking", password="senha123")

        self.criar_partida_finalizada(
            usuario=usuario,
            pontuacao=50,
            acertos=5,
            encerrada_em=agora,
        )
        self.criar_partida_finalizada(
            usuario=None,
            pontuacao=99,
            acertos=9,
            encerrada_em=agora,
        )
        Partida.objects.create(
            usuario=usuario,
            status=Partida.STATUS_EM_ANDAMENTO,
            total_perguntas=TOTAL_PERGUNTAS,
            pontuacao_total=200,
            acertos=20,
            erros=0,
        )

        response = self.client.get(reverse("ranking"))
        ranking_semanal = response.context["ranking_semanal"]

        self.assertEqual(len(ranking_semanal), 1)
        self.assertEqual(ranking_semanal[0]["usuario__username"], "ranking")
        self.assertEqual(ranking_semanal[0]["total_pontos"], 50)

    def test_home_mostra_tema_padrao_para_visitante(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Classico SOS")
        self.assertContains(response, "Login")
        self.assertContains(response, "Criar usuario")

    def test_home_esconde_login_e_criar_usuario_para_usuario_logado(self):
        usuario = User.objects.create_user(username="visivel", password="senha123")
        self.client.force_login(usuario)

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Conta conectada")
        self.assertContains(response, "visivel")
        self.assertNotContains(response, 'href="/login/"')
        self.assertNotContains(response, 'href="/criar-usuario/"')

    def test_login_com_sucesso_mostra_confirmacao_na_home(self):
        User.objects.create_user(username="arthurx", password="senha123")

        response = self.client.post(
            reverse("login"),
            {"username": "arthurx", "password": "senha123"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Login efetuado com sucesso")
        self.assertContains(response, "arthurx")

    def test_temas_libera_catalogo_gratuito_para_usuario_logado(self):
        usuario = User.objects.create_user(username="temauser", password="senha123")
        self.client.force_login(usuario)

        response = self.client.get(reverse("temas"))

        self.assertEqual(response.status_code, 200)
        perfil = PerfilUsuario.objects.get(usuario=usuario)
        self.assertEqual(perfil.tema_ativo, DEFAULT_THEME_SLUG)
        self.assertIn("classico-sos", perfil.temas_liberados)
        self.assertIn("oceano-vivo", perfil.temas_liberados)
        self.assertIn("solar-premium", perfil.temas_liberados)
        self.assertContains(response, "Oceano Vivo")
        self.assertContains(response, "Solar Premium")

    def test_usuario_pode_ativar_tema_gratuito(self):
        usuario = User.objects.create_user(username="temaok", password="senha123")
        self.client.force_login(usuario)

        response = self.client.post(reverse("ativar_tema", args=["oceano-vivo"]), follow=True)

        self.assertEqual(response.status_code, 200)
        perfil = PerfilUsuario.objects.get(usuario=usuario)
        self.assertEqual(perfil.tema_ativo, "oceano-vivo")
        self.assertContains(response, "Tema Oceano Vivo ativado com sucesso.")

    def test_usuario_pode_ativar_solar_premium_com_catalogo_liberado(self):
        usuario = User.objects.create_user(username="temasolar", password="senha123")
        self.client.force_login(usuario)

        response = self.client.post(reverse("ativar_tema", args=["solar-premium"]), follow=True)

        self.assertEqual(response.status_code, 200)
        perfil = PerfilUsuario.objects.get(usuario=usuario)
        self.assertEqual(perfil.tema_ativo, "solar-premium")
        self.assertContains(response, "Tema Solar Premium ativado com sucesso.")

    def test_login_indica_google_nao_configurado(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GOOGLE_CLIENT_ID")
        self.assertNotContains(response, "Entrar com Google")

    @override_settings(
        SOCIALACCOUNT_PROVIDERS={
            "google": {
                "APP": {
                    "client_id": "teste-client-id",
                    "secret": "teste-secret",
                    "key": "",
                },
                "SCOPE": ["profile", "email"],
                "AUTH_PARAMS": {"prompt": "select_account"},
            }
        }
    )
    def test_login_exibe_botao_google_quando_configurado(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Entrar com Google")
        self.assertContains(response, reverse("google_login"))

    @override_settings(
        SOCIALACCOUNT_PROVIDERS={
            "google": {
                "APP": {
                    "client_id": "teste-client-id",
                    "secret": "teste-secret",
                    "key": "",
                },
                "SCOPE": ["profile", "email"],
                "AUTH_PARAMS": {"prompt": "select_account"},
            }
        }
    )
    def test_google_login_redireciona_para_oauth_quando_configurado(self):
        response = self.client.post(reverse("google_login"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("accounts.google.com", response["Location"])

    def test_kahoot_exige_login(self):
        response = self.client.get(reverse("kahoot_inicio"), follow=True)

        self.assertRedirects(response, reverse("login"))
        self.assertContains(response, "Faca login para acessar o modo Kahoot.")

    def test_usuario_logado_pode_criar_sala_kahoot(self):
        self.criar_perguntas()
        usuario = User.objects.create_user(username="host", password="senha123")
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("criar_sala_kahoot"),
            {"titulo": "Historia local", "total_rodadas": 8, "tempo_por_rodada": 25},
        )

        sala = SalaKahoot.objects.get(anfitriao=usuario)
        self.assertRedirects(response, reverse("sala_kahoot", args=[sala.codigo]))
        self.assertEqual(sala.titulo, "Historia local")
        self.assertEqual(sala.total_rodadas, 8)
        self.assertEqual(sala.tempo_por_rodada, 25)
        self.assertTrue(ParticipanteSalaKahoot.objects.filter(sala=sala, usuario=usuario).exists())

    def test_usuario_logado_pode_entrar_em_sala_kahoot(self):
        self.criar_perguntas()
        anfitriao = User.objects.create_user(username="anfitriao", password="senha123")
        jogador = User.objects.create_user(username="jogador", password="senha123")
        sala = SalaKahoot.objects.create(
            anfitriao=anfitriao,
            codigo="ABC123",
            titulo="Sala local",
            total_rodadas=5,
            tempo_por_rodada=20,
        )

        self.client.force_login(jogador)
        response = self.client.post(reverse("entrar_sala_kahoot"), {"codigo": "abc123"})

        self.assertRedirects(response, reverse("sala_kahoot", args=[sala.codigo]))
        self.assertTrue(ParticipanteSalaKahoot.objects.filter(sala=sala, usuario=jogador).exists())

    def test_anfitriao_pode_iniciar_sala_kahoot(self):
        self.criar_perguntas()
        anfitriao = User.objects.create_user(username="host2", password="senha123")
        sala = SalaKahoot.objects.create(
            anfitriao=anfitriao,
            codigo="ZXCV12",
            titulo="Sala ativa",
            total_rodadas=5,
            tempo_por_rodada=20,
        )
        ParticipanteSalaKahoot.objects.create(sala=sala, usuario=anfitriao, apelido="host2")

        self.client.force_login(anfitriao)
        response = self.client.post(reverse("iniciar_sala_kahoot", args=[sala.codigo]))

        self.assertRedirects(response, reverse("sala_kahoot", args=[sala.codigo]))
        sala.refresh_from_db()
        self.assertEqual(sala.status, SalaKahoot.STATUS_EM_ANDAMENTO)
        self.assertEqual(sala.rodada_atual, 1)
        self.assertIsNotNone(sala.pergunta_atual)
        self.assertEqual(len(sala.perguntas_sorteadas), 5)

    def test_jogador_responde_sala_kahoot_e_recebe_pontos(self):
        self.criar_perguntas()
        anfitriao = User.objects.create_user(username="host3", password="senha123")
        jogador = User.objects.create_user(username="jogador3", password="senha123")
        pergunta = Pergunta.objects.first()
        sala = SalaKahoot.objects.create(
            anfitriao=anfitriao,
            codigo="QWE789",
            titulo="Sala pontuacao",
            status=SalaKahoot.STATUS_EM_ANDAMENTO,
            total_rodadas=5,
            rodada_atual=1,
            tempo_por_rodada=20,
            pergunta_atual=pergunta,
            pergunta_iniciada_em=timezone.now(),
            perguntas_sorteadas=[pergunta.id],
        )
        ParticipanteSalaKahoot.objects.create(sala=sala, usuario=anfitriao, apelido="host3")
        participante = ParticipanteSalaKahoot.objects.create(sala=sala, usuario=jogador, apelido="jogador3")

        self.client.force_login(jogador)
        response = self.client.post(
            reverse("responder_kahoot", args=[sala.codigo]),
            {"answer": pergunta.resposta_correta},
        )

        self.assertRedirects(response, reverse("sala_kahoot", args=[sala.codigo]))
        participante.refresh_from_db()
        self.assertGreater(participante.pontuacao_total, 0)
        self.assertEqual(participante.respostas_certas, 1)

    def test_anfitriao_pode_editar_sala_kahoot(self):
        self.criar_perguntas()
        anfitriao = User.objects.create_user(username="edithost", password="senha123")
        sala = SalaKahoot.objects.create(
            anfitriao=anfitriao,
            codigo="EDIT12",
            titulo="Sala antiga",
            total_rodadas=5,
            tempo_por_rodada=20,
        )
        ParticipanteSalaKahoot.objects.create(sala=sala, usuario=anfitriao, apelido="edithost")

        self.client.force_login(anfitriao)
        response = self.client.post(
            reverse("editar_sala_kahoot", args=[sala.codigo]),
            {"titulo": "Sala nova", "total_rodadas": 4, "tempo_por_rodada": 30},
        )

        self.assertRedirects(response, reverse("sala_kahoot", args=[sala.codigo]))
        sala.refresh_from_db()
        self.assertEqual(sala.titulo, "Sala nova")
        self.assertEqual(sala.total_rodadas, 4)
        self.assertEqual(sala.tempo_por_rodada, 30)

    def test_anfitriao_pode_criar_pergunta_personalizada(self):
        anfitriao = User.objects.create_user(username="perghost", password="senha123")
        sala = SalaKahoot.objects.create(
            anfitriao=anfitriao,
            codigo="PER123",
            titulo="Sala personalizada",
            total_rodadas=1,
            tempo_por_rodada=20,
        )

        self.client.force_login(anfitriao)
        response = self.client.post(
            reverse("criar_pergunta_personalizada_kahoot", args=[sala.codigo]),
            {
                "pergunta": "Qual a cor do ceu?",
                "alternativa_a": "Azul",
                "alternativa_b": "Verde",
                "alternativa_c": "Preto",
                "alternativa_d": "Branco",
                "alternativa_e": "Rosa",
                "resposta_correta": "A",
                "materia": "Ciencias",
                "serie": "5 ano",
            },
        )

        self.assertRedirects(response, reverse("gerenciar_perguntas_kahoot", args=[sala.codigo]))
        pergunta = PerguntaSalaKahoot.objects.get(sala=sala)
        self.assertEqual(pergunta.resposta_correta, "A")
        self.assertEqual(pergunta.materia, "Ciencias")

    def test_sala_usa_pergunta_personalizada_ao_iniciar(self):
        anfitriao = User.objects.create_user(username="customhost", password="senha123")
        sala = SalaKahoot.objects.create(
            anfitriao=anfitriao,
            codigo="CUS123",
            titulo="Sala custom",
            total_rodadas=1,
            tempo_por_rodada=20,
        )
        ParticipanteSalaKahoot.objects.create(sala=sala, usuario=anfitriao, apelido="customhost")
        PerguntaSalaKahoot.objects.create(
            sala=sala,
            pergunta="Pergunta da sala?",
            alternativa_a="A",
            alternativa_b="B",
            alternativa_c="C",
            alternativa_d="D",
            alternativa_e="E",
            resposta_correta="B",
            materia="Livre",
            serie="Livre",
            ordem=1,
        )

        self.client.force_login(anfitriao)
        response = self.client.post(reverse("iniciar_sala_kahoot", args=[sala.codigo]))

        self.assertRedirects(response, reverse("sala_kahoot", args=[sala.codigo]))
        sala.refresh_from_db()
        self.assertEqual(sala.status, SalaKahoot.STATUS_EM_ANDAMENTO)
        self.assertIsNotNone(sala.pergunta_personalizada_atual)
        self.assertIsNone(sala.pergunta_atual)

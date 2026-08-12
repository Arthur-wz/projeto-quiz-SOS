import io
import json
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = "Cria backups das perguntas e dos demais dados em UTF-8."

    def handle(self, *args, **options):
        pasta_backups = Path(settings.BASE_DIR) / "backups"
        pasta_backups.mkdir(parents=True, exist_ok=True)

        arquivo_perguntas = pasta_backups / "perguntas.json"
        arquivo_dados = pasta_backups / "dados_limpos.json"

        self.stdout.write("Criando backup das perguntas...")

        # ==========================================================
        # PERGUNTAS
        # ==========================================================
        buffer_perguntas = io.StringIO()

        call_command(
            "dumpdata",
            "quiz.Pergunta",
            indent=2,
            stdout=buffer_perguntas,
        )

        dados_perguntas = json.loads(buffer_perguntas.getvalue())

        with open(
            arquivo_perguntas,
            "w",
            encoding="utf-8",
            newline="\n",
        ) as arquivo:
            json.dump(
                dados_perguntas,
                arquivo,
                ensure_ascii=False,
                indent=2,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Perguntas salvas: {arquivo_perguntas}"
            )
        )

        # ==========================================================
        # OUTROS DADOS
        # ==========================================================
        self.stdout.write("Criando backup dos demais dados...")

        buffer_dados = io.StringIO()

        call_command(
            "dumpdata",
            exclude=[
                "quiz.pergunta",
                "contenttypes.contenttype",
                "auth.permission",
                "admin.logentry",
                "sessions.session",
            ],
            indent=2,
            stdout=buffer_dados,
        )

        dados = json.loads(buffer_dados.getvalue())

        with open(
            arquivo_dados,
            "w",
            encoding="utf-8",
            newline="\n",
        ) as arquivo:
            json.dump(
                dados,
                arquivo,
                ensure_ascii=False,
                indent=2,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Dados salvos: {arquivo_dados}"
            )
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Backup concluído! "
                f"{len(dados_perguntas)} perguntas e "
                f"{len(dados)} outros registros."
            )
        )
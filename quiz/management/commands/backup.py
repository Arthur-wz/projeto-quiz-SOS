from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Cria um backup JSON do banco em BASE_DIR/backups."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            help="Caminho opcional do arquivo de backup.",
        )

    def handle(self, *args, **options):
        backup_dir = Path(settings.BASE_DIR) / "backups"
        backup_dir.mkdir(exist_ok=True)

        output = options.get("output")
        if output:
            backup_path = Path(output)
            if not backup_path.is_absolute():
                backup_path = Path(settings.BASE_DIR) / backup_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            backup_path = backup_dir / f"backup_{timestamp}.json"

        try:
            call_command("dumpdata", indent=2, output=str(backup_path))
        except Exception as exc:
            raise CommandError(f"Erro ao criar backup: {exc}") from exc

        self.stdout.write(self.style.SUCCESS(f"Backup criado: {backup_path}"))

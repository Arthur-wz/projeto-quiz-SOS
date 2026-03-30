from django.db import migrations, models


def normalizar_respostas(apps, schema_editor):
    Pergunta = apps.get_model("quiz", "Pergunta")
    for pergunta in Pergunta.objects.all():
        resposta = (pergunta.resposta_correta or "").upper()
        if resposta != pergunta.resposta_correta:
            pergunta.resposta_correta = resposta
            pergunta.save(update_fields=["resposta_correta"])


class Migration(migrations.Migration):
    dependencies = [
        ("quiz", "0002_sync_pergunta_schema"),
    ]

    operations = [
        migrations.AddField(
            model_name="pergunta",
            name="alternativa_e",
            field=models.CharField(default="Opcao pendente", max_length=200),
            preserve_default=False,
        ),
        migrations.RunPython(normalizar_respostas, migrations.RunPython.noop),
    ]

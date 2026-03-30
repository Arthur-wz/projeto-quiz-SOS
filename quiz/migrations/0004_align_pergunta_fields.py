from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("quiz", "0003_add_alternativa_e"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pergunta",
            name="materia",
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name="pergunta",
            name="resposta_correta",
            field=models.CharField(
                choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D"), ("E", "E")],
                max_length=1,
            ),
        ),
        migrations.AlterField(
            model_name="pergunta",
            name="serie",
            field=models.CharField(max_length=50),
        ),
    ]

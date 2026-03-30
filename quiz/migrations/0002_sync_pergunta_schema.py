from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("quiz", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pergunta",
            name="pergunta",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="pergunta",
            name="alternativa_a",
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name="pergunta",
            name="alternativa_b",
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name="pergunta",
            name="alternativa_c",
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name="pergunta",
            name="alternativa_d",
            field=models.CharField(max_length=200),
        ),
        migrations.AddField(
            model_name="pergunta",
            name="serie",
            field=models.CharField(default="Nao informada", max_length=50),
        ),
        migrations.AddField(
            model_name="pergunta",
            name="materia",
            field=models.CharField(default="Geral", max_length=50),
        ),
    ]

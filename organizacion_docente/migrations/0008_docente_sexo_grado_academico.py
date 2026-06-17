# Generated manually for Railway deployment compatibility.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organizacion_docente", "0007_organizaciondocente_cantidad_posiciones_a_utilizar_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="docente",
            name="sexo",
            field=models.CharField(
                choices=[
                    ("M", "Hombre"),
                    ("F", "Mujer"),
                ],
                default="M",
                max_length=1,
                verbose_name="Sexo",
            ),
        ),
        migrations.AddField(
            model_name="docente",
            name="grado_academico",
            field=models.CharField(
                choices=[
                    ("MAGISTER", "Magíster"),
                    ("DOCTOR", "Doctor/a"),
                ],
                default="MAGISTER",
                max_length=20,
                verbose_name="Grado académico",
            ),
        ),
    ]

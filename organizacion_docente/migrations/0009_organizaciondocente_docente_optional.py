# Generated manually to allow draft organizations without an assigned teacher.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("organizacion_docente", "0008_docente_sexo_grado_academico"),
    ]

    operations = [
        migrations.AlterField(
            model_name="organizaciondocente",
            name="docente",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="organizaciones",
                to="organizacion_docente.docente",
                verbose_name="Docente",
            ),
        ),
    ]

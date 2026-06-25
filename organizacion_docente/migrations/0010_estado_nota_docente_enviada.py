# Generated manually to add the administrative state for sending the note to the teacher.

from django.db import migrations, models


TIPO_ESTADO_NOTA_DOCENTE = "nota_docente_enviada_docente"


def crear_estado_nota_docente(apps, schema_editor):
    OrganizacionDocente = apps.get_model("organizacion_docente", "OrganizacionDocente")
    EstadoProcesoOrganizacion = apps.get_model(
        "organizacion_docente",
        "EstadoProcesoOrganizacion",
    )

    for organizacion in OrganizacionDocente.objects.all().iterator():
        EstadoProcesoOrganizacion.objects.get_or_create(
            organizacion=organizacion,
            tipo_estado=TIPO_ESTADO_NOTA_DOCENTE,
            defaults={
                "completado": False,
                "observacion": "",
            },
        )


def eliminar_estado_nota_docente(apps, schema_editor):
    EstadoProcesoOrganizacion = apps.get_model(
        "organizacion_docente",
        "EstadoProcesoOrganizacion",
    )
    EstadoProcesoOrganizacion.objects.filter(
        tipo_estado=TIPO_ESTADO_NOTA_DOCENTE,
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("organizacion_docente", "0009_organizaciondocente_docente_optional"),
    ]

    operations = [
        migrations.AlterField(
            model_name="estadoprocesoorganizacion",
            name="tipo_estado",
            field=models.CharField(
                choices=[
                    (
                        TIPO_ESTADO_NOTA_DOCENTE,
                        "Nota docente enviada al docente",
                    ),
                    ("horario_elaborado", "Horario elaborado"),
                    (
                        "organizacion_docente_elaborada",
                        "Organización docente elaborada",
                    ),
                    (
                        "calendario_pago_elaborado_enviado",
                        "Calendario de pago elaborado y enviado",
                    ),
                    (
                        "organizacion_enviada_vipe",
                        "Organización docente enviada a la VIPE",
                    ),
                    (
                        "organizacion_con_numero_posicion",
                        "Organización docente con número de posición",
                    ),
                    (
                        "organizacion_enviada_firma_electronica",
                        "Organización docente enviada para firma electrónica",
                    ),
                    ("firmado_por_autoridades", "Firmado por autoridades"),
                    (
                        "organizacion_enviada_recursos_humanos",
                        "Organización docente enviada a Recursos Humanos",
                    ),
                    ("acta_recibida", "Acta recibida"),
                    (
                        "acta_firmada_enviada_rh",
                        "Acta firmada enviada a Recursos Humanos",
                    ),
                ],
                max_length=100,
                verbose_name="Tipo de estado",
            ),
        ),
        migrations.RunPython(
            crear_estado_nota_docente,
            eliminar_estado_nota_docente,
        ),
    ]

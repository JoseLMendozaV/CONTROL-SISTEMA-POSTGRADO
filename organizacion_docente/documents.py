from io import BytesIO
import re
from decimal import Decimal

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH



def limpiar_nombre_archivo(texto):
    """
    Limpia un texto para usarlo como nombre de archivo.
    """
    texto = texto or "documento"
    texto = texto.strip().lower()
    texto = re.sub(r"[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ_-]+", "_", texto)
    texto = texto.strip("_")
    return texto[:80]


def contexto_nota_docente(organizacion):
    """
    Prepara el contexto común para PDF y DOCX.
    """

    fecha_actual = timezone.localtime(timezone.now())

    return {
        "organizacion": organizacion,
        "fecha_actual": fecha_actual,
        "fecha_actual_texto": fecha_actual.strftime("%d de %B de %Y"),

        "docente": organizacion.docente,
        "nombre_docente": organizacion.docente.nombre_completo,
        "cedula_docente": organizacion.cedula_docente or organizacion.docente.cedula,

        "facultad": organizacion.facultad,
        "programa": organizacion.programa,
        "asignatura": organizacion.asignatura,

        "numero_pago": organizacion.numero_pago or "",
        "anio": organizacion.anio,
        "semestre": organizacion.get_semestre_display(),
        "grupo_aula": organizacion.grupo_aula,

        "codigo_asignatura": organizacion.codigo_asignatura or organizacion.asignatura.codigo_asignatura,
        "codigo_horario": organizacion.codigo_horario or organizacion.asignatura.codigo_horario or "",
        "total_horas": organizacion.total_horas,
        "total_creditos": organizacion.total_creditos,

        "fechas_clases": organizacion.fechas_clases or "",
        "horario": organizacion.horario or "",
        "observaciones": organizacion.observaciones or "",
    }


def nombre_archivo_nota(organizacion, extension):
    docente = limpiar_nombre_archivo(organizacion.docente.nombre_completo)
    asignatura = limpiar_nombre_archivo(organizacion.asignatura.nombre)
    fecha = timezone.localtime(timezone.now()).strftime("%Y%m%d_%H%M")

    return f"nota_docente_{docente}_{asignatura}_{fecha}.{extension}"


def generar_pdf_nota_docente(organizacion, request=None):
    """
    Genera la nota al docente en PDF usando un template HTML.
    """

    from weasyprint import HTML

    context = contexto_nota_docente(organizacion)

    html_string = render_to_string(
        "organizacion_docente/documentos/nota_docente_pdf.html",
        context,
    )

    base_url = None

    if request:
        base_url = request.build_absolute_uri("/")

    pdf_file = HTML(
        string=html_string,
        base_url=base_url,
    ).write_pdf()

    filename = nombre_archivo_nota(organizacion, "pdf")

    response = HttpResponse(
        pdf_file,
        content_type="application/pdf",
    )

    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response


def agregar_parrafo(documento, texto="", bold=False, align=None, space_after=6):
    """
    Agrega un párrafo con formato básico a un documento Word.
    """

    parrafo = documento.add_paragraph()
    run = parrafo.add_run(texto)
    run.bold = bold
    run.font.name = "Arial"
    run.font.size = Pt(11)

    if align:
        parrafo.alignment = align

    parrafo.paragraph_format.space_after = Pt(space_after)

    return parrafo


def agregar_linea_dato(documento, etiqueta, valor):
    """
    Agrega una línea de dato en formato: Etiqueta: Valor
    """

    parrafo = documento.add_paragraph()
    parrafo.paragraph_format.space_after = Pt(3)

    run_label = parrafo.add_run(f"{etiqueta}: ")
    run_label.bold = True
    run_label.font.name = "Arial"
    run_label.font.size = Pt(10)

    run_value = parrafo.add_run(str(valor or "-"))
    run_value.font.name = "Arial"
    run_value.font.size = Pt(10)

    return parrafo


def generar_docx_nota_docente(organizacion):
    """
    Genera la nota al docente en Word DOCX.
    """

    context = contexto_nota_docente(organizacion)

    documento = Document()

    # Márgenes
    section = documento.sections[0]
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.9)
    section.right_margin = Inches(0.9)

    # Encabezado institucional
    agregar_parrafo(
        documento,
        "UNIVERSIDAD TECNOLÓGICA DE PANAMÁ",
        bold=True,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=2,
    )

    agregar_parrafo(
        documento,
        "CENTRO REGIONAL DE CHIRIQUÍ",
        bold=True,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=2,
    )

    agregar_parrafo(
        documento,
        "VICERRECTORÍA DE INVESTIGACIÓN, POSTGRADO Y EXTENSIÓN",
        bold=True,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=14,
    )

    # Fecha
    agregar_parrafo(
        documento,
        f"David, {context['fecha_actual_texto']}",
        align=WD_ALIGN_PARAGRAPH.RIGHT,
        space_after=18,
    )

    # Destinatario
    agregar_parrafo(
        documento,
        f"Profesor(a): {context['nombre_docente']}",
        bold=True,
        space_after=2,
    )

    agregar_parrafo(
        documento,
        f"Cédula: {context['cedula_docente']}",
        space_after=12,
    )

    agregar_parrafo(
        documento,
        "Estimado(a) profesor(a):",
        space_after=12,
    )

    # Cuerpo base editable
    cuerpo = (
        "Por este medio se le comunica que ha sido considerado(a) para participar "
        "como docente en el programa de postgrado indicado a continuación, de acuerdo "
        "con la organización docente correspondiente al periodo académico señalado."
    )

    agregar_parrafo(
        documento,
        cuerpo,
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        space_after=12,
    )

    agregar_parrafo(
        documento,
        "Datos de la organización docente",
        bold=True,
        space_after=8,
    )

    agregar_linea_dato(documento, "Facultad", context["facultad"])
    agregar_linea_dato(documento, "Programa", context["programa"].nombre)
    agregar_linea_dato(documento, "Asignatura", context["asignatura"].nombre)
    agregar_linea_dato(documento, "Código de asignatura", context["codigo_asignatura"])
    agregar_linea_dato(documento, "Código de horario", context["codigo_horario"])
    agregar_linea_dato(documento, "Grupo / Aula", context["grupo_aula"])
    agregar_linea_dato(documento, "Semestre", context["semestre"])
    agregar_linea_dato(documento, "Año académico", context["anio"])
    agregar_linea_dato(documento, "Total de horas", context["total_horas"])
    agregar_linea_dato(documento, "Total de créditos", context["total_creditos"])
    agregar_linea_dato(documento, "Fechas de clases", context["fechas_clases"])
    agregar_linea_dato(documento, "Horario", context["horario"])

    if context["observaciones"]:
        agregar_linea_dato(documento, "Observaciones", context["observaciones"])

    agregar_parrafo(
        documento,
        "",
        space_after=10,
    )

    cierre = (
        "Agradecemos su apoyo académico y compromiso con la formación de los "
        "estudiantes de postgrado."
    )

    agregar_parrafo(
        documento,
        cierre,
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        space_after=22,
    )

    agregar_parrafo(
        documento,
        "Atentamente,",
        space_after=32,
    )

    agregar_parrafo(
        documento,
        "__________________________________",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=2,
    )

    agregar_parrafo(
        documento,
        "Coordinación de Postgrado",
        bold=True,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=0,
    )

    agregar_parrafo(
        documento,
        "Centro Regional de Chiriquí",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=0,
    )

    output = BytesIO()
    documento.save(output)
    output.seek(0)

    filename = nombre_archivo_nota(organizacion, "docx")

    response = HttpResponse(
        output.getvalue(),
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
    )

    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response


# ============================================================
# Calendario de pago
# ============================================================

def formatear_moneda(valor):
    """
    Formatea un valor decimal como moneda panameña.
    """
    valor = valor or Decimal("0.00")
    return f"B/. {valor:,.2f}"


def calcular_distribucion_pago(organizacion, cuotas=1):
    """
    Calcula una distribución sencilla del pago docente.

    Por defecto genera 1 pago.
    Si se pasa cuotas=2, cuotas=3, etc., divide el pago docente.
    """

    try:
        cuotas = int(cuotas)
    except (TypeError, ValueError):
        cuotas = 1

    if cuotas < 1:
        cuotas = 1

    if cuotas > 12:
        cuotas = 12

    pago_total = organizacion.pago_docente or Decimal("0.00")

    if pago_total <= 0:
        return [
            {
                "numero": 1,
                "concepto": "Pago pendiente de definir",
                "descripcion": "No se ha registrado monto de pago docente.",
                "porcentaje": "100%",
                "monto": Decimal("0.00"),
                "monto_texto": formatear_moneda(Decimal("0.00")),
            }
        ]

    monto_base = (pago_total / Decimal(cuotas)).quantize(Decimal("0.01"))
    distribucion = []
    acumulado = Decimal("0.00")

    for numero in range(1, cuotas + 1):
        if numero == cuotas:
            monto = pago_total - acumulado
        else:
            monto = monto_base
            acumulado += monto

        porcentaje = round((monto / pago_total) * Decimal("100"), 2)

        distribucion.append(
            {
                "numero": numero,
                "concepto": f"Pago {numero} de {cuotas}",
                "descripcion": "Pago correspondiente a la asignatura registrada.",
                "porcentaje": f"{porcentaje}%",
                "monto": monto,
                "monto_texto": formatear_moneda(monto),
            }
        )

    return distribucion


def contexto_calendario_pago(organizacion, cuotas=1):
    """
    Prepara el contexto común para generar el calendario de pago.
    """

    fecha_actual = timezone.localtime(timezone.now())
    distribucion = calcular_distribucion_pago(organizacion, cuotas=cuotas)

    return {
        "organizacion": organizacion,
        "fecha_actual": fecha_actual,
        "fecha_actual_texto": fecha_actual.strftime("%d de %B de %Y"),

        "docente": organizacion.docente,
        "nombre_docente": organizacion.docente.nombre_completo,
        "cedula_docente": organizacion.cedula_docente or organizacion.docente.cedula,

        "facultad": organizacion.facultad,
        "programa": organizacion.programa,
        "asignatura": organizacion.asignatura,

        "numero_pago": organizacion.numero_pago or "",
        "anio": organizacion.anio,
        "semestre": organizacion.get_semestre_display(),
        "grupo_aula": organizacion.grupo_aula,

        "codigo_asignatura": organizacion.codigo_asignatura or organizacion.asignatura.codigo_asignatura,
        "codigo_horario": organizacion.codigo_horario or organizacion.asignatura.codigo_horario or "",
        "total_horas": organizacion.total_horas,
        "total_creditos": organizacion.total_creditos,

        "fechas_clases": organizacion.fechas_clases or "",
        "horario": organizacion.horario or "",
        "observaciones": organizacion.observaciones or "",

        "pago_docente": organizacion.pago_docente or Decimal("0.00"),
        "pago_docente_texto": formatear_moneda(organizacion.pago_docente),
        "cuotas": cuotas,
        "distribucion_pago": distribucion,
    }


def nombre_archivo_calendario(organizacion, extension):
    docente = limpiar_nombre_archivo(organizacion.docente.nombre_completo)
    asignatura = limpiar_nombre_archivo(organizacion.asignatura.nombre)
    fecha = timezone.localtime(timezone.now()).strftime("%Y%m%d_%H%M")

    return f"calendario_pago_{docente}_{asignatura}_{fecha}.{extension}"


def generar_pdf_calendario_pago(organizacion, request=None, cuotas=1):
    """
    Genera el calendario de pago en PDF usando un template HTML.
    """

    from weasyprint import HTML

    context = contexto_calendario_pago(
        organizacion=organizacion,
        cuotas=cuotas,
    )

    html_string = render_to_string(
        "organizacion_docente/documentos/calendario_pago_pdf.html",
        context,
    )

    base_url = None

    if request:
        base_url = request.build_absolute_uri("/")

    pdf_file = HTML(
        string=html_string,
        base_url=base_url,
    ).write_pdf()

    filename = nombre_archivo_calendario(organizacion, "pdf")

    response = HttpResponse(
        pdf_file,
        content_type="application/pdf",
    )

    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response


def generar_docx_calendario_pago(organizacion, cuotas=1):
    """
    Genera el calendario de pago en Word DOCX.
    """

    context = contexto_calendario_pago(
        organizacion=organizacion,
        cuotas=cuotas,
    )

    documento = Document()

    section = documento.sections[0]
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)

    agregar_parrafo(
        documento,
        "UNIVERSIDAD TECNOLÓGICA DE PANAMÁ",
        bold=True,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=2,
    )

    agregar_parrafo(
        documento,
        "CENTRO REGIONAL DE CHIRIQUÍ",
        bold=True,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=2,
    )

    agregar_parrafo(
        documento,
        "CALENDARIO DE PAGO DOCENTE DE POSTGRADO",
        bold=True,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=16,
    )

    agregar_parrafo(
        documento,
        f"Fecha de generación: {context['fecha_actual_texto']}",
        align=WD_ALIGN_PARAGRAPH.RIGHT,
        space_after=14,
    )

    agregar_parrafo(
        documento,
        "Datos del docente",
        bold=True,
        space_after=6,
    )

    agregar_linea_dato(documento, "Docente", context["nombre_docente"])
    agregar_linea_dato(documento, "Cédula", context["cedula_docente"])

    agregar_parrafo(
        documento,
        "Datos académicos",
        bold=True,
        space_after=6,
    )

    agregar_linea_dato(documento, "Facultad", context["facultad"])
    agregar_linea_dato(documento, "Programa", context["programa"].nombre)
    agregar_linea_dato(documento, "Asignatura", context["asignatura"].nombre)
    agregar_linea_dato(documento, "Código de asignatura", context["codigo_asignatura"])
    agregar_linea_dato(documento, "Código de horario", context["codigo_horario"])
    agregar_linea_dato(documento, "Grupo / Aula", context["grupo_aula"])
    agregar_linea_dato(documento, "Semestre", context["semestre"])
    agregar_linea_dato(documento, "Año académico", context["anio"])
    agregar_linea_dato(documento, "Total de horas", context["total_horas"])
    agregar_linea_dato(documento, "Fechas de clases", context["fechas_clases"])
    agregar_linea_dato(documento, "Horario", context["horario"])

    agregar_parrafo(
        documento,
        "Distribución de pago",
        bold=True,
        space_after=8,
    )

    tabla = documento.add_table(rows=1, cols=5)
    tabla.style = "Table Grid"

    encabezados = [
        "No.",
        "Concepto",
        "Descripción",
        "Porcentaje",
        "Monto",
    ]

    hdr_cells = tabla.rows[0].cells

    for index, encabezado in enumerate(encabezados):
        hdr_cells[index].text = encabezado

        for paragraph in hdr_cells[index].paragraphs:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in paragraph.runs:
                run.bold = True
                run.font.name = "Arial"
                run.font.size = Pt(9)

    for item in context["distribucion_pago"]:
        row_cells = tabla.add_row().cells
        row_cells[0].text = str(item["numero"])
        row_cells[1].text = item["concepto"]
        row_cells[2].text = item["descripcion"]
        row_cells[3].text = item["porcentaje"]
        row_cells[4].text = item["monto_texto"]

        for cell in row_cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.name = "Arial"
                    run.font.size = Pt(9)

    agregar_parrafo(
        documento,
        "",
        space_after=8,
    )

    agregar_linea_dato(
        documento,
        "Pago total del docente",
        context["pago_docente_texto"],
    )

    if context["observaciones"]:
        agregar_linea_dato(
            documento,
            "Observaciones",
            context["observaciones"],
        )

    agregar_parrafo(
        documento,
        "",
        space_after=16,
    )

    agregar_parrafo(
        documento,
        "__________________________________",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=2,
    )

    agregar_parrafo(
        documento,
        "Coordinación de Postgrado",
        bold=True,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=0,
    )

    agregar_parrafo(
        documento,
        "Centro Regional de Chiriquí",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=0,
    )

    output = BytesIO()
    documento.save(output)
    output.seek(0)

    filename = nombre_archivo_calendario(organizacion, "docx")

    response = HttpResponse(
        output.getvalue(),
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
    )

    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response
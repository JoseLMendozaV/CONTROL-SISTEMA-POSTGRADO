from io import BytesIO
from decimal import Decimal

from django.db.models import Count, Sum
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils import get_column_letter


COLOR_PRIMARIO = "0F3D5E"
COLOR_GRIS = "F1F5F9"
COLOR_BLANCO = "FFFFFF"
COLOR_BORDE = "CBD5E1"


def decimal_0(valor):
    return valor or Decimal("0.00")


def contar_pendientes(organizaciones, tipo_estado):
    return organizaciones.filter(
        estados__tipo_estado=tipo_estado,
        estados__completado=False,
    ).distinct().count()


def contar_completados(organizaciones, tipo_estado):
    return organizaciones.filter(
        estados__tipo_estado=tipo_estado,
        estados__completado=True,
    ).distinct().count()


def construir_contexto_reportes(organizaciones):
    """
    Construye todos los datos necesarios para la vista, PDF y Excel.
    """

    totales = organizaciones.aggregate(
        total_organizaciones=Count("id"),
        total_ingresos=Sum("total_ingresos"),
        total_pagos=Sum("pago_docente"),
        utilidad_neta=Sum("utilidad_neta"),
        ingreso_laboratorio=Sum("ingreso_laboratorio"),
    )

    total_organizaciones = totales.get("total_organizaciones") or 0
    total_ingresos = decimal_0(totales.get("total_ingresos"))
    total_pagos = decimal_0(totales.get("total_pagos"))
    utilidad_neta = decimal_0(totales.get("utilidad_neta"))
    ingreso_laboratorio = decimal_0(totales.get("ingreso_laboratorio"))

    pendientes_vipe = contar_pendientes(
        organizaciones,
        "organizacion_enviada_vipe",
    )

    enviadas_vipe = contar_completados(
        organizaciones,
        "organizacion_enviada_vipe",
    )

    pendientes_firma = contar_pendientes(
        organizaciones,
        "organizacion_enviada_firma_electronica",
    )

    firmadas_autoridades = contar_completados(
        organizaciones,
        "firmado_por_autoridades",
    )

    pendientes_rh = contar_pendientes(
        organizaciones,
        "organizacion_enviada_recursos_humanos",
    )

    enviadas_rh = contar_completados(
        organizaciones,
        "organizacion_enviada_recursos_humanos",
    )

    actas_pendientes = contar_pendientes(
        organizaciones,
        "acta_recibida",
    )

    actas_recibidas = contar_completados(
        organizaciones,
        "acta_recibida",
    )

    calendarios_pendientes = contar_pendientes(
        organizaciones,
        "calendario_pago_elaborado_enviado",
    )

    calendarios_enviados = contar_completados(
        organizaciones,
        "calendario_pago_elaborado_enviado",
    )

    por_facultad = list(
        organizaciones
        .values("facultad__nombre", "facultad__siglas")
        .annotate(
            total=Count("id"),
            total_ingresos=Sum("total_ingresos"),
            total_pagos=Sum("pago_docente"),
            utilidad_neta=Sum("utilidad_neta"),
        )
        .order_by("facultad__nombre")
    )

    por_programa = list(
        organizaciones
        .values("programa__nombre", "facultad__siglas")
        .annotate(
            total=Count("id"),
            total_ingresos=Sum("total_ingresos"),
            total_pagos=Sum("pago_docente"),
            utilidad_neta=Sum("utilidad_neta"),
        )
        .order_by("programa__nombre")
    )

    por_docente = list(
        organizaciones
        .values("docente__nombre_completo", "cedula_docente")
        .annotate(
            total=Count("id"),
            total_horas=Sum("total_horas"),
            total_pagos=Sum("pago_docente"),
        )
        .order_by("docente__nombre_completo")
    )

    pagos_por_semestre = list(
        organizaciones
        .values("anio", "semestre")
        .annotate(
            total=Count("id"),
            total_pagos=Sum("pago_docente"),
            total_ingresos=Sum("total_ingresos"),
            utilidad_neta=Sum("utilidad_neta"),
        )
        .order_by("-anio", "semestre")
    )

    pendientes_firma_listado = organizaciones.filter(
        estados__tipo_estado="organizacion_enviada_firma_electronica",
        estados__completado=False,
    ).distinct().order_by("-anio", "semestre", "docente__nombre_completo")

    actas_pendientes_listado = organizaciones.filter(
        estados__tipo_estado="acta_recibida",
        estados__completado=False,
    ).distinct().order_by("-anio", "semestre", "docente__nombre_completo")

    calendarios_pendientes_listado = organizaciones.filter(
        estados__tipo_estado="calendario_pago_elaborado_enviado",
        estados__completado=False,
    ).distinct().order_by("-anio", "semestre", "docente__nombre_completo")

    context = {
        "fecha_generacion": timezone.localtime(timezone.now()),

        "total_organizaciones": total_organizaciones,
        "total_ingresos": total_ingresos,
        "total_pagos": total_pagos,
        "utilidad_neta": utilidad_neta,
        "ingreso_laboratorio": ingreso_laboratorio,

        "pendientes_vipe": pendientes_vipe,
        "enviadas_vipe": enviadas_vipe,
        "pendientes_firma": pendientes_firma,
        "firmadas_autoridades": firmadas_autoridades,
        "pendientes_rh": pendientes_rh,
        "enviadas_rh": enviadas_rh,
        "actas_pendientes": actas_pendientes,
        "actas_recibidas": actas_recibidas,
        "calendarios_pendientes": calendarios_pendientes,
        "calendarios_enviados": calendarios_enviados,

        "por_facultad": por_facultad,
        "por_programa": por_programa,
        "por_docente": por_docente,
        "pagos_por_semestre": pagos_por_semestre,

        "pendientes_firma_listado": pendientes_firma_listado[:50],
        "actas_pendientes_listado": actas_pendientes_listado[:50],
        "calendarios_pendientes_listado": calendarios_pendientes_listado[:50],
    }

    return context


def aplicar_estilo_header(cell):
    cell.font = Font(bold=True, color=COLOR_BLANCO)
    cell.fill = PatternFill("solid", fgColor=COLOR_PRIMARIO)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def aplicar_bordes(ws):
    borde = Border(
        left=Side(style="thin", color=COLOR_BORDE),
        right=Side(style="thin", color=COLOR_BORDE),
        top=Side(style="thin", color=COLOR_BORDE),
        bottom=Side(style="thin", color=COLOR_BORDE),
    )

    for row in ws.iter_rows():
        for cell in row:
            cell.border = borde
            cell.alignment = Alignment(vertical="center", wrap_text=True)


def ajustar_columnas(ws):
    for column_cells in ws.columns:
        max_length = 0
        col = get_column_letter(column_cells[0].column)

        for cell in column_cells:
            value = str(cell.value) if cell.value is not None else ""
            max_length = max(max_length, len(value))

        ws.column_dimensions[col].width = min(max_length + 3, 45)


def escribir_tabla(ws, titulo, headers, filas, fila_inicio):
    ws.merge_cells(
        start_row=fila_inicio,
        start_column=1,
        end_row=fila_inicio,
        end_column=len(headers),
    )

    titulo_cell = ws.cell(row=fila_inicio, column=1)
    titulo_cell.value = titulo
    titulo_cell.font = Font(bold=True, color=COLOR_BLANCO, size=13)
    titulo_cell.fill = PatternFill("solid", fgColor=COLOR_PRIMARIO)

    fila_header = fila_inicio + 1

    for col_index, header in enumerate(headers, start=1):
        cell = ws.cell(row=fila_header, column=col_index)
        cell.value = header
        aplicar_estilo_header(cell)

    fila_actual = fila_header + 1

    for fila in filas:
        for col_index, valor in enumerate(fila, start=1):
            ws.cell(row=fila_actual, column=col_index).value = valor

        fila_actual += 1

    return fila_actual + 2


def generar_excel_reportes(organizaciones):
    """
    Genera Excel con reportes consolidados.
    """

    context = construir_contexto_reportes(organizaciones)

    wb = Workbook()

    # ========================================================
    # Hoja resumen
    # ========================================================
    ws = wb.active
    ws.title = "Resumen"

    resumen = [
        ["Fecha de generación", context["fecha_generacion"].strftime("%d/%m/%Y %H:%M")],
        ["Total de organizaciones", context["total_organizaciones"]],
        ["Total de ingresos", float(context["total_ingresos"])],
        ["Total de pagos docentes", float(context["total_pagos"])],
        ["Utilidad neta", float(context["utilidad_neta"])],
        ["Ingreso laboratorio", float(context["ingreso_laboratorio"])],
        ["Pendientes VIPE", context["pendientes_vipe"]],
        ["Enviadas a VIPE", context["enviadas_vipe"]],
        ["Pendientes firma electrónica", context["pendientes_firma"]],
        ["Firmadas por autoridades", context["firmadas_autoridades"]],
        ["Pendientes RH", context["pendientes_rh"]],
        ["Enviadas a RH", context["enviadas_rh"]],
        ["Actas pendientes", context["actas_pendientes"]],
        ["Actas recibidas", context["actas_recibidas"]],
        ["Calendarios pendientes", context["calendarios_pendientes"]],
        ["Calendarios enviados", context["calendarios_enviados"]],
    ]

    ws.append(["Reporte general de Organización Docente", ""])
    ws["A1"].font = Font(bold=True, color=COLOR_BLANCO, size=14)
    ws["A1"].fill = PatternFill("solid", fgColor=COLOR_PRIMARIO)
    ws["B1"].fill = PatternFill("solid", fgColor=COLOR_PRIMARIO)

    for fila in resumen:
        ws.append(fila)

    for row in range(2, ws.max_row + 1):
        ws[f"A{row}"].font = Font(bold=True)
        ws[f"A{row}"].fill = PatternFill("solid", fgColor=COLOR_GRIS)

    for cell in ["B4", "B5", "B6", "B7"]:
        ws[cell].number_format = '"B/." #,##0.00'

    aplicar_bordes(ws)
    ajustar_columnas(ws)

    # ========================================================
    # Hoja por facultad
    # ========================================================
    ws_fac = wb.create_sheet("Por Facultad")
    ws_fac.append(["Facultad", "Siglas", "Total", "Ingresos", "Pagos", "Utilidad"])

    for cell in ws_fac[1]:
        aplicar_estilo_header(cell)

    for item in context["por_facultad"]:
        ws_fac.append([
            item["facultad__nombre"],
            item["facultad__siglas"] or "",
            item["total"],
            float(decimal_0(item["total_ingresos"])),
            float(decimal_0(item["total_pagos"])),
            float(decimal_0(item["utilidad_neta"])),
        ])

    aplicar_bordes(ws_fac)
    ajustar_columnas(ws_fac)

    for row in range(2, ws_fac.max_row + 1):
        for col in ["D", "E", "F"]:
            ws_fac[f"{col}{row}"].number_format = '"B/." #,##0.00'

    # ========================================================
    # Hoja por programa
    # ========================================================
    ws_prog = wb.create_sheet("Por Programa")
    ws_prog.append(["Facultad", "Programa", "Total", "Ingresos", "Pagos", "Utilidad"])

    for cell in ws_prog[1]:
        aplicar_estilo_header(cell)

    for item in context["por_programa"]:
        ws_prog.append([
            item["facultad__siglas"] or "",
            item["programa__nombre"],
            item["total"],
            float(decimal_0(item["total_ingresos"])),
            float(decimal_0(item["total_pagos"])),
            float(decimal_0(item["utilidad_neta"])),
        ])

    aplicar_bordes(ws_prog)
    ajustar_columnas(ws_prog)

    for row in range(2, ws_prog.max_row + 1):
        for col in ["D", "E", "F"]:
            ws_prog[f"{col}{row}"].number_format = '"B/." #,##0.00'

    # ========================================================
    # Hoja por docente
    # ========================================================
    ws_doc = wb.create_sheet("Por Docente")
    ws_doc.append(["Docente", "Cédula", "Total organizaciones", "Total horas", "Total pagos"])

    for cell in ws_doc[1]:
        aplicar_estilo_header(cell)

    for item in context["por_docente"]:
        ws_doc.append([
            item["docente__nombre_completo"],
            item["cedula_docente"] or "",
            item["total"],
            float(decimal_0(item["total_horas"])),
            float(decimal_0(item["total_pagos"])),
        ])

    aplicar_bordes(ws_doc)
    ajustar_columnas(ws_doc)

    for row in range(2, ws_doc.max_row + 1):
        ws_doc[f"E{row}"].number_format = '"B/." #,##0.00'

    # ========================================================
    # Hoja pagos por semestre
    # ========================================================
    ws_sem = wb.create_sheet("Pagos Semestre")
    ws_sem.append(["Año", "Semestre", "Total", "Ingresos", "Pagos", "Utilidad"])

    for cell in ws_sem[1]:
        aplicar_estilo_header(cell)

    for item in context["pagos_por_semestre"]:
        ws_sem.append([
            item["anio"],
            item["semestre"],
            item["total"],
            float(decimal_0(item["total_ingresos"])),
            float(decimal_0(item["total_pagos"])),
            float(decimal_0(item["utilidad_neta"])),
        ])

    aplicar_bordes(ws_sem)
    ajustar_columnas(ws_sem)

    for row in range(2, ws_sem.max_row + 1):
        for col in ["D", "E", "F"]:
            ws_sem[f"{col}{row}"].number_format = '"B/." #,##0.00'

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"reporte_organizacion_docente_{timezone.now().strftime('%Y%m%d_%H%M')}.xlsx"

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response


def generar_pdf_reportes(organizaciones, request=None):
    """
    Genera PDF del reporte consolidado.
    """

    from weasyprint import HTML

    context = construir_contexto_reportes(organizaciones)

    html_string = render_to_string(
        "organizacion_docente/documentos/reporte_general_pdf.html",
        context,
    )

    base_url = request.build_absolute_uri("/") if request else None

    pdf_file = HTML(
        string=html_string,
        base_url=base_url,
    ).write_pdf()

    filename = f"reporte_organizacion_docente_{timezone.now().strftime('%Y%m%d_%H%M')}.pdf"

    response = HttpResponse(
        pdf_file,
        content_type="application/pdf",
    )

    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response
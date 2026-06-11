from django.urls import path
from . import views


urlpatterns = [
    # ========================================================
    # Dashboard
    # ========================================================
    path(
        "",
        views.dashboard,
        name="dashboard",
    ),

    # ========================================================
    # Organización Docente
    # ========================================================
    path(
        "organizaciones/",
        views.organizacion_listado,
        name="organizacion_listado",
    ),

    path(
        "organizaciones/crear/",
        views.organizacion_crear,
        name="organizacion_crear",
    ),

    path(
        "organizaciones/<int:pk>/",
        views.organizacion_detalle,
        name="organizacion_detalle",
    ),

    path(
        "organizaciones/<int:pk>/editar/",
        views.organizacion_editar,
        name="organizacion_editar",
    ),

    path(
        "organizaciones/<int:pk>/eliminar/",
        views.organizacion_eliminar,
        name="organizacion_eliminar",
    ),

    path(
        "organizaciones/<int:pk>/duplicar/",
        views.organizacion_duplicar,
        name="organizacion_duplicar",
    ),

    path(
        "organizaciones/<int:pk>/estado/<str:tipo_estado>/",
        views.organizacion_marcar_estado,
        name="organizacion_marcar_estado",
    ),

    path(
        "organizaciones/actualizacion-masiva/",
        views.organizaciones_actualizacion_masiva,
        name="organizaciones_actualizacion_masiva",
    ),

    # ========================================================
    # Importación y exportación
    # ========================================================
    path(
        "organizaciones/importar-excel/",
        views.importar_organizaciones_excel,
        name="importar_organizaciones_excel",
    ),

    path(
        "organizaciones/exportar-excel/",
        views.exportar_organizaciones_excel,
        name="exportar_organizaciones_excel",
    ),

    # ========================================================
    # Documentos por organización docente
    # ========================================================
    path(
        "organizaciones/<int:pk>/nota-docente/",
        views.generar_nota_docente,
        name="generar_nota_docente",
    ),

    path(
        "organizaciones/<int:pk>/calendario-pago/",
        views.generar_calendario_pago,
        name="generar_calendario_pago",
    ),

    # ========================================================
    # Facultades
    # ========================================================
    path(
        "facultades/",
        views.facultad_listado,
        name="facultad_listado",
    ),

    path(
        "facultades/crear/",
        views.facultad_crear,
        name="facultad_crear",
    ),

    path(
        "facultades/<int:pk>/editar/",
        views.facultad_editar,
        name="facultad_editar",
    ),

    path(
        "facultades/<int:pk>/eliminar/",
        views.facultad_eliminar,
        name="facultad_eliminar",
    ),

    # ========================================================
    # Programas de Postgrado
    # ========================================================
    path(
        "programas/",
        views.programa_listado,
        name="programa_listado",
    ),

    path(
        "programas/crear/",
        views.programa_crear,
        name="programa_crear",
    ),

    path(
        "programas/<int:pk>/editar/",
        views.programa_editar,
        name="programa_editar",
    ),

    path(
        "programas/<int:pk>/eliminar/",
        views.programa_eliminar,
        name="programa_eliminar",
    ),

    # ========================================================
    # Docentes
    # ========================================================
    path(
        "docentes/",
        views.docente_listado,
        name="docente_listado",
    ),

    path(
        "docentes/crear/",
        views.docente_crear,
        name="docente_crear",
    ),

    path(
        "docentes/<int:pk>/editar/",
        views.docente_editar,
        name="docente_editar",
    ),

    path(
        "docentes/<int:pk>/eliminar/",
        views.docente_eliminar,
        name="docente_eliminar",
    ),

    # ========================================================
    # Asignaturas
    # ========================================================
    path(
        "asignaturas/",
        views.asignatura_listado,
        name="asignatura_listado",
    ),

    path(
        "asignaturas/crear/",
        views.asignatura_crear,
        name="asignatura_crear",
    ),

    path(
        "asignaturas/<int:pk>/editar/",
        views.asignatura_editar,
        name="asignatura_editar",
    ),

    path(
        "asignaturas/<int:pk>/eliminar/",
        views.asignatura_eliminar,
        name="asignatura_eliminar",
    ),

    # ========================================================
    # Plantillas de documentos
    # ========================================================
    path(
        "plantillas/",
        views.plantilla_listado,
        name="plantilla_listado",
    ),

    path(
        "plantillas/crear/",
        views.plantilla_crear,
        name="plantilla_crear",
    ),

    path(
        "plantillas/<int:pk>/editar/",
        views.plantilla_editar,
        name="plantilla_editar",
    ),

    # ========================================================
    # Reportes
    # ========================================================
    path(
        "reportes/",
        views.reportes,
        name="reportes",
    ),

    path(
    "reportes/exportar-excel/",
    views.reportes_exportar_excel,
    name="reportes_exportar_excel",
    ),

    path(
        "reportes/exportar-pdf/",
        views.reportes_exportar_pdf,
        name="reportes_exportar_pdf",
    ),


    # ========================================================
    # AJAX — Combos dinámicos
    # ========================================================
    path(
        "ajax/programas/",
        views.ajax_programas_por_facultad,
        name="ajax_programas_por_facultad",
    ),

    path(
        "ajax/asignaturas/",
        views.ajax_asignaturas_por_programa,
        name="ajax_asignaturas_por_programa",
    ),

    path(
        "ajax/docentes/",
        views.ajax_docentes_por_facultad,
        name="ajax_docentes_por_facultad",
    ),

    path(
        "ajax/docente/datos/",
        views.ajax_datos_docente,
        name="ajax_datos_docente",
    ),

    path(
        "ajax/asignatura/datos/",
        views.ajax_datos_asignatura,
        name="ajax_datos_asignatura",
    ),

    path(
    "organizaciones/exportar-excel/",
    views.exportar_organizaciones_excel,
    name="exportar_organizaciones_excel",
    ),

    path(
    "organizaciones/<int:pk>/nota-docente/",
    views.generar_nota_docente,
    name="generar_nota_docente",
    ),

    path(
    "organizaciones/<int:pk>/calendario-pago/",
    views.generar_calendario_pago,
    name="generar_calendario_pago",
    ),

    path(
    "reportes/informe-programas/",
    views.informe_programas_postgrado,
    name="informe_programas_postgrado",
    ),
]
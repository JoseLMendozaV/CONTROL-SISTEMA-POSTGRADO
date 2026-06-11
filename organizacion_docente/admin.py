from django.contrib import admin, messages
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    Facultad,
    ProgramaPostgrado,
    Docente,
    Asignatura,
    OrganizacionDocente,
    EstadoProcesoOrganizacion,
    PlantillaDocumento,
    HistorialCambio,
    CohorteProgramaPostgrado,
)


# ============================================================
# Configuración visual general del Django Admin
# ============================================================

admin.site.site_header = "Control de Organización Docente de Postgrado"
admin.site.site_title = "Organización Docente"
admin.site.index_title = "Panel Administrativo"


# ============================================================
# Filtro personalizado por estado general
# ============================================================

class EstadoGeneralFilter(admin.SimpleListFilter):
    title = "Estado general"
    parameter_name = "estado_general"

    def lookups(self, request, model_admin):
        return (
            ("sin_iniciar", "Sin iniciar"),
            ("en_proceso", "En proceso"),
            ("enviado", "Enviado a otra unidad"),
            ("completo", "Proceso completo"),
        )

    def queryset(self, request, queryset):
        total_estados = len(EstadoProcesoOrganizacion.TIPO_ESTADO_CHOICES)

        queryset = queryset.annotate(
            total_completados=Count(
                "estados",
                filter=Q(estados__completado=True),
                distinct=True,
            )
        )

        if self.value() == "sin_iniciar":
            return queryset.filter(total_completados=0)

        if self.value() == "completo":
            return queryset.filter(total_completados=total_estados)

        if self.value() == "enviado":
            estados_enviados = [
                "organizacion_enviada_vipe",
                "organizacion_con_numero_posicion",
                "organizacion_enviada_firma_electronica",
                "firmado_por_autoridades",
                "organizacion_enviada_recursos_humanos",
            ]

            return queryset.filter(
                estados__tipo_estado__in=estados_enviados,
                estados__completado=True,
            ).exclude(
                total_completados=total_estados
            ).distinct()

        if self.value() == "en_proceso":
            return queryset.filter(
                total_completados__gt=0,
                total_completados__lt=total_estados,
            ).distinct()

        return queryset


# ============================================================
# Facultad
# ============================================================

@admin.register(Facultad)
class FacultadAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "siglas",
        "activo_badge",
        "creado_en",
        "actualizado_en",
    )
    list_filter = ("activo",)
    search_fields = ("nombre", "siglas")
    ordering = ("nombre",)
    list_per_page = 25

    @admin.display(description="Estado")
    def activo_badge(self, obj):
        if obj.activo:
            return format_html(
                '<span style="background:#dcfce7;color:#166534;'
                'padding:4px 10px;border-radius:999px;font-weight:600;">'
                'Activo</span>'
            )

        return format_html(
            '<span style="background:#fee2e2;color:#991b1b;'
            'padding:4px 10px;border-radius:999px;font-weight:600;">'
            'Inactivo</span>'
        )


# ============================================================
# Programa de Postgrado
# ============================================================

@admin.register(ProgramaPostgrado)
class ProgramaPostgradoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "facultad",
        "codigo",
        "activo_badge",
        "creado_en",
    )
    list_filter = (
        "activo",
        ("facultad", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = (
        "nombre",
        "codigo",
        "facultad__nombre",
        "facultad__siglas",
    )
    autocomplete_fields = ("facultad",)
    ordering = ("facultad__nombre", "nombre")
    list_per_page = 25

    @admin.display(description="Estado")
    def activo_badge(self, obj):
        if obj.activo:
            return format_html(
                '<span style="background:#dcfce7;color:#166534;'
                'padding:4px 10px;border-radius:999px;font-weight:600;">'
                'Activo</span>'
            )

        return format_html(
            '<span style="background:#fee2e2;color:#991b1b;'
            'padding:4px 10px;border-radius:999px;font-weight:600;">'
            'Inactivo</span>'
        )


# ============================================================
# Docente
# ============================================================

@admin.register(Docente)
class DocenteAdmin(admin.ModelAdmin):
    list_display = (
        "nombre_completo",
        "cedula",
        "correo",
        "telefono",
        "facultad",
        "especialidad",
        "activo_badge",
    )
    list_filter = (
        "activo",
        ("facultad", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = (
        "nombre_completo",
        "cedula",
        "correo",
        "telefono",
        "especialidad",
        "facultad__nombre",
    )
    autocomplete_fields = ("facultad",)
    ordering = ("nombre_completo",)
    list_per_page = 25

    @admin.display(description="Estado")
    def activo_badge(self, obj):
        if obj.activo:
            return format_html(
                '<span style="background:#dcfce7;color:#166534;'
                'padding:4px 10px;border-radius:999px;font-weight:600;">'
                'Activo</span>'
            )

        return format_html(
            '<span style="background:#fee2e2;color:#991b1b;'
            'padding:4px 10px;border-radius:999px;font-weight:600;">'
            'Inactivo</span>'
        )


# ============================================================
# Asignatura
# ============================================================

@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = (
        "codigo_asignatura",
        "nombre",
        "programa",
        "codigo_horario",
        "total_horas",
        "total_creditos",
        "total_laboratorio",
        "activo_badge",
    )
    list_filter = (
        "activo",
        ("programa", admin.RelatedOnlyFieldListFilter),
        ("programa__facultad", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = (
        "nombre",
        "codigo_asignatura",
        "codigo_horario",
        "programa__nombre",
        "programa__facultad__nombre",
    )
    autocomplete_fields = ("programa",)
    ordering = ("programa__nombre", "nombre")
    list_per_page = 25

    @admin.display(description="Estado")
    def activo_badge(self, obj):
        if obj.activo:
            return format_html(
                '<span style="background:#dcfce7;color:#166534;'
                'padding:4px 10px;border-radius:999px;font-weight:600;">'
                'Activo</span>'
            )

        return format_html(
            '<span style="background:#fee2e2;color:#991b1b;'
            'padding:4px 10px;border-radius:999px;font-weight:600;">'
            'Inactivo</span>'
        )


# ============================================================
# Inline de estados administrativos
# ============================================================

class EstadoProcesoInline(admin.TabularInline):
    model = EstadoProcesoOrganizacion
    extra = 0
    can_delete = False

    fields = (
        "tipo_estado",
        "completado",
        "fecha_completado",
        "usuario_completo",
        "observacion",
    )

    readonly_fields = (
        "tipo_estado",
        "fecha_completado",
        "usuario_completo",
    )

    ordering = ("id",)

    def has_add_permission(self, request, obj=None):
        return False


# ============================================================
# Organización Docente
# ============================================================

@admin.register(OrganizacionDocente)
class OrganizacionDocenteAdmin(admin.ModelAdmin):
    list_display = (
        "numero_pago",
        "anio",
        "semestre",
        "docente_nombre",
        "cedula_docente",
        "facultad",
        "programa",
        "asignatura_nombre",
        "grupo_aula",
        "total_horas",
        "cantidad_estudiantes_matriculados",
        "pago_docente_formato",
        "utilidad_neta_formato",
        "avance_badge",
        "estado_badge",
    )

    list_filter = (
        "anio",
        "semestre",
        EstadoGeneralFilter,
        ("facultad", admin.RelatedOnlyFieldListFilter),
        ("programa", admin.RelatedOnlyFieldListFilter),
        ("docente", admin.RelatedOnlyFieldListFilter),
        ("asignatura", admin.RelatedOnlyFieldListFilter),
        "activo",
        "incluir_en_informe_programas",
        "estado_informe_programa",
        "periodo_inicio_programa",
        "periodo_finalizacion_programa",
    )

    search_fields = (
        "numero_pago",
        "docente__nombre_completo",
        "docente__cedula",
        "cedula_docente",
        "facultad__nombre",
        "facultad__siglas",
        "programa__nombre",
        "asignatura__nombre",
        "asignatura__codigo_asignatura",
        "codigo_asignatura",
        "codigo_horario",
        "grupo_aula",
    )

    autocomplete_fields = (
        "docente",
        "facultad",
        "programa",
        "asignatura",
    )

    readonly_fields = (
        "cedula_docente",
        "codigo_asignatura",
        "codigo_horario",
        "utilidad_neta",
        "estado_badge_detalle",
        "porcentaje_avance_detalle",
        "creado_en",
        "actualizado_en",
    )

    fieldsets = (
        (
            "Información general",
            {
                "fields": (
                    "numero_pago",
                    "anio",
                    "semestre",
                    "facultad",
                    "programa",
                    "activo",
                )
            },
        ),
        (
            "Información del docente",
            {
                "fields": (
                    "docente",
                    "cedula_docente",
                )
            },
        ),
        (
            "Información académica",
            {
                "fields": (
                    "asignatura",
                    "codigo_asignatura",
                    "codigo_horario",
                    "grupo_aula",
                    "total_horas",
                    "fechas_clases",
                    "horario",
                    "total_creditos",
                    "total_laboratorio",
                )
            },
        ),
        (
            "Información de matrícula y calendario de pago",
            {
                "fields": (
                    "fecha_matricula",

                    "fecha_matricula_texto",
                    "primer_pago_texto",
                    "segundo_pago_texto",
                    "tercer_pago_texto",
                    "retiro_inclusion_texto",
                    "retiro_fuera_texto",

                    "cantidad_estudiantes_matriculados",
                    "total_no_exonerados",
                    "cantidad_exoneracion_50",
                    "cantidad_exoneracion_25",
                )
            },
        ),
        (
            "Información financiera",
            {
                "fields": (
                    "ingreso_laboratorio",
                    "total_ingresos",
                    "pago_docente",
                    "utilidad_neta",
                )
            },
        ),
        (
            "Estado general calculado",
            {
                "fields": (
                    "estado_badge_detalle",
                    "porcentaje_avance_detalle",
                )
            },
        ),

        (
            "Informe anual de programas de postgrado",
            {
                "fields": (
                    "incluir_en_informe_programas",
                    "estado_informe_programa",
                    "matriculados_inicio_programa",
                    "matriculados_actuales_programa",
                    "periodo_inicio_programa",
                    "periodo_finalizacion_programa",
                    "inicio_texto_programa",
                    "finaliza_texto_programa",
                    "observacion_informe_programa",
                )
            },
        ),



        (
            "Observaciones y auditoría",
            {
                "fields": (
                    "observaciones",
                    "creado_en",
                    "actualizado_en",
                )
            },
        ),
    )

    inlines = [EstadoProcesoInline]

    actions = (
        "accion_recalcular_utilidad",
        "accion_marcar_enviada_vipe",
        "accion_marcar_enviada_firma",
        "accion_marcar_firmado_autoridades",
        "accion_marcar_enviada_rh",
        "accion_marcar_acta_recibida",
        "accion_marcar_acta_firmada_enviada_rh",
        "accion_duplicar_organizaciones",
    )

    ordering = (
        "-anio",
        "semestre",
        "facultad__nombre",
        "programa__nombre",
    )

    list_per_page = 25
    list_select_related = (
        "docente",
        "facultad",
        "programa",
        "asignatura",
    )

    save_on_top = True

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            "docente",
            "facultad",
            "programa",
            "asignatura",
        ).prefetch_related("estados")

    @admin.display(description="Docente", ordering="docente__nombre_completo")
    def docente_nombre(self, obj):
        return obj.docente.nombre_completo

    @admin.display(description="Asignatura", ordering="asignatura__nombre")
    def asignatura_nombre(self, obj):
        return obj.asignatura.nombre

    @admin.display(description="Pago docente")
    def pago_docente_formato(self, obj):
        valor = obj.pago_docente or 0
        return f"B/. {valor:,.2f}"

    @admin.display(description="Utilidad neta")
    def utilidad_neta_formato(self, obj):
        valor = obj.utilidad_neta or 0
        color = "#166534" if valor >= 0 else "#991b1b"
        valor_formateado = f"B/. {valor:,.2f}"

        return format_html(
            '<strong style="color:{};">{}</strong>',
            color,
            valor_formateado,
        )

    @admin.display(description="Avance")
    def avance_badge(self, obj):
        porcentaje = obj.porcentaje_avance

        if porcentaje == 100:
            fondo = "#dcfce7"
            texto = "#166534"
        elif porcentaje == 0:
            fondo = "#f1f5f9"
            texto = "#475569"
        else:
            fondo = "#fef9c3"
            texto = "#854d0e"

        return format_html(
            '<span style="background:{};color:{};padding:4px 10px;'
            'border-radius:999px;font-weight:700;">{}%</span>',
            fondo,
            texto,
            porcentaje,
        )

    @admin.display(description="Estado")
    def estado_badge(self, obj):
        codigo = obj.estado_general_codigo
        texto = obj.estado_general_texto

        estilos = {
            "sin_iniciar": ("#f1f5f9", "#475569"),
            "en_proceso": ("#fef9c3", "#854d0e"),
            "enviado": ("#dbeafe", "#1e40af"),
            "completo": ("#dcfce7", "#166534"),
            "pendiente": ("#fee2e2", "#991b1b"),
        }

        fondo, color = estilos.get(codigo, ("#f1f5f9", "#475569"))

        return format_html(
            '<span style="background:{};color:{};padding:4px 10px;'
            'border-radius:999px;font-weight:700;">{}</span>',
            fondo,
            color,
            texto,
        )

    @admin.display(description="Estado general")
    def estado_badge_detalle(self, obj):
        return self.estado_badge(obj)

    @admin.display(description="Porcentaje de avance")
    def porcentaje_avance_detalle(self, obj):
        return f"{obj.porcentaje_avance}%"

    def save_formset(self, request, form, formset, change):
        """
        Permite que cuando se marquen estados desde el inline,
        se registre automáticamente la fecha y el usuario.
        """

        instances = formset.save(commit=False)

        for instance in instances:
            if isinstance(instance, EstadoProcesoOrganizacion):
                if instance.completado and not instance.fecha_completado:
                    instance.fecha_completado = timezone.now()
                    instance.usuario_completo = request.user

                if not instance.completado:
                    instance.fecha_completado = None
                    instance.usuario_completo = None

            instance.save()

        formset.save_m2m()

    def _marcar_estado_masivo(self, request, queryset, tipo_estado, mensaje):
        total = 0

        for organizacion in queryset:
            estado, creado = EstadoProcesoOrganizacion.objects.get_or_create(
                organizacion=organizacion,
                tipo_estado=tipo_estado,
            )

            estado.marcar_completado(usuario=request.user)
            total += 1

        self.message_user(
            request,
            f"{total} organización(es) actualizada(s): {mensaje}.",
            messages.SUCCESS,
        )

    @admin.action(description="Recalcular utilidad neta")
    def accion_recalcular_utilidad(self, request, queryset):
        total = 0

        for organizacion in queryset:
            organizacion.utilidad_neta = organizacion.calcular_utilidad_neta()
            organizacion.save()
            total += 1

        self.message_user(
            request,
            f"Se recalculó la utilidad neta de {total} organización(es).",
            messages.SUCCESS,
        )

    @admin.action(description="Marcar como enviada a la VIPE")
    def accion_marcar_enviada_vipe(self, request, queryset):
        self._marcar_estado_masivo(
            request,
            queryset,
            "organizacion_enviada_vipe",
            "enviada a la VIPE",
        )

    @admin.action(description="Marcar como enviada a firma electrónica")
    def accion_marcar_enviada_firma(self, request, queryset):
        self._marcar_estado_masivo(
            request,
            queryset,
            "organizacion_enviada_firma_electronica",
            "enviada a firma electrónica",
        )

    @admin.action(description="Marcar como firmada por autoridades")
    def accion_marcar_firmado_autoridades(self, request, queryset):
        self._marcar_estado_masivo(
            request,
            queryset,
            "firmado_por_autoridades",
            "firmada por autoridades",
        )

    @admin.action(description="Marcar como enviada a Recursos Humanos")
    def accion_marcar_enviada_rh(self, request, queryset):
        self._marcar_estado_masivo(
            request,
            queryset,
            "organizacion_enviada_recursos_humanos",
            "enviada a Recursos Humanos",
        )

    @admin.action(description="Marcar acta como recibida")
    def accion_marcar_acta_recibida(self, request, queryset):
        self._marcar_estado_masivo(
            request,
            queryset,
            "acta_recibida",
            "acta recibida",
        )

    @admin.action(description="Marcar acta firmada enviada a RH")
    def accion_marcar_acta_firmada_enviada_rh(self, request, queryset):
        self._marcar_estado_masivo(
            request,
            queryset,
            "acta_firmada_enviada_rh",
            "acta firmada enviada a Recursos Humanos",
        )

    @admin.action(description="Duplicar organización docente seleccionada")
    def accion_duplicar_organizaciones(self, request, queryset):
        total = 0

        for organizacion in queryset:
            organizacion.pk = None
            organizacion.numero_pago = None
            organizacion.observaciones = (
                f"Registro duplicado desde el Admin el "
                f"{timezone.now().strftime('%d/%m/%Y %H:%M')}."
            )
            organizacion.save()
            total += 1

        self.message_user(
            request,
            f"Se duplicaron {total} organización(es) docente(s).",
            messages.SUCCESS,
        )


# ============================================================
# Estado del Proceso
# ============================================================

@admin.register(EstadoProcesoOrganizacion)
class EstadoProcesoOrganizacionAdmin(admin.ModelAdmin):
    list_display = (
        "organizacion",
        "tipo_estado",
        "completado_badge",
        "fecha_completado",
        "usuario_completo",
    )

    list_filter = (
        "tipo_estado",
        "completado",
        "fecha_completado",
        "organizacion__anio",
    )

    search_fields = (
        "organizacion__numero_pago",
        "organizacion__docente__nombre_completo",
        "organizacion__cedula_docente",
        "organizacion__programa__nombre",
        "organizacion__asignatura__nombre",
        "observacion",
    )

    autocomplete_fields = (
        "organizacion",
        "usuario_completo",
    )

    readonly_fields = (
        "creado_en",
        "actualizado_en",
    )

    actions = (
        "accion_marcar_completado",
        "accion_marcar_pendiente",
    )

    ordering = (
        "organizacion",
        "id",
    )

    list_per_page = 50

    @admin.display(description="Estado")
    def completado_badge(self, obj):
        if obj.completado:
            return format_html(
                '<span style="background:#dcfce7;color:#166534;'
                'padding:4px 10px;border-radius:999px;font-weight:700;">'
                'Completado</span>'
            )

        return format_html(
            '<span style="background:#fee2e2;color:#991b1b;'
            'padding:4px 10px;border-radius:999px;font-weight:700;">'
            'Pendiente</span>'
        )

    @admin.action(description="Marcar estados seleccionados como completados")
    def accion_marcar_completado(self, request, queryset):
        total = 0

        for estado in queryset:
            estado.marcar_completado(usuario=request.user)
            total += 1

        self.message_user(
            request,
            f"Se marcaron {total} estado(s) como completados.",
            messages.SUCCESS,
        )

    @admin.action(description="Marcar estados seleccionados como pendientes")
    def accion_marcar_pendiente(self, request, queryset):
        total = 0

        for estado in queryset:
            estado.marcar_pendiente()
            total += 1

        self.message_user(
            request,
            f"Se marcaron {total} estado(s) como pendientes.",
            messages.WARNING,
        )


# ============================================================
# Plantilla de Documento
# ============================================================

@admin.register(PlantillaDocumento)
class PlantillaDocumentoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "tipo_documento",
        "activo_badge",
        "archivo",
        "creado_en",
    )

    list_filter = (
        "tipo_documento",
        "activo",
    )

    search_fields = (
        "nombre",
        "descripcion",
        "contenido_html",
    )

    readonly_fields = (
        "creado_en",
        "actualizado_en",
    )

    fieldsets = (
        (
            "Información de la plantilla",
            {
                "fields": (
                    "nombre",
                    "tipo_documento",
                    "descripcion",
                    "activo",
                )
            },
        ),
        (
            "Archivo o contenido editable",
            {
                "fields": (
                    "archivo",
                    "contenido_html",
                )
            },
        ),
        (
            "Auditoría",
            {
                "fields": (
                    "creado_en",
                    "actualizado_en",
                )
            },
        ),
    )

    ordering = (
        "tipo_documento",
        "nombre",
    )

    @admin.display(description="Estado")
    def activo_badge(self, obj):
        if obj.activo:
            return format_html(
                '<span style="background:#dcfce7;color:#166534;'
                'padding:4px 10px;border-radius:999px;font-weight:600;">'
                'Activo</span>'
            )

        return format_html(
            '<span style="background:#fee2e2;color:#991b1b;'
            'padding:4px 10px;border-radius:999px;font-weight:600;">'
            'Inactivo</span>'
        )


# ============================================================
# Historial de Cambios
# ============================================================

@admin.register(HistorialCambio)
class HistorialCambioAdmin(admin.ModelAdmin):
    list_display = (
        "organizacion",
        "usuario",
        "campo",
        "valor_anterior_corto",
        "valor_nuevo_corto",
        "creado_en",
    )

    list_filter = (
        "campo",
        "usuario",
        "creado_en",
    )

    search_fields = (
        "organizacion__numero_pago",
        "organizacion__docente__nombre_completo",
        "organizacion__cedula_docente",
        "campo",
        "valor_anterior",
        "valor_nuevo",
        "descripcion",
    )

    autocomplete_fields = (
        "organizacion",
        "usuario",
    )

    readonly_fields = (
        "organizacion",
        "usuario",
        "campo",
        "valor_anterior",
        "valor_nuevo",
        "descripcion",
        "creado_en",
        "actualizado_en",
    )

    ordering = (
        "-creado_en",
    )

    list_per_page = 50

    @admin.display(description="Valor anterior")
    def valor_anterior_corto(self, obj):
        if not obj.valor_anterior:
            return "-"

        return obj.valor_anterior[:50] + "..." if len(obj.valor_anterior) > 50 else obj.valor_anterior

    @admin.display(description="Valor nuevo")
    def valor_nuevo_corto(self, obj):
        if not obj.valor_nuevo:
            return "-"

        return obj.valor_nuevo[:50] + "..." if len(obj.valor_nuevo) > 50 else obj.valor_nuevo

    def has_add_permission(self, request):
        """
        El historial no debería crearse manualmente desde el Admin.
        Más adelante lo llenaremos automáticamente.
        """
        return False

    def has_change_permission(self, request, obj=None):
        """
        Solo lectura.
        """
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """
        Solo el superusuario puede eliminar historial.
        """
        return request.user.is_superuser


@admin.register(CohorteProgramaPostgrado)
class CohorteProgramaPostgradoAdmin(admin.ModelAdmin):
    list_display = (
        "programa",
        "grupo",
        "facultad_nombre",
        "anio_reporte",
        "estado_informe",
        "matriculados_inicio",
        "matriculados_actualmente",
        "periodo_inicio",
        "periodo_finalizacion",
        "observacion",
        "activo",
    )

    list_filter = (
        "anio_reporte",
        "estado_informe",
        "periodo_inicio",
        "periodo_finalizacion",
        "programa__facultad",
        "activo",
    )

    search_fields = (
        "programa__nombre",
        "programa__facultad__nombre",
        "programa__facultad__siglas",
        "grupo",
        "inicio_texto",
        "finaliza_texto",
        "observacion",
    )

    autocomplete_fields = (
        "programa",
    )

    fieldsets = (
        (
            "Información del programa",
            {
                "fields": (
                    "programa",
                    "grupo",
                    "anio_reporte",
                    "estado_informe",
                    "activo",
                )
            },
        ),
        (
            "Matrícula",
            {
                "fields": (
                    "matriculados_inicio",
                    "matriculados_actualmente",
                )
            },
        ),
        (
            "Periodos",
            {
                "fields": (
                    "periodo_inicio",
                    "periodo_finalizacion",
                    "inicio_texto",
                    "finaliza_texto",
                )
            },
        ),
        (
            "Observación",
            {
                "fields": (
                    "observacion",
                )
            },
        ),
    )

    @admin.display(description="Facultad")
    def facultad_nombre(self, obj):
        return obj.programa.facultad
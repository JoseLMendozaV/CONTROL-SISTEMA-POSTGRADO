from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .exports import generar_excel_organizaciones

from .documents import (
    generar_pdf_nota_docente,
    generar_docx_nota_docente,
    generar_pdf_calendario_pago,
    generar_docx_calendario_pago,
)



from .forms import (
    FacultadForm,
    ProgramaPostgradoForm,
    DocenteForm,
    AsignaturaForm,
    OrganizacionDocenteForm,
    EstadoProcesoOrganizacionFormSet,
    DuplicarOrganizacionDocenteForm,
    ActualizacionMasivaEstadoForm,
    ImportarOrganizacionesExcelForm,
    OrganizacionDocenteFiltroForm,
    PlantillaDocumentoForm,
)

from .models import (
    Facultad,
    ProgramaPostgrado,
    Docente,
    Asignatura,
    OrganizacionDocente,
    EstadoProcesoOrganizacion,
    PlantillaDocumento,
)


# ============================================================
# Helpers de permisos básicos
# Más adelante los reforzaremos en la Parte 14 — Permisos por rol
# ============================================================

def pertenece_a_grupo(user, nombre_grupo):
    return user.groups.filter(name=nombre_grupo).exists()


def es_administrador(user):
    return user.is_superuser or pertenece_a_grupo(user, "Administrador")


def es_coordinador(user):
    return pertenece_a_grupo(user, "Coordinador de Postgrado")


def es_consulta(user):
    return pertenece_a_grupo(user, "Consulta")


def puede_editar(user):
    return es_administrador(user) or es_coordinador(user)


def puede_eliminar(user):
    return es_administrador(user)


def puede_ver(user):
    return (
        user.is_authenticated
        and (
            es_administrador(user)
            or es_coordinador(user)
            or es_consulta(user)
            or user.is_staff
        )
    )


def validar_permiso_edicion(request):
    if not puede_editar(request.user):
        messages.error(
            request,
            "No tienes permiso para crear o editar registros."
        )
        return False
    return True


def validar_permiso_eliminacion(request):
    if not puede_eliminar(request.user):
        messages.error(
            request,
            "No tienes permiso para eliminar registros."
        )
        return False
    return True


# ============================================================
# Helpers generales
# ============================================================

def paginar_queryset(request, queryset, cantidad=15):
    paginator = Paginator(queryset, cantidad)
    numero_pagina = request.GET.get("page")
    return paginator.get_page(numero_pagina)


def queryset_organizaciones_base():
    return (
        OrganizacionDocente.objects
        .filter(activo=True)
        .select_related(
            "docente",
            "facultad",
            "programa",
            "asignatura",
        )
        .prefetch_related("estados")
    )


def aplicar_filtros_organizaciones(queryset, form):
    """
    Aplica filtros al listado principal de organizaciones docentes.
    """

    if not form.is_valid():
        return queryset

    q = form.cleaned_data.get("q")
    anio = form.cleaned_data.get("anio")
    semestre = form.cleaned_data.get("semestre")
    facultad = form.cleaned_data.get("facultad")
    programa = form.cleaned_data.get("programa")
    docente = form.cleaned_data.get("docente")
    asignatura = form.cleaned_data.get("asignatura")
    estado_general = form.cleaned_data.get("estado_general")
    tipo_estado = form.cleaned_data.get("tipo_estado")
    situacion_estado = form.cleaned_data.get("situacion_estado")
    fecha_inicio = form.cleaned_data.get("fecha_inicio")
    fecha_fin = form.cleaned_data.get("fecha_fin")

    if q:
        queryset = queryset.filter(
            Q(numero_pago__icontains=q)
            | Q(docente__nombre_completo__icontains=q)
            | Q(docente__cedula__icontains=q)
            | Q(cedula_docente__icontains=q)
            | Q(facultad__nombre__icontains=q)
            | Q(facultad__siglas__icontains=q)
            | Q(programa__nombre__icontains=q)
            | Q(asignatura__nombre__icontains=q)
            | Q(asignatura__codigo_asignatura__icontains=q)
            | Q(codigo_asignatura__icontains=q)
            | Q(codigo_horario__icontains=q)
            | Q(grupo_aula__icontains=q)
            | Q(horario__icontains=q)
            | Q(fechas_clases__icontains=q)
            | Q(observaciones__icontains=q)
        )

    if anio:
        queryset = queryset.filter(anio=anio)

    if semestre:
        queryset = queryset.filter(semestre=semestre)

    if facultad:
        queryset = queryset.filter(facultad=facultad)

    if programa:
        queryset = queryset.filter(programa=programa)

    if docente:
        queryset = queryset.filter(docente=docente)

    if asignatura:
        queryset = queryset.filter(asignatura=asignatura)

    if fecha_inicio:
        queryset = queryset.filter(fecha_matricula__gte=fecha_inicio)

    if fecha_fin:
        queryset = queryset.filter(fecha_matricula__lte=fecha_fin)

    # Filtro por estado administrativo específico
    if tipo_estado:
        queryset = queryset.filter(estados__tipo_estado=tipo_estado)

        if situacion_estado == "completado":
            queryset = queryset.filter(estados__completado=True)

        elif situacion_estado == "pendiente":
            queryset = queryset.filter(estados__completado=False)

        queryset = queryset.distinct()

    # Filtro por estado general calculado
    if estado_general:
        total_estados = len(EstadoProcesoOrganizacion.TIPO_ESTADO_CHOICES)

        queryset = queryset.annotate(
            total_completados=Count(
                "estados",
                filter=Q(estados__completado=True),
                distinct=True,
            )
        )

        if estado_general == "sin_iniciar":
            queryset = queryset.filter(total_completados=0)

        elif estado_general == "completo":
            queryset = queryset.filter(total_completados=total_estados)

        elif estado_general == "en_proceso":
            queryset = queryset.filter(
                total_completados__gt=0,
                total_completados__lt=total_estados,
            )

        elif estado_general == "enviado":
            estados_enviados = [
                "organizacion_enviada_vipe",
                "organizacion_con_numero_posicion",
                "organizacion_enviada_firma_electronica",
                "firmado_por_autoridades",
                "organizacion_enviada_recursos_humanos",
            ]

            queryset = queryset.filter(
                estados__tipo_estado__in=estados_enviados,
                estados__completado=True,
            ).exclude(
                total_completados=total_estados
            ).distinct()

    return queryset.distinct()


def guardar_formset_estados(formset, usuario):
    """
    Guarda los estados administrativos y asigna usuario/fecha
    cuando un estado se marca como completado.
    """

    estados = formset.save(commit=False)

    for estado in estados:
        if estado.completado:
            if not estado.fecha_completado:
                estado.fecha_completado = timezone.now()

            if not estado.usuario_completo:
                estado.usuario_completo = usuario
        else:
            estado.fecha_completado = None
            estado.usuario_completo = None

        estado.save()

    formset.save_m2m()


# ============================================================
# Dashboard principal
# ============================================================

@login_required
def dashboard(request):
    """
    Dashboard ejecutivo del sistema de organización docente.
    Muestra resumen general, estados administrativos, finanzas,
    distribución por facultad, año, semestre y últimos registros.
    """

    organizaciones = queryset_organizaciones_base()
    total_organizaciones = organizaciones.count()

    total_estados = len(EstadoProcesoOrganizacion.TIPO_ESTADO_CHOICES)

    organizaciones_anotadas = organizaciones.annotate(
        total_completados=Count(
            "estados",
            filter=Q(estados__completado=True),
            distinct=True,
        )
    )

    def porcentaje(valor, total):
        if not total:
            return 0
        return round((valor / total) * 100, 2)

    # ========================================================
    # Totales financieros
    # ========================================================
    totales = organizaciones.aggregate(
        total_ingresos=Sum("total_ingresos"),
        total_pagos=Sum("pago_docente"),
        utilidad_neta=Sum("utilidad_neta"),
        ingreso_laboratorio=Sum("ingreso_laboratorio"),
    )

    total_ingresos = totales.get("total_ingresos") or Decimal("0.00")
    total_pagos = totales.get("total_pagos") or Decimal("0.00")
    utilidad_neta = totales.get("utilidad_neta") or Decimal("0.00")
    ingreso_laboratorio = totales.get("ingreso_laboratorio") or Decimal("0.00")

    # ========================================================
    # Estados generales
    # ========================================================
    organizaciones_completas = organizaciones_anotadas.filter(
        total_completados=total_estados
    ).count()

    organizaciones_sin_iniciar = organizaciones_anotadas.filter(
        total_completados=0
    ).count()

    organizaciones_en_proceso = organizaciones_anotadas.filter(
        total_completados__gt=0,
        total_completados__lt=total_estados,
    ).count()

    estados_enviados = [
        "organizacion_enviada_vipe",
        "organizacion_con_numero_posicion",
        "organizacion_enviada_firma_electronica",
        "firmado_por_autoridades",
        "organizacion_enviada_recursos_humanos",
    ]

    organizaciones_enviadas = organizaciones_anotadas.filter(
        estados__tipo_estado__in=estados_enviados,
        estados__completado=True,
    ).exclude(
        total_completados=total_estados
    ).distinct().count()

    resumen_estados = [
        {
            "nombre": "Proceso completo",
            "total": organizaciones_completas,
            "porcentaje": porcentaje(organizaciones_completas, total_organizaciones),
            "clase": "bg-green-500",
            "badge": "bg-green-100 text-green-800",
        },
        {
            "nombre": "En proceso",
            "total": organizaciones_en_proceso,
            "porcentaje": porcentaje(organizaciones_en_proceso, total_organizaciones),
            "clase": "bg-yellow-500",
            "badge": "bg-yellow-100 text-yellow-800",
        },
        {
            "nombre": "Enviado a otra unidad",
            "total": organizaciones_enviadas,
            "porcentaje": porcentaje(organizaciones_enviadas, total_organizaciones),
            "clase": "bg-blue-500",
            "badge": "bg-blue-100 text-blue-800",
        },
        {
            "nombre": "Sin iniciar",
            "total": organizaciones_sin_iniciar,
            "porcentaje": porcentaje(organizaciones_sin_iniciar, total_organizaciones),
            "clase": "bg-slate-400",
            "badge": "bg-slate-100 text-slate-700",
        },
    ]

    # ========================================================
    # Pendientes clave
    # ========================================================
    pendientes_vipe = organizaciones.filter(
        estados__tipo_estado="organizacion_enviada_vipe",
        estados__completado=False,
    ).distinct().count()

    pendientes_firma = organizaciones.filter(
        estados__tipo_estado="organizacion_enviada_firma_electronica",
        estados__completado=False,
    ).distinct().count()

    pendientes_rh = organizaciones.filter(
        estados__tipo_estado="organizacion_enviada_recursos_humanos",
        estados__completado=False,
    ).distinct().count()

    actas_pendientes = organizaciones.filter(
        estados__tipo_estado="acta_recibida",
        estados__completado=False,
    ).distinct().count()

    calendarios_pendientes = organizaciones.filter(
        estados__tipo_estado="calendario_pago_elaborado_enviado",
        estados__completado=False,
    ).distinct().count()

    pendientes_clave = [
        {
            "titulo": "Pendientes VIPE",
            "total": pendientes_vipe,
            "descripcion": "Organizaciones sin envío a VIPE",
            "color": "text-yellow-700",
            "fondo": "bg-yellow-50",
            "borde": "border-yellow-200",
        },
        {
            "titulo": "Pendientes firma",
            "total": pendientes_firma,
            "descripcion": "Sin firma electrónica",
            "color": "text-red-700",
            "fondo": "bg-red-50",
            "borde": "border-red-200",
        },
        {
            "titulo": "Pendientes RH",
            "total": pendientes_rh,
            "descripcion": "Sin envío a Recursos Humanos",
            "color": "text-blue-700",
            "fondo": "bg-blue-50",
            "borde": "border-blue-200",
        },
        {
            "titulo": "Actas pendientes",
            "total": actas_pendientes,
            "descripcion": "Actas aún no recibidas",
            "color": "text-indigo-700",
            "fondo": "bg-indigo-50",
            "borde": "border-indigo-200",
        },
        {
            "titulo": "Calendarios pendientes",
            "total": calendarios_pendientes,
            "descripcion": "Calendarios de pago no enviados",
            "color": "text-orange-700",
            "fondo": "bg-orange-50",
            "borde": "border-orange-200",
        },
    ]

    # ========================================================
    # Agrupaciones
    # ========================================================
    total_por_facultad = list(
        organizaciones
        .values("facultad__nombre", "facultad__siglas")
        .annotate(
            total=Count("id"),
            total_ingresos=Sum("total_ingresos"),
            total_pagos=Sum("pago_docente"),
            utilidad_neta=Sum("utilidad_neta"),
        )
        .order_by("-total", "facultad__nombre")
    )

    for item in total_por_facultad:
        item["porcentaje"] = porcentaje(item["total"], total_organizaciones)
        item["total_ingresos"] = item["total_ingresos"] or Decimal("0.00")
        item["total_pagos"] = item["total_pagos"] or Decimal("0.00")
        item["utilidad_neta"] = item["utilidad_neta"] or Decimal("0.00")

    total_por_semestre = list(
        organizaciones
        .values("semestre")
        .annotate(total=Count("id"))
        .order_by("semestre")
    )

    for item in total_por_semestre:
        item["porcentaje"] = porcentaje(item["total"], total_organizaciones)

    total_por_anio = list(
        organizaciones
        .values("anio")
        .annotate(total=Count("id"))
        .order_by("-anio")
    )

    for item in total_por_anio:
        item["porcentaje"] = porcentaje(item["total"], total_organizaciones)

    top_programas_utilidad = list(
        organizaciones
        .values(
            "programa__nombre",
            "facultad__siglas",
        )
        .annotate(
            total=Count("id"),
            total_ingresos=Sum("total_ingresos"),
            total_pagos=Sum("pago_docente"),
            utilidad_neta=Sum("utilidad_neta"),
        )
        .order_by("-utilidad_neta")[:6]
    )

    for item in top_programas_utilidad:
        item["total_ingresos"] = item["total_ingresos"] or Decimal("0.00")
        item["total_pagos"] = item["total_pagos"] or Decimal("0.00")
        item["utilidad_neta"] = item["utilidad_neta"] or Decimal("0.00")

    ultimas_organizaciones = organizaciones.order_by("-creado_en")[:8]

    context = {
        "titulo": "Dashboard de Organización Docente",
        "fecha_actual": timezone.now(),

        # Totales principales
        "total_organizaciones": total_organizaciones,
        "total_ingresos": total_ingresos,
        "total_pagos": total_pagos,
        "utilidad_neta": utilidad_neta,
        "ingreso_laboratorio": ingreso_laboratorio,

        # Estados generales
        "organizaciones_completas": organizaciones_completas,
        "organizaciones_en_proceso": organizaciones_en_proceso,
        "organizaciones_enviadas": organizaciones_enviadas,
        "organizaciones_sin_iniciar": organizaciones_sin_iniciar,
        "resumen_estados": resumen_estados,

        # Pendientes clave
        "pendientes_vipe": pendientes_vipe,
        "pendientes_firma": pendientes_firma,
        "pendientes_rh": pendientes_rh,
        "actas_pendientes": actas_pendientes,
        "calendarios_pendientes": calendarios_pendientes,
        "pendientes_clave": pendientes_clave,

        # Agrupaciones
        "total_por_facultad": total_por_facultad,
        "total_por_semestre": total_por_semestre,
        "total_por_anio": total_por_anio,
        "top_programas_utilidad": top_programas_utilidad,

        # Últimos registros
        "ultimas_organizaciones": ultimas_organizaciones,
    }

    return render(request, "organizacion_docente/dashboard.html", context)

# ============================================================
# Organización Docente — Listado, detalle, crear, editar, eliminar
# ============================================================

@login_required
def organizacion_listado(request):
    organizaciones = queryset_organizaciones_base()

    filtro_form = OrganizacionDocenteFiltroForm(request.GET or None)
    organizaciones = aplicar_filtros_organizaciones(
        organizaciones,
        filtro_form
    ).order_by("-anio", "semestre", "facultad__nombre", "programa__nombre")

    total_filtrado = organizaciones.count()

    totales_filtrados = organizaciones.aggregate(
        total_ingresos=Sum("total_ingresos"),
        total_pagos=Sum("pago_docente"),
        utilidad_neta=Sum("utilidad_neta"),
    )

    page_obj = paginar_queryset(request, organizaciones, cantidad=15)

    query_params = request.GET.copy()

    if "page" in query_params:
        query_params.pop("page")

    querystring = query_params.urlencode()

    context = {
        "titulo": "Organizaciones Docentes",
        "organizaciones": page_obj,
        "page_obj": page_obj,
        "filtro_form": filtro_form,
        "total_filtrado": total_filtrado,
        "total_ingresos_filtrado": totales_filtrados.get("total_ingresos") or Decimal("0.00"),
        "total_pagos_filtrado": totales_filtrados.get("total_pagos") or Decimal("0.00"),
        "utilidad_neta_filtrada": totales_filtrados.get("utilidad_neta") or Decimal("0.00"),
        "form_actualizacion_masiva": ActualizacionMasivaEstadoForm(),
        "querystring": querystring,
    }

    return render(
        request,
        "organizacion_docente/organizacion_list.html",
        context
    )


@login_required
def organizacion_detalle(request, pk):
    organizacion = get_object_or_404(
        queryset_organizaciones_base(),
        pk=pk,
    )

    # Por seguridad, si por alguna razón no existen los estados,
    # se vuelven a crear.
    organizacion.crear_estados_iniciales()

    estados = organizacion.estados.select_related(
        "usuario_completo"
    ).order_by("id")

    context = {
        "titulo": "Detalle de Organización Docente",
        "organizacion": organizacion,
        "estados": estados,
    }

    return render(
        request,
        "organizacion_docente/organizacion_detail.html",
        context
    )


@login_required
def organizacion_crear(request):
    if not validar_permiso_edicion(request):
        return redirect("organizacion_listado")

    if request.method == "POST":
        form = OrganizacionDocenteForm(request.POST)

        if form.is_valid():
            organizacion = form.save()

            messages.success(
                request,
                "La organización docente fue creada correctamente."
            )

            return redirect(
                "organizacion_detalle",
                pk=organizacion.pk,
            )
        else:
            messages.error(
                request,
                "Revisa los errores del formulario antes de continuar."
            )
    else:
        form = OrganizacionDocenteForm(
            initial={
                "anio": timezone.now().year,
                "activo": True,
            }
        )

    context = {
        "titulo": "Crear Organización Docente",
        "form": form,
        "modo": "crear",
    }

    return render(
        request,
        "organizacion_docente/organizacion_form.html",
        context
    )


@login_required
def organizacion_editar(request, pk):
    if not validar_permiso_edicion(request):
        return redirect("organizacion_detalle", pk=pk)

    organizacion = get_object_or_404(
        queryset_organizaciones_base(),
        pk=pk,
    )

    organizacion.crear_estados_iniciales()

    if request.method == "POST":
        form = OrganizacionDocenteForm(
            request.POST,
            instance=organizacion,
        )

        formset = EstadoProcesoOrganizacionFormSet(
            request.POST,
            instance=organizacion,
        )

        if form.is_valid() and formset.is_valid():
            organizacion = form.save()
            guardar_formset_estados(formset, request.user)

            messages.success(
                request,
                "La organización docente fue actualizada correctamente."
            )

            return redirect(
                "organizacion_detalle",
                pk=organizacion.pk,
            )
        else:
            messages.error(
                request,
                "Revisa los errores del formulario antes de continuar."
            )
    else:
        form = OrganizacionDocenteForm(instance=organizacion)
        formset = EstadoProcesoOrganizacionFormSet(instance=organizacion)

    context = {
        "titulo": "Editar Organización Docente",
        "form": form,
        "formset": formset,
        "organizacion": organizacion,
        "modo": "editar",
    }

    return render(
        request,
        "organizacion_docente/organizacion_form.html",
        context
    )


@login_required
def organizacion_eliminar(request, pk):
    if not validar_permiso_eliminacion(request):
        return redirect("organizacion_detalle", pk=pk)

    organizacion = get_object_or_404(
        OrganizacionDocente,
        pk=pk,
        activo=True,
    )

    if request.method == "POST":
        # Eliminación lógica para no perder trazabilidad.
        organizacion.activo = False
        organizacion.save()

        messages.success(
            request,
            "La organización docente fue eliminada del listado activo."
        )

        return redirect("organizacion_listado")

    context = {
        "titulo": "Eliminar Organización Docente",
        "organizacion": organizacion,
    }

    return render(
        request,
        "organizacion_docente/confirm_delete.html",
        context
    )


# ============================================================
# Organización Docente — Duplicar
# ============================================================

@login_required
def organizacion_duplicar(request, pk):
    if not validar_permiso_edicion(request):
        return redirect("organizacion_detalle", pk=pk)

    organizacion_original = get_object_or_404(
        queryset_organizaciones_base(),
        pk=pk,
    )

    if request.method == "POST":
        form = DuplicarOrganizacionDocenteForm(request.POST)

        if form.is_valid():
            nueva_organizacion = OrganizacionDocente.objects.create(
                numero_pago=form.cleaned_data.get("numero_pago") or None,
                docente=organizacion_original.docente,
                anio=form.cleaned_data["anio"],
                semestre=form.cleaned_data["semestre"],
                facultad=organizacion_original.facultad,
                programa=organizacion_original.programa,
                grupo_aula=form.cleaned_data.get("grupo_aula")
                or organizacion_original.grupo_aula,
                asignatura=organizacion_original.asignatura,
                total_horas=organizacion_original.total_horas,
                fechas_clases=organizacion_original.fechas_clases,
                horario=organizacion_original.horario,
                fecha_matricula=organizacion_original.fecha_matricula,
                cantidad_estudiantes_matriculados=organizacion_original.cantidad_estudiantes_matriculados,
                total_creditos=organizacion_original.total_creditos,
                total_laboratorio=organizacion_original.total_laboratorio,
                total_no_exonerados=organizacion_original.total_no_exonerados,
                cantidad_exoneracion_50=organizacion_original.cantidad_exoneracion_50,
                cantidad_exoneracion_25=organizacion_original.cantidad_exoneracion_25,
                ingreso_laboratorio=organizacion_original.ingreso_laboratorio,
                total_ingresos=organizacion_original.total_ingresos,
                pago_docente=organizacion_original.pago_docente,
                observaciones=(
                    f"Registro duplicado desde la organización #{organizacion_original.pk} "
                    f"el {timezone.now().strftime('%d/%m/%Y %H:%M')}."
                ),
                activo=True,
            )

            messages.success(
                request,
                "La organización docente fue duplicada correctamente."
            )

            return redirect(
                "organizacion_editar",
                pk=nueva_organizacion.pk,
            )
        else:
            messages.error(
                request,
                "Revisa los datos para duplicar la organización docente."
            )
    else:
        form = DuplicarOrganizacionDocenteForm(
            initial={
                "anio": organizacion_original.anio,
                "semestre": organizacion_original.semestre,
                "grupo_aula": organizacion_original.grupo_aula,
            }
        )

    context = {
        "titulo": "Duplicar Organización Docente",
        "form": form,
        "organizacion_original": organizacion_original,
    }

    return render(
        request,
        "organizacion_docente/organizacion_duplicar.html",
        context
    )


# ============================================================
# Organización Docente — Actualizar estado individual
# ============================================================

@login_required
@require_POST
def organizacion_marcar_estado(request, pk, tipo_estado):
    if not validar_permiso_edicion(request):
        return redirect("organizacion_detalle", pk=pk)

    organizacion = get_object_or_404(
        OrganizacionDocente,
        pk=pk,
        activo=True,
    )

    estado, creado = EstadoProcesoOrganizacion.objects.get_or_create(
        organizacion=organizacion,
        tipo_estado=tipo_estado,
    )

    accion = request.POST.get("accion", "completar")
    observacion = request.POST.get("observacion", "")

    if accion == "pendiente":
        estado.marcar_pendiente()
        messages.warning(
            request,
            f"El estado '{estado.get_tipo_estado_display()}' fue marcado como pendiente."
        )
    else:
        estado.marcar_completado(
            usuario=request.user,
            observacion=observacion,
        )

        messages.success(
            request,
            f"El estado '{estado.get_tipo_estado_display()}' fue marcado como completado."
        )

    return redirect("organizacion_detalle", pk=organizacion.pk)


# ============================================================
# Organización Docente — Actualización masiva de estados
# ============================================================

@login_required
@require_POST
def organizaciones_actualizacion_masiva(request):
    if not validar_permiso_edicion(request):
        return redirect("organizacion_listado")

    ids = request.POST.getlist("seleccionados")
    form = ActualizacionMasivaEstadoForm(request.POST)

    if not ids:
        messages.warning(
            request,
            "Debes seleccionar al menos una organización docente."
        )
        return redirect("organizacion_listado")

    if not form.is_valid():
        messages.error(
            request,
            "Los datos de actualización masiva no son válidos."
        )
        return redirect("organizacion_listado")

    tipo_estado = form.cleaned_data["tipo_estado"]
    completado = form.cleaned_data["completado"]
    observacion = form.cleaned_data.get("observacion") or ""

    organizaciones = OrganizacionDocente.objects.filter(
        id__in=ids,
        activo=True,
    )

    total_actualizadas = 0

    for organizacion in organizaciones:
        estado, creado = EstadoProcesoOrganizacion.objects.get_or_create(
            organizacion=organizacion,
            tipo_estado=tipo_estado,
        )

        if completado:
            estado.marcar_completado(
                usuario=request.user,
                observacion=observacion,
            )
        else:
            estado.marcar_pendiente()

        total_actualizadas += 1

    messages.success(
        request,
        f"Se actualizaron {total_actualizadas} organización(es) docente(s)."
    )

    return redirect("organizacion_listado")


# ============================================================
# CRUD — Facultades
# ============================================================

@login_required
def facultad_listado(request):
    facultades = Facultad.objects.all().order_by("nombre")

    q = request.GET.get("q")

    if q:
        facultades = facultades.filter(
            Q(nombre__icontains=q)
            | Q(siglas__icontains=q)
        )

    page_obj = paginar_queryset(request, facultades, cantidad=15)

    context = {
        "titulo": "Facultades",
        "facultades": page_obj,
        "page_obj": page_obj,
        "q": q,
    }

    return render(
        request,
        "organizacion_docente/facultad_list.html",
        context
    )


@login_required
def facultad_crear(request):
    if not validar_permiso_edicion(request):
        return redirect("facultad_listado")

    if request.method == "POST":
        form = FacultadForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "La facultad fue creada correctamente.")
            return redirect("facultad_listado")
    else:
        form = FacultadForm()

    context = {
        "titulo": "Crear Facultad",
        "form": form,
        "modo": "crear",
    }

    return render(
        request,
        "organizacion_docente/form_generico.html",
        context
    )


@login_required
def facultad_editar(request, pk):
    if not validar_permiso_edicion(request):
        return redirect("facultad_listado")

    facultad = get_object_or_404(Facultad, pk=pk)

    if request.method == "POST":
        form = FacultadForm(request.POST, instance=facultad)

        if form.is_valid():
            form.save()
            messages.success(request, "La facultad fue actualizada correctamente.")
            return redirect("facultad_listado")
    else:
        form = FacultadForm(instance=facultad)

    context = {
        "titulo": "Editar Facultad",
        "form": form,
        "modo": "editar",
        "objeto": facultad,
    }

    return render(
        request,
        "organizacion_docente/form_generico.html",
        context
    )


@login_required
def facultad_eliminar(request, pk):
    if not validar_permiso_eliminacion(request):
        return redirect("facultad_listado")

    facultad = get_object_or_404(Facultad, pk=pk)

    if request.method == "POST":
        facultad.activo = False
        facultad.save()

        messages.success(
            request,
            "La facultad fue marcada como inactiva."
        )

        return redirect("facultad_listado")

    context = {
        "titulo": "Eliminar Facultad",
        "objeto": facultad,
        "cancelar_url": "facultad_listado",
    }

    return render(
        request,
        "organizacion_docente/confirm_delete.html",
        context
    )


# ============================================================
# CRUD — Programas de Postgrado
# ============================================================

@login_required
def programa_listado(request):
    programas = ProgramaPostgrado.objects.select_related(
        "facultad"
    ).order_by("facultad__nombre", "nombre")

    q = request.GET.get("q")

    if q:
        programas = programas.filter(
            Q(nombre__icontains=q)
            | Q(codigo__icontains=q)
            | Q(facultad__nombre__icontains=q)
            | Q(facultad__siglas__icontains=q)
        )

    page_obj = paginar_queryset(request, programas, cantidad=15)

    context = {
        "titulo": "Programas de Postgrado",
        "programas": page_obj,
        "page_obj": page_obj,
        "q": q,
    }

    return render(
        request,
        "organizacion_docente/programa_list.html",
        context
    )


@login_required
def programa_crear(request):
    if not validar_permiso_edicion(request):
        return redirect("programa_listado")

    if request.method == "POST":
        form = ProgramaPostgradoForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "El programa fue creado correctamente.")
            return redirect("programa_listado")
    else:
        form = ProgramaPostgradoForm()

    context = {
        "titulo": "Crear Programa de Postgrado",
        "form": form,
        "modo": "crear",
    }

    return render(
        request,
        "organizacion_docente/form_generico.html",
        context
    )


@login_required
def programa_editar(request, pk):
    if not validar_permiso_edicion(request):
        return redirect("programa_listado")

    programa = get_object_or_404(ProgramaPostgrado, pk=pk)

    if request.method == "POST":
        form = ProgramaPostgradoForm(request.POST, instance=programa)

        if form.is_valid():
            form.save()
            messages.success(request, "El programa fue actualizado correctamente.")
            return redirect("programa_listado")
    else:
        form = ProgramaPostgradoForm(instance=programa)

    context = {
        "titulo": "Editar Programa de Postgrado",
        "form": form,
        "modo": "editar",
        "objeto": programa,
    }

    return render(
        request,
        "organizacion_docente/form_generico.html",
        context
    )


@login_required
def programa_eliminar(request, pk):
    if not validar_permiso_eliminacion(request):
        return redirect("programa_listado")

    programa = get_object_or_404(ProgramaPostgrado, pk=pk)

    if request.method == "POST":
        programa.activo = False
        programa.save()

        messages.success(
            request,
            "El programa fue marcado como inactivo."
        )

        return redirect("programa_listado")

    context = {
        "titulo": "Eliminar Programa",
        "objeto": programa,
        "cancelar_url": "programa_listado",
    }

    return render(
        request,
        "organizacion_docente/confirm_delete.html",
        context
    )


# ============================================================
# CRUD — Docentes
# ============================================================

@login_required
def docente_listado(request):
    docentes = Docente.objects.select_related(
        "facultad"
    ).order_by("nombre_completo")

    q = request.GET.get("q")

    if q:
        docentes = docentes.filter(
            Q(nombre_completo__icontains=q)
            | Q(cedula__icontains=q)
            | Q(correo__icontains=q)
            | Q(telefono__icontains=q)
            | Q(especialidad__icontains=q)
            | Q(facultad__nombre__icontains=q)
        )

    page_obj = paginar_queryset(request, docentes, cantidad=15)

    context = {
        "titulo": "Docentes",
        "docentes": page_obj,
        "page_obj": page_obj,
        "q": q,
    }

    return render(
        request,
        "organizacion_docente/docente_list.html",
        context
    )


@login_required
def docente_crear(request):
    if not validar_permiso_edicion(request):
        return redirect("docente_listado")

    if request.method == "POST":
        form = DocenteForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "El docente fue creado correctamente.")
            return redirect("docente_listado")
    else:
        form = DocenteForm()

    context = {
        "titulo": "Crear Docente",
        "form": form,
        "modo": "crear",
    }

    return render(
        request,
        "organizacion_docente/form_generico.html",
        context
    )


@login_required
def docente_editar(request, pk):
    if not validar_permiso_edicion(request):
        return redirect("docente_listado")

    docente = get_object_or_404(Docente, pk=pk)

    if request.method == "POST":
        form = DocenteForm(request.POST, instance=docente)

        if form.is_valid():
            form.save()
            messages.success(request, "El docente fue actualizado correctamente.")
            return redirect("docente_listado")
    else:
        form = DocenteForm(instance=docente)

    context = {
        "titulo": "Editar Docente",
        "form": form,
        "modo": "editar",
        "objeto": docente,
    }

    return render(
        request,
        "organizacion_docente/form_generico.html",
        context
    )


@login_required
def docente_eliminar(request, pk):
    if not validar_permiso_eliminacion(request):
        return redirect("docente_listado")

    docente = get_object_or_404(Docente, pk=pk)

    if request.method == "POST":
        docente.activo = False
        docente.save()

        messages.success(
            request,
            "El docente fue marcado como inactivo."
        )

        return redirect("docente_listado")

    context = {
        "titulo": "Eliminar Docente",
        "objeto": docente,
        "cancelar_url": "docente_listado",
    }

    return render(
        request,
        "organizacion_docente/confirm_delete.html",
        context
    )


# ============================================================
# CRUD — Asignaturas
# ============================================================

@login_required
def asignatura_listado(request):
    asignaturas = Asignatura.objects.select_related(
        "programa",
        "programa__facultad",
    ).order_by("programa__nombre", "nombre")

    q = request.GET.get("q")

    if q:
        asignaturas = asignaturas.filter(
            Q(nombre__icontains=q)
            | Q(codigo_asignatura__icontains=q)
            | Q(codigo_horario__icontains=q)
            | Q(programa__nombre__icontains=q)
            | Q(programa__facultad__nombre__icontains=q)
        )

    page_obj = paginar_queryset(request, asignaturas, cantidad=15)

    context = {
        "titulo": "Asignaturas",
        "asignaturas": page_obj,
        "page_obj": page_obj,
        "q": q,
    }

    return render(
        request,
        "organizacion_docente/asignatura_list.html",
        context
    )


@login_required
def asignatura_crear(request):
    if not validar_permiso_edicion(request):
        return redirect("asignatura_listado")

    if request.method == "POST":
        form = AsignaturaForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "La asignatura fue creada correctamente.")
            return redirect("asignatura_listado")
    else:
        form = AsignaturaForm()

    context = {
        "titulo": "Crear Asignatura",
        "form": form,
        "modo": "crear",
    }

    return render(
        request,
        "organizacion_docente/form_generico.html",
        context
    )


@login_required
def asignatura_editar(request, pk):
    if not validar_permiso_edicion(request):
        return redirect("asignatura_listado")

    asignatura = get_object_or_404(Asignatura, pk=pk)

    if request.method == "POST":
        form = AsignaturaForm(request.POST, instance=asignatura)

        if form.is_valid():
            form.save()
            messages.success(request, "La asignatura fue actualizada correctamente.")
            return redirect("asignatura_listado")
    else:
        form = AsignaturaForm(instance=asignatura)

    context = {
        "titulo": "Editar Asignatura",
        "form": form,
        "modo": "editar",
        "objeto": asignatura,
    }

    return render(
        request,
        "organizacion_docente/form_generico.html",
        context
    )


@login_required
def asignatura_eliminar(request, pk):
    if not validar_permiso_eliminacion(request):
        return redirect("asignatura_listado")

    asignatura = get_object_or_404(Asignatura, pk=pk)

    if request.method == "POST":
        asignatura.activo = False
        asignatura.save()

        messages.success(
            request,
            "La asignatura fue marcada como inactiva."
        )

        return redirect("asignatura_listado")

    context = {
        "titulo": "Eliminar Asignatura",
        "objeto": asignatura,
        "cancelar_url": "asignatura_listado",
    }

    return render(
        request,
        "organizacion_docente/confirm_delete.html",
        context
    )


# ============================================================
# Plantillas de documentos
# ============================================================

@login_required
def plantilla_listado(request):
    plantillas = PlantillaDocumento.objects.all().order_by(
        "tipo_documento",
        "nombre",
    )

    q = request.GET.get("q")

    if q:
        plantillas = plantillas.filter(
            Q(nombre__icontains=q)
            | Q(descripcion__icontains=q)
            | Q(contenido_html__icontains=q)
        )

    page_obj = paginar_queryset(request, plantillas, cantidad=15)

    context = {
        "titulo": "Plantillas de Documentos",
        "plantillas": page_obj,
        "page_obj": page_obj,
        "q": q,
    }

    return render(
        request,
        "organizacion_docente/plantilla_list.html",
        context
    )


@login_required
def plantilla_crear(request):
    if not validar_permiso_edicion(request):
        return redirect("plantilla_listado")

    if request.method == "POST":
        form = PlantillaDocumentoForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "La plantilla fue creada correctamente.")
            return redirect("plantilla_listado")
    else:
        form = PlantillaDocumentoForm()

    context = {
        "titulo": "Crear Plantilla",
        "form": form,
        "modo": "crear",
    }

    return render(
        request,
        "organizacion_docente/form_generico.html",
        context
    )


@login_required
def plantilla_editar(request, pk):
    if not validar_permiso_edicion(request):
        return redirect("plantilla_listado")

    plantilla = get_object_or_404(PlantillaDocumento, pk=pk)

    if request.method == "POST":
        form = PlantillaDocumentoForm(
            request.POST,
            request.FILES,
            instance=plantilla,
        )

        if form.is_valid():
            form.save()
            messages.success(request, "La plantilla fue actualizada correctamente.")
            return redirect("plantilla_listado")
    else:
        form = PlantillaDocumentoForm(instance=plantilla)

    context = {
        "titulo": "Editar Plantilla",
        "form": form,
        "modo": "editar",
        "objeto": plantilla,
    }

    return render(
        request,
        "organizacion_docente/form_generico.html",
        context
    )


# ============================================================
# Importación, exportación y documentos
# Estas vistas quedan listas como puente para las siguientes partes.
# ============================================================

@login_required
def importar_organizaciones_excel(request):
    if not validar_permiso_edicion(request):
        return redirect("organizacion_listado")

    if request.method == "POST":
        form = ImportarOrganizacionesExcelForm(request.POST, request.FILES)

        if form.is_valid():
            messages.info(
                request,
                "La importación desde Excel se conectará en la Parte 10."
            )
            return redirect("organizacion_listado")
    else:
        form = ImportarOrganizacionesExcelForm()

    context = {
        "titulo": "Importar Organizaciones desde Excel",
        "form": form,
    }

    return render(
        request,
        "organizacion_docente/importar_excel.html",
        context
    )


@login_required
def exportar_organizaciones_excel(request):
    """
    Exporta a Excel las organizaciones docentes.
    Respeta los filtros aplicados desde el listado principal.
    """

    organizaciones = queryset_organizaciones_base()

    filtro_form = OrganizacionDocenteFiltroForm(request.GET or None)

    organizaciones = aplicar_filtros_organizaciones(
        organizaciones,
        filtro_form,
    ).order_by(
        "-anio",
        "semestre",
        "facultad__nombre",
        "programa__nombre",
        "docente__nombre_completo",
    )

    return generar_excel_organizaciones(organizaciones)


@login_required
def generar_nota_docente(request, pk):
    """
    Genera la nota dirigida al docente.
    Formatos disponibles:
    - PDF:  ?formato=pdf
    - Word: ?formato=docx
    """

    organizacion = get_object_or_404(
        OrganizacionDocente.objects.select_related(
            "docente",
            "facultad",
            "programa",
            "asignatura",
        ),
        pk=pk,
        activo=True,
    )

    formato = request.GET.get("formato", "pdf").lower()

    if formato == "docx":
        return generar_docx_nota_docente(organizacion)

    return generar_pdf_nota_docente(
        organizacion=organizacion,
        request=request,
    )

@login_required
def generar_calendario_pago(request, pk):
    """
    Genera calendario de pago del docente.
    Formatos disponibles:
    - PDF:  ?formato=pdf
    - Word: ?formato=docx

    También permite dividir el pago:
    - ?formato=pdf&cuotas=2
    - ?formato=docx&cuotas=3
    """

    organizacion = get_object_or_404(
        OrganizacionDocente.objects.select_related(
            "docente",
            "facultad",
            "programa",
            "asignatura",
        ),
        pk=pk,
        activo=True,
    )

    formato = request.GET.get("formato", "pdf").lower()
    cuotas = request.GET.get("cuotas", 1)

    try:
        cuotas = int(cuotas)
    except (TypeError, ValueError):
        cuotas = 1

    if cuotas < 1:
        cuotas = 1

    if cuotas > 12:
        cuotas = 12

    if formato == "docx":
        return generar_docx_calendario_pago(
            organizacion=organizacion,
            cuotas=cuotas,
        )

    return generar_pdf_calendario_pago(
        organizacion=organizacion,
        request=request,
        cuotas=cuotas,
    )


# ============================================================
# Reportes
# ============================================================

@login_required
def reportes(request):
    organizaciones = queryset_organizaciones_base()

    totales = organizaciones.aggregate(
        total_ingresos=Sum("total_ingresos"),
        total_pagos=Sum("pago_docente"),
        utilidad_neta=Sum("utilidad_neta"),
    )

    por_facultad = (
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

    por_programa = (
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

    context = {
        "titulo": "Reportes",
        "total_ingresos": totales.get("total_ingresos") or Decimal("0.00"),
        "total_pagos": totales.get("total_pagos") or Decimal("0.00"),
        "utilidad_neta": totales.get("utilidad_neta") or Decimal("0.00"),
        "por_facultad": por_facultad,
        "por_programa": por_programa,
    }

    return render(
        request,
        "organizacion_docente/reportes.html",
        context
    )



# ============================================================
# AJAX — Combos dinámicos y autocompletado
# ============================================================

@login_required
def ajax_programas_por_facultad(request):
    facultad_id = request.GET.get("facultad_id")

    programas = ProgramaPostgrado.objects.filter(
        activo=True
    ).select_related("facultad").order_by("nombre")

    if facultad_id:
        programas = programas.filter(facultad_id=facultad_id)

    data = [
        {
            "id": programa.id,
            "nombre": programa.nombre,
            "codigo": programa.codigo or "",
            "facultad": programa.facultad.nombre,
            "facultad_siglas": programa.facultad.siglas or "",
        }
        for programa in programas
    ]

    return JsonResponse({"programas": data})


@login_required
def ajax_asignaturas_por_programa(request):
    programa_id = request.GET.get("programa_id")

    asignaturas = Asignatura.objects.filter(
        activo=True
    ).select_related("programa").order_by("nombre")

    if programa_id:
        asignaturas = asignaturas.filter(programa_id=programa_id)

    data = [
        {
            "id": asignatura.id,
            "nombre": asignatura.nombre,
            "codigo_asignatura": asignatura.codigo_asignatura or "",
            "codigo_horario": asignatura.codigo_horario or "",
            "total_horas": str(asignatura.total_horas or "0.00"),
            "total_creditos": str(asignatura.total_creditos or "0.00"),
            "total_laboratorio": str(asignatura.total_laboratorio or "0.00"),
        }
        for asignatura in asignaturas
    ]

    return JsonResponse({"asignaturas": data})


@login_required
def ajax_docentes_por_facultad(request):
    facultad_id = request.GET.get("facultad_id")

    docentes = Docente.objects.filter(
        activo=True
    ).select_related("facultad").order_by("nombre_completo")

    if facultad_id:
        docentes = docentes.filter(
            Q(facultad_id=facultad_id) | Q(facultad__isnull=True)
        )

    data = [
        {
            "id": docente.id,
            "nombre": docente.nombre_completo,
            "cedula": docente.cedula or "",
            "correo": docente.correo or "",
            "telefono": docente.telefono or "",
            "facultad": docente.facultad.nombre if docente.facultad else "",
        }
        for docente in docentes
    ]

    return JsonResponse({"docentes": data})


@login_required
def ajax_datos_docente(request):
    docente_id = request.GET.get("docente_id")

    if not docente_id:
        return JsonResponse({"error": "No se recibió docente_id."}, status=400)

    docente = get_object_or_404(Docente, pk=docente_id)

    data = {
        "id": docente.id,
        "nombre": docente.nombre_completo,
        "cedula": docente.cedula or "",
        "correo": docente.correo or "",
        "telefono": docente.telefono or "",
        "especialidad": docente.especialidad or "",
        "facultad_id": docente.facultad_id,
    }

    return JsonResponse(data)


@login_required
def ajax_datos_asignatura(request):
    asignatura_id = request.GET.get("asignatura_id")

    if not asignatura_id:
        return JsonResponse({"error": "No se recibió asignatura_id."}, status=400)

    asignatura = get_object_or_404(
        Asignatura.objects.select_related("programa", "programa__facultad"),
        pk=asignatura_id,
    )

    data = {
        "id": asignatura.id,
        "nombre": asignatura.nombre,
        "codigo_asignatura": asignatura.codigo_asignatura or "",
        "codigo_horario": asignatura.codigo_horario or "",
        "total_horas": str(asignatura.total_horas or "0.00"),
        "total_creditos": str(asignatura.total_creditos or "0.00"),
        "total_laboratorio": str(asignatura.total_laboratorio or "0.00"),
        "programa_id": asignatura.programa_id,
        "facultad_id": asignatura.programa.facultad_id,
    }

    return JsonResponse(data)
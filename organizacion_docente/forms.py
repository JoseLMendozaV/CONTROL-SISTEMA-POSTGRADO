from decimal import Decimal

from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone

from .models import (
    Facultad,
    ProgramaPostgrado,
    CohorteProgramaPostgrado,
    Docente,
    Asignatura,
    OrganizacionDocente,
    EstadoProcesoOrganizacion,
    PlantillaDocumento,
)

# ============================================================
# Mixin para aplicar clases Tailwind CSS a todos los formularios
# ============================================================

class TailwindFormMixin:
    """
    Agrega clases de Tailwind CSS automáticamente a los campos del formulario.
    Esto evita repetir clases campo por campo.
    """

    input_class = (
        "w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 "
        "text-slate-700 shadow-sm outline-none transition "
        "focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
    )

    select_class = (
        "w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 "
        "text-slate-700 shadow-sm outline-none transition "
        "focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
    )

    textarea_class = (
        "w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 "
        "text-slate-700 shadow-sm outline-none transition min-h-[110px] "
        "focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
    )

    checkbox_class = (
        "h-5 w-5 rounded border-slate-300 text-blue-600 "
        "focus:ring-blue-500"
    )

    file_class = (
        "w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 "
        "text-slate-700 shadow-sm file:mr-4 file:rounded-lg file:border-0 "
        "file:bg-blue-50 file:px-4 file:py-2 file:text-blue-700 "
        "hover:file:bg-blue-100"
    )

    readonly_class = (
        "w-full rounded-xl border border-slate-200 bg-slate-100 px-4 py-2.5 "
        "text-slate-500 shadow-sm cursor-not-allowed"
    )

    def aplicar_estilos_tailwind(self):
        for field_name, field in self.fields.items():
            widget = field.widget

            if isinstance(widget, forms.HiddenInput):
                continue

            current_class = widget.attrs.get("class", "")

            if field.disabled:
                css_class = self.readonly_class
            elif isinstance(widget, forms.CheckboxInput):
                css_class = self.checkbox_class
            elif isinstance(widget, forms.Select):
                css_class = self.select_class
            elif isinstance(widget, forms.Textarea):
                css_class = self.textarea_class
            elif isinstance(widget, forms.ClearableFileInput):
                css_class = self.file_class
            else:
                css_class = self.input_class

            widget.attrs["class"] = f"{current_class} {css_class}".strip()

            if field.required:
                widget.attrs["required"] = "required"


# ============================================================
# Facultad
# ============================================================

class FacultadForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Facultad
        fields = [
            "nombre",
            "siglas",
            "activo",
        ]

        labels = {
            "nombre": "Nombre de la facultad",
            "siglas": "Siglas",
            "activo": "Activo",
        }

        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "placeholder": "Ejemplo: Facultad de Ingeniería Eléctrica"
                }
            ),
            "siglas": forms.TextInput(
                attrs={
                    "placeholder": "Ejemplo: FIE"
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aplicar_estilos_tailwind()


# ============================================================
# Programa de Postgrado
# ============================================================

class ProgramaPostgradoForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = ProgramaPostgrado
        fields = [
            "facultad",
            "nombre",
            "codigo",
            "activo",
        ]

        labels = {
            "facultad": "Facultad",
            "nombre": "Nombre del programa",
            "codigo": "Código del programa",
            "activo": "Activo",
        }

        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "placeholder": "Ejemplo: Maestría en Seguridad Informática"
                }
            ),
            "codigo": forms.TextInput(
                attrs={
                    "placeholder": "Opcional"
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["facultad"].queryset = Facultad.objects.filter(
            activo=True
        ).order_by("nombre")

        self.aplicar_estilos_tailwind()

    def clean_nombre(self):
        nombre = self.cleaned_data.get("nombre")

        if nombre:
            nombre = nombre.strip()

        return nombre


# ============================================================
# Docente
# ============================================================

class DocenteForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Docente
        fields = [
            "facultad",
            "nombre_completo",
            "cedula",
            "correo",
            "telefono",
            "especialidad",
            "activo",
        ]

        labels = {
            "facultad": "Facultad relacionada",
            "nombre_completo": "Nombre completo",
            "cedula": "Cédula",
            "correo": "Correo electrónico",
            "telefono": "Teléfono",
            "especialidad": "Especialidad",
            "activo": "Activo",
        }

        widgets = {
            "nombre_completo": forms.TextInput(
                attrs={
                    "placeholder": "Nombre completo del docente"
                }
            ),
            "cedula": forms.TextInput(
                attrs={
                    "placeholder": "Ejemplo: 4-444-4444"
                }
            ),
            "correo": forms.EmailInput(
                attrs={
                    "placeholder": "correo@ejemplo.com"
                }
            ),
            "telefono": forms.TextInput(
                attrs={
                    "placeholder": "Ejemplo: 6666-0000"
                }
            ),
            "especialidad": forms.TextInput(
                attrs={
                    "placeholder": "Ejemplo: Automatización, Ciberseguridad, Educación Superior"
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["facultad"].queryset = Facultad.objects.filter(
            activo=True
        ).order_by("nombre")

        self.aplicar_estilos_tailwind()

    def clean_nombre_completo(self):
        nombre = self.cleaned_data.get("nombre_completo")

        if nombre:
            nombre = nombre.strip().title()

        return nombre

    def clean_cedula(self):
        cedula = self.cleaned_data.get("cedula")

        if cedula:
            cedula = cedula.strip()

        return cedula


# ============================================================
# Asignatura
# ============================================================

class AsignaturaForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Asignatura
        fields = [
            "programa",
            "nombre",
            "codigo_asignatura",
            "codigo_horario",
            "total_horas",
            "total_creditos",
            "total_laboratorio",
            "activo",
        ]

        labels = {
            "programa": "Programa de postgrado",
            "nombre": "Nombre de la asignatura",
            "codigo_asignatura": "Código de asignatura",
            "codigo_horario": "Código de horario",
            "total_horas": "Total de horas",
            "total_creditos": "Total de créditos",
            "total_laboratorio": "Total laboratorio",
            "activo": "Activo",
        }

        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "placeholder": "Ejemplo: Automatización Industrial"
                }
            ),
            "codigo_asignatura": forms.TextInput(
                attrs={
                    "placeholder": "Ejemplo: 4034"
                }
            ),
            "codigo_horario": forms.TextInput(
                attrs={
                    "placeholder": "Código de horario, si aplica"
                }
            ),
            "total_horas": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0"
                }
            ),
            "total_creditos": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0"
                }
            ),
            "total_laboratorio": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0"
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["programa"].queryset = ProgramaPostgrado.objects.filter(
            activo=True
        ).select_related("facultad").order_by("facultad__nombre", "nombre")

        self.aplicar_estilos_tailwind()

    def clean(self):
        cleaned_data = super().clean()

        total_horas = cleaned_data.get("total_horas") or Decimal("0.00")
        total_creditos = cleaned_data.get("total_creditos") or Decimal("0.00")
        total_laboratorio = cleaned_data.get("total_laboratorio") or Decimal("0.00")

        if total_horas < 0:
            self.add_error("total_horas", "El total de horas no puede ser negativo.")

        if total_creditos < 0:
            self.add_error("total_creditos", "El total de créditos no puede ser negativo.")

        if total_laboratorio < 0:
            self.add_error("total_laboratorio", "El total de laboratorio no puede ser negativo.")

        return cleaned_data


# ============================================================
# Organización Docente
# ============================================================

class OrganizacionDocenteForm(TailwindFormMixin, forms.ModelForm):
    """
    Formulario principal para crear y editar organizaciones docentes.
    Los campos calculados se muestran como solo lectura.
    """

    cedula_docente_display = forms.CharField(
        label="Cédula del docente",
        required=False,
        disabled=True,
    )

    codigo_asignatura_display = forms.CharField(
        label="Código de asignatura",
        required=False,
        disabled=True,
    )

    codigo_horario_display = forms.CharField(
        label="Código de horario",
        required=False,
        disabled=True,
    )

    utilidad_neta_display = forms.CharField(
        label="Utilidad neta",
        required=False,
        disabled=True,
    )

    class Meta:
        model = OrganizacionDocente

        fields = [
            # Información general
            "numero_pago",
            "anio",
            "semestre",
            "facultad",
            "programa",
            "activo",

            # Información del docente
            "docente",

            # Campos solo visuales
            "cedula_docente_display",

            # Información académica
            "asignatura",
            "codigo_asignatura_display",
            "codigo_horario_display",
            "grupo_aula",
            "total_horas",
            "fechas_clases",
            "horario",
            "total_creditos",
            "total_laboratorio",

            # Matrícula
            "fecha_matricula",

            # Calendario de matrícula y pago
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

            # Finanzas
            "ingreso_laboratorio",
            "total_ingresos",
            "pago_docente",
            "utilidad_neta_display",

            # Observaciones
            "observaciones",


            # Informe anual de programas
            "incluir_en_informe_programas",
            "estado_informe_programa",
            "matriculados_inicio_programa",
            "matriculados_actuales_programa",
            "periodo_inicio_programa",
            "periodo_finalizacion_programa",
            "inicio_texto_programa",
            "finaliza_texto_programa",
            "observacion_informe_programa",
        ]

        labels = {
            "numero_pago": "Número de pago",
            "anio": "Año académico",
            "semestre": "Semestre",
            "facultad": "Facultad",
            "programa": "Programa de postgrado",
            "activo": "Activo",
            "docente": "Docente",
            "asignatura": "Asignatura",
            "grupo_aula": "Grupo / Aula",
            "total_horas": "Total de horas",
            "fechas_clases": "Fechas de clases",
            "horario": "Horario",
            "total_creditos": "Total de créditos",
            "total_laboratorio": "Total laboratorio",
            "fecha_matricula": "Fecha de matrícula",
            "cantidad_estudiantes_matriculados": "Cantidad de estudiantes matriculados",
            "total_no_exonerados": "Total no exonerados",
            "cantidad_exoneracion_50": "Cantidad de estudiantes con exoneración del 50%",
            "cantidad_exoneracion_25": "Cantidad de estudiantes con exoneración del 25%",
            "ingreso_laboratorio": "Ingreso por laboratorio B/.",
            "total_ingresos": "Total de ingresos",
            "pago_docente": "Pago del docente B/.",
            "observaciones": "Observaciones",
            "fecha_matricula_texto": "Fecha de matrícula para calendario",
            "primer_pago_texto": "Primer tercio / Pago total con descuento",
            "segundo_pago_texto": "Segundo tercio",
            "tercer_pago_texto": "Tercer tercio",
            "retiro_inclusion_texto": "Retiro/Inclusión de asignaturas",
            "retiro_fuera_texto": "Retiro fuera del periodo",


            "incluir_en_informe_programas": "Incluir en informe anual de programas",
            "estado_informe_programa": "Estado del programa en el informe",
            "matriculados_inicio_programa": "Matriculados al inicio del programa",
            "matriculados_actuales_programa": "Matriculados actualmente",
            "periodo_inicio_programa": "Periodo de inicio",
            "periodo_finalizacion_programa": "Periodo de finalización",
            "inicio_texto_programa": "Inicio texto",
            "finaliza_texto_programa": "Finaliza texto",
            "observacion_informe_programa": "Observación del informe",
        }

        widgets = {
            "numero_pago": forms.TextInput(
                attrs={
                    "placeholder": "Ejemplo: 1"
                }
            ),
            "anio": forms.NumberInput(
                attrs={
                    "min": "2000",
                    "max": "2100",
                    "placeholder": "Ejemplo: 2026"
                }
            ),
            "grupo_aula": forms.TextInput(
                attrs={
                    "placeholder": "Ejemplo: 2IL104"
                }
            ),
            "total_horas": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0"
                }
            ),
            "fechas_clases": forms.Textarea(
                attrs={
                    "placeholder": "Ejemplo: Del 30 de junio al 18 de julio de 2026, viernes y sábados"
                }
            ),
            "horario": forms.Textarea(
                attrs={
                    "placeholder": "Ejemplo: Viernes de 6:00 p.m. a 10:00 p.m. y sábados de 8:00 a.m. a 4:00 p.m."
                }
            ),
            "total_creditos": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0"
                }
            ),
            "total_laboratorio": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0"
                }
            ),
            "fecha_matricula": forms.DateInput(
                attrs={
                    "type": "date"
                },
                format="%Y-%m-%d"
            ),
            "cantidad_estudiantes_matriculados": forms.NumberInput(
                attrs={
                    "min": "0"
                }
            ),
            "total_no_exonerados": forms.NumberInput(
                attrs={
                    "min": "0"
                }
            ),
            "cantidad_exoneracion_50": forms.NumberInput(
                attrs={
                    "min": "0"
                }
            ),
            "cantidad_exoneracion_25": forms.NumberInput(
                attrs={
                    "min": "0"
                }
            ),
            "ingreso_laboratorio": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0"
                }
            ),
            "total_ingresos": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0"
                }
            ),
            "pago_docente": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0"
                }
            ),
            "observaciones": forms.Textarea(
                attrs={
                    "placeholder": "Observaciones generales de la organización docente"
                }
            ),
            # seccion de calendario de pago
            "fecha_matricula_texto": forms.TextInput(
                attrs={
                    "placeholder": "Ejemplo: 16 y 17 de junio, 2026"
                }
            ),
            "primer_pago_texto": forms.TextInput(
                attrs={
                    "placeholder": "Ejemplo: Del 17 al 30 de junio de 2026"
                }
            ),
            "segundo_pago_texto": forms.TextInput(
                attrs={
                    "placeholder": "Ejemplo: Del 1 al 15 de julio de 2026"
                }
            ),
            "tercer_pago_texto": forms.TextInput(
                attrs={
                    "placeholder": "Ejemplo: Del 16 al 27 de julio de 2026"
                }
            ),
            "retiro_inclusion_texto": forms.TextInput(
                attrs={
                    "placeholder": "Ejemplo: Del 22 al 28 de junio de 2026"
                }
            ),
            "retiro_fuera_texto": forms.TextInput(
                attrs={
                    "placeholder": "Ejemplo: Del 29 de junio al 24 de julio de 2026"
                }
            ),

            "inicio_texto_programa": forms.TextInput(
                attrs={
                    "placeholder": "Ejemplo: I Semestre, 2025 (Mayo, 2025)"
                }
            ),
            "finaliza_texto_programa": forms.TextInput(
                attrs={
                    "placeholder": "Ejemplo: Verano, 2027 (Enero - Abril, 2027)"
                }
            ),
            "observacion_informe_programa": forms.TextInput(
                attrs={
                    "placeholder": "Ejemplo: ACTIVO, CULMINÓ, ACTIVO AL 2026"
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["facultad"].queryset = Facultad.objects.filter(
            activo=True
        ).order_by("nombre")

        self.fields["programa"].queryset = ProgramaPostgrado.objects.filter(
            activo=True
        ).select_related("facultad").order_by("facultad__nombre", "nombre")

        self.fields["docente"].queryset = Docente.objects.filter(
            activo=True
        ).select_related("facultad").order_by("nombre_completo")

        self.fields["asignatura"].queryset = Asignatura.objects.filter(
            activo=True
        ).select_related("programa", "programa__facultad").order_by(
            "programa__nombre",
            "nombre"
        )

        self.fields["fecha_matricula"].input_formats = ["%Y-%m-%d"]

        instance = getattr(self, "instance", None)

        if instance and instance.pk:
            self.fields["cedula_docente_display"].initial = instance.cedula_docente or ""
            self.fields["codigo_asignatura_display"].initial = instance.codigo_asignatura or ""
            self.fields["codigo_horario_display"].initial = instance.codigo_horario or ""
            self.fields["utilidad_neta_display"].initial = f"B/. {instance.utilidad_neta:,.2f}"
        else:
            self.fields["cedula_docente_display"].initial = "Se completará al guardar"
            self.fields["codigo_asignatura_display"].initial = "Se completará al guardar"
            self.fields["codigo_horario_display"].initial = "Se completará al guardar"
            self.fields["utilidad_neta_display"].initial = "Se calculará al guardar"

        self.aplicar_estilos_tailwind()

    def clean_anio(self):
        anio = self.cleaned_data.get("anio")
        anio_actual = timezone.now().year

        if anio < 2000:
            raise forms.ValidationError("El año académico no puede ser menor a 2000.")

        if anio > anio_actual + 5:
            raise forms.ValidationError(
                f"El año académico no puede ser mayor a {anio_actual + 5}."
            )

        return anio

    def clean(self):
        cleaned_data = super().clean()

        facultad = cleaned_data.get("facultad")
        programa = cleaned_data.get("programa")
        asignatura = cleaned_data.get("asignatura")

        cantidad_estudiantes = cleaned_data.get("cantidad_estudiantes_matriculados") or 0
        total_no_exonerados = cleaned_data.get("total_no_exonerados") or 0
        exonerados_50 = cleaned_data.get("cantidad_exoneracion_50") or 0
        exonerados_25 = cleaned_data.get("cantidad_exoneracion_25") or 0

        ingreso_laboratorio = cleaned_data.get("ingreso_laboratorio") or Decimal("0.00")
        total_ingresos = cleaned_data.get("total_ingresos") or Decimal("0.00")
        pago_docente = cleaned_data.get("pago_docente") or Decimal("0.00")

        total_horas = cleaned_data.get("total_horas") or Decimal("0.00")
        total_creditos = cleaned_data.get("total_creditos") or Decimal("0.00")
        total_laboratorio = cleaned_data.get("total_laboratorio") or Decimal("0.00")

        incluir_en_informe = cleaned_data.get("incluir_en_informe_programas")
        estado_informe = cleaned_data.get("estado_informe_programa")

        if incluir_en_informe and not estado_informe:
            self.add_error(
                "estado_informe_programa",
                "Debes seleccionar si el programa continúa, inició o culminó."
            )

        if programa and facultad and programa.facultad_id != facultad.id:
            self.add_error(
                "programa",
                "El programa seleccionado no pertenece a la facultad indicada."
            )

        if asignatura and programa and asignatura.programa_id != programa.id:
            self.add_error(
                "asignatura",
                "La asignatura seleccionada no pertenece al programa indicado."
            )

        total_distribuido = total_no_exonerados + exonerados_50 + exonerados_25

        if total_distribuido > cantidad_estudiantes:
            self.add_error(
                "total_no_exonerados",
                "La suma de no exonerados, exonerados 50% y exonerados 25% no puede superar la cantidad matriculada."
            )

        if total_horas < 0:
            self.add_error("total_horas", "El total de horas no puede ser negativo.")

        if total_creditos < 0:
            self.add_error("total_creditos", "El total de créditos no puede ser negativo.")

        if total_laboratorio < 0:
            self.add_error("total_laboratorio", "El total laboratorio no puede ser negativo.")

        if ingreso_laboratorio < 0:
            self.add_error("ingreso_laboratorio", "El ingreso por laboratorio no puede ser negativo.")

        if total_ingresos < 0:
            self.add_error("total_ingresos", "El total de ingresos no puede ser negativo.")

        if pago_docente < 0:
            self.add_error("pago_docente", "El pago del docente no puede ser negativo.")

        return cleaned_data


# ============================================================
# Estado del proceso administrativo
# ============================================================

class EstadoProcesoOrganizacionForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = EstadoProcesoOrganizacion

        fields = [
            "tipo_estado",
            "completado",
            "fecha_completado",
            "observacion",
        ]

        labels = {
            "tipo_estado": "Estado",
            "completado": "Completado",
            "fecha_completado": "Fecha de completado",
            "observacion": "Observación",
        }

        widgets = {
            "fecha_completado": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local"
                },
                format="%Y-%m-%dT%H:%M"
            ),
            "observacion": forms.Textarea(
                attrs={
                    "rows": 2,
                    "placeholder": "Observación opcional"
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["tipo_estado"].disabled = True
        self.fields["fecha_completado"].required = False
        self.fields["observacion"].required = False

        self.fields["fecha_completado"].input_formats = [
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M:%S",
        ]

        self.aplicar_estilos_tailwind()

    def clean(self):
        cleaned_data = super().clean()

        completado = cleaned_data.get("completado")
        fecha_completado = cleaned_data.get("fecha_completado")

        if completado and not fecha_completado:
            cleaned_data["fecha_completado"] = timezone.now()

        if not completado:
            cleaned_data["fecha_completado"] = None

        return cleaned_data


EstadoProcesoOrganizacionFormSet = inlineformset_factory(
    OrganizacionDocente,
    EstadoProcesoOrganizacion,
    form=EstadoProcesoOrganizacionForm,
    extra=0,
    can_delete=False,
)


# ============================================================
# Plantilla de Documento
# ============================================================

class PlantillaDocumentoForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = PlantillaDocumento

        fields = [
            "nombre",
            "tipo_documento",
            "descripcion",
            "archivo",
            "contenido_html",
            "activo",
        ]

        labels = {
            "nombre": "Nombre de la plantilla",
            "tipo_documento": "Tipo de documento",
            "descripcion": "Descripción",
            "archivo": "Archivo de plantilla",
            "contenido_html": "Contenido HTML",
            "activo": "Activo",
        }

        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "placeholder": "Ejemplo: Nota estándar al docente"
                }
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "placeholder": "Descripción breve de la plantilla"
                }
            ),
            "contenido_html": forms.Textarea(
                attrs={
                    "placeholder": "Contenido HTML editable para generar PDF",
                    "rows": 12,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aplicar_estilos_tailwind()


# ============================================================
# Formulario para duplicar organización docente
# ============================================================

class DuplicarOrganizacionDocenteForm(TailwindFormMixin, forms.Form):
    anio = forms.IntegerField(
        label="Nuevo año académico",
        min_value=2000,
        max_value=2100,
        widget=forms.NumberInput(
            attrs={
                "placeholder": "Ejemplo: 2026"
            }
        )
    )

    semestre = forms.ChoiceField(
        label="Nuevo semestre",
        choices=OrganizacionDocente.SEMESTRE_CHOICES,
    )

    numero_pago = forms.CharField(
        label="Nuevo número de pago",
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Opcional"
            }
        )
    )

    grupo_aula = forms.CharField(
        label="Nuevo grupo / aula",
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Opcional"
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aplicar_estilos_tailwind()


# ============================================================
# Formulario para actualización masiva de estados
# ============================================================

class ActualizacionMasivaEstadoForm(TailwindFormMixin, forms.Form):
    tipo_estado = forms.ChoiceField(
        label="Estado a actualizar",
        choices=EstadoProcesoOrganizacion.TIPO_ESTADO_CHOICES,
    )

    completado = forms.BooleanField(
        label="Marcar como completado",
        required=False,
        initial=True,
    )

    observacion = forms.CharField(
        label="Observación",
        required=False,
        widget=forms.Textarea(
            attrs={
                "placeholder": "Observación opcional para esta actualización masiva",
                "rows": 3,
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aplicar_estilos_tailwind()


# ============================================================
# Formulario para importar desde Excel
# ============================================================

class ImportarOrganizacionesExcelForm(TailwindFormMixin, forms.Form):
    archivo_excel = forms.FileField(
        label="Archivo Excel",
        help_text="Sube un archivo .xlsx con las columnas originales de organización docente."
    )

    actualizar_existentes = forms.BooleanField(
        label="Actualizar registros existentes si coinciden",
        required=False,
        initial=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aplicar_estilos_tailwind()

    def clean_archivo_excel(self):
        archivo = self.cleaned_data.get("archivo_excel")

        if archivo:
            nombre = archivo.name.lower()

            if not nombre.endswith(".xlsx"):
                raise forms.ValidationError(
                    "El archivo debe estar en formato .xlsx."
                )

        return archivo


# ============================================================
# Formulario para filtros básicos de organización docente
# Se usará más adelante en la vista de listado.
# ============================================================

class OrganizacionDocenteFiltroForm(TailwindFormMixin, forms.Form):
    q = forms.CharField(
        label="Buscar",
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Buscar por docente, cédula, asignatura, programa o número de pago"
            }
        )
    )

    anio = forms.IntegerField(
        label="Año",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "placeholder": "Ejemplo: 2026"
            }
        )
    )

    semestre = forms.ChoiceField(
        label="Semestre",
        required=False,
        choices=[("", "Todos los semestres")] + OrganizacionDocente.SEMESTRE_CHOICES,
    )

    facultad = forms.ModelChoiceField(
        label="Facultad",
        required=False,
        queryset=Facultad.objects.none(),
        empty_label="Todas las facultades",
    )

    programa = forms.ModelChoiceField(
        label="Programa",
        required=False,
        queryset=ProgramaPostgrado.objects.none(),
        empty_label="Todos los programas",
    )

    docente = forms.ModelChoiceField(
        label="Docente",
        required=False,
        queryset=Docente.objects.none(),
        empty_label="Todos los docentes",
    )

    asignatura = forms.ModelChoiceField(
        label="Asignatura",
        required=False,
        queryset=Asignatura.objects.none(),
        empty_label="Todas las asignaturas",
    )

    estado_general = forms.ChoiceField(
        label="Estado general",
        required=False,
        choices=[
            ("", "Todos los estados"),
            ("sin_iniciar", "Sin iniciar"),
            ("en_proceso", "En proceso"),
            ("enviado", "Enviado a otra unidad"),
            ("completo", "Proceso completo"),
        ],
    )

    tipo_estado = forms.ChoiceField(
        label="Estado administrativo",
        required=False,
        choices=[("", "Todos los estados administrativos")]
        + EstadoProcesoOrganizacion.TIPO_ESTADO_CHOICES,
    )

    situacion_estado = forms.ChoiceField(
        label="Situación del estado",
        required=False,
        choices=[
            ("", "Completado o pendiente"),
            ("completado", "Completado"),
            ("pendiente", "Pendiente"),
        ],
    )

    fecha_inicio = forms.DateField(
        label="Fecha inicial",
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date"
            },
            format="%Y-%m-%d"
        )
    )

    fecha_fin = forms.DateField(
        label="Fecha final",
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date"
            },
            format="%Y-%m-%d"
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["facultad"].queryset = Facultad.objects.filter(
            activo=True
        ).order_by("nombre")

        self.fields["programa"].queryset = ProgramaPostgrado.objects.filter(
            activo=True
        ).select_related("facultad").order_by("facultad__nombre", "nombre")

        self.fields["docente"].queryset = Docente.objects.filter(
            activo=True
        ).select_related("facultad").order_by("nombre_completo")

        self.fields["asignatura"].queryset = Asignatura.objects.filter(
            activo=True
        ).select_related("programa", "programa__facultad").order_by(
            "programa__nombre",
            "nombre"
        )

        self.fields["fecha_inicio"].input_formats = ["%Y-%m-%d"]
        self.fields["fecha_fin"].input_formats = ["%Y-%m-%d"]

        self.aplicar_estilos_tailwind()

    def clean(self):
        cleaned_data = super().clean()

        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")
        tipo_estado = cleaned_data.get("tipo_estado")
        situacion_estado = cleaned_data.get("situacion_estado")

        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            self.add_error(
                "fecha_fin",
                "La fecha final no puede ser menor que la fecha inicial."
            )

        if situacion_estado and not tipo_estado:
            self.add_error(
                "tipo_estado",
                "Selecciona primero un estado administrativo."
            )

        return cleaned_data


class InformeProgramasFiltroForm(TailwindFormMixin, forms.Form):
    anio = forms.IntegerField(
        label="Año del informe",
        required=True,
        widget=forms.NumberInput(
            attrs={
                "placeholder": "Ejemplo: 2025"
            }
        ),
    )

    tipo_periodo = forms.ChoiceField(
        label="Tipo de periodo",
        required=False,
        choices=[
            ("TODO", "Todo el año"),
            ("SEMESTRE", "Por semestre"),
            ("CUATRIMESTRE", "Por cuatrimestre"),
            ("TRIMESTRE", "Por trimestre"),
            ("VERANO", "Verano"),
        ],
    )

    periodo = forms.ChoiceField(
        label="Periodo específico",
        required=False,
        choices=[
            ("", "Todos"),
            ("VERANO", "Verano"),
            ("I", "I Semestre"),
            ("II", "II Semestre"),
            ("C1", "I Cuatrimestre"),
            ("C2", "II Cuatrimestre"),
            ("C3", "III Cuatrimestre"),
            ("T1", "I Trimestre"),
            ("T2", "II Trimestre"),
            ("T3", "III Trimestre"),
            ("T4", "IV Trimestre"),
            ("ESPECIAL", "Periodo Especial"),
        ],
    )

    facultad = forms.ModelChoiceField(
        label="Facultad",
        required=False,
        queryset=Facultad.objects.none(),
        empty_label="Todas las facultades",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["facultad"].queryset = Facultad.objects.filter(
            activo=True
        ).order_by("nombre")

        self.aplicar_estilos_tailwind()
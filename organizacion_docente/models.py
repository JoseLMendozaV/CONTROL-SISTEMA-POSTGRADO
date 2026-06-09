from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone


class ModeloBase(models.Model):
    """
    Modelo base abstracto para campos comunes.
    """

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Facultad(ModeloBase):
    """
    Facultad o Centro Regional al que pertenece un programa,
    docente u organización docente.
    """

    nombre = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Nombre de la facultad"
    )
    siglas = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Siglas"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )

    class Meta:
        verbose_name = "Facultad"
        verbose_name_plural = "Facultades"
        ordering = ["nombre"]

    def __str__(self):
        if self.siglas:
            return f"{self.siglas} - {self.nombre}"
        return self.nombre


class ProgramaPostgrado(ModeloBase):
    """
    Programa de postgrado asociado a una facultad.
    """

    facultad = models.ForeignKey(
        Facultad,
        on_delete=models.PROTECT,
        related_name="programas",
        verbose_name="Facultad"
    )
    nombre = models.CharField(
        max_length=255,
        verbose_name="Nombre del programa"
    )
    codigo = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Código del programa"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )

    class Meta:
        verbose_name = "Programa de Postgrado"
        verbose_name_plural = "Programas de Postgrado"
        ordering = ["facultad__nombre", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["facultad", "nombre"],
                name="programa_unico_por_facultad"
            )
        ]

    def __str__(self):
        return self.nombre


class Docente(ModeloBase):
    """
    Docente de postgrado.
    """

    facultad = models.ForeignKey(
        Facultad,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="docentes",
        verbose_name="Facultad relacionada"
    )
    nombre_completo = models.CharField(
        max_length=200,
        verbose_name="Nombre completo"
    )
    cedula = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Cédula"
    )
    correo = models.EmailField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Correo electrónico"
    )
    telefono = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Teléfono"
    )
    especialidad = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Especialidad"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )

    class Meta:
        verbose_name = "Docente"
        verbose_name_plural = "Docentes"
        ordering = ["nombre_completo"]

    def __str__(self):
        return f"{self.nombre_completo} - {self.cedula}"


class Asignatura(ModeloBase):
    """
    Asignatura perteneciente a un programa de postgrado.
    """

    programa = models.ForeignKey(
        ProgramaPostgrado,
        on_delete=models.PROTECT,
        related_name="asignaturas",
        verbose_name="Programa de postgrado"
    )
    nombre = models.CharField(
        max_length=255,
        verbose_name="Nombre de la asignatura"
    )
    codigo_asignatura = models.CharField(
        max_length=50,
        verbose_name="Código de asignatura"
    )
    codigo_horario = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Código de horario"
    )
    total_horas = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Total de horas"
    )
    total_creditos = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Total de créditos"
    )
    total_laboratorio = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Total de laboratorio"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )

    class Meta:
        verbose_name = "Asignatura"
        verbose_name_plural = "Asignaturas"
        ordering = ["programa__nombre", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["programa", "codigo_asignatura"],
                name="codigo_asignatura_unico_por_programa"
            )
        ]

    def __str__(self):
        return f"{self.codigo_asignatura} - {self.nombre}"


class OrganizacionDocente(ModeloBase):
    """
    Modelo principal del sistema.
    Representa una organización docente por docente, asignatura,
    grupo, semestre y año académico.
    """

    SEMESTRE_CHOICES = [
        ("I", "I Semestre"),
        ("II", "II Semestre"),
        ("VERANO", "Verano"),
        ("ESPECIAL", "Periodo Especial"),
    ]

    numero_pago = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Número de pago"
    )

    docente = models.ForeignKey(
        Docente,
        on_delete=models.PROTECT,
        related_name="organizaciones",
        verbose_name="Docente"
    )

    cedula_docente = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Cédula del docente"
    )

    anio = models.PositiveIntegerField(
        verbose_name="Año académico"
    )

    semestre = models.CharField(
        max_length=20,
        choices=SEMESTRE_CHOICES,
        verbose_name="Semestre"
    )

    facultad = models.ForeignKey(
        Facultad,
        on_delete=models.PROTECT,
        related_name="organizaciones",
        verbose_name="Facultad"
    )

    programa = models.ForeignKey(
        ProgramaPostgrado,
        on_delete=models.PROTECT,
        related_name="organizaciones",
        verbose_name="Programa de postgrado"
    )

    grupo_aula = models.CharField(
        max_length=100,
        verbose_name="Grupo / Aula"
    )

    asignatura = models.ForeignKey(
        Asignatura,
        on_delete=models.PROTECT,
        related_name="organizaciones",
        verbose_name="Asignatura"
    )

    codigo_asignatura = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Código de asignatura"
    )

    codigo_horario = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Código de horario"
    )

    total_horas = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Total de horas"
    )

    fechas_clases = models.TextField(
        blank=True,
        null=True,
        verbose_name="Fechas de clases",
        help_text="Puede escribir las fechas separadas por coma, rango o descripción."
    )

    horario = models.TextField(
        blank=True,
        null=True,
        verbose_name="Horario"
    )

    fecha_matricula = models.DateField(
        blank=True,
        null=True,
        verbose_name="Fecha de matrícula"
    )

    cantidad_estudiantes_matriculados = models.PositiveIntegerField(
        default=0,
        verbose_name="Cantidad de estudiantes matriculados"
    )

    total_creditos = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Total de créditos"
    )

    total_laboratorio = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Total laboratorio"
    )

    total_no_exonerados = models.PositiveIntegerField(
        default=0,
        verbose_name="Total no exonerados"
    )

    cantidad_exoneracion_50 = models.PositiveIntegerField(
        default=0,
        verbose_name="Cantidad de estudiantes con exoneración del 50%"
    )

    cantidad_exoneracion_25 = models.PositiveIntegerField(
        default=0,
        verbose_name="Cantidad de estudiantes con exoneración del 25%"
    )

    ingreso_laboratorio = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Ingreso por laboratorio B/."
    )

    total_ingresos = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Total de ingresos"
    )

    pago_docente = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Pago del docente B/."
    )

    utilidad_neta = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Utilidad neta"
    )

    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )

    activo = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )

    class Meta:
        verbose_name = "Organización Docente"
        verbose_name_plural = "Organizaciones Docentes"
        ordering = ["-anio", "semestre", "facultad__nombre", "programa__nombre"]
        indexes = [
            models.Index(fields=["anio", "semestre"]),
            models.Index(fields=["numero_pago"]),
            models.Index(fields=["cedula_docente"]),
        ]

    def __str__(self):
        return f"{self.anio} - {self.semestre} - {self.docente.nombre_completo} - {self.asignatura.nombre}"

    def clean(self):
        """
        Validaciones lógicas antes de guardar.
        """

        if self.programa and self.facultad:
            if self.programa.facultad_id != self.facultad_id:
                raise ValidationError(
                    "El programa seleccionado no pertenece a la facultad indicada."
                )

        if self.asignatura and self.programa:
            if self.asignatura.programa_id != self.programa_id:
                raise ValidationError(
                    "La asignatura seleccionada no pertenece al programa indicado."
                )

    def save(self, *args, **kwargs):
        """
        Antes de guardar se sincronizan datos repetidos útiles para reportes
        e importaciones desde Excel.
        """

        if self.docente:
            self.cedula_docente = self.docente.cedula

        if self.asignatura:
            self.codigo_asignatura = self.asignatura.codigo_asignatura
            self.codigo_horario = self.asignatura.codigo_horario

            if not self.total_horas:
                self.total_horas = self.asignatura.total_horas

            if not self.total_creditos:
                self.total_creditos = self.asignatura.total_creditos

            if not self.total_laboratorio:
                self.total_laboratorio = self.asignatura.total_laboratorio

        self.utilidad_neta = self.calcular_utilidad_neta()

        self.full_clean()
        super().save(*args, **kwargs)

        self.crear_estados_iniciales()

    def calcular_utilidad_neta(self):
        """
        Utilidad neta = Total de ingresos - Pago del docente.
        """

        total_ingresos = self.total_ingresos or Decimal("0.00")
        pago_docente = self.pago_docente or Decimal("0.00")
        return total_ingresos - pago_docente

    def crear_estados_iniciales(self):
        """
        Crea automáticamente los estados administrativos para cada organización docente.
        """

        for codigo, nombre in EstadoProcesoOrganizacion.TIPO_ESTADO_CHOICES:
            EstadoProcesoOrganizacion.objects.get_or_create(
                organizacion=self,
                tipo_estado=codigo,
                defaults={
                    "completado": False,
                    "observacion": "",
                }
            )

    @property
    def total_estados(self):
        return self.estados.count()

    @property
    def total_estados_completados(self):
        return self.estados.filter(completado=True).count()

    @property
    def porcentaje_avance(self):
        total = self.total_estados

        if total == 0:
            return 0

        return round((self.total_estados_completados / total) * 100, 2)

    @property
    def proceso_completo(self):
        total = self.total_estados
        completados = self.total_estados_completados

        return total > 0 and total == completados

    @property
    def estado_general_codigo(self):
        """
        Retorna un código de estado general para pintar badges en el frontend.
        """

        total = self.total_estados
        completados = self.total_estados_completados

        if total == 0 or completados == 0:
            return "sin_iniciar"

        if completados == total:
            return "completo"

        estados_enviados = [
            "organizacion_enviada_vipe",
            "organizacion_con_numero_posicion",
            "organizacion_enviada_firma_electronica",
            "firmado_por_autoridades",
            "organizacion_enviada_recursos_humanos",
        ]

        if self.estados.filter(
            tipo_estado__in=estados_enviados,
            completado=True
        ).exists():
            return "enviado"

        return "en_proceso"

    @property
    def estado_general_texto(self):
        estados = {
            "sin_iniciar": "Sin iniciar",
            "en_proceso": "En proceso",
            "enviado": "Enviado a otra unidad",
            "completo": "Proceso completo",
            "pendiente": "Pendiente",
        }
        return estados.get(self.estado_general_codigo, "Sin definir")

    @property
    def estado_general_color(self):
        """
        Clases Tailwind sugeridas para mostrar el estado.
        """

        colores = {
            "sin_iniciar": "bg-gray-100 text-gray-700 border-gray-200",
            "en_proceso": "bg-yellow-100 text-yellow-800 border-yellow-200",
            "enviado": "bg-blue-100 text-blue-800 border-blue-200",
            "completo": "bg-green-100 text-green-800 border-green-200",
            "pendiente": "bg-red-100 text-red-800 border-red-200",
        }
        return colores.get(
            self.estado_general_codigo,
            "bg-gray-100 text-gray-700 border-gray-200"
        )

    def get_absolute_url(self):
        return reverse("organizacion_detalle", kwargs={"pk": self.pk})


class EstadoProcesoOrganizacion(ModeloBase):
    """
    Estado administrativo de una organización docente.
    Cada organización tendrá varios estados del proceso.
    """

    TIPO_ESTADO_CHOICES = [
        ("horario_elaborado", "Horario elaborado"),
        ("organizacion_docente_elaborada", "Organización docente elaborada"),
        ("calendario_pago_elaborado_enviado", "Calendario de pago elaborado y enviado"),
        ("organizacion_enviada_vipe", "Organización docente enviada a la VIPE"),
        ("organizacion_con_numero_posicion", "Organización docente con número de posición"),
        ("organizacion_enviada_firma_electronica", "Organización docente enviada para firma electrónica"),
        ("firmado_por_autoridades", "Firmado por autoridades"),
        ("organizacion_enviada_recursos_humanos", "Organización docente enviada a Recursos Humanos"),
        ("acta_recibida", "Acta recibida"),
        ("acta_firmada_enviada_rh", "Acta firmada enviada a Recursos Humanos"),
    ]

    organizacion = models.ForeignKey(
        OrganizacionDocente,
        on_delete=models.CASCADE,
        related_name="estados",
        verbose_name="Organización docente"
    )

    tipo_estado = models.CharField(
        max_length=100,
        choices=TIPO_ESTADO_CHOICES,
        verbose_name="Tipo de estado"
    )

    completado = models.BooleanField(
        default=False,
        verbose_name="Completado"
    )

    fecha_completado = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de completado"
    )

    usuario_completo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="estados_completados",
        verbose_name="Usuario que completó"
    )

    observacion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observación"
    )

    class Meta:
        verbose_name = "Estado del Proceso"
        verbose_name_plural = "Estados del Proceso"
        ordering = ["organizacion", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["organizacion", "tipo_estado"],
                name="estado_unico_por_organizacion"
            )
        ]

    def __str__(self):
        estado = "Completado" if self.completado else "Pendiente"
        return f"{self.get_tipo_estado_display()} - {estado}"

    def marcar_completado(self, usuario=None, observacion=None):
        """
        Marca el estado como completado.
        """

        self.completado = True
        self.fecha_completado = timezone.now()

        if usuario:
            self.usuario_completo = usuario

        if observacion is not None:
            self.observacion = observacion

        self.save()

    def marcar_pendiente(self):
        """
        Devuelve el estado a pendiente.
        """

        self.completado = False
        self.fecha_completado = None
        self.usuario_completo = None
        self.save()


class PlantillaDocumento(ModeloBase):
    """
    Plantillas editables para documentos:
    nota al docente, calendario de pago, reportes u otros.
    """

    TIPO_DOCUMENTO_CHOICES = [
        ("nota_docente", "Nota dirigida al docente"),
        ("calendario_pago", "Calendario de pago"),
        ("reporte", "Reporte"),
        ("otro", "Otro"),
    ]

    nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre de la plantilla"
    )

    tipo_documento = models.CharField(
        max_length=50,
        choices=TIPO_DOCUMENTO_CHOICES,
        verbose_name="Tipo de documento"
    )

    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción"
    )

    archivo = models.FileField(
        upload_to="plantillas/",
        blank=True,
        null=True,
        verbose_name="Archivo de plantilla"
    )

    contenido_html = models.TextField(
        blank=True,
        null=True,
        verbose_name="Contenido HTML",
        help_text="Plantilla HTML editable para generar PDF."
    )

    activo = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )

    class Meta:
        verbose_name = "Plantilla de Documento"
        verbose_name_plural = "Plantillas de Documentos"
        ordering = ["tipo_documento", "nombre"]

    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_documento_display()}"


class HistorialCambio(ModeloBase):
    """
    Historial de cambios de una organización docente.
    Más adelante se puede alimentar automáticamente desde signals o desde las vistas.
    """

    organizacion = models.ForeignKey(
        OrganizacionDocente,
        on_delete=models.CASCADE,
        related_name="historial",
        verbose_name="Organización docente"
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="cambios_organizacion_docente",
        verbose_name="Usuario"
    )

    campo = models.CharField(
        max_length=150,
        verbose_name="Campo modificado"
    )

    valor_anterior = models.TextField(
        blank=True,
        null=True,
        verbose_name="Valor anterior"
    )

    valor_nuevo = models.TextField(
        blank=True,
        null=True,
        verbose_name="Valor nuevo"
    )

    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción del cambio"
    )

    class Meta:
        verbose_name = "Historial de Cambio"
        verbose_name_plural = "Historial de Cambios"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.organizacion} - {self.campo}"
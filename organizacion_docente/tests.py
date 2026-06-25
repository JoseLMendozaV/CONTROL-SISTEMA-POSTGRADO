from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase, TestCase

from .documents import calcular_fechas_calendario_estudiantes, texto_periodo_academico
from .models import Asignatura, Docente, Facultad, OrganizacionDocente, ProgramaPostgrado


class CalendarioPagoEstudiantesTests(SimpleTestCase):
    def organizacion(self, **overrides):
        datos = {
            "fecha_matricula": date(2026, 6, 17),
            "fechas_clases": "Del 30 de junio al 27 de julio de 2026, viernes y sábados",
            "fecha_matricula_texto": "",
            "primer_pago_texto": "",
            "segundo_pago_texto": "",
            "tercer_pago_texto": "",
            "retiro_inclusion_texto": "",
            "retiro_fuera_texto": "",
            "total_creditos": Decimal("3.00"),
        }
        datos.update(overrides)
        return SimpleNamespace(**datos)

    def test_calcula_tercios_con_quincena_y_ultima_clase(self):
        fechas = calcular_fechas_calendario_estudiantes(self.organizacion())

        self.assertEqual(fechas["matricula"], "17 de junio de 2026")
        self.assertEqual(fechas["primer_pago"], "Del 17 al 30 de junio de 2026")
        self.assertEqual(fechas["segundo_pago"], "Del 1 al 15 de julio de 2026")
        self.assertEqual(fechas["tercer_pago"], "Del 16 al 27 de julio de 2026")
        self.assertEqual(fechas["retiro_inclusion"], "Del 22 al 28 de junio de 2026")
        self.assertEqual(
            fechas["retiro_fuera"],
            "Del 29 de junio de 2026 al 24 de julio de 2026",
        )

    def test_respeta_valores_manual_escritos(self):
        fechas = calcular_fechas_calendario_estudiantes(
            self.organizacion(primer_pago_texto="Fecha manual")
        )

        self.assertEqual(fechas["primer_pago"], "Fecha manual")
        self.assertEqual(fechas["segundo_pago"], "Del 1 al 15 de julio de 2026")

    def test_credito_unico_genera_un_solo_periodo_de_pago(self):
        fechas = calcular_fechas_calendario_estudiantes(
            self.organizacion(total_creditos=Decimal("1.00"))
        )

        self.assertTrue(fechas["pago_unico"])
        self.assertEqual(fechas["primer_pago"], "Del 17 de junio de 2026 al 27 de julio de 2026")
        self.assertEqual(fechas["segundo_pago"], "No aplica")
        self.assertEqual(fechas["tercer_pago"], "No aplica")


class FinanzasOrganizacionDocenteTests(SimpleTestCase):
    def test_calcula_ingresos_con_estudiantes_matriculados(self):
        organizacion = OrganizacionDocente(
            total_creditos=Decimal("3.00"),
            cantidad_estudiantes_matriculados=10,
        )

        self.assertEqual(
            organizacion.calcular_total_ingresos(),
            Decimal("2400.00"),
        )

    def test_calcula_ingresos_con_exoneraciones(self):
        organizacion = OrganizacionDocente(
            total_creditos=Decimal("3.00"),
            cantidad_estudiantes_matriculados=10,
            total_no_exonerados=4,
            cantidad_exoneracion_50=2,
            cantidad_exoneracion_25=2,
        )

        self.assertEqual(
            organizacion.estudiantes_equivalentes_pago(),
            Decimal("6.50"),
        )
        self.assertEqual(
            organizacion.calcular_total_ingresos(),
            Decimal("1560.00"),
        )

    def test_calcula_pago_docente_por_posicion(self):
        organizacion = OrganizacionDocente(
            tipo_posicion="32",
            cantidad_posiciones_a_utilizar=2,
            total_horas=Decimal("99.00"),
        )

        self.assertEqual(
            organizacion.calcular_pago_docente(),
            Decimal("2560.00"),
        )

    def test_calcula_pago_docente_por_hora_si_no_hay_posicion(self):
        organizacion = OrganizacionDocente(
            total_horas=Decimal("10.00"),
        )

        self.assertEqual(
            organizacion.calcular_pago_docente(),
            Decimal("400.00"),
        )

    def test_organizacion_sin_docente_tiene_textos_fallback(self):
        organizacion = OrganizacionDocente()

        self.assertEqual(
            organizacion.docente_nombre_display,
            "Docente por asignar",
        )
        self.assertEqual(
            organizacion.cedula_docente_display,
            "-",
        )


class CodigoHorarioOrganizacionDocenteTests(TestCase):
    def setUp(self):
        self.facultad = Facultad.objects.create(
            nombre="Facultad de Ingeniería",
            siglas="FI",
        )
        self.programa = ProgramaPostgrado.objects.create(
            facultad=self.facultad,
            nombre="Maestría en Sistemas",
        )
        self.asignatura = Asignatura.objects.create(
            programa=self.programa,
            nombre="Arquitectura de Software",
            codigo_asignatura="ASW-101",
            codigo_horario="HOR-ASIG",
            total_horas=Decimal("40.00"),
            total_creditos=Decimal("3.00"),
        )

    def organizacion(self, **overrides):
        datos = {
            "anio": 2026,
            "semestre": "I",
            "facultad": self.facultad,
            "programa": self.programa,
            "grupo_aula": "1MS101",
            "asignatura": self.asignatura,
        }
        datos.update(overrides)
        return OrganizacionDocente.objects.create(**datos)

    def test_respeta_codigo_horario_escrito_en_organizacion(self):
        organizacion = self.organizacion(codigo_horario="HOR-MANUAL")

        self.assertEqual(organizacion.codigo_horario, "HOR-MANUAL")

    def test_usa_codigo_horario_de_asignatura_si_organizacion_esta_vacio(self):
        organizacion = self.organizacion()

        self.assertEqual(organizacion.codigo_horario, "HOR-ASIG")


class TratamientoDocenteTests(SimpleTestCase):
    def test_tratamiento_magister_masculino(self):
        docente = Docente(
            nombre_completo="Juan Perez",
            cedula="1",
            sexo="M",
            grado_academico="MAGISTER",
        )

        self.assertEqual(docente.tratamiento_destinatario, "Magíster")
        self.assertEqual(docente.saludo_respetado, "Respetado")
        self.assertEqual(docente.tratamiento_saludo, "magíster")

    def test_tratamiento_doctora_femenino(self):
        docente = Docente(
            nombre_completo="Ana Perez",
            cedula="2",
            sexo="F",
            grado_academico="DOCTOR",
        )

        self.assertEqual(docente.tratamiento_destinatario, "Doctora")
        self.assertEqual(docente.saludo_respetado, "Respetada")
        self.assertEqual(docente.tratamiento_saludo, "doctora")


class TextoPeriodoAcademicoTests(SimpleTestCase):
    def test_muestra_cuatrimestre_completo(self):
        self.assertEqual(
            texto_periodo_academico("C3", 2026),
            "tercer cuatrimestre de 2026",
        )

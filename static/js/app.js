console.log("Sistema de Organización Docente cargado correctamente.");

document.addEventListener("DOMContentLoaded", function () {
    const facultadSelect = document.getElementById("id_facultad");
    const programaSelect = document.getElementById("id_programa");
    const asignaturaSelect = document.getElementById("id_asignatura");
    const docenteSelect = document.getElementById("id_docente");

    const cedulaDocenteDisplay = document.getElementById("id_cedula_docente_display");
    const codigoAsignaturaDisplay = document.getElementById("id_codigo_asignatura_display");
    const codigoHorarioDisplay = document.getElementById("id_codigo_horario_display");

    const totalHorasInput = document.getElementById("id_total_horas");
    const totalCreditosInput = document.getElementById("id_total_creditos");
    const totalLaboratorioInput = document.getElementById("id_total_laboratorio");
    const cantidadEstudiantesInput = document.getElementById("id_cantidad_estudiantes_matriculados");
    const totalNoExoneradosInput = document.getElementById("id_total_no_exonerados");
    const exoneracion50Input = document.getElementById("id_cantidad_exoneracion_50");
    const exoneracion25Input = document.getElementById("id_cantidad_exoneracion_25");
    const totalIngresosInput = document.getElementById("id_total_ingresos");
    const pagoDocenteInput = document.getElementById("id_pago_docente");
    const utilidadNetaInput = document.getElementById("id_utilidad_neta_display");
    const tipoPosicionSelect = document.getElementById("id_tipo_posicion");
    const montoUnitarioPosicionInput = document.getElementById("id_monto_unitario_posicion");
    const cantidadPosicionesUtilizarInput = document.getElementById("id_cantidad_posiciones_a_utilizar");

    const COSTO_CREDITO = 80;
    const TARIFA_HORA_DOCENTE = 40;
    const MONTOS_POSICION = {
        "16": 640,
        "32": 1280,
        "48": 1920,
        "64": 2560,
    };

    function numeroCampo(input) {
        if (!input) return 0;

        const valor = parseFloat(String(input.value || "0").replace(",", "."));
        return Number.isFinite(valor) ? valor : 0;
    }

    function formatoDecimal(valor) {
        return Number(valor || 0).toFixed(2);
    }

    function formatoMoneda(valor) {
        return `B/. ${Number(valor || 0).toLocaleString("en-US", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        })}`;
    }

    function estudiantesEquivalentesPago() {
        const estudiantes = numeroCampo(cantidadEstudiantesInput);
        const noExonerados = numeroCampo(totalNoExoneradosInput);
        const exonerados50 = numeroCampo(exoneracion50Input) * 0.5;
        const exonerados25 = numeroCampo(exoneracion25Input) * 0.75;
        const totalEquivalente = noExonerados + exonerados50 + exonerados25;

        return totalEquivalente > 0 ? totalEquivalente : estudiantes;
    }

    function calcularTotalIngresos() {
        return numeroCampo(totalCreditosInput) * COSTO_CREDITO * estudiantesEquivalentesPago();
    }

    function calcularPagoDocente() {
        const montoManualPosicion = numeroCampo(montoUnitarioPosicionInput);
        const tipoPosicion = tipoPosicionSelect ? tipoPosicionSelect.value : "";
        const montoPosicion = montoManualPosicion || MONTOS_POSICION[tipoPosicion] || 0;

        if (montoPosicion > 0) {
            const cantidadPosiciones = numeroCampo(cantidadPosicionesUtilizarInput) || 1;
            return montoPosicion * cantidadPosiciones;
        }

        return numeroCampo(totalHorasInput) * TARIFA_HORA_DOCENTE;
    }

    function calcularFinanzas() {
        const totalIngresos = calcularTotalIngresos();
        const pagoDocente = calcularPagoDocente();

        if (totalIngresosInput) {
            totalIngresosInput.value = formatoDecimal(totalIngresos);
        }

        if (pagoDocenteInput) {
            pagoDocenteInput.value = formatoDecimal(pagoDocente);
        }

        if (utilidadNetaInput) {
            utilidadNetaInput.value = formatoMoneda(totalIngresos - pagoDocente);
        }
    }

    function limpiarSelect(select, textoInicial) {
        if (!select) return;

        select.innerHTML = "";

        const option = document.createElement("option");
        option.value = "";
        option.textContent = textoInicial;
        select.appendChild(option);
    }

    function agregarOption(select, value, text) {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = text;
        select.appendChild(option);
    }

    async function cargarProgramasPorFacultad(facultadId) {
        if (!programaSelect) return;

        limpiarSelect(programaSelect, "Seleccione un programa");

        if (asignaturaSelect) {
            limpiarSelect(asignaturaSelect, "Seleccione una asignatura");
        }

        let url = "/ajax/programas/";

        if (facultadId) {
            url += `?facultad_id=${facultadId}`;
        }

        try {
            const response = await fetch(url);
            const data = await response.json();

            data.programas.forEach(programa => {
                agregarOption(programaSelect, programa.id, programa.nombre);
            });
        } catch (error) {
            console.error("Error cargando programas:", error);
        }
    }

    async function cargarAsignaturasPorPrograma(programaId) {
        if (!asignaturaSelect) return;

        limpiarSelect(asignaturaSelect, "Seleccione una asignatura");

        let url = "/ajax/asignaturas/";

        if (programaId) {
            url += `?programa_id=${programaId}`;
        }

        try {
            const response = await fetch(url);
            const data = await response.json();

            data.asignaturas.forEach(asignatura => {
                const texto = `${asignatura.codigo_asignatura} - ${asignatura.nombre}`;
                agregarOption(asignaturaSelect, asignatura.id, texto);
            });
        } catch (error) {
            console.error("Error cargando asignaturas:", error);
        }
    }

    async function cargarDocentesPorFacultad(facultadId) {
        if (!docenteSelect) return;

        limpiarSelect(docenteSelect, "Seleccione un docente");

        let url = "/ajax/docentes/";

        if (facultadId) {
            url += `?facultad_id=${facultadId}`;
        }

        try {
            const response = await fetch(url);
            const data = await response.json();

            data.docentes.forEach(docente => {
                const texto = `${docente.nombre} - ${docente.cedula}`;
                agregarOption(docenteSelect, docente.id, texto);
            });
        } catch (error) {
            console.error("Error cargando docentes:", error);
        }
    }

    async function cargarDatosDocente(docenteId) {
        if (!cedulaDocenteDisplay) return;

        if (!docenteId) {
            cedulaDocenteDisplay.value = "";
            return;
        }

        try {
            const response = await fetch(`/ajax/docente/datos/?docente_id=${docenteId}`);
            const data = await response.json();

            cedulaDocenteDisplay.value = data.cedula || "";
        } catch (error) {
            console.error("Error cargando datos del docente:", error);
        }
    }

    async function cargarDatosAsignatura(asignaturaId) {
        if (!asignaturaId) return;

        try {
            const response = await fetch(`/ajax/asignatura/datos/?asignatura_id=${asignaturaId}`);
            const data = await response.json();

            if (codigoAsignaturaDisplay) {
                codigoAsignaturaDisplay.value = data.codigo_asignatura || "";
            }

            if (codigoHorarioDisplay) {
                codigoHorarioDisplay.value = data.codigo_horario || "";
            }

            if (totalHorasInput && data.total_horas) {
                totalHorasInput.value = data.total_horas;
            }

            if (totalCreditosInput && data.total_creditos) {
                totalCreditosInput.value = data.total_creditos;
            }

            if (totalLaboratorioInput && data.total_laboratorio) {
                totalLaboratorioInput.value = data.total_laboratorio;
            }

            calcularFinanzas();
        } catch (error) {
            console.error("Error cargando datos de asignatura:", error);
        }
    }

    if (facultadSelect) {
        facultadSelect.addEventListener("change", function () {
            const facultadId = this.value;

            cargarProgramasPorFacultad(facultadId);
            cargarDocentesPorFacultad(facultadId);
        });
    }

    if (programaSelect) {
        programaSelect.addEventListener("change", function () {
            const programaId = this.value;
            cargarAsignaturasPorPrograma(programaId);
        });
    }

    if (docenteSelect) {
        docenteSelect.addEventListener("change", function () {
            const docenteId = this.value;
            cargarDatosDocente(docenteId);
        });
    }

    if (asignaturaSelect) {
        asignaturaSelect.addEventListener("change", function () {
            const asignaturaId = this.value;
            cargarDatosAsignatura(asignaturaId);
        });
    }

    [
        totalHorasInput,
        totalCreditosInput,
        cantidadEstudiantesInput,
        totalNoExoneradosInput,
        exoneracion50Input,
        exoneracion25Input,
        tipoPosicionSelect,
        montoUnitarioPosicionInput,
        cantidadPosicionesUtilizarInput,
    ].forEach(function (input) {
        if (!input) return;
        input.addEventListener("input", calcularFinanzas);
        input.addEventListener("change", calcularFinanzas);
    });

    calcularFinanzas();
});

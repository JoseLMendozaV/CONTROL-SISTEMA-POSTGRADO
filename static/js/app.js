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
        if (!docenteId || !cedulaDocenteDisplay) return;

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
});
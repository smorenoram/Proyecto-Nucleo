let estadoGlobal = {
    grupos: [],
    docentes: [],
    aulas: [],
    franjas: [],
    asignaciones: []
};

let rolActual = "COORDINADOR";
let idReferenciaSesion = "DOC-01";

const DIAS = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"];
const BLOQUES = [
    { num: 1, label: "Bloque 1 (07:00 - 09:00)" },
    { num: 2, label: "Bloque 2 (09:00 - 11:00)" },
    { num: 3, label: "Bloque 3 (14:00 - 16:00)" }
];

function esModoSoloLectura() {
    return rolActual === "ESTUDIANTE" || rolActual === "DOCENTE";
}

function cambiarVista(idVista) {
    document.querySelectorAll(".app-view").forEach(sec => {
        if (sec.id === idVista) {
            sec.classList.remove("hidden");
            sec.classList.add("active-view");
        } else {
            sec.classList.add("hidden");
            sec.classList.remove("active-view");
        }
    });
    document.querySelectorAll(".nav-item").forEach(btn => {
        if (btn.dataset.target === idVista) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });
}

function actualizarToast(mensaje, esError = false) {
    const toast = document.getElementById("status-toast");
    const txt = document.getElementById("status-toast-text");
    if (toast && txt) {
        txt.textContent = mensaje;
        toast.style.borderLeftColor = esError ? "#c9184a" : "#00794c";
        toast.style.background = esError ? "#fff0f3" : "#f0fdf4";
    }
}

function registrarLog(mensaje, esError = false) {
    const consola = document.getElementById("consola-log");
    const hora = new Date().toLocaleTimeString();
    if (consola) {
        consola.textContent += `[${hora}] ${mensaje}\n`;
        consola.scrollTop = consola.scrollHeight;
    }
    actualizarToast(mensaje, esError);
}

async function cargarEstado() {
    try {
        const resp = await fetch("/api/estado?t=" + Date.now(), { cache: "no-store" });
        if (!resp.ok) throw new Error("Error HTTP al consultar /api/estado");
        estadoGlobal = await resp.json();
        renderizarControles();
        renderizarPanelDocente();
        renderizarGrilla();
        renderizarTablaAsignaciones();
        renderizarTablasCatalogos();
    } catch (err) {
        console.error("Error cargando estado de BD:", err);
        actualizarToast("Error conectando con la base de datos SQLite.", true);
    }
}

function renderizarPanelDocente() {
    const box = document.getElementById("teacher-panel-box");
    const selDoc = document.getElementById("select-docente-activo");
    const grid = document.getElementById("teacher-availability-grid");
    if (!box || !selDoc || !grid) return;

    if (rolActual !== "DOCENTE") {
        box.classList.add("hidden");
        return;
    }
    box.classList.remove("hidden");

    const prev = selDoc.value || (idReferenciaSesion && idReferenciaSesion.startsWith("DOC-") ? idReferenciaSesion : "DOC-02");
    selDoc.innerHTML = estadoGlobal.docentes.map(d =>
        `<option value="${d.id_docente}">${d.id_docente} | ${d.nombre_completo} (${d.tipo_vinculacion} - Máx ${d.max_horas_semanales}h)</option>`
    ).join("");
    if (estadoGlobal.docentes.some(d => d.id_docente === prev)) {
        selDoc.value = prev;
    }

    const docObj = estadoGlobal.docentes.find(d => d.id_docente === selDoc.value);
    if (!docObj) return;

    grid.innerHTML = estadoGlobal.franjas.map(f => {
        const hab = docObj.franjas_disponibles.includes(f.id_franja);
        const bg = hab ? "#dcfce7" : "#ffe4e6";
        const border = hab ? "#16a34a" : "#e11d48";
        const color = hab ? "#14532d" : "#881337";
        const icon = hab ? "✔ Disponible" : "⛔ Bloqueada";
        return `<button type="button" class="btn-toggle-disp" data-franja="${f.id_franja}" data-hab="${hab ? '1' : '0'}"
                    style="background:${bg};border:1.5px solid ${border};color:${color};padding:8px 12px;border-radius:8px;cursor:pointer;font-size:0.78rem;font-weight:700;text-align:left;">
                    <div>${f.id_franja} (${f.dia_semana} ${f.hora_inicio}-${f.hora_fin})</div>
                    <div style="font-size:0.72rem;margin-top:2px;">${icon} (Clic para cambiar)</div>
                </button>`;
    }).join("");

    document.querySelectorAll(".btn-toggle-disp").forEach(btn => {
        btn.addEventListener("click", async () => {
            const idFranja = btn.dataset.franja;
            const estadoActual = btn.dataset.hab === "1";
            const resp = await fetch("/api/toggle-disponibilidad", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    id_docente: selDoc.value,
                    id_franja: idFranja,
                    disponible: !estadoActual
                })
            });
            const data = await resp.json();
            if (data.exito) {
                registrarLog(data.mensaje, false);
                await cargarEstado();
            } else {
                registrarLog(data.mensaje, true);
                mostrarModalConflicto([{
                    codigo_regla: data.codigo_regla || "RD-05",
                    mensaje_detalle: data.mensaje
                }], []);
            }
        });
    });
}

function renderizarControles() {
    const elDoc = document.getElementById("stat-docentes");
    const elAul = document.getElementById("stat-aulas");
    const elGrp = document.getElementById("stat-grupos");
    const elAct = document.getElementById("stat-activas");
    if (elDoc) elDoc.textContent = estadoGlobal.docentes.length;
    if (elAul) elAul.textContent = estadoGlobal.aulas.length;
    if (elGrp) elGrp.textContent = estadoGlobal.grupos.length;
    if (elAct) elAct.textContent = estadoGlobal.asignaciones.length;

    const selGrupo = document.getElementById("select-grupo");
    if (selGrupo) {
        const valorPrevioGrupo = selGrupo.value;
        selGrupo.innerHTML = estadoGlobal.grupos.map(g =>
            `<option value="${g.id_grupo}">${g.id_grupo} | ${g.nombre_curso} (Insc: ${g.numero_inscritos}, Mín: ${g.cupo_minimo_apertura}, ${g.requiere_laboratorio ? 'LAB' : 'TEO'})</option>`
        ).join("");
        if (valorPrevioGrupo && estadoGlobal.grupos.some(x => x.id_grupo === valorPrevioGrupo)) {
            selGrupo.value = valorPrevioGrupo;
        } else if (estadoGlobal.grupos.length > 2) {
            selGrupo.value = "GRP-03";
        }
    }

    verificarBannerCupo();

    const selDoc = document.getElementById("select-docente");
    if (selDoc) {
        const valDoc = selDoc.value;
        selDoc.innerHTML = estadoGlobal.docentes.map(d =>
            `<option value="${d.id_docente}">${d.id_docente} | ${d.nombre_completo} (${d.tipo_vinculacion} - Máx ${d.max_horas_semanales}h)</option>`
        ).join("");
        if (valDoc && estadoGlobal.docentes.some(d => d.id_docente === valDoc)) selDoc.value = valDoc;
    }

    const selAula = document.getElementById("select-aula");
    if (selAula) {
        const valAula = selAula.value;
        selAula.innerHTML = estadoGlobal.aulas.map(a =>
            `<option value="${a.id_aula}">${a.id_aula} | Cap: ${a.capacidad_maxima} est. (${a.tipo_texto})</option>`
        ).join("");
        if (valAula && estadoGlobal.aulas.some(a => a.id_aula === valAula)) selAula.value = valAula;
    }

    const selFranja = document.getElementById("select-franja");
    if (selFranja) {
        const valFranja = selFranja.value;
        selFranja.innerHTML = estadoGlobal.franjas.map(f =>
            `<option value="${f.id_franja}">${f.etiqueta}</option>`
        ).join("");
        if (valFranja && estadoGlobal.franjas.some(f => f.id_franja === valFranja)) selFranja.value = valFranja;
    }

    const selFiltro = document.getElementById("filtro-vista");
    if (selFiltro) {
        const valFiltro = selFiltro.value || "TODOS";
        let opcionesFiltro = `<option value="TODOS">Todas las Sesiones Programadas (${estadoGlobal.asignaciones.length})</option>`;

        const semestresUnicos = [...new Set(estadoGlobal.grupos.map(g => g.semestre_plan))].sort((a, b) => a - b);
        semestresUnicos.forEach(sem => {
            opcionesFiltro += `<option value="SEM:${sem}">🎓 Estudiante — Semestre ${sem}</option>`;
        });

        estadoGlobal.grupos.forEach(g => {
            opcionesFiltro += `<option value="GRP:${g.id_grupo}">📘 Grupo: ${g.id_grupo} — ${g.nombre_curso}</option>`;
        });

        estadoGlobal.docentes.forEach(d => {
            opcionesFiltro += `<option value="DOC:${d.id_docente}">👨‍🏫 Docente: ${d.nombre_completo}</option>`;
        });
        estadoGlobal.aulas.forEach(a => {
            opcionesFiltro += `<option value="AULA:${a.id_aula}">🏛 Aula: ${a.id_aula} (${a.tipo_texto})</option>`;
        });
        selFiltro.innerHTML = opcionesFiltro;
        if ([...selFiltro.options].some(o => o.value === valFiltro)) {
            selFiltro.value = valFiltro;
        }
    }

    const chipsDiv = document.getElementById("grupos-chips");
    if (chipsDiv) {
        chipsDiv.innerHTML = estadoGlobal.grupos.map(g => {
            const cls = [
                "group-chip",
                !g.cumple_cupo ? "low-cupo" : "",
                g.requiere_laboratorio ? "lab-req" : ""
            ].join(" ");
            return `<div class="${cls}" draggable="${!esModoSoloLectura()}" data-grupo="${g.id_grupo}" title="${g.nombre_curso} | Inscritos: ${g.numero_inscritos}">
                <strong>${g.id_grupo}</strong> · ${g.codigo_asignatura} (${g.numero_inscritos})
            </div>`;
        }).join("");

        if (!esModoSoloLectura()) {
            document.querySelectorAll(".group-chip").forEach(chip => {
                chip.addEventListener("dragstart", ev => {
                    ev.dataTransfer.setData("text/plain", chip.dataset.grupo);
                    document.getElementById("select-grupo").value = chip.dataset.grupo;
                    verificarBannerCupo();
                });
                chip.addEventListener("click", () => {
                    document.getElementById("select-grupo").value = chip.dataset.grupo;
                    verificarBannerCupo();
                });
            });
        }
    }
}

function verificarBannerCupo() {
    const selGrupo = document.getElementById("select-grupo");
    if (!selGrupo) return;
    const idGrupo = selGrupo.value;
    const g = estadoGlobal.grupos.find(x => x.id_grupo === idGrupo);
    const banner = document.getElementById("banner-cupo-alerta");
    const lblCupo = document.getElementById("lbl-cupo-actual");
    const inputDirecto = document.getElementById("input-inscritos-directo");

    if (g) {
        if (lblCupo) {
            lblCupo.textContent = `${g.numero_inscritos} inscritos (Mín: ${g.cupo_minimo_apertura} / Máx: 44)`;
        }
        if (inputDirecto) {
            inputDirecto.value = g.numero_inscritos;
        }
        if (banner) {
            if (!g.cumple_cupo) {
                banner.classList.remove("hidden");
            } else {
                banner.classList.add("hidden");
            }
        }
    }
}

async function modificarInscritosGrupo(idGrupo, cantidadASumar = null, nuevoTotal = null) {
    if (esModoSoloLectura()) {
        actualizarToast("Acción denegada: solo el Director de Programa puede añadir estudiantes.", true);
        return;
    }
    const payload = { id_grupo: idGrupo };
    if (nuevoTotal !== null) payload.nuevo_total = parseInt(nuevoTotal, 10);
    if (cantidadASumar !== null) payload.cantidad_a_sumar = parseInt(cantidadASumar, 10);

    const resp = await fetch("/api/actualizar-inscritos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });
    const data = await resp.json();

    if (data.exito) {
        registrarLog(`[MATRÍCULA ACTUALIZADA] ${data.mensaje}`, false);
        await cargarEstado();
    } else {
        registrarLog(`[BLOQUEO MATRÍCULA ${data.codigo_regla}] ${data.mensaje}`, true);
        mostrarModalConflicto([{
            codigo_regla: data.codigo_regla || "RD-03",
            mensaje_detalle: data.mensaje
        }], []);
    }
}

function renderizarGrilla() {
    const tbody = document.getElementById("grilla-body");
    if (!tbody) return;
    const selFiltro = document.getElementById("filtro-vista");
    const filtro = (selFiltro && selFiltro.value) ? selFiltro.value : "TODOS";

    tbody.innerHTML = BLOQUES.map(b => {
        const celdas = DIAS.map(dia => {
            const prefijo = dia.substring(0, 3) + "-B" + b.num;
            const sesionesCelda = estadoGlobal.asignaciones.filter(a => {
                if (a.id_franja !== prefijo) return false;
                if (filtro.startsWith("DOC:")) return a.id_docente === filtro.split(":")[1];
                if (filtro.startsWith("AULA:")) return a.id_aula === filtro.split(":")[1];
                if (filtro.startsWith("GRP:")) return a.id_grupo === filtro.split(":")[1];
                if (filtro.startsWith("SEM:")) {
                    const semBuscado = parseInt(filtro.split(":")[1], 10);
                    const gObj = estadoGlobal.grupos.find(x => x.id_grupo === a.id_grupo);
                    return gObj && gObj.semestre_plan === semBuscado;
                }
                return true;
            });

            const htmlSesiones = sesionesCelda.map(s => `
                <div class="scheduled-badge">
                    <strong>${s.id_grupo} · ${s.nombre_curso}</strong>
                    <div class="scheduled-meta"><span>Docente:</span> ${s.nombre_docente}</div>
                    <div class="scheduled-meta"><span>Aula:</span> ${s.id_aula} (Insc: ${s.numero_inscritos})</div>
                </div>
            `).join("");

            return `<td class="slot-cell" data-franja="${prefijo}">${htmlSesiones}</td>`;
        }).join("");

        return `<tr><td class="time-col">${b.label}</td>${celdas}</tr>`;
    }).join("");

    if (!esModoSoloLectura()) {
        document.querySelectorAll(".slot-cell").forEach(cell => {
            cell.addEventListener("dragover", ev => {
                ev.preventDefault();
                cell.classList.add("drag-over");
            });
            cell.addEventListener("dragleave", () => cell.classList.remove("drag-over"));
            cell.addEventListener("drop", ev => {
                ev.preventDefault();
                cell.classList.remove("drag-over");
                const idGrupo = ev.dataTransfer.getData("text/plain");
                const idFranja = cell.dataset.franja;
                if (idGrupo) document.getElementById("select-grupo").value = idGrupo;
                if (idFranja) document.getElementById("select-franja").value = idFranja;
                solicitarAsignacion(false);
            });
        });
    }
}

function renderizarTablaAsignaciones() {
    const tbody = document.getElementById("tabla-asignaciones");
    if (!tbody) return;
    if (estadoGlobal.asignaciones.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;color:#64748b;">No hay sesiones programadas aún.</td></tr>`;
        return;
    }
    tbody.innerHTML = estadoGlobal.asignaciones.map(a => `
        <tr>
            <td><strong>${a.id_asignacion}</strong></td>
            <td>${a.id_grupo}</td>
            <td>${a.codigo_asignatura}</td>
            <td>${a.nombre_curso}</td>
            <td>${a.numero_inscritos} est.</td>
            <td>${a.nombre_docente}</td>
            <td>${a.id_aula}</td>
            <td>${a.id_franja} (${a.dia_semana} ${a.hora_inicio}-${a.hora_fin})</td>
            <td><span class="badge-ok">${a.estado_validacion}</span></td>
        </tr>
    `).join("");
}

function renderizarTablasCatalogos() {
    const tbDoc = document.getElementById("tabla-catalogo-docentes");
    if (tbDoc) {
        tbDoc.innerHTML = estadoGlobal.docentes.map(d => `
            <tr>
                <td><strong>${d.id_docente}</strong></td>
                <td>${d.documento_identidad}</td>
                <td>${d.nombre_completo}</td>
                <td><span class="badge-ok">${d.tipo_vinculacion}</span></td>
                <td>Máx ${d.max_horas_semanales}h / sem</td>
                <td>${d.especialidad}</td>
            </tr>
        `).join("");
    }

    const tbAulas = document.getElementById("tabla-catalogo-aulas");
    if (tbAulas) {
        tbAulas.innerHTML = estadoGlobal.aulas.map(a => `
            <tr>
                <td><strong>${a.id_aula}</strong></td>
                <td>${a.edificio}</td>
                <td>${a.capacidad_maxima} puestos</td>
                <td><span class="badge-ok">${a.tipo_texto}</span></td>
            </tr>
        `).join("");
    }

    const tbGrupos = document.getElementById("tabla-catalogo-grupos");
    if (tbGrupos) {
        tbGrupos.innerHTML = estadoGlobal.grupos.map(g => {
            const controlesAdmin = esModoSoloLectura()
                ? `<span style="color:#64748b;font-size:0.75rem;">Solo lectura</span>`
                : `<div class="inline-enroll-actions">
                       <button type="button" class="btn-enroll btn-inline-enroll" data-grupo="${g.id_grupo}" data-delta="1">+1 Est.</button>
                       <button type="button" class="btn-enroll btn-inline-enroll" data-grupo="${g.id_grupo}" data-delta="5">+5 Est.</button>
                       <button type="button" class="btn-enroll btn-enroll-sub btn-inline-enroll" data-grupo="${g.id_grupo}" data-delta="-1">-1</button>
                   </div>`;
            return `
            <tr>
                <td><strong>${g.id_grupo}</strong></td>
                <td>${g.codigo_asignatura}</td>
                <td>${g.nombre_curso}</td>
                <td>Sem. ${g.semestre_plan}</td>
                <td><strong>${g.numero_inscritos}</strong> / 44 est.</td>
                <td>Mín ${g.cupo_minimo_apertura} est.</td>
                <td>${g.requiere_laboratorio ? 'LAB' : 'TEO'}</td>
                <td><span class="badge-ok" style="${!g.cumple_cupo ? 'background:#fef3c7;color:#92400e;' : ''}">${g.estado_grupo}</span></td>
                <td>${controlesAdmin}</td>
            </tr>`;
        }).join("");

        document.querySelectorAll(".btn-inline-enroll").forEach(btn => {
            btn.addEventListener("click", () => {
                modificarInscritosGrupo(btn.dataset.grupo, parseInt(btn.dataset.delta, 10), null);
            });
        });
    }
}

async function solicitarAsignacion(autorizarExcepcionCupo = false) {
    if (esModoSoloLectura()) return;

    const payload = {
        id_grupo: document.getElementById("select-grupo").value,
        id_docente: document.getElementById("select-docente").value,
        id_aula: document.getElementById("select-aula").value,
        id_franja: document.getElementById("select-franja").value,
        autorizar_excepcion_cupo: autorizarExcepcionCupo
    };

    const resp = await fetch("/api/asignar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });
    const resultado = await resp.json();

    if (resultado.exito) {
        const asig = resultado.asignacion;
        registrarLog(`[OK - VERDE | ${resultado.latencia_ms} ms] Asignación persistida en 3FN: ${asig.id_grupo} (${asig.nombre_curso}) -> ${asig.id_aula} con ${asig.nombre_docente} en ${asig.id_franja}.`, false);
        await cargarEstado();
    } else if (resultado.tipo_bloqueo === "BLANDA") {
        const err = resultado.errores[0];
        registrarLog(`[ALERTA PREVENTIVA ${err.codigo_regla} | ${resultado.latencia_ms} ms] ${err.mensaje_detalle}`, true);
        const txtAlerta = document.getElementById("texto-alerta-blanda");
        if (txtAlerta) txtAlerta.textContent = err.mensaje_detalle;
        const modalBlanda = document.getElementById("modal-blanda");
        if (modalBlanda) modalBlanda.classList.remove("hidden");
    } else {
        resultado.errores.forEach(e => {
            registrarLog(`[BLOQUEO ROJO ${e.codigo_regla} | ${resultado.latencia_ms} ms] ${e.mensaje_detalle}`, true);
        });
        mostrarModalConflicto(resultado.errores, resultado.alternativas_aula);
    }
}

function mostrarModalConflicto(errores, alternativas) {
    const lista = document.getElementById("lista-errores-modal");
    if (lista) {
        lista.innerHTML = errores.map(e => `<li>[${e.codigo_regla}] ${e.mensaje_detalle}</li>`).join("");
    }

    const contAlt = document.getElementById("contenedor-alternativas");
    const contAgotado = document.getElementById("contenedor-agotado");
    const selAlt = document.getElementById("select-aula-alternativa");

    if (alternativas && alternativas.length > 0) {
        if (contAlt) contAlt.classList.remove("hidden");
        if (contAgotado) contAgotado.classList.add("hidden");
        if (selAlt) {
            selAlt.innerHTML = alternativas.map(a =>
                `<option value="${a.id_aula}">${a.id_aula} | Capacidad: ${a.capacidad_maxima} puestos (${a.tipo_texto})</option>`
            ).join("");
        }
    } else {
        if (contAlt) contAlt.classList.add("hidden");
        if (contAgotado) contAgotado.classList.remove("hidden");
    }

    const modalConflicto = document.getElementById("modal-conflicto");
    if (modalConflicto) modalConflicto.classList.remove("hidden");
}

function aplicarPermisosPorRol(rol, idRef) {
    rolActual = rol;
    idReferenciaSesion = idRef || "";

    const adminLeftPanel = document.getElementById("admin-left-panel");
    const workspaceGrid = document.getElementById("workspace-grid");
    const studentBanner = document.getElementById("student-welcome-banner");
    const teacherBox = document.getElementById("teacher-panel-box");
    const sidebarAdminActions = document.getElementById("sidebar-admin-actions");
    const sidebarReadonlyNotice = document.getElementById("sidebar-readonly-notice");
    const readonlyRoleLabel = document.getElementById("readonly-role-label");
    const navBtnCatalogos = document.getElementById("nav-btn-catalogos");
    const navBtnAuditoria = document.getElementById("nav-btn-auditoria");
    const navTitle01 = document.getElementById("nav-title-01");
    const navSub01 = document.getElementById("nav-sub-01");

    if (rol === "ESTUDIANTE") {
        if (adminLeftPanel) adminLeftPanel.classList.add("hidden");
        if (workspaceGrid) workspaceGrid.classList.add("student-mode");
        if (studentBanner) studentBanner.classList.remove("hidden");
        if (teacherBox) teacherBox.classList.add("hidden");
        if (sidebarAdminActions) sidebarAdminActions.classList.add("hidden");
        if (sidebarReadonlyNotice) sidebarReadonlyNotice.classList.remove("hidden");
        if (readonlyRoleLabel) readonlyRoleLabel.textContent = "ESTUDIANTE (Solo Consulta)";
        if (navBtnCatalogos) navBtnCatalogos.classList.add("hidden");
        if (navBtnAuditoria) navBtnAuditoria.classList.add("hidden");
        if (navTitle01) navTitle01.textContent = "Mi Horario Estudiantil";
        if (navSub01) navSub01.textContent = "Consulta por Semestre o Grupo";
        document.querySelectorAll(".admin-only-btn").forEach(b => b.classList.add("hidden"));
    } else if (rol === "DOCENTE") {
        if (adminLeftPanel) adminLeftPanel.classList.add("hidden");
        if (workspaceGrid) workspaceGrid.classList.add("student-mode");
        if (studentBanner) studentBanner.classList.add("hidden");
        if (teacherBox) teacherBox.classList.remove("hidden");
        if (sidebarAdminActions) sidebarAdminActions.classList.add("hidden");
        if (sidebarReadonlyNotice) sidebarReadonlyNotice.classList.remove("hidden");
        if (readonlyRoleLabel) readonlyRoleLabel.textContent = "DOCENTE (Mi Horario + Disponibilidad)";
        if (navBtnCatalogos) navBtnCatalogos.classList.add("hidden");
        if (navBtnAuditoria) navBtnAuditoria.classList.add("hidden");
        if (navTitle01) navTitle01.textContent = "Portal Docente";
        if (navSub01) navSub01.textContent = "Disponibilidad RF-02 y Mi Horario";
        document.querySelectorAll(".admin-only-btn").forEach(b => b.classList.add("hidden"));
    } else {
        // DIRECTOR / COORDINADOR (Acceso Total)
        if (adminLeftPanel) adminLeftPanel.classList.remove("hidden");
        if (workspaceGrid) workspaceGrid.classList.remove("student-mode");
        if (studentBanner) studentBanner.classList.add("hidden");
        if (teacherBox) teacherBox.classList.add("hidden");
        if (sidebarAdminActions) sidebarAdminActions.classList.remove("hidden");
        if (sidebarReadonlyNotice) sidebarReadonlyNotice.classList.add("hidden");
        if (navBtnCatalogos) navBtnCatalogos.classList.remove("hidden");
        if (navBtnAuditoria) navBtnAuditoria.classList.remove("hidden");
        if (navTitle01) navTitle01.textContent = "Programación y Grilla";
        if (navSub01) navSub01.textContent = "Asignación asistida y Drag & Drop";
        document.querySelectorAll(".admin-only-btn").forEach(b => b.classList.remove("hidden"));
    }

    cambiarVista("vista-programacion");
    renderizarControles();
    renderizarPanelDocente();

    // Si entra un Docente o Estudiante, filtrar la grilla automáticamente por su perfil
    const selFiltro = document.getElementById("filtro-vista");
    if (selFiltro) {
        if (rol === "DOCENTE" && idReferenciaSesion.startsWith("DOC-")) {
            selFiltro.value = `DOC:${idReferenciaSesion}`;
        } else if (rol === "ESTUDIANTE" && idReferenciaSesion.startsWith("SEM-")) {
            const numSem = idReferenciaSesion.split("-")[1];
            selFiltro.value = `SEM:${numSem}`;
        } else {
            selFiltro.value = "TODOS";
        }
    }

    renderizarGrilla();
    renderizarTablaAsignaciones();
    renderizarTablasCatalogos();
}

async function autenticarEnServidor(correo, password, rol) {
    const errBox = document.getElementById("login-error-msg");
    if (errBox) errBox.classList.add("hidden");

    const resp = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ correo, password, rol })
    });
    const data = await resp.json();

    if (!data.autenticado) {
        if (errBox) {
            errBox.textContent = "⛔ " + data.mensaje;
            errBox.classList.remove("hidden");
        }
        return;
    }

    document.getElementById("session-user-name").textContent = data.nombre;
    document.getElementById("session-user-role").textContent = data.rol;
    document.getElementById("login-screen").classList.add("hidden");
    document.getElementById("app-shell").classList.remove("hidden");
    await cargarEstado();
    aplicarPermisosPorRol(data.rol, data.id_referencia);
    registrarLog(`Autenticación verificada en SQLite: ${data.nombre} (${data.correo}) [Rol: ${data.rol}].`, false);
}

async function ejecutarSuiteQA() {
    const resp = await fetch("/api/qa", { method: "POST" });
    const data = await resp.json();
    registrarLog("\n" + data.reporte, false);
    cambiarVista("vista-auditoria");
}

document.addEventListener("DOMContentLoaded", async () => {
    await cargarEstado();
    registrarLog(`Sistema Web inicializado. Catálogo cargado desde SQLite 3FN: ${estadoGlobal.docentes.length} docentes, ${estadoGlobal.aulas.length} aulas, ${estadoGlobal.grupos.length} grupos, ${estadoGlobal.asignaciones.length} sesiones activas.`);

    const loginRol = document.getElementById("login-rol");
    if (loginRol) {
        loginRol.addEventListener("change", ev => {
            const r = ev.target.value;
            const inpUser = document.getElementById("login-user");
            const inpPass = document.getElementById("login-pass");
            if (r === "ESTUDIANTE") {
                inpUser.value = "dquijanoa@unbosque.edu.co";
                inpPass.value = "Estudiante2026*";
            } else if (r === "DOCENTE") {
                inpUser.value = "emorales@unbosque.edu.co";
                inpPass.value = "Docente2026*";
            } else {
                inpUser.value = "director@unbosque.edu.co";
                inpPass.value = "Director2026*";
            }
        });
    }

    const loginForm = document.getElementById("login-form");
    if (loginForm) {
        loginForm.addEventListener("submit", ev => {
            ev.preventDefault();
            const correo = document.getElementById("login-user").value.trim();
            const password = document.getElementById("login-pass").value.trim();
            const rol = document.getElementById("login-rol").value;
            autenticarEnServidor(correo, password, rol);
        });
    }

    document.querySelectorAll(".chip-role").forEach(btn => {
        btn.addEventListener("click", () => {
            document.getElementById("login-rol").value = btn.dataset.role;
            document.getElementById("login-user").value = btn.dataset.email;
            document.getElementById("login-pass").value = btn.dataset.pass;
            autenticarEnServidor(btn.dataset.email, btn.dataset.pass, btn.dataset.role);
        });
    });

    const btnLogout = document.getElementById("btn-logout");
    if (btnLogout) {
        btnLogout.addEventListener("click", () => {
            document.getElementById("app-shell").classList.add("hidden");
            document.getElementById("login-screen").classList.remove("hidden");
        });
    }

    const selDocActivo = document.getElementById("select-docente-activo");
    if (selDocActivo) {
        selDocActivo.addEventListener("change", () => {
            idReferenciaSesion = selDocActivo.value;
            renderizarPanelDocente();
            document.getElementById("filtro-vista").value = `DOC:${selDocActivo.value}`;
            renderizarGrilla();
        });
    }

    document.querySelectorAll(".nav-item").forEach(btn => {
        btn.addEventListener("click", () => {
            cambiarVista(btn.dataset.target);
        });
    });

    const selGrupo = document.getElementById("select-grupo");
    if (selGrupo) selGrupo.addEventListener("change", verificarBannerCupo);

    const selFiltro = document.getElementById("filtro-vista");
    if (selFiltro) selFiltro.addEventListener("change", renderizarGrilla);

    const btnAdd1 = document.getElementById("btn-add-1-est");
    if (btnAdd1) btnAdd1.addEventListener("click", () => {
        modificarInscritosGrupo(document.getElementById("select-grupo").value, 1, null);
    });
    const btnAdd5 = document.getElementById("btn-add-5-est");
    if (btnAdd5) btnAdd5.addEventListener("click", () => {
        modificarInscritosGrupo(document.getElementById("select-grupo").value, 5, null);
    });
    const btnSub1 = document.getElementById("btn-sub-1-est");
    if (btnSub1) btnSub1.addEventListener("click", () => {
        modificarInscritosGrupo(document.getElementById("select-grupo").value, -1, null);
    });
    const btnSetEst = document.getElementById("btn-set-est");
    if (btnSetEst) btnSetEst.addEventListener("click", () => {
        const idG = document.getElementById("select-grupo").value;
        const val = document.getElementById("input-inscritos-directo").value;
        if (val) modificarInscritosGrupo(idG, null, parseInt(val, 10));
    });

    const btnAsignar = document.getElementById("btn-asignar");
    if (btnAsignar) btnAsignar.addEventListener("click", () => solicitarAsignacion(false));

    const btnCerrarModal = document.getElementById("btn-cerrar-modal");
    if (btnCerrarModal) {
        btnCerrarModal.addEventListener("click", () => {
            document.getElementById("modal-conflicto").classList.add("hidden");
        });
    }

    const btnCerrarModalBlanda = document.getElementById("btn-cerrar-modal-blanda");
    if (btnCerrarModalBlanda) {
        btnCerrarModalBlanda.addEventListener("click", () => {
            document.getElementById("modal-blanda").classList.add("hidden");
        });
    }

    // Permitir cerrar modales haciendo clic en el fondo oscuro (backdrop) o presionando Escape
    ["modal-conflicto", "modal-blanda"].forEach(mid => {
        const modalEl = document.getElementById(mid);
        if (modalEl) {
            modalEl.addEventListener("click", ev => {
                if (ev.target === modalEl) {
                    modalEl.classList.add("hidden");
                }
            });
        }
    });

    document.addEventListener("keydown", ev => {
        if (ev.key === "Escape") {
            const m1 = document.getElementById("modal-conflicto");
            const m2 = document.getElementById("modal-blanda");
            if (m1) m1.classList.add("hidden");
            if (m2) m2.classList.add("hidden");
        }
    });

    const btnAplicarAlt = document.getElementById("btn-aplicar-alternativa");
    if (btnAplicarAlt) {
        btnAplicarAlt.addEventListener("click", async () => {
            const nuevaAula = document.getElementById("select-aula-alternativa").value;
            document.getElementById("select-aula").value = nuevaAula;
            document.getElementById("modal-conflicto").classList.add("hidden");
            await solicitarAsignacion(false);
        });
    }

    const btnAutorizarCupo = document.getElementById("btn-autorizar-cupo");
    if (btnAutorizarCupo) {
        btnAutorizarCupo.addEventListener("click", async () => {
            document.getElementById("modal-blanda").classList.add("hidden");
            await solicitarAsignacion(true);
        });
    }

    const btnCancelarCupo = document.getElementById("btn-cancelar-cupo");
    if (btnCancelarCupo) {
        btnCancelarCupo.addEventListener("click", () => {
            document.getElementById("modal-blanda").classList.add("hidden");
            registrarLog("[INFO] Operación cancelada por el coordinador ante alerta de bajo cupo [RB-01].", true);
        });
    }

    const btnDemo = document.getElementById("btn-demo");
    if (btnDemo) {
        btnDemo.addEventListener("click", async () => {
            cambiarVista("vista-programacion");
            const resp = await fetch("/api/demo-ruptura", { method: "POST" });
            const data = await resp.json();
            await cargarEstado();
            document.getElementById("select-grupo").value = data.seleccion_intentada.id_grupo;
            document.getElementById("select-docente").value = data.seleccion_intentada.id_docente;
            document.getElementById("select-aula").value = data.seleccion_intentada.id_aula;
            document.getElementById("select-franja").value = data.seleccion_intentada.id_franja;
            verificarBannerCupo();
            registrarLog(`[DEMO] ${data.mensaje_demo}`, false);
            data.resultado_choque.errores.forEach(e => {
                registrarLog(`[BLOQUEO ROJO ${e.codigo_regla} | ${data.resultado_choque.latencia_ms} ms] ${e.mensaje_detalle}`, true);
            });
            mostrarModalConflicto(data.resultado_choque.errores, data.resultado_choque.alternativas_aula);
        });
    }

    const btnQa = document.getElementById("btn-qa");
    if (btnQa) btnQa.addEventListener("click", ejecutarSuiteQA);

    const btnQaSide = document.getElementById("btn-qa-sidebar");
    if (btnQaSide) btnQaSide.addEventListener("click", ejecutarSuiteQA);

    async function reiniciarBaseDatos() {
        await fetch("/api/reiniciar", { method: "POST" });
        await cargarEstado();
        registrarLog("[RESET] Se limpiaron todas las asignaciones activas en la base de datos SQLite.", false);
    }

    ["btn-reiniciar", "btn-reiniciar-sidebar", "btn-reiniciar-form"].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener("click", reiniciarBaseDatos);
    });
});

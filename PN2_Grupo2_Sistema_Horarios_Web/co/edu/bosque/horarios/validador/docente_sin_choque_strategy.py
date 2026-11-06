# -*- coding: utf-8 -*-
from typing import List
from co.edu.bosque.horarios.dominio.asignacion_horario import AsignacionHorario
from .i_restriccion_strategy import IRestriccionStrategy
from .resultado_validacion import ResultadoValidacion

class DocenteSinChoqueStrategy(IRestriccionStrategy):
    """
    SRP: Valida exclusivamente las restricciones asociadas al Docente:
    - RD-01: Unicidad temporal del docente (sin solapamiento en la misma franja).
    - RD-05: Disponibilidad declarada por el docente y tope de horas semanales según vinculación.
    """
    def validar(
        self,
        nueva: AsignacionHorario,
        existentes: List[AsignacionHorario]
    ) -> ResultadoValidacion:
        if not nueva.docente.esta_disponible_en(nueva.franja.id_franja):
            return ResultadoValidacion(
                es_valido=False,
                tipo_restriccion="DURA",
                codigo_regla="RD-05",
                mensaje_detalle=(
                    f"Indisponibilidad Docente: {nueva.docente.nombre_completo} no tiene "
                    f"habilitada la franja {nueva.franja}."
                )
            )

        for asig in existentes:
            if asig.docente.id_docente == nueva.docente.id_docente and asig.franja.se_solapa_con(nueva.franja):
                return ResultadoValidacion(
                    es_valido=False,
                    tipo_restriccion="DURA",
                    codigo_regla="RD-01",
                    mensaje_detalle=(
                        f"Choque de Docente: {nueva.docente.nombre_completo} ya dicta clase al "
                        f"grupo {asig.grupo.id_grupo} ({asig.grupo.curso.nombre_curso}) en {nueva.franja}."
                    )
                )

        horas_actuales = nueva.docente.calcular_horas_asignadas(existentes)
        if horas_actuales + 2 > nueva.docente.max_horas_semanales:
            return ResultadoValidacion(
                es_valido=False,
                tipo_restriccion="DURA",
                codigo_regla="RD-05",
                mensaje_detalle=(
                    f"Sobrecarga Horaria: {nueva.docente.nombre_completo} superaría su tope de "
                    f"{nueva.docente.max_horas_semanales}h semanales ({nueva.docente.tipo_vinculacion})."
                )
            )

        return ResultadoValidacion(True, "DURA", "RD-01/RD-05", "Docente disponible y sin cruce horario.")

# -*- coding: utf-8 -*-
from typing import List
from co.edu.bosque.horarios.dominio.asignacion_horario import AsignacionHorario
from .i_restriccion_strategy import IRestriccionStrategy
from .resultado_validacion import ResultadoValidacion

class CapacidadYTipoAulaStrategy(IRestriccionStrategy):
    """
    SRP: Valida exclusivamente la idoneidad física del aula frente al grupo:
    - RD-03: Capacidad física del aula >= número de estudiantes inscritos (y límite institucional 44 con tolerancia 10%).
    - RD-04: Requerimiento de laboratorio especializado.
    """
    def validar(
        self,
        nueva: AsignacionHorario,
        existentes: List[AsignacionHorario]
    ) -> ResultadoValidacion:
        if nueva.grupo.numero_inscritos > 44:
            return ResultadoValidacion(
                es_valido=False,
                tipo_restriccion="DURA",
                codigo_regla="RD-03",
                mensaje_detalle=(
                    f"Exceso de Tope Institucional: El grupo {nueva.grupo.id_grupo} registra "
                    f"{nueva.grupo.numero_inscritos} estudiantes, superando el máximo permitido de 44 (40 + 10%)."
                )
            )

        if not nueva.aula.cumple_capacidad(nueva.grupo.numero_inscritos):
            return ResultadoValidacion(
                es_valido=False,
                tipo_restriccion="DURA",
                codigo_regla="RD-03",
                mensaje_detalle=(
                    f"Sobrecupo de Aula: El grupo {nueva.grupo.id_grupo} registra {nueva.grupo.numero_inscritos} "
                    f"estudiantes inscritos, superando la capacidad del aula {nueva.aula.id_aula} ({nueva.aula.capacidad_maxima} puestos)."
                )
            )

        if nueva.grupo.curso.requiere_laboratorio and not nueva.aula.es_laboratorio:
            return ResultadoValidacion(
                es_valido=False,
                tipo_restriccion="DURA",
                codigo_regla="RD-04",
                mensaje_detalle=(
                    f"Incompatibilidad de Infraestructura: La asignatura '{nueva.grupo.curso.nombre_curso}' "
                    f"requiere laboratorio especializado y el salón {nueva.aula.id_aula} es aula teórica."
                )
            )

        return ResultadoValidacion(True, "DURA", "RD-03/RD-04", "Capacidad física y tipo de aula compatibles.")

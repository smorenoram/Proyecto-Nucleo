# -*- coding: utf-8 -*-
from typing import List
from co.edu.bosque.horarios.dominio.asignacion_horario import AsignacionHorario
from .i_restriccion_strategy import IRestriccionStrategy
from .resultado_validacion import ResultadoValidacion

class CupoMinimoGrupoStrategy(IRestriccionStrategy):
    """
    SRP: Valida la coherencia entre datos de matrícula y apertura/cierre de grupos (RB-01 / RF-10).
    Si el número de inscritos es menor al cupo_minimo_apertura del curso, emite alerta preventiva.
    """
    def validar(
        self,
        nueva: AsignacionHorario,
        existentes: List[AsignacionHorario]
    ) -> ResultadoValidacion:
        if not nueva.grupo.cumple_cupo_minimo():
            return ResultadoValidacion(
                es_valido=False,
                tipo_restriccion="BLANDA",
                codigo_regla="RB-01",
                mensaje_detalle=(
                    f"Alerta de Cierre Preventivo por Bajo Cupo: El grupo {nueva.grupo.id_grupo} "
                    f"registra {nueva.grupo.numero_inscritos} matriculados y el umbral mínimo de apertura "
                    f"es de {nueva.grupo.curso.cupo_minimo_apertura} estudiantes."
                )
            )
        return ResultadoValidacion(True, "BLANDA", "RB-01", "El grupo cumple el umbral mínimo de matrícula.")

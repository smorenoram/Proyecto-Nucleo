# -*- coding: utf-8 -*-
from typing import List
from co.edu.bosque.horarios.dominio.asignacion_horario import AsignacionHorario
from .i_restriccion_strategy import IRestriccionStrategy
from .resultado_validacion import ResultadoValidacion

class UnicidadGrupoEnFranjaStrategy(IRestriccionStrategy):
    """
    SRP: Impide que un mismo grupo tenga dos sesiones simultáneas en la misma franja (RD-06)
    o supere las sesiones semanales exigidas por el plan de estudios.
    """
    def validar(
        self,
        nueva: AsignacionHorario,
        existentes: List[AsignacionHorario]
    ) -> ResultadoValidacion:
        sesiones_grupo = 0
        for asig in existentes:
            if asig.grupo.id_grupo == nueva.grupo.id_grupo:
                sesiones_grupo += 1
                if asig.franja.se_solapa_con(nueva.franja):
                    return ResultadoValidacion(
                        es_valido=False,
                        tipo_restriccion="DURA",
                        codigo_regla="RD-06",
                        mensaje_detalle=(
                            f"Choque de Grupo: El grupo {nueva.grupo.id_grupo} ya posee una sesión "
                            f"asignada en la franja {nueva.franja}."
                        )
                    )
        if sesiones_grupo >= nueva.grupo.curso.sesiones_semanales:
            return ResultadoValidacion(
                es_valido=False,
                tipo_restriccion="DURA",
                codigo_regla="RD-06",
                mensaje_detalle=(
                    f"Sesiones Completas: El grupo {nueva.grupo.id_grupo} ya tiene programadas sus "
                    f"{nueva.grupo.curso.sesiones_semanales} sesiones semanales."
                )
            )
        return ResultadoValidacion(True, "DURA", "RD-06", "Grupo sin cruce ni exceso de sesiones semanales.")

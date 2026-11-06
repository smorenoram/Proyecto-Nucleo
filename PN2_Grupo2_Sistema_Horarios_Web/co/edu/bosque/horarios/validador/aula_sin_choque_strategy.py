# -*- coding: utf-8 -*-
from typing import List
from co.edu.bosque.horarios.dominio.asignacion_horario import AsignacionHorario
from .i_restriccion_strategy import IRestriccionStrategy
from .resultado_validacion import ResultadoValidacion

class AulaSinChoqueStrategy(IRestriccionStrategy):
    """
    SRP: Valida exclusivamente que el aula física no esté reservada por otro grupo
    en la misma franja horaria (RD-02).
    """
    def validar(
        self,
        nueva: AsignacionHorario,
        existentes: List[AsignacionHorario]
    ) -> ResultadoValidacion:
        for asig in existentes:
            if asig.aula.id_aula == nueva.aula.id_aula and asig.franja.se_solapa_con(nueva.franja):
                return ResultadoValidacion(
                    es_valido=False,
                    tipo_restriccion="DURA",
                    codigo_regla="RD-02",
                    mensaje_detalle=(
                        f"Choque de Aula: El salón {nueva.aula.id_aula} ya se encuentra reservado por el "
                        f"grupo {asig.grupo.id_grupo} ({asig.grupo.curso.nombre_curso}) en {nueva.franja}."
                    )
                )
        return ResultadoValidacion(True, "DURA", "RD-02", "Aula libre en la franja seleccionada.")

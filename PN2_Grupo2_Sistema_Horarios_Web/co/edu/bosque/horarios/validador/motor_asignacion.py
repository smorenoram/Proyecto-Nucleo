# -*- coding: utf-8 -*-
from typing import List
from co.edu.bosque.horarios.dominio.asignacion_horario import AsignacionHorario
from .i_restriccion_strategy import IRestriccionStrategy
from .resultado_validacion import ResultadoValidacion

class MotorAsignacion:
    """
    Contexto del Patrón GoF Strategy.
    Evalúa polimórficamente todas las reglas de restricción registradas en tiempo O(|S| * |A|).
    Cumple 100% con el Principio Abierto/Cerrado (OCP) e Inversión de Dependencias (DIP).
    """
    def __init__(self) -> None:
        self._estrategias: List[IRestriccionStrategy] = []

    def registrar_estrategia(self, estrategia: IRestriccionStrategy) -> None:
        self._estrategias.append(estrategia)

    def evaluar_asignacion(
        self,
        nueva: AsignacionHorario,
        existentes: List[AsignacionHorario]
    ) -> List[ResultadoValidacion]:
        return [estrategia.validar(nueva, existentes) for estrategia in self._estrategias]

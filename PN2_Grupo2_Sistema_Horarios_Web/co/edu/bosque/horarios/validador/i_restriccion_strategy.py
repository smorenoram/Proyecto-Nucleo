# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import List
from co.edu.bosque.horarios.dominio.asignacion_horario import AsignacionHorario
from .resultado_validacion import ResultadoValidacion

class IRestriccionStrategy(ABC):
    """
    Interfaz común del Patrón GoF Strategy (Cumple OCP y DIP de SOLID).
    Recibe la asignación candidata y el contexto activo de asignaciones existentes.
    """
    @abstractmethod
    def validar(
        self,
        nueva: AsignacionHorario,
        existentes: List[AsignacionHorario]
    ) -> ResultadoValidacion:
        pass

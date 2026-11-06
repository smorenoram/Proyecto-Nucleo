# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .asignacion_horario import AsignacionHorario

@dataclass
class Docente:
    """Entidad de dominio que modela un profesor, su tipo de vinculación y disponibilidad."""
    id_docente: str
    documento_identidad: str
    nombre_completo: str
    tipo_vinculacion: str
    max_horas_semanales: int
    especialidad: str
    franjas_disponibles: List[str] = field(default_factory=list)

    def esta_disponible_en(self, id_franja: str) -> bool:
        return id_franja in self.franjas_disponibles

    def calcular_horas_asignadas(self, existentes: List['AsignacionHorario']) -> int:
        sesiones = sum(1 for a in existentes if a.docente.id_docente == self.id_docente)
        return sesiones * 2  # Cada bloque institucional equivale a 2 horas

    def to_dict(self) -> dict:
        return {
            "id_docente": self.id_docente,
            "documento_identidad": self.documento_identidad,
            "nombre_completo": self.nombre_completo,
            "tipo_vinculacion": self.tipo_vinculacion,
            "max_horas_semanales": self.max_horas_semanales,
            "especialidad": self.especialidad,
            "franjas_disponibles": self.franjas_disponibles
        }

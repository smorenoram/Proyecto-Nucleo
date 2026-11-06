# -*- coding: utf-8 -*-
from dataclasses import dataclass

@dataclass
class FranjaHoraria:
    """Representa un bloque académico discreto de 2 horas dentro de la oferta institucional."""
    id_franja: str
    dia_semana: str
    hora_inicio: str
    hora_fin: str
    bloque_academico: int

    def se_solapa_con(self, otra: 'FranjaHoraria') -> bool:
        if self.dia_semana != otra.dia_semana:
            return False
        return not (self.hora_fin <= otra.hora_inicio or self.hora_inicio >= otra.hora_fin)

    def to_dict(self) -> dict:
        return {
            "id_franja": self.id_franja,
            "dia_semana": self.dia_semana,
            "hora_inicio": self.hora_inicio,
            "hora_fin": self.hora_fin,
            "bloque_academico": self.bloque_academico,
            "etiqueta": f"{self.id_franja} ({self.dia_semana} {self.hora_inicio}-{self.hora_fin})"
        }

    def __str__(self) -> str:
        return f"{self.id_franja} ({self.dia_semana} {self.hora_inicio}-{self.hora_fin})"

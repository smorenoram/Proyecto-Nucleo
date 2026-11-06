# -*- coding: utf-8 -*-
from dataclasses import dataclass

@dataclass
class Aula:
    """Entidad de dominio que representa un salón físico o laboratorio especializado."""
    id_aula: str
    edificio: str
    capacidad_maxima: int
    es_laboratorio: bool
    estado_operativo: bool = True

    def cumple_capacidad(self, inscritos: int) -> bool:
        return self.capacidad_maxima >= inscritos

    def to_dict(self) -> dict:
        return {
            "id_aula": self.id_aula,
            "edificio": self.edificio,
            "capacidad_maxima": self.capacidad_maxima,
            "es_laboratorio": self.es_laboratorio,
            "estado_operativo": self.estado_operativo,
            "tipo_texto": "LABORATORIO" if self.es_laboratorio else "AULA TEÓRICA"
        }

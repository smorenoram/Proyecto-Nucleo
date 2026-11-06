# -*- coding: utf-8 -*-
from dataclasses import dataclass

@dataclass
class Curso:
    """Entidad de dominio que modela una asignatura del plan de estudios."""
    id_curso: str
    codigo_asignatura: str
    nombre_curso: str
    semestre_plan: int
    creditos: int
    sesiones_semanales: int
    requiere_laboratorio: bool
    cupo_minimo_apertura: int = 10

    def to_dict(self) -> dict:
        return {
            "id_curso": self.id_curso,
            "codigo_asignatura": self.codigo_asignatura,
            "nombre_curso": self.nombre_curso,
            "semestre_plan": self.semestre_plan,
            "creditos": self.creditos,
            "sesiones_semanales": self.sesiones_semanales,
            "requiere_laboratorio": self.requiere_laboratorio,
            "cupo_minimo_apertura": self.cupo_minimo_apertura
        }

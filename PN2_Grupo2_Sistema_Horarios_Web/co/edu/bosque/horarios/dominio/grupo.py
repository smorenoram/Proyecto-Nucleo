# -*- coding: utf-8 -*-
from dataclasses import dataclass
from .curso import Curso

@dataclass
class Grupo:
    """Representa una sección abierta de un curso con su matrícula registrada."""
    id_grupo: str
    curso: Curso
    periodo_academico: str
    numero_seccion: int
    numero_inscritos: int
    estado_grupo: str = "ACTIVO"

    def cumple_cupo_minimo(self) -> bool:
        return self.numero_inscritos >= self.curso.cupo_minimo_apertura

    def to_dict(self) -> dict:
        return {
            "id_grupo": self.id_grupo,
            "id_curso": self.curso.id_curso,
            "codigo_asignatura": self.curso.codigo_asignatura,
            "nombre_curso": self.curso.nombre_curso,
            "semestre_plan": self.curso.semestre_plan,
            "sesiones_semanales": self.curso.sesiones_semanales,
            "requiere_laboratorio": self.curso.requiere_laboratorio,
            "cupo_minimo_apertura": self.curso.cupo_minimo_apertura,
            "periodo_academico": self.periodo_academico,
            "numero_seccion": self.numero_seccion,
            "numero_inscritos": self.numero_inscritos,
            "estado_grupo": self.estado_grupo,
            "cumple_cupo": self.cumple_cupo_minimo()
        }

# -*- coding: utf-8 -*-
from dataclasses import dataclass
from .grupo import Grupo
from .docente import Docente
from .aula import Aula
from .franja_horaria import FranjaHoraria

@dataclass
class AsignacionHorario:
    """Vincula un Grupo, un Docente, un Aula y una FranjaHoraria validada."""
    id_asignacion: str
    grupo: Grupo
    docente: Docente
    aula: Aula
    franja: FranjaHoraria
    estado_validacion: str = "PENDIENTE"

    def to_dict(self) -> dict:
        return {
            "id_asignacion": self.id_asignacion,
            "id_grupo": self.grupo.id_grupo,
            "codigo_asignatura": self.grupo.curso.codigo_asignatura,
            "nombre_curso": self.grupo.curso.nombre_curso,
            "numero_inscritos": self.grupo.numero_inscritos,
            "id_docente": self.docente.id_docente,
            "nombre_docente": self.docente.nombre_completo,
            "id_aula": self.aula.id_aula,
            "edificio": self.aula.edificio,
            "es_laboratorio": self.aula.es_laboratorio,
            "id_franja": self.franja.id_franja,
            "dia_semana": self.franja.dia_semana,
            "hora_inicio": self.franja.hora_inicio,
            "hora_fin": self.franja.hora_fin,
            "bloque_academico": self.franja.bloque_academico,
            "estado_validacion": self.estado_validacion
        }

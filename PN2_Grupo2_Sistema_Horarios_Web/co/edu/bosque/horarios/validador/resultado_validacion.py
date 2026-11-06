# -*- coding: utf-8 -*-
from dataclasses import dataclass

@dataclass
class ResultadoValidacion:
    """Objeto de transferencia tipado que encapsula el dictamen de una estrategia de validación."""
    es_valido: bool
    tipo_restriccion: str  # "DURA" o "BLANDA"
    codigo_regla: str      # Ej: "RD-01", "RD-02", "RD-03", "RD-04", "RD-05", "RD-06", "RB-01"
    mensaje_detalle: str

    def is_es_valido(self) -> bool:
        return self.es_valido

    def get_mensaje_detalle(self) -> str:
        return self.mensaje_detalle

    def to_dict(self) -> dict:
        return {
            "es_valido": self.es_valido,
            "tipo_restriccion": self.tipo_restriccion,
            "codigo_regla": self.codigo_regla,
            "mensaje_detalle": self.mensaje_detalle
        }

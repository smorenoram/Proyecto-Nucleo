#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO NÚCLEO 2 - MÓDULO 3: ENTREGA FINAL
Sistema Web de Asignación Asistida de Horarios Académicos
Universidad El Bosque - Programa de Ingeniería de Sistemas (Grupo 2)
Integrantes: Keving Cárdenas, Daniel Quijano, Santiago Moreno, Samuel Vera

Modos de ejecución:
  1. Aplicación Web Interactiva (abre http://127.0.0.1:8080 en el navegador):
     python main.py
  2. Auditoría QA y Prueba de Estrés por Consola (sin interfaz):
     python main.py --cli-qa
"""
import argparse
from co.edu.bosque.horarios.controlador.controlador_asignacion import ControladorAsignacion
from co.edu.bosque.horarios.vista.servidor_web import iniciar_servidor_web

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sistema Web de Asignación Asistida de Horarios Académicos - PN2"
    )
    parser.add_argument(
        "--cli-qa",
        action="store_true",
        help="Ejecuta la suite de auditoría QA (CP-01 a CP-08) y la prueba de estrés de 200 sesiones por consola."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Puerto HTTP para el servidor web (por defecto: 8080)."
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Inicia el servidor web sin abrir automáticamente el navegador."
    )
    args = parser.parse_args()

    controlador = ControladorAsignacion()

    if args.cli_qa:
        print(controlador.ejecutar_suite_qa_y_estres())
    else:
        iniciar_servidor_web(
            controlador=controlador,
            host="127.0.0.1",
            port=args.port,
            abrir_navegador=not args.no_browser
        )

if __name__ == "__main__":
    main()

# Sistema Web de Asignación Asistida de Horarios Académicos (SGAH — MVP)

**Universidad El Bosque · Facultad de Ingeniería · Programa de Ingeniería de Sistemas**  
**Asignatura:** Proyecto Núcleo 2 (Código 15319) — Semestre 2026-2  
**Docente:** Ing. Samuel Galindo Pinzón  
**Integrantes (Grupo 2):**
- Keving Cárdenas Cárdenas
- Daniel Alejandro Quijano Acevedo
- Santiago Moreno Ramírez
- Samuel Vera Carreño

---

## 1. Descripción General y Arquitectura

Este proyecto implementa el **Producto Mínimo Viable (MVP)** para el problema de programación asistida de horarios universitarios (*University Course Timetabling Problem - UCTP*), estructurado bajo una **Arquitectura en 5 Paquetes** (`co.edu.bosque.horarios`), el **Patrón de Diseño GoF Strategy** (`IRestriccionStrategy`), los **Principios SOLID (SRP, OCP, DIP)** y persistencia relacional en **Tercera Forma Normal (3FN)** sobre **SQLite 3**.

### Estructura de Paquetes del Proyecto

```text
PN2_Grupo2_Sistema_Horarios_Web/
├── main.py                                       # Punto de entrada (Servidor Web o CLI QA)
├── requirements.txt                              # Sin dependencias externas (100% Python Stdlib)
├── README.md                                     # Manual rápido de instalación y despliegue
├── co/edu/bosque/horarios/
│   ├── dominio/                                  # Entidades del negocio
│   │   ├── franja_horaria.py                     # Clase FranjaHoraria
│   │   ├── docente.py                            # Clase Docente
│   │   ├── aula.py                               # Clase Aula
│   │   ├── curso.py                              # Clase Curso (incluye cupo_minimo_apertura)
│   │   ├── grupo.py                              # Clase Grupo (incluye numero_inscritos)
│   │   └── asignacion_horario.py                 # Clase AsignacionHorario
│   ├── validador/                                # Patrón GoF Strategy y Motor Polimórfico
│   │   ├── resultado_validacion.py               # DTO tipado ResultadoValidacion
│   │   ├── i_restriccion_strategy.py             # Interfaz abstracta IRestriccionStrategy
│   │   ├── motor_asignacion.py                   # Contexto MotorAsignacion
│   │   ├── docente_sin_choque_strategy.py        # Reglas RD-01 y RD-05
│   │   ├── aula_sin_choque_strategy.py           # Regla RD-02
│   │   ├── capacidad_y_tipo_aula_strategy.py     # Reglas RD-03 y RD-04
│   │   ├── unicidad_grupo_strategy.py            # Regla RD-06
│   │   └── cupo_minimo_grupo_strategy.py         # Regla RB-01 (Cierre preventivo por bajo cupo)
│   ├── persistencia/                             # Capa de Datos Relacional en 3FN
│   │   └── gestor_bd_sqlite.py                   # Creación 3FN, candados UNIQUE y semilla (12/6/20)
│   ├── controlador/                              # Orquestación y Filtro de Alternativas
│   │   └── controlador_asignacion.py             # Procesamiento, buscar_aulas_alternativas y QA
│   └── vista/                                    # Capa de Presentación Web (API REST + SPA)
│       ├── servidor_web.py                       # Servidor HTTP/REST en http://127.0.0.1:8080
│       └── static/
│           ├── index.html                        # Interfaz Web con Grilla Semanal Drag & Drop y Modales
│           ├── styles.css                        # Hoja de estilos institucional
│           └── app.js                            # Lógica cliente, modales asistidos y trazabilidad
├── tests/
│   └── test_suite_qa.py                          # 8 pruebas unitarias automatizadas (CP-01 a CP-08)
└── diagramas_puml/                               # Fuentes PlantUML (.puml) sincronizados con el código
```

---

## 2. Requisitos del Sistema e Instalación

- **Python:** 3.8 o superior (compatible con Python 3.9, 3.10, 3.11, 3.12 y 3.13 en Windows, macOS y Linux).
- **Dependencias:** Utiliza exclusivamente la biblioteca estándar de Python (`http.server`, `sqlite3`, `dataclasses`, `abc`, `csv`, `json`, `unittest`), por lo que **no requiere instalar paquetes con `pip`** ni motores de bases de datos externos.
- **Navegador Web:** Google Chrome, Mozilla Firefox, Microsoft Edge o Safari.

---

## 3. Comandos de Ejecución

### A. Iniciar la Aplicación Web Interactiva (Para Sustentación en Vivo)
Desde la carpeta raíz del proyecto, ejecute:
```bash
python main.py
```
El sistema creará automáticamente la base de datos `horarios_pn2.db` en 3FN con **12 docentes, 6 aulas, 15 franjas y 20 asignaturas/grupos**, iniciará el servidor web local en `http://127.0.0.1:8080` y abrirá el navegador automáticamente.

### B. Ejecutar la Suite de Pruebas Unitarias (`unittest`)
```bash
python -m unittest discover -s tests -v
```

### C. Ejecutar la Auditoría QA (CP-01 a CP-08) y Prueba de Estrés (200 sesiones) por Consola
```bash
python main.py --cli-qa
```

# -*- coding: utf-8 -*-
import os
import sqlite3
from typing import Dict, List, Tuple
from co.edu.bosque.horarios.dominio.franja_horaria import FranjaHoraria
from co.edu.bosque.horarios.dominio.docente import Docente
from co.edu.bosque.horarios.dominio.aula import Aula
from co.edu.bosque.horarios.dominio.curso import Curso
from co.edu.bosque.horarios.dominio.grupo import Grupo
from co.edu.bosque.horarios.dominio.asignacion_horario import AsignacionHorario

class GestorBDSQLite:
    """
    Capa de Persistencia Relacional en Tercera Forma Normal (3FN) sobre SQLite 3.
    Implementa candados de integridad referencial y restricciones UNIQUE compuestas.
    """
    def __init__(self, db_path: str = None) -> None:
        if db_path is None:
            # Resolver siempre respecto a la raíz del proyecto para que funcione desde cualquier directorio
            project_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
            )
            db_path = os.path.join(project_root, "horarios_pn2.db")
        self.db_path = db_path
        self.inicializar_esquema_3fn()

    def inicializar_esquema_3fn(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.executescript("""
            PRAGMA journal_mode = MEMORY;
            PRAGMA synchronous = OFF;
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS USUARIO_SISTEMA (
                correo_institucional VARCHAR(80) PRIMARY KEY,
                password_acceso VARCHAR(40) NOT NULL,
                rol VARCHAR(20) NOT NULL,
                nombre_mostrar VARCHAR(100) NOT NULL,
                id_referencia VARCHAR(20)
            );

            CREATE TABLE IF NOT EXISTS DOCENTE (
                id_docente VARCHAR(15) PRIMARY KEY,
                documento_identidad VARCHAR(20) UNIQUE NOT NULL,
                nombre_completo VARCHAR(100) NOT NULL,
                tipo_vinculacion VARCHAR(20) NOT NULL,
                max_horas_semanales INT NOT NULL,
                especialidad VARCHAR(80) NOT NULL
            );

            CREATE TABLE IF NOT EXISTS FRANJA_HORARIA (
                id_franja VARCHAR(15) PRIMARY KEY,
                dia_semana VARCHAR(12) NOT NULL,
                hora_inicio TIME NOT NULL,
                hora_fin TIME NOT NULL,
                bloque_academico INT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS DISPONIBILIDAD_DOCENTE (
                id_disponibilidad INTEGER PRIMARY KEY AUTOINCREMENT,
                id_docente VARCHAR(15) NOT NULL,
                id_franja VARCHAR(15) NOT NULL,
                disponible BOOLEAN NOT NULL DEFAULT 1,
                FOREIGN KEY (id_docente) REFERENCES DOCENTE(id_docente),
                FOREIGN KEY (id_franja) REFERENCES FRANJA_HORARIA(id_franja)
            );

            CREATE TABLE IF NOT EXISTS AULA (
                id_aula VARCHAR(15) PRIMARY KEY,
                edificio VARCHAR(40) NOT NULL,
                capacidad_maxima INT NOT NULL,
                es_laboratorio BOOLEAN NOT NULL DEFAULT 0,
                estado_operativo BOOLEAN NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS CURSO (
                id_curso VARCHAR(15) PRIMARY KEY,
                codigo_asignatura VARCHAR(15) UNIQUE NOT NULL,
                nombre_curso VARCHAR(100) NOT NULL,
                semestre_plan INT NOT NULL,
                creditos INT NOT NULL,
                sesiones_semanales INT NOT NULL,
                requiere_laboratorio BOOLEAN NOT NULL DEFAULT 0,
                cupo_minimo_apertura INT NOT NULL DEFAULT 10
            );

            CREATE TABLE IF NOT EXISTS GRUPO (
                id_grupo VARCHAR(15) PRIMARY KEY,
                id_curso VARCHAR(15) NOT NULL,
                periodo_academico VARCHAR(10) NOT NULL,
                numero_seccion INT NOT NULL,
                numero_inscritos INT NOT NULL,
                estado_grupo VARCHAR(25) NOT NULL DEFAULT 'ACTIVO',
                FOREIGN KEY (id_curso) REFERENCES CURSO(id_curso)
            );

            CREATE TABLE IF NOT EXISTS ASIGNACION_HORARIO (
                id_asignacion VARCHAR(20) PRIMARY KEY,
                id_grupo VARCHAR(15) NOT NULL,
                id_docente VARCHAR(15) NOT NULL,
                id_aula VARCHAR(15) NOT NULL,
                id_franja VARCHAR(15) NOT NULL,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_grupo) REFERENCES GRUPO(id_grupo),
                FOREIGN KEY (id_docente) REFERENCES DOCENTE(id_docente),
                FOREIGN KEY (id_aula) REFERENCES AULA(id_aula),
                FOREIGN KEY (id_franja) REFERENCES FRANJA_HORARIA(id_franja),
                CONSTRAINT UQ_DOCENTE_FRANJA UNIQUE (id_docente, id_franja),
                CONSTRAINT UQ_AULA_FRANJA UNIQUE (id_aula, id_franja),
                CONSTRAINT UQ_GRUPO_FRANJA UNIQUE (id_grupo, id_franja)
            );
        """)
        cur.execute("SELECT COUNT(*) FROM DOCENTE")
        if cur.fetchone()[0] == 0:
            self._insertar_datos_semilla(cur)
        conn.commit()
        conn.close()

    def _insertar_datos_semilla(self, cur: sqlite3.Cursor) -> None:
        # Usuarios del Sistema para Control de Acceso Basado en Roles (RNF-04)
        usuarios_seed = [
            ("director@unbosque.edu.co", "Director2026*", "COORDINADOR", "Ing. Samuel Galindo (Director de Programa)", "DOC-01"),
            ("coordinacion.sistemas@unbosque.edu.co", "UEB-PN2-2026", "COORDINADOR", "Comité Táctico (Administrador)", "ADMIN"),
            ("emorales@unbosque.edu.co", "Docente2026*", "DOCENTE", "Dra. Elena Morales (Docente TC)", "DOC-02"),
            ("jmendez@unbosque.edu.co", "Docente2026*", "DOCENTE", "Ing. Jorge Méndez (Docente Cátedra)", "DOC-07"),
            ("dquijanoa@unbosque.edu.co", "Estudiante2026*", "ESTUDIANTE", "Daniel Alejandro Quijano (Estudiante Sem. 4)", "SEM-4"),
            ("kcardenas@unbosque.edu.co", "Estudiante2026*", "ESTUDIANTE", "Keving Cárdenas (Estudiante Sem. 5)", "SEM-5"),
        ]
        cur.executemany("INSERT OR IGNORE INTO USUARIO_SISTEMA VALUES (?, ?, ?, ?, ?)", usuarios_seed)

        # 15 Franjas Horarias (Lunes a Viernes, 3 bloques de 2h por día; excluye 12:00-13:00 bloqueado)
        dias = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"]
        bloques = [
            (1, "07:00", "09:00"),
            (2, "09:00", "11:00"),
            (3, "14:00", "16:00"),
        ]
        franjas_ids = []
        for d in dias:
            for num_b, ini, fin in bloques:
                fid = f"{d[:3]}-B{num_b}"
                franjas_ids.append(fid)
                cur.execute(
                    "INSERT INTO FRANJA_HORARIA VALUES (?, ?, ?, ?, ?)",
                    (fid, d, ini, fin, num_b)
                )

        # 12 Docentes (Supera el mínimo exigido de 10 docentes)
        docentes_seed = [
            ("DOC-01", "79100101", "Ing. Samuel Galindo", "TC", 16, "Arquitectura y Diseño de Software"),
            ("DOC-02", "79100102", "Dra. Elena Morales", "TC", 16, "Bases de Datos e IA"),
            ("DOC-03", "79100103", "Mag. Carlos Ruiz", "TC", 16, "Redes y Telecomunicaciones"),
            ("DOC-04", "79100104", "Ing. Laura Gómez", "MT", 10, "Ingeniería de Requisitos"),
            ("DOC-05", "79100105", "Dr. Andrés Pineda", "TC", 16, "Algoritmia y Estructuras"),
            ("DOC-06", "79100106", "Mag. Diana Castro", "MT", 10, "Dinámica de Sistemas"),
            ("DOC-07", "79100107", "Ing. Jorge Méndez", "CATEDRA", 6, "Seguridad Informática"),
            ("DOC-08", "79100108", "Dra. Sofía Vargas", "TC", 16, "Matemáticas Discretas"),
            ("DOC-09", "79100109", "Mag. Felipe León", "MT", 10, "Sistemas Operativos"),
            ("DOC-10", "79100110", "Ing. Camila Reyes", "TC", 16, "Verificación y Pruebas QA"),
            ("DOC-11", "79100111", "Mag. Óscar Pardo", "CATEDRA", 4, "Gestión de Proyectos TI"),
            ("DOC-12", "79100112", "Ing. Natalia Ríos", "TC", 16, "Computación en la Nube"),
        ]
        cur.executemany("INSERT INTO DOCENTE VALUES (?, ?, ?, ?, ?, ?)", docentes_seed)

        for doc_id, _, _, vinc, _, _ in docentes_seed:
            for fid in franjas_ids:
                if vinc == "CATEDRA" and not (fid.startswith("LUN") or fid.startswith("MAR")):
                    continue
                cur.execute(
                    "INSERT INTO DISPONIBILIDAD_DOCENTE (id_docente, id_franja, disponible) VALUES (?, ?, 1)",
                    (doc_id, fid)
                )

        # 6 Aulas (Supera el mínimo exigido de 5 aulas; incluye teóricas y laboratorios)
        aulas_seed = [
            ("AULA-A101", "Bloque A", 35, 0, 1),
            ("AULA-A102", "Bloque A", 25, 0, 1),
            ("AULA-A104", "Bloque A", 40, 0, 1),
            ("AULA-B201", "Bloque B", 44, 0, 1),
            ("LAB-C301", "Laboratorios C", 30, 1, 1),
            ("LAB-C302", "Laboratorios C", 35, 1, 1),
        ]
        cur.executemany("INSERT INTO AULA VALUES (?, ?, ?, ?, ?)", aulas_seed)

        # 20 Cursos y 20 Grupos (Cumple el requisito de >= 20 asignaturas)
        cursos_grupos_seed = [
            ("CUR-01", "SIS-101", "Programación Orientada a Objetos", 2, 3, 2, 1, 10, "GRP-01", 28),
            ("CUR-02", "SIS-102", "Estructuras de Datos", 3, 3, 2, 1, 10, "GRP-02", 26),
            ("CUR-03", "SIS-201", "Proyecto Núcleo 2", 4, 4, 2, 0, 10, "GRP-03", 32),
            ("CUR-04", "SIS-202", "Bases de Datos I", 4, 3, 2, 1, 10, "GRP-04", 29),
            ("CUR-05", "SIS-203", "Bases de Datos II", 5, 3, 2, 1, 10, "GRP-05", 24),
            ("CUR-06", "SIS-301", "Redes de Computadores", 5, 3, 2, 1, 10, "GRP-06", 30),
            ("CUR-07", "SIS-302", "Ingeniería de Software I", 5, 3, 2, 0, 10, "GRP-07", 34),
            ("CUR-08", "SIS-303", "Ingeniería de Software II", 6, 3, 2, 0, 10, "GRP-08", 22),
            ("CUR-09", "SIS-304", "Arquitectura de Software", 7, 3, 2, 0, 10, "GRP-09", 38),
            ("CUR-10", "SIS-401", "Dinámica de Sistemas", 6, 3, 2, 1, 10, "GRP-10", 25),
            ("CUR-11", "SIS-402", "Sistemas Operativos", 4, 3, 2, 1, 10, "GRP-11", 27),
            ("CUR-12", "SIS-403", "Seguridad de la Información", 7, 3, 1, 1, 10, "GRP-12", 20),
            ("CUR-13", "SIS-404", "Matemáticas Discretas", 2, 3, 2, 0, 12, "GRP-13", 31),
            ("CUR-14", "SIS-405", "Gerencia de Proyectos TI", 8, 3, 1, 0, 10, "GRP-14", 19),
            ("CUR-15", "SIS-406", "Calidad y Pruebas de Software", 7, 3, 2, 0, 10, "GRP-15", 23),
            ("CUR-16", "SIS-407", "Computación en la Nube", 8, 3, 2, 1, 10, "GRP-16", 28),
            ("CUR-17", "SIS-408", "Inteligencia Artificial", 8, 3, 2, 1, 10, "GRP-17", 33),
            ("CUR-18", "SIS-409", "Teoría General de Sistemas", 1, 2, 1, 0, 12, "GRP-18", 42),
            ("CUR-19", "SIS-410", "Electiva Analítica Avanzada (Bajo Cupo)", 9, 3, 1, 0, 12, "GRP-19", 6),
            ("CUR-20", "SIS-411", "Seminario de Investigación", 9, 2, 1, 0, 10, "GRP-20", 18),
        ]
        for cid, cod, nom, sem, cred, ses, lab, min_c, gid, insc in cursos_grupos_seed:
            cur.execute(
                "INSERT INTO CURSO VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (cid, cod, nom, sem, cred, ses, lab, min_c)
            )
            estado = "ACTIVO" if insc >= min_c else "ALERTA_CIERRE_POR_CUPO"
            cur.execute(
                "INSERT INTO GRUPO VALUES (?, ?, '2026-2', 1, ?, ?)",
                (gid, cid, insc, estado)
            )

    def cargar_catalogos(self) -> Tuple[
        Dict[str, FranjaHoraria],
        Dict[str, Docente],
        Dict[str, Aula],
        Dict[str, Curso],
        Dict[str, Grupo],
        List[AsignacionHorario]
    ]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        franjas: Dict[str, FranjaHoraria] = {}
        cur.execute("SELECT * FROM FRANJA_HORARIA")
        for row in cur.fetchall():
            franjas[row[0]] = FranjaHoraria(row[0], row[1], row[2], row[3], int(row[4]))

        docentes: Dict[str, Docente] = {}
        cur.execute("SELECT * FROM DOCENTE")
        for row in cur.fetchall():
            cur.execute(
                "SELECT id_franja FROM DISPONIBILIDAD_DOCENTE WHERE id_docente = ? AND disponible = 1",
                (row[0],)
            )
            disp = [r[0] for r in cur.fetchall()]
            docentes[row[0]] = Docente(row[0], row[1], row[2], row[3], int(row[4]), row[5], disp)

        aulas: Dict[str, Aula] = {}
        cur.execute("SELECT * FROM AULA")
        for row in cur.fetchall():
            aulas[row[0]] = Aula(row[0], row[1], int(row[2]), bool(row[3]), bool(row[4]))

        cursos: Dict[str, Curso] = {}
        cur.execute("SELECT * FROM CURSO")
        for row in cur.fetchall():
            cursos[row[0]] = Curso(
                row[0], row[1], row[2], int(row[3]), int(row[4]), int(row[5]), bool(row[6]), int(row[7])
            )

        grupos: Dict[str, Grupo] = {}
        cur.execute("SELECT * FROM GRUPO")
        for row in cur.fetchall():
            grupos[row[0]] = Grupo(row[0], cursos[row[1]], row[2], int(row[3]), int(row[4]), row[5])

        asignaciones: List[AsignacionHorario] = []
        cur.execute("SELECT id_asignacion, id_grupo, id_docente, id_aula, id_franja FROM ASIGNACION_HORARIO")
        for row in cur.fetchall():
            asignaciones.append(
                AsignacionHorario(
                    row[0], grupos[row[1]], docentes[row[2]], aulas[row[3]], franjas[row[4]], "APROBADA"
                )
            )

        conn.close()
        return franjas, docentes, aulas, cursos, grupos, asignaciones

    def guardar_asignacion(self, asig: AsignacionHorario) -> None:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode = MEMORY;")
        cur.execute("PRAGMA synchronous = OFF;")
        cur.execute("PRAGMA foreign_keys = ON;")
        cur.execute(
            "INSERT INTO ASIGNACION_HORARIO (id_asignacion, id_grupo, id_docente, id_aula, id_franja) "
            "VALUES (?, ?, ?, ?, ?)",
            (asig.id_asignacion, asig.grupo.id_grupo, asig.docente.id_docente, asig.aula.id_aula, asig.franja.id_franja)
        )
        conn.commit()
        conn.close()

    def limpiar_asignaciones(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode = MEMORY;")
        cur.execute("PRAGMA synchronous = OFF;")
        cur.execute("DELETE FROM ASIGNACION_HORARIO")
        conn.commit()
        conn.close()

    def actualizar_inscritos_grupo(self, id_grupo: str, nuevo_inscritos: int, nuevo_estado: str) -> None:
        """Actualiza en SQLite 3FN el número de estudiantes inscritos y el estado (ACTIVO / ALERTA_CIERRE_POR_CUPO)."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode = MEMORY;")
        cur.execute("PRAGMA synchronous = OFF;")
        cur.execute("PRAGMA foreign_keys = ON;")
        cur.execute(
            "UPDATE GRUPO SET numero_inscritos = ?, estado_grupo = ? WHERE id_grupo = ?",
            (nuevo_inscritos, nuevo_estado, id_grupo)
        )
        conn.commit()
        conn.close()

    def autenticar_usuario(self, correo: str, password: str, rol_esperado: str = None) -> dict:
        """Verifica en SQLite que el correo, la contraseña y el rol coincidan exactamente con un usuario registrado."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT correo_institucional, rol, nombre_mostrar, id_referencia FROM USUARIO_SISTEMA "
            "WHERE LOWER(correo_institucional) = LOWER(?) AND password_acceso = ?",
            (correo.strip(), password.strip())
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return {"autenticado": False, "mensaje": "Credenciales inválidas: correo institucional o contraseña incorrectos."}
        if rol_esperado and row[1] != rol_esperado:
            return {
                "autenticado": False,
                "mensaje": f"El usuario '{row[0]}' pertenece al rol {row[1]}, no al rol {rol_esperado} seleccionado."
            }
        return {
            "autenticado": True,
            "correo": row[0],
            "rol": row[1],
            "nombre": row[2],
            "id_referencia": row[3]
        }

    def actualizar_disponibilidad_docente(self, id_docente: str, id_franja: str, disponible: bool) -> None:
        """Permite al rol DOCENTE habilitar o bloquear una franja horaria en DISPONIBILIDAD_DOCENTE (RF-02 / RD-05)."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode = MEMORY;")
        cur.execute("PRAGMA synchronous = OFF;")
        cur.execute("PRAGMA foreign_keys = ON;")
        cur.execute(
            "DELETE FROM DISPONIBILIDAD_DOCENTE WHERE id_docente = ? AND id_franja = ?",
            (id_docente, id_franja)
        )
        if disponible:
            cur.execute(
                "INSERT INTO DISPONIBILIDAD_DOCENTE (id_docente, id_franja, disponible) VALUES (?, ?, 1)",
                (id_docente, id_franja)
            )
        conn.commit()
        conn.close()

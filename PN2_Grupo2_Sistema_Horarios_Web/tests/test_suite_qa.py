# -*- coding: utf-8 -*-
import os
import tempfile
import unittest
from co.edu.bosque.horarios.controlador.controlador_asignacion import ControladorAsignacion

class TestMotorHorariosQA(unittest.TestCase):
    """
    Suite formal de pruebas unitarias automatizadas (CP-01 a CP-08).
    Verifica extremo a extremo cada restricción del Módulo 1, su clase Strategy del Módulo 2
    y la persistencia SQLite 3FN del Módulo 3.
    """
    def setUp(self) -> None:
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.ctrl = ControladorAsignacion(db_path=self.temp_db.name)
        # Sesión base: GRP-03 con DOC-01 en AULA-A101 durante LUN-B1
        res_base = self.ctrl.procesar_asignacion("GRP-03", "DOC-01", "AULA-A101", "LUN-B1")
        self.assertTrue(res_base["exito"])

    def tearDown(self) -> None:
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_cp01_bloqueo_choque_docente_rd01(self) -> None:
        """CP-01 (RD-01): Impide asignar el mismo docente (DOC-01) a dos grupos en la misma franja (LUN-B1)."""
        res = self.ctrl.procesar_asignacion("GRP-07", "DOC-01", "AULA-A104", "LUN-B1")
        self.assertFalse(res["exito"])
        self.assertEqual(res["tipo_bloqueo"], "DURA")
        codigos = [e.codigo_regla for e in res["errores"]]
        self.assertIn("RD-01", codigos)

    def test_cp02_bloqueo_choque_aula_rd02(self) -> None:
        """CP-02 (RD-02): Impide asignar la misma aula (AULA-A101) a dos grupos en la misma franja (LUN-B1)."""
        res = self.ctrl.procesar_asignacion("GRP-08", "DOC-04", "AULA-A101", "LUN-B1")
        self.assertFalse(res["exito"])
        codigos = [e.codigo_regla for e in res["errores"]]
        self.assertIn("RD-02", codigos)

    def test_cp03_bloqueo_sobrecupo_aula_rd03(self) -> None:
        """CP-03 (RD-03): Impide asignar un grupo de 38 estudiantes (GRP-09) en un aula de capacidad 25 (AULA-A102)."""
        res = self.ctrl.procesar_asignacion("GRP-09", "DOC-02", "AULA-A102", "MAR-B1")
        self.assertFalse(res["exito"])
        codigos = [e.codigo_regla for e in res["errores"]]
        self.assertIn("RD-03", codigos)

    def test_cp04_incompatibilidad_laboratorio_rd04(self) -> None:
        """CP-04 (RD-04): Impide programar un curso que requiere laboratorio (GRP-01) en un aula teórica (AULA-A101)."""
        res = self.ctrl.procesar_asignacion("GRP-01", "DOC-05", "AULA-A101", "MIE-B1")
        self.assertFalse(res["exito"])
        codigos = [e.codigo_regla for e in res["errores"]]
        self.assertIn("RD-04", codigos)

    def test_cp05_indisponibilidad_docente_catedra_rd05(self) -> None:
        """CP-05 (RD-05): Impide programar al docente de cátedra DOC-07 en jueves (JUE-B1) fuera de su disponibilidad."""
        res = self.ctrl.procesar_asignacion("GRP-12", "DOC-07", "LAB-C301", "JUE-B1")
        self.assertFalse(res["exito"])
        codigos = [e.codigo_regla for e in res["errores"]]
        self.assertIn("RD-05", codigos)

    def test_cp06_unicidad_grupo_en_franja_rd06(self) -> None:
        """CP-06 (RD-06): Impide que un mismo grupo (GRP-03) reciba dos sesiones simultáneas en la misma franja."""
        res = self.ctrl.procesar_asignacion("GRP-03", "DOC-04", "AULA-B201", "LUN-B1")
        self.assertFalse(res["exito"])
        codigos = [e.codigo_regla for e in res["errores"]]
        self.assertIn("RD-06", codigos)

    def test_cp07_alerta_cierre_preventivo_bajo_cupo_rb01(self) -> None:
        """CP-07 (RB-01): Emite alerta preventiva para GRP-19 (6 inscritos < mínimo 12) salvo excepción autorizada."""
        res_alerta = self.ctrl.procesar_asignacion("GRP-19", "DOC-08", "AULA-A102", "VIE-B1", autorizar_excepcion_cupo=False)
        self.assertFalse(res_alerta["exito"])
        self.assertEqual(res_alerta["tipo_bloqueo"], "BLANDA")
        self.assertEqual(res_alerta["errores"][0].codigo_regla, "RB-01")

        # Si el coordinador autoriza excepción administrativa, se permite el registro
        res_autorizado = self.ctrl.procesar_asignacion("GRP-19", "DOC-08", "AULA-A102", "VIE-B1", autorizar_excepcion_cupo=True)
        self.assertTrue(res_autorizado["exito"])

    def test_cp08_sugerencia_asistida_aulas_alternativas_rui01(self) -> None:
        """CP-08 (RUI-01): Ante choque en AULA-A101 para GRP-07 (34 inscritos), sugiere AULA-A104 y AULA-B201 excluyendo AULA-A102."""
        res = self.ctrl.procesar_asignacion("GRP-07", "DOC-04", "AULA-A101", "LUN-B1")
        self.assertFalse(res["exito"])
        ids_sugeridas = [a.id_aula for a in res["alternativas_aula"]]
        self.assertIn("AULA-A104", ids_sugeridas)
        self.assertIn("AULA-B201", ids_sugeridas)
        self.assertNotIn("AULA-A101", ids_sugeridas)  # Ocupada
        self.assertNotIn("AULA-A102", ids_sugeridas)  # Cap 25 < 34 inscritos


    def test_cp09_actualizacion_dinamica_estudiantes(self) -> None:
        """CP-09 (RF-04 / RB-01): Permite al Administrador añadir estudiantes, activar GRP-19 y bloquear excesos > 44."""
        # GRP-19 inicia con 6 inscritos (< mínimo 12) en estado ALERTA_CIERRE_POR_CUPO
        self.assertEqual(self.ctrl.grupos["GRP-19"].estado_grupo, "ALERTA_CIERRE_POR_CUPO")
        res_ok = self.ctrl.actualizar_inscritos_grupo("GRP-19", cantidad_a_sumar=6)
        self.assertTrue(res_ok["exito"])
        self.assertEqual(res_ok["nuevo_inscritos"], 12)
        self.assertEqual(res_ok["estado_grupo"], "ACTIVO")

        # Intentar subir por encima del tope institucional de 44 (40 + 10%) debe bloquearse
        res_tope = self.ctrl.actualizar_inscritos_grupo("GRP-19", nuevo_total=45)
        self.assertFalse(res_tope["exito"])
        self.assertIn("RD-03", res_tope["codigo_regla"])


    def test_cp10_autenticacion_roles_y_disponibilidad_docente(self) -> None:
        """CP-10 (RNF-04 / RF-02): Verifica rechazo de credenciales falsas y bloqueo de franjas por el Docente."""
        # Credencial falsa debe ser rechazada
        res_bad = self.ctrl.autenticar_usuario("falso@unbosque.edu.co", "12345", "COORDINADOR")
        self.assertFalse(res_bad["autenticado"])

        # Credencial real de Director debe aprobarse
        res_dir = self.ctrl.autenticar_usuario("director@unbosque.edu.co", "Director2026*", "COORDINADOR")
        self.assertTrue(res_dir["autenticado"])

        # El rol Docente (DOC-02) bloquea su franja VIE-B3 (RF-02) y luego el motor impide asignarlo ahí (RD-05)
        res_disp = self.ctrl.cambiar_disponibilidad_docente("DOC-02", "VIE-B3", disponible=False)
        self.assertTrue(res_disp["exito"])
        res_asig = self.ctrl.procesar_asignacion("GRP-04", "DOC-02", "LAB-C301", "VIE-B3")
        self.assertFalse(res_asig["exito"])
        self.assertEqual(res_asig["errores"][0].codigo_regla, "RD-05")

if __name__ == "__main__":
    unittest.main()

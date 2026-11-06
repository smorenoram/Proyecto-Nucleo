# -*- coding: utf-8 -*-
import json
import os
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from co.edu.bosque.horarios.controlador.controlador_asignacion import ControladorAsignacion

class VistaGrillaWebHandler(BaseHTTPRequestHandler):
    """
    Controlador HTTP / API REST nativo (sin dependencias externas) que sirve la
    interfaz Web de Asignación Asistida de Horarios (VistaGrillaHorario Web).
    """
    controlador: ControladorAsignacion = None
    static_dir: str = os.path.join(os.path.dirname(__file__), "static")

    def log_message(self, format: str, *args) -> None:
        # Silenciar logs repetitivos de consola salvo errores
        pass

    def _send_json(self, payload: dict, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, filename: str, content_type: str) -> None:
        filepath = os.path.join(self.static_dir, filename)
        if not os.path.exists(filepath):
            self.send_error(404, "Archivo no encontrado")
            return
        with open(filepath, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self._send_file("index.html", "text/html; charset=utf-8")
        elif path == "/styles.css":
            self._send_file("styles.css", "text/css; charset=utf-8")
        elif path == "/app.js":
            self._send_file("app.js", "application/javascript; charset=utf-8")
        elif path == "/api/estado":
            ctrl = self.controlador
            self._send_json({
                "grupos": [g.to_dict() for g in ctrl.grupos.values()],
                "docentes": [d.to_dict() for d in ctrl.docentes.values()],
                "aulas": [a.to_dict() for a in ctrl.aulas.values()],
                "franjas": [f.to_dict() for f in ctrl.franjas.values()],
                "asignaciones": [asig.to_dict() for asig in ctrl.asignaciones_activas],
            })
        elif path == "/api/exportar-csv":
            csv_data = self.controlador.generar_contenido_csv().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="Horario_Validado_PN2.csv"')
            self.send_header("Content-Length", str(len(csv_data)))
            self.end_headers()
            self.wfile.write(csv_data)
        else:
            self.send_error(404, "Ruta no encontrada")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}

        ctrl = self.controlador

        if path == "/api/login":
            res = ctrl.autenticar_usuario(
                correo=body.get("correo", ""),
                password=body.get("password", ""),
                rol_esperado=body.get("rol")
            )
            self._send_json(res)
            return

        if path == "/api/toggle-disponibilidad":
            res = ctrl.cambiar_disponibilidad_docente(
                id_docente=body["id_docente"],
                id_franja=body["id_franja"],
                disponible=bool(body["disponible"])
            )
            self._send_json(res)
            return

        if path == "/api/asignar":
            res = ctrl.procesar_asignacion(
                id_grupo=body["id_grupo"],
                id_docente=body["id_docente"],
                id_aula=body["id_aula"],
                id_franja=body["id_franja"],
                autorizar_excepcion_cupo=bool(body.get("autorizar_excepcion_cupo", False))
            )
            payload = {
                "exito": res["exito"],
                "latencia_ms": round(res["latencia_ms"], 4),
            }
            if res["exito"]:
                payload["asignacion"] = res["asignacion"].to_dict()
            else:
                payload["tipo_bloqueo"] = res["tipo_bloqueo"]
                payload["errores"] = [e.to_dict() for e in res["errores"]]
                payload["alternativas_aula"] = [a.to_dict() for a in res["alternativas_aula"]]
            self._send_json(payload)

        elif path == "/api/demo-ruptura":
            ctrl.limpiar_asignaciones()
            ctrl.procesar_asignacion("GRP-03", "DOC-01", "AULA-A101", "LUN-B1")
            ctrl.procesar_asignacion("GRP-01", "DOC-05", "LAB-C301", "MAR-B1")
            # Forzar choque en AULA-A101 LUN-B1 con GRP-07 (34 inscritos)
            res = ctrl.procesar_asignacion("GRP-07", "DOC-04", "AULA-A101", "LUN-B1")
            self._send_json({
                "mensaje_demo": "Se cargaron 2 sesiones base (GRP-03 en AULA-A101 LUN-B1 y GRP-01 en LAB-C301 MAR-B1) y se intentó asignar GRP-07 en AULA-A101 LUN-B1.",
                "seleccion_intentada": {
                    "id_grupo": "GRP-07",
                    "id_docente": "DOC-04",
                    "id_aula": "AULA-A101",
                    "id_franja": "LUN-B1"
                },
                "resultado_choque": {
                    "exito": res["exito"],
                    "tipo_bloqueo": res["tipo_bloqueo"],
                    "latencia_ms": round(res["latencia_ms"], 4),
                    "errores": [e.to_dict() for e in res["errores"]],
                    "alternativas_aula": [a.to_dict() for a in res["alternativas_aula"]]
                }
            })

        elif path == "/api/qa":
            reporte = ctrl.ejecutar_suite_qa_y_estres()
            self._send_json({"reporte": reporte})

        elif path == "/api/actualizar-inscritos":
            res = ctrl.actualizar_inscritos_grupo(
                id_grupo=body["id_grupo"],
                cantidad_a_sumar=body.get("cantidad_a_sumar"),
                nuevo_total=body.get("nuevo_total")
            )
            self._send_json(res)

        elif path == "/api/reiniciar":
            ctrl.limpiar_asignaciones()
            self._send_json({"exito": True, "mensaje": "Todas las asignaciones fueron reiniciadas en SQLite 3FN."})

        else:
            self.send_error(404, "Endpoint no encontrado")


def iniciar_servidor_web(controlador: ControladorAsignacion, host: str = "127.0.0.1", port: int = 8080, abrir_navegador: bool = True) -> None:
    VistaGrillaWebHandler.controlador = controlador
    server = HTTPServer((host, port), VistaGrillaWebHandler)
    url = f"http://{host}:{port}"
    print("=" * 76)
    print(" SISTEMA WEB DE ASIGNACIÓN ASISTIDA DE HORARIOS ACADÉMICOS - PN2 (GRUPO 2)")
    print(" Universidad El Bosque | Arquitectura en Capas + Patrón Strategy + SQLite 3FN")
    print("=" * 76)
    print(f" -> Servidor Web activo en: {url}")
    print(f" -> Base de datos 3FN cargada: {len(controlador.docentes)} docentes, {len(controlador.aulas)} aulas, {len(controlador.grupos)} grupos.")
    print(" -> Presione Ctrl+C en esta terminal para detener el servidor.")
    print("=" * 76)
    if abrir_navegador:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[INFO] Servidor detenido correctamente.")
        server.server_close()

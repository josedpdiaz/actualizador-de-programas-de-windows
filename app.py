#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03-IA-ACTUALIZADOR-PROGRAMAS-WINDOWS
Aplicación ultraligera y eficiente para escanear y actualizar programas de Windows.
Desarrollado para pair-programming con Antigravity.
"""

import os
import sys
import json
import time
import socket
import threading
import subprocess
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Asegurar codificación UTF-8 en consola de Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PORT = 5055
HOST = "127.0.0.1"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")

# Estado global de la aplicación
app_state = {
    "is_scanning": False,
    "is_updating": False,
    "last_scan_time": None,
    "outdated_apps": [],
    "installed_apps": [],
    "logs": [],
    "current_action": "Listo",
    "progress_percent": 0,
    "total_to_update": 0,
    "updated_count": 0,
    "updated_ids": [],
    "failed_ids": [],
}

state_lock = threading.Lock()


def add_log(message: str, level: str = "info"):
    timestamp = time.strftime("%H:%M:%S")
    entry = {"time": timestamp, "message": message, "level": level}
    with state_lock:
        app_state["logs"].append(entry)
        if len(app_state["logs"]) > 2000:
            app_state["logs"].pop(0)
    try:
        print(f"[{timestamp}] [{level.upper()}] {message}", flush=True)
    except Exception:
        try:
            clean = message.encode("ascii", "replace").decode("ascii")
            print(f"[{timestamp}] [{level.upper()}] {clean}", flush=True)
        except Exception:
            pass


def parse_winget_table(output_text: str):
    """
    Parsea la salida tabular de winget de forma robusta e infalible.
    """
    lines = output_text.splitlines()
    sep_index = -1
    for i, line in enumerate(lines):
        if line.startswith("---") or (len(line) > 10 and set(line.strip()) == {"-"}):
            sep_index = i
            break

    if sep_index <= 0:
        return []

    header_line = lines[sep_index - 1]
    id_pos = header_line.find("Id")
    if id_pos == -1:
        id_pos = 30

    items = []
    for line in lines[sep_index + 1:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("-"):
            continue
        if "actualizaciones disponibles" in line or "actualización disponible" in line or "paquete(s)" in line:
            break

        name = line[:id_pos].strip()
        rest = line[id_pos:].strip().split()

        if len(rest) >= 4:
            pkg_id = rest[0]
            source = rest[-1]
            avail = rest[-2]
            curr = " ".join(rest[1:-2])
            items.append({
                "name": name if name else pkg_id,
                "id": pkg_id,
                "current_version": curr,
                "available_version": avail,
                "source": source,
                "selected": True
            })

    return items


def scan_updates_thread():
    with state_lock:
        app_state["is_scanning"] = True
        app_state["current_action"] = "Buscando actualizaciones de programas..."
    
    add_log("Iniciando escaneo de programas con Windows Package Manager (winget)...", "info")
    
    try:
        cmd = ["winget", "upgrade", "--include-unknown", "--accept-source-agreements"]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        stdout, _ = process.communicate()
        
        apps = parse_winget_table(stdout)
        
        with state_lock:
            app_state["outdated_apps"] = apps
            app_state["last_scan_time"] = time.strftime("%d/%m/%Y %H:%M:%S")
            app_state["current_action"] = f"Escaneo completado. {len(apps)} actualizaciones encontradas."
            
        add_log(f"Escaneo finalizado exitosamente. Se detectaron {len(apps)} programas con actualización.", "success")
        
    except Exception as e:
        add_log(f"Error durante el escaneo: {str(e)}", "error")
        with state_lock:
            app_state["current_action"] = "Error al escanear"
    finally:
        with state_lock:
            app_state["is_scanning"] = False


def scan_all_installed_thread():
    add_log("Listando todos los programas instalados en el sistema...", "info")
    try:
        cmd = ["winget", "list", "--accept-source-agreements"]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        stdout, _ = process.communicate()
        
        lines = stdout.splitlines()
        sep_index = -1
        for i, line in enumerate(lines):
            if line.startswith("---") or (len(line) > 10 and set(line.strip()) == {"-"}):
                sep_index = i
                break
                
        all_apps = []
        if sep_index > 0:
            header_line = lines[sep_index - 1]
            id_pos = header_line.find("Id")
            if id_pos == -1:
                id_pos = 30
                    
            for line in lines[sep_index + 1:]:
                stripped = line.strip()
                if not stripped or stripped.startswith("-"):
                    continue
                name = line[:id_pos].strip()
                rest = line[id_pos:].strip().split()
                if len(rest) >= 2:
                    pkg_id = rest[0]
                    source = rest[-1] if len(rest) >= 4 else ""
                    avail = rest[-2] if len(rest) >= 4 else ""
                    curr = " ".join(rest[1:-2]) if len(rest) >= 4 else (" ".join(rest[1:]) if len(rest) > 1 else "")
                    all_apps.append({
                        "name": name if name else pkg_id,
                        "id": pkg_id,
                        "version": curr,
                        "available": avail,
                        "source": source
                    })
                    
        with state_lock:
            app_state["installed_apps"] = all_apps
        add_log(f"Se listaron {len(all_apps)} programas instalados en total.", "info")
    except Exception as e:
        add_log(f"Error listando programas instalados: {str(e)}", "error")


def upgrade_all_thread():
    with state_lock:
        app_state["is_updating"] = True
        app_state["current_action"] = "Actualizando todos los programas automáticamente..."
        app_state["progress_percent"] = 5
        
    add_log("=== INICIANDO ACTUALIZACIÓN AUTOMÁTICA DE TODOS LOS PROGRAMAS ===", "info")
    add_log("Ejecutando: winget upgrade --all --silent --include-unknown --accept-package-agreements --accept-source-agreements", "info")
    
    try:
        cmd = [
            "winget", "upgrade", "--all",
            "--include-unknown",
            "--accept-package-agreements",
            "--accept-source-agreements",
            "--silent"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1
        )
        
        for raw_line in iter(process.stdout.readline, ''):
            line = raw_line.strip()
            if line:
                add_log(line, "process")
                
        process.stdout.close()
        return_code = process.wait()
        
        if return_code == 0:
            add_log("¡Todas las actualizaciones procesadas correctamente!", "success")
        else:
            add_log(f"Proceso finalizado con código: {return_code}.", "warning")
            
        scan_updates_thread()
        
    except Exception as e:
        add_log(f"Error en la actualización automática: {str(e)}", "error")
    finally:
        with state_lock:
            app_state["is_updating"] = False
            app_state["progress_percent"] = 100
            app_state["current_action"] = "Actualización concluida."


def upgrade_selected_thread(package_ids: list):
    total = len(package_ids)
    with state_lock:
        app_state["is_updating"] = True
        app_state["total_to_update"] = total
        app_state["updated_count"] = 0
        app_state["progress_percent"] = 0
        app_state["current_action"] = f"Actualizando {total} programas seleccionados..."
        
    add_log(f"Iniciando actualización selectiva de {total} programas...", "info")
    add_log("Aviso: Si el programa requiere permisos de Administrador, acepta la ventana de confirmación de Windows (UAC).", "info")
    
    for index, pkg_id in enumerate(package_ids):
        with state_lock:
            app_state["updated_count"] = index
            app_state["progress_percent"] = int((index / total) * 100)
            app_state["current_action"] = f"Actualizando [{index + 1}/{total}]: {pkg_id}"
            
        add_log(f"[{index + 1}/{total}] Actualizando: {pkg_id} ...", "info")
        
        cmd = [
            "winget", "upgrade",
            "--id", pkg_id,
            "--include-unknown",
            "--accept-package-agreements",
            "--accept-source-agreements",
            "--silent"
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1
            )
            for raw_line in iter(process.stdout.readline, ''):
                line = raw_line.strip()
                if line:
                    add_log(f"[{pkg_id}] {line}", "process")
            process.stdout.close()
            ret = process.wait(timeout=300)
            if ret == 0:
                add_log(f"OK: {pkg_id} actualizado exitosamente.", "success")
                with state_lock:
                    app_state["outdated_apps"] = [
                        a for a in app_state["outdated_apps"]
                        if a.get("id", "").lower() != pkg_id.lower()
                    ]
                    if pkg_id not in app_state["updated_ids"]:
                        app_state["updated_ids"].append(pkg_id)
            else:
                add_log(f"Aviso: {pkg_id} finalizó con código {ret}. Consulta la terminal para ver el detalle.", "warning")
                with state_lock:
                    if pkg_id not in [f.get("id") for f in app_state["failed_ids"]]:
                        app_state["failed_ids"].append({"id": pkg_id, "code": ret})
        except subprocess.TimeoutExpired:
            process.kill()
            add_log(f"Tiempo de espera agotado actualizando {pkg_id}.", "warning")
        except Exception as e:
            add_log(f"Error al actualizar {pkg_id}: {str(e)}", "error")
            
    with state_lock:
        app_state["updated_count"] = total
        app_state["progress_percent"] = 100
        app_state["is_updating"] = False
        app_state["current_action"] = "Actualización selectiva completada."
        
    add_log("=== Actualización selectiva finalizada ===", "success")
    scan_updates_thread()


class AppRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def log_message(self, format, *args):
        return

    def send_json_response(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            with state_lock:
                data = {
                    "is_scanning": app_state["is_scanning"],
                    "is_updating": app_state["is_updating"],
                    "last_scan_time": app_state["last_scan_time"],
                    "outdated_count": len(app_state["outdated_apps"]),
                    "installed_count": len(app_state["installed_apps"]),
                    "current_action": app_state["current_action"],
                    "progress_percent": app_state["progress_percent"],
                    "updated_count": app_state["updated_count"],
                    "total_to_update": app_state["total_to_update"],
                    "updated_ids": list(app_state["updated_ids"]),
                    "failed_ids": list(app_state["failed_ids"])
                }
            self.send_json_response(data)
            return

        elif path == "/api/apps":
            with state_lock:
                data = app_state["outdated_apps"]
            self.send_json_response(data)
            return

        elif path == "/api/all-installed":
            with state_lock:
                data = app_state["installed_apps"]
            self.send_json_response(data)
            return

        elif path == "/api/logs":
            query = parse_qs(parsed.query)
            since_index = int(query.get("since", [0])[0])
            with state_lock:
                all_logs = app_state["logs"]
                sliced_logs = all_logs[since_index:]
                total_len = len(all_logs)
            self.send_json_response({"logs": sliced_logs, "total": total_len})
            return

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b""
        payload = {}
        if post_data:
            try:
                payload = json.loads(post_data.decode("utf-8"))
            except Exception:
                pass

        if path == "/api/scan":
            if not app_state["is_scanning"] and not app_state["is_updating"]:
                threading.Thread(target=scan_updates_thread, daemon=True).start()
                self.send_json_response({"status": "started", "message": "Escaneo iniciado"})
            else:
                self.send_json_response({"status": "busy", "message": "Operación en curso"}, 409)
            return

        elif path == "/api/scan-all":
            threading.Thread(target=scan_all_installed_thread, daemon=True).start()
            self.send_json_response({"status": "started", "message": "Listado general iniciado"})
            return

        elif path == "/api/upgrade-all":
            if not app_state["is_updating"]:
                threading.Thread(target=upgrade_all_thread, daemon=True).start()
                self.send_json_response({"status": "started", "message": "Actualización global iniciada"})
            else:
                self.send_json_response({"status": "busy", "message": "Ya hay una actualización en curso"}, 409)
            return

        elif path == "/api/upgrade-selected":
            package_ids = payload.get("ids", [])
            if not package_ids:
                self.send_json_response({"status": "error", "message": "No se enviaron paquetes"}, 400)
                return
            if not app_state["is_updating"]:
                threading.Thread(target=upgrade_selected_thread, args=(package_ids,), daemon=True).start()
                self.send_json_response({"status": "started", "count": len(package_ids)})
            else:
                self.send_json_response({"status": "busy", "message": "Ya hay una actualización en curso"}, 409)
            return

        self.send_response(404)
        self.end_headers()


def is_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, port)) != 0


def open_desktop_window(url: str):
    time.sleep(1.2)
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for edge in edge_paths:
        if os.path.isfile(edge):
            try:
                subprocess.Popen([edge, f"--app={url}", "--window-size=1240,820"])
                return
            except Exception:
                pass
    webbrowser.open(url)


def main():
    global PORT
    while not is_port_available(PORT) and PORT < 5100:
        PORT += 1

    server_address = (HOST, PORT)
    httpd = HTTPServer(server_address, AppRequestHandler)
    app_url = f"http://{HOST}:{PORT}"

    print(f"============================================================")
    print(f"  03-IA-ACTUALIZADOR-PROGRAMAS-WINDOWS")
    print(f"  Servidor iniciado en: {app_url}")
    print(f"============================================================")

    # Iniciar escaneo inicial en segundo plano
    threading.Thread(target=scan_updates_thread, daemon=True).start()
    threading.Thread(target=scan_all_installed_thread, daemon=True).start()

    if "--no-browser" not in sys.argv:
        threading.Thread(target=open_desktop_window, args=(app_url,), daemon=True).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrando aplicación...")
        httpd.server_close()


if __name__ == "__main__":
    main()

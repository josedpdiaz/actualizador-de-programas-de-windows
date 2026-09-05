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
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request

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
APP_VERSION = "1.3.0"

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
    "uninstalled_ids": [],
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
            has_tech_conflict = False
            for raw_line in iter(process.stdout.readline, ''):
                line = raw_line.strip()
                if line:
                    add_log(f"[{pkg_id}] {line}", "process")
                    if "tecnología de instalación es diferente" in line.lower():
                        has_tech_conflict = True
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
                if has_tech_conflict:
                    add_log(f"ℹ️ {pkg_id}: Existen versiones anteriores con tecnologías de instalación distintas instaladas en este equipo (ej. EXE vs MSI). Winget requiere desinstalar la versión antigua desde Configuración de Windows > Aplicaciones para poder instalar la nueva.", "warning")
                else:
                    add_log(f"Aviso: {pkg_id} finalizó con código {ret}. Consulta la terminal para ver el detalle.", "warning")
                with state_lock:
                    if pkg_id not in [f.get("id") for f in app_state["failed_ids"]]:
                        app_state["failed_ids"].append({"id": pkg_id, "code": ret, "reason": "conflict" if has_tech_conflict else "other"})
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


def _find_registry_uninstall_string(pkg_id: str, pkg_name: str = "") -> str:
    """Busca el UninstallString en el Registro de Windows para un paquete dado."""
    import winreg
    search_terms = [t.lower() for t in [pkg_id, pkg_name] if t]
    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    for hive, base_path in reg_paths:
        try:
            with winreg.OpenKey(hive, base_path) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                            except FileNotFoundError:
                                continue
                            display_lower = display_name.lower()
                            matched = any(term in display_lower or display_lower in term for term in search_terms if term)
                            if not matched and pkg_id:
                                matched = subkey_name.lower() == pkg_id.lower()
                            if matched:
                                try:
                                    return winreg.QueryValueEx(subkey, "UninstallString")[0]
                                except FileNotFoundError:
                                    pass
                    except OSError:
                        continue
        except OSError:
            continue
    return ""


def _run_uninstall_cmd(cmd: list, pkg_id: str, timeout: int = 60) -> tuple:
    """Ejecuta un comando de desinstalación y retorna (código_retorno, fue_no_encontrado, salida).
    Incluye un watchdog que mata el proceso si se queda sin producir salida por más de 45 segundos."""
    output_lines = []
    not_found = False
    last_activity = [time.time()]
    STALL_TIMEOUT = 45  # segundos sin actividad antes de matar

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

        # Watchdog: si el proceso no produce salida en STALL_TIMEOUT segundos, lo mata
        def watchdog():
            while process.poll() is None:
                elapsed = time.time() - last_activity[0]
                if elapsed > STALL_TIMEOUT:
                    add_log(f"⏱️ El proceso lleva {int(elapsed)}s sin responder. Terminando automáticamente...", "warning")
                    try:
                        # Matar el proceso y todos sus hijos
                        subprocess.run(
                            ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                            capture_output=True, timeout=5
                        )
                    except Exception:
                        try:
                            process.kill()
                        except Exception:
                            pass
                    return
                time.sleep(3)

        watchdog_thread = threading.Thread(target=watchdog, daemon=True)
        watchdog_thread.start()

        for raw_line in iter(process.stdout.readline, ''):
            line = raw_line.strip()
            if line:
                last_activity[0] = time.time()
                add_log(f"[{pkg_id}] {line}", "process")
                output_lines.append(line)
                lower_line = line.lower()
                if "no se encontr" in lower_line or "no package found" in lower_line:
                    not_found = True
        process.stdout.close()
        ret = process.wait(timeout=timeout)
        return ret, not_found, output_lines
    except subprocess.TimeoutExpired:
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True, timeout=5)
        except Exception:
            process.kill()
        add_log(f"Tiempo de espera agotado ({timeout}s) ejecutando comando para {pkg_id}.", "warning")
        return -1, False, output_lines
    except Exception as e:
        add_log(f"Error ejecutando comando para {pkg_id}: {str(e)}", "error")
        return -99, False, output_lines


def uninstall_thread(pkg_id: str):
    with state_lock:
        app_state["is_updating"] = True
        app_state["current_action"] = f"Desinstalando programa: {pkg_id}..."
        app_state["progress_percent"] = 10

    # Buscar el nombre legible del programa en las listas internas
    pkg_name = ""
    with state_lock:
        for a in app_state["outdated_apps"] + app_state["installed_apps"]:
            if a.get("id", "").lower() == pkg_id.lower():
                pkg_name = a.get("name", "")
                break

    add_log(f"=== INICIANDO DESINSTALACIÓN DE: {pkg_name or pkg_id} ({pkg_id}) ===", "info")
    add_log("Aviso: Si el desinstalador o Windows (UAC) abre una ventana, confirma la desinstalación para proceder.", "info")

    success = False

    # ── INTENTO 1: winget uninstall --id (método estándar) ──
    add_log(f"[Intento 1/4] Desinstalando por ID con winget...", "info")
    with state_lock:
        app_state["progress_percent"] = 20
    cmd1 = ["winget", "uninstall", "--id", pkg_id, "--accept-source-agreements"]
    ret1, not_found1, _ = _run_uninstall_cmd(cmd1, pkg_id)

    if ret1 == 0:
        add_log(f"✅ Desinstalación exitosa por ID (método estándar).", "success")
        success = True

    # ── INTENTO 2: winget uninstall --name (fallback por nombre) ──
    uninstaller_broken = False  # Si el desinstalador del fabricante está roto/colgado
    if not success and (not_found1 or ret1 != 0) and pkg_name:
        add_log(f"[Intento 2/4] El ID no fue reconocido. Reintentando por nombre: \"{pkg_name}\"...", "info")
        with state_lock:
            app_state["progress_percent"] = 40
        cmd2 = ["winget", "uninstall", "--name", pkg_name, "--accept-source-agreements"]
        ret2, not_found2, _ = _run_uninstall_cmd(cmd2, pkg_id)

        if ret2 == 0:
            add_log(f"✅ Desinstalación exitosa por nombre.", "success")
            success = True
        elif ret2 == 50 or ret2 == -1:
            # Código 50 = desinstalador roto/no soporta silent. -1 = watchdog lo mató por colgarse.
            # No tiene sentido reintentar con --interactive: es el MISMO desinstalador y se colgará igual.
            uninstaller_broken = True
            add_log(f"⚠️ El desinstalador del fabricante no responde o no es compatible (código {ret2}). Saltando al método directo del Registro...", "warning")
        elif not_found2:
            add_log(f"Winget no pudo localizar el paquete por nombre tampoco.", "warning")

    # ── INTENTO 3: winget sin modo silencioso (interactivo) ──
    # SOLO se ejecuta si el desinstalador NO fue marcado como roto (evita repetir cuelgue)
    if not success and not uninstaller_broken:
        add_log(f"[Intento 3/4] Ejecutando desinstalador en modo interactivo (sin --silent)...", "info")
        add_log("📢 Si aparece una ventana del desinstalador o de permisos (UAC), acéptala para continuar.", "warning")
        with state_lock:
            app_state["progress_percent"] = 60

        # Intentar primero por nombre (más fiable según diagnóstico), luego por ID
        if pkg_name:
            cmd3 = ["winget", "uninstall", "--name", pkg_name, "--accept-source-agreements", "--interactive"]
        else:
            cmd3 = ["winget", "uninstall", "--id", pkg_id, "--accept-source-agreements", "--interactive"]
        ret3, _, _ = _run_uninstall_cmd(cmd3, pkg_id, timeout=90)

        if ret3 == 0:
            add_log(f"✅ Desinstalación exitosa en modo interactivo.", "success")
            success = True
    elif not success and uninstaller_broken:
        add_log(f"[Intento 3/4] Omitido — el desinstalador del fabricante está defectuoso. Pasando al Registro...", "info")

    # ── INTENTO 4: Ejecutar UninstallString directamente del Registro ──
    if not success:
        add_log(f"[Intento 4/4] Último recurso: buscando desinstalador en el Registro de Windows...", "info")
        with state_lock:
            app_state["progress_percent"] = 80

        uninstall_str = _find_registry_uninstall_string(pkg_id, pkg_name)
        if uninstall_str and not uninstaller_broken:
            add_log(f"Encontrado en el Registro: {uninstall_str}", "info")
            add_log("📢 Ejecutando desinstalador nativo. Si aparece una ventana, acéptala.", "warning")
            try:
                last_activity = [time.time()]
                STALL_TIMEOUT = 45
                process = subprocess.Popen(
                    uninstall_str,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1
                )

                def watchdog_reg():
                    while process.poll() is None:
                        if time.time() - last_activity[0] > STALL_TIMEOUT:
                            add_log(f"⏱️ Desinstalador nativo sin respuesta por {STALL_TIMEOUT}s. Terminando...", "warning")
                            try:
                                subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True, timeout=5)
                            except Exception:
                                process.kill()
                            return
                        time.sleep(3)

                threading.Thread(target=watchdog_reg, daemon=True).start()

                for raw_line in iter(process.stdout.readline, ''):
                    line = raw_line.strip()
                    if line:
                        last_activity[0] = time.time()
                        add_log(f"[Registro] {line}", "process")
                process.stdout.close()
                ret4 = process.wait(timeout=90)

                if ret4 == 0:
                    add_log(f"✅ Desinstalación exitosa mediante desinstalador nativo del Registro.", "success")
                    success = True
                else:
                    add_log(f"El desinstalador nativo finalizó con código {ret4}.", "warning")
            except subprocess.TimeoutExpired:
                try:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True, timeout=5)
                except Exception:
                    process.kill()
                add_log(f"Tiempo de espera agotado (90s) con el desinstalador nativo.", "warning")
            except Exception as e:
                add_log(f"Error ejecutando desinstalador nativo: {str(e)}", "error")
        elif uninstall_str and uninstaller_broken:
            add_log(f"El desinstalador registrado es el mismo que ya falló: {uninstall_str}", "warning")
            add_log(f"❌ Este programa tiene un desinstalador defectuoso que no funciona en modo automático.", "error")
        else:
            add_log(f"No se encontró entrada de desinstalación en el Registro de Windows para este programa.", "warning")

    # ── RESULTADO FINAL ──
    if success:
        add_log(f"🎉 {pkg_name or pkg_id} se ha desinstalado oficialmente con éxito.", "success")
        with state_lock:
            app_state["outdated_apps"] = [
                a for a in app_state["outdated_apps"]
                if a.get("id", "").lower() != pkg_id.lower()
            ]
            app_state["installed_apps"] = [
                a for a in app_state["installed_apps"]
                if a.get("id", "").lower() != pkg_id.lower()
            ]
            if pkg_id not in app_state["uninstalled_ids"]:
                app_state["uninstalled_ids"].append(pkg_id)
    else:
        add_log(f"❌ No se pudo completar la desinstalación de {pkg_name or pkg_id} tras agotar todos los métodos disponibles.", "error")
        add_log("💡 Sugerencia: Intenta desinstalar manualmente desde Configuración de Windows > Aplicaciones > Aplicaciones instaladas.", "info")

    with state_lock:
        app_state["is_updating"] = False
        app_state["progress_percent"] = 100
        app_state["current_action"] = "Desinstalación concluida."
    scan_updates_thread()
    scan_all_installed_thread()


class AppRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def log_message(self, format, *args):
        return

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def send_json_response(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
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
                    "failed_ids": list(app_state["failed_ids"]),
                    "uninstalled_ids": list(app_state["uninstalled_ids"]),
                    "app_version": APP_VERSION
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

        elif path == "/api/uninstall":
            pkg_id = payload.get("id", "").strip()
            if not pkg_id:
                self.send_json_response({"status": "error", "message": "Identificador no válido"}, 400)
                return
            if not app_state["is_updating"]:
                threading.Thread(target=uninstall_thread, args=(pkg_id,), daemon=True).start()
                self.send_json_response({"status": "started", "message": f"Desinstalando {pkg_id}"})
            else:
                self.send_json_response({"status": "busy", "message": "Ya hay una operación en curso"}, 409)
            return

        self.send_response(404)
        self.end_headers()


class ReusableHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def free_port(port: int):
    try:
        cmd = f'powershell -NoProfile -Command "$conns = Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue; if ($conns) {{ foreach ($c in $conns) {{ Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue }} }}"'
        subprocess.run(cmd, shell=True, timeout=4)
        time.sleep(0.3)
    except Exception:
        pass


def is_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, port)) != 0


def open_desktop_window(url: str):
    time.sleep(1.0)
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for edge in edge_paths:
        if os.path.isfile(edge):
            try:
                subprocess.Popen([edge, f"--app={url}", "--window-size=1320,860"])
                return
            except Exception:
                pass
    webbrowser.open(url)


def check_already_running() -> bool:
    try:
        req = urllib.request.Request(f"http://{HOST}:{PORT}/api/status", headers={"User-Agent": "SingleInstance"})
        with urllib.request.urlopen(req, timeout=0.8) as resp:
            if resp.status == 200:
                return True
    except Exception:
        pass
    return False


def main():
    global PORT

    # 1. Si la aplicación ya está activa en segundo plano
    if check_already_running():
        app_url = f"http://{HOST}:{PORT}"
        print(f"El Actualizador de Programas ya se encuentra en ejecución en {app_url}.")
        if "--no-browser" not in sys.argv:
            focused = False
            try:
                cmd = 'powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $ws.AppActivate(\'Actualizador de Programas\')"'
                res = subprocess.check_output(cmd, shell=True, text=True).strip()
                if "True" in res:
                    focused = True
            except Exception:
                pass
            if not focused:
                open_desktop_window(app_url)
        sys.exit(0)

    # 2. Si no estaba corriendo, limpiar posibles procesos muertos e iniciar
    free_port(PORT)
    while not is_port_available(PORT) and PORT < 5060:
        PORT += 1

    server_address = (HOST, PORT)
    httpd = ReusableHTTPServer(server_address, AppRequestHandler)
    app_url = f"http://{HOST}:{PORT}"

    print(f"============================================================")
    print(f"  Actualizador de Programas de Windows (v{APP_VERSION})")
    print(f"  Servidor iniciado en: {app_url}")
    print(f"============================================================")

    # Iniciar escaneo inicial en segundo plano
    threading.Thread(target=scan_updates_thread, daemon=True).start()
    threading.Thread(target=scan_all_installed_thread, daemon=True).start()

    if "--no-browser" not in sys.argv:
        threading.Thread(target=open_desktop_window, args=(app_url,), daemon=True).start()

    try:
        httpd.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        print(f"Excepción en servidor: {e}")
    finally:
        try:
            httpd.server_close()
        except Exception:
            pass


if __name__ == "__main__":
    main()

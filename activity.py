"""Conservative activity hints from process names; never stops processes."""
import json
import os
import subprocess
import threading
import time

# Explicit associations only. Components without a reliable executable stay unknown.
EXECUTABLES = {
    'videolan.vlc': ('vlc.exe',),
    'nextcloud.nextclouddesktop': ('nextcloud.exe',),
    'tailscale.tailscale': ('tailscale.exe', 'tailscaled.exe', 'tailscale-ipn.exe'),
    'notepad++.notepad++': ('notepad++.exe',),
    'google.antigravity': ('antigravity.exe',),
    'anydesk.anydesk': ('anydesk.exe',),
    'bitwarden.bitwarden': ('bitwarden.exe',),
    'calibre.calibre': ('calibre.exe', 'ebook-viewer.exe', 'ebook-edit.exe'),
    'anthropic.claude': ('claude.exe',),
    'docker.dockerdesktop': ('docker desktop.exe', 'com.docker.backend.exe'),
    'epicgames.epicgameslauncher': ('epicgameslauncher.exe', 'epicwebhelper.exe'),
    'gyan.ffmpeg': ('ffmpeg.exe', 'ffplay.exe', 'ffprobe.exe'),
    'github.cli': ('gh.exe',),
    'greenshot.greenshot': ('greenshot.exe',),
    'kde.kdenlive': ('kdenlive.exe', 'melt.exe'),
    'thedocumentfoundation.libreoffice': ('soffice.exe', 'soffice.bin'),
    'microsoft.teams': ('ms-teams.exe', 'teams.exe'),
    'microsoft.visualstudiocode': ('code.exe',),
    'nvidia.geforcenow': ('geforcenow.exe', 'geforcenowcontainer.exe'),
    'obsidian.obsidian': ('obsidian.exe',),
    'ollama.ollama': ('ollama.exe', 'ollama app.exe', 'ollama_llama_server.exe'),
    'openshot.openshot': ('openshot-qt.exe',),
    'oracle.virtualbox': ('virtualbox.exe', 'virtualboxvm.exe', 'vboxheadless.exe', 'vboxsvc.exe'),
    'microsoft.outlook': ('olk.exe', 'outlook.exe'),
    'johnmacfarlane.pandoc': ('pandoc.exe',),
    'pdfgear.pdfgear': ('pdfgear.exe', 'pdfgeareditor.exe'),
    'proton.protonvpn': ('protonvpn.exe', 'protonvpnservice.exe'),
    'emoteinteractive.remotemouse': ('remotemouse.exe',),
    'burntsushi.ripgrep.msvc': ('rg.exe',),
    'codesector.teracopy': ('teracopy.exe',),
    'microsoft.windowsterminal': ('windowsterminal.exe',),
    'veyonsolutions.veyon': ('veyon-master.exe', 'veyon-service.exe', 'veyon-server.exe'),
    'microsoft.wingetcreate': ('wingetcreate.exe',),
    'mozilla.firefox': ('firefox.exe',),
    'google.chrome': ('chrome.exe',),
    'microsoft.edge': ('msedge.exe',),
}
_lock = threading.Lock()
_cached_at = 0
_cached_processes = None
_cached_checked_at = ''


def classify_activity(package_id, processes):
    names = EXECUTABLES.get(package_id.casefold())
    if not names or processes is None:
        return {'status': 'unknown', 'label': 'Sin comprobar', 'processes': []}
    matches = []
    for process in processes:
        name = str(process.get('ProcessName', '')).casefold()
        if not name.endswith(('.exe', '.bin')):
            name += '.exe'
        if name in names:
            matches.append({'name': name, 'pid': process.get('Id')})
    return {'status': 'running' if matches else 'not_detected',
            'label': 'En ejecución' if matches else 'Sin actividad detectada',
            'processes': matches}


def snapshot_processes(force=False):
    global _cached_at, _cached_processes, _cached_checked_at
    with _lock:
        if not force and time.monotonic() - _cached_at < 5:
            return _cached_processes
        try:
            if os.name != 'nt':
                return None
            powershell = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
            result = subprocess.run([powershell, '-NoProfile', '-NonInteractive', '-Command',
                                     "$ErrorActionPreference='Stop'; Get-Process | Select-Object ProcessName,Id | ConvertTo-Json -Compress"],
                                    capture_output=True, text=True, encoding='utf-8', errors='replace',
                                    timeout=8, creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode:
                raise ValueError('No se pudo consultar la actividad')
            data = json.loads(result.stdout.lstrip('\ufeff'))
            _cached_processes = [data] if isinstance(data, dict) else data
            if not isinstance(_cached_processes, list):
                raise ValueError('Respuesta no válida')
        except (OSError, ValueError, subprocess.TimeoutExpired):
            _cached_processes = None
        _cached_at = time.monotonic()
        _cached_checked_at = time.strftime('%H:%M:%S')
        return _cached_processes


def annotate_activity(items, force=False):
    processes = snapshot_processes(force=force)
    checked_at = _cached_checked_at
    return [{**item, 'activity': {**classify_activity(item['id'], processes), 'checked_at': checked_at}}
            for item in items]


def open_task_manager():
    executable = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32', 'Taskmgr.exe')
    subprocess.Popen([executable])

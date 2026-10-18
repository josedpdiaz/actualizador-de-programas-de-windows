"""Process supervision and exclusive operations; no third-party dependencies."""
from dataclasses import dataclass
import os
import queue
import subprocess
import threading
import time


@dataclass(frozen=True)
class CommandResult:
    code: int
    timed_out: bool = False


class OperationGate:
    def __init__(self):
        self._lock = threading.Lock()

    def acquire(self):
        return self._lock.acquire(blocking=False)

    def release(self):
        self._lock.release()


def validate_ids(values, allowed):
    if not isinstance(values, list) or not values or len(values) > 1000:
        raise ValueError('Selecciona al menos un programa de la lista actual.')
    allowed = set(allowed)
    result = []
    for value in values:
        if not isinstance(value, str) or value not in allowed or value.startswith('-'):
            raise ValueError('La selección contiene un programa que no está en la lista actual.')
        if value not in result:
            result.append(value)
    return result


def upgrade_command(package_id):
    return ['winget', 'upgrade', '--id', package_id, '--exact', '--silent',
            '--disable-interactivity', '--accept-package-agreements', '--accept-source-agreements']


def result_kind(code):
    unsigned = code & 0xFFFFFFFF
    if code == 0:
        return 'success'
    if unsigned == 0x8A15002B:
        return 'no_update'
    if unsigned in (3010, 1641, 0x8A150109, 0x8A15010B):
        return 'restart'
    if unsigned == 0x8A15010A:
        return 'restart_before'
    return 'failed'


def run_command(command, on_line, timeout=1800, on_tick=None):
    """Read output off-thread so an installer with no output cannot hide a timeout.

    On timeout only the WinGet client is stopped, never arbitrary installer trees.
    Callers must stop the queue: a separately launched installer might remain active.
    """
    options = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding='utf-8', errors='replace', **options)
    output = queue.Queue()
    def read_output():
        try:
            for line in process.stdout:
                output.put(line.rstrip())
        finally:
            process.stdout.close()
            output.put(None)
    threading.Thread(target=read_output, daemon=True).start()
    started = time.monotonic()
    next_tick = 0
    output_done = False
    try:
        while True:
            elapsed = time.monotonic() - started
            if elapsed >= timeout:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill()
                return CommandResult(process.poll() if process.poll() is not None else -1, True)
            if on_tick and elapsed >= next_tick:
                on_tick(int(elapsed))
                next_tick = elapsed + 1
            if output_done:
                code = process.poll()
                if code is not None:
                    return CommandResult(code)
                time.sleep(.1)
                continue
            try:
                line = output.get(timeout=min(.1, max(.01, timeout - elapsed)))
            except queue.Empty:
                continue
            if line is None:
                output_done = True
                continue
            if line:
                on_line(line)
    except BaseException:
        if process.poll() is None:
            process.terminate()
        raise

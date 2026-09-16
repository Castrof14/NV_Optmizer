"""Executor de jobs em threads com captura de stdout e progresso.

Segurança: a thread de trabalho NUNCA toca no Tk. Ela apenas acumula
eventos numa fila; a thread principal os entrega via drain_all() (pump).
"""

import io
import re
import sys
import threading
import time
from collections import deque

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
PROGRESS_RE = re.compile(r"(\d{1,3})\s*%")
STEP_RE = re.compile(r"\[?\s*[-[]?\s*(\d+)\s*/\s*(\d+)\s*\]?")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def parse_progress(line: str):
    """Extrai percentual de uma linha (percentual, [i/n] ou Fase i/n)."""
    m = PROGRESS_RE.search(line)
    if m:
        v = int(m.group(1))
        if v <= 100:
            return v / 100.0
    m = STEP_RE.search(line)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if b > 0:
            return a / b
    if "Fase" in line.lower():
        vals = re.findall(r"(\d+)", line)
        if len(vals) >= 2 and int(vals[1]) > 0:
            return int(vals[0]) / int(vals[1])
    return None


_active = []
_lock = threading.Lock()


class Job:
    """Roda uma função do backend em thread, entregando eventos via fila."""

    def __init__(self, label="Operação", fn=None, on_start=None, on_progress=None,
                 on_log=None, on_done=None, on_error=None):
        self.label = label
        self.fn = fn
        self.on_start = on_start
        self.on_progress = on_progress
        self.on_log = on_log
        self.on_done = on_done
        self.on_error = on_error
        self.started = time.time()
        self.duration = 0.0
        self._queue = deque()
        self._finished = False

    def start(self):
        if self.on_start:
            self._queue.append((self.on_start, ()))
        t = threading.Thread(target=self._run, daemon=True)
        with _lock:
            _active.append(self)
        t.start()

    def _run(self):
        buf = io.StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout = buf
        sys.stderr = buf
        result, error = None, None
        try:
            result = self.fn()
        except Exception as e:  # noqa: BLE001
            error = e
        finally:
            sys.stdout, sys.stderr = old_out, old_err
            self.duration = time.time() - self.started

        lines = buf.getvalue()
        lines = strip_ansi(lines).replace("\r", "\n")
        for line in lines.split("\n"):
            line = line.strip()
            if not line:
                continue
            if self.on_progress:
                p = parse_progress(line)
                if p is not None:
                    self._queue.append((lambda cb, v: cb(v), (self.on_progress, p)))
            if self.on_log:
                self._queue.append((lambda cb, ln: cb(ln), (self.on_log, line)))

        if error is not None:
            if self.on_error:
                self._queue.append((lambda cb, e: cb(e), (self.on_error, error)))
        else:
            if self.on_done:
                self._queue.append((lambda cb, r: cb(r), (self.on_done, result)))
        self._finished = True

    def drain(self):
        """Entrega os eventos acumulados (executar apenas na thread principal)."""
        while self._queue:
            fn, args = self._queue.popleft()
            try:
                fn(*args)
            except Exception:
                pass


def drain_all():
    """Processa a fila de todos os jobs ativos (thread principal)."""
    finished = []
    for job in _active:
        job.drain()
        if job._finished:
            finished.append(job)
    for job in finished:
        try:
            _active.remove(job)
        except ValueError:
            pass
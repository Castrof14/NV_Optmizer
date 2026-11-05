"""Executor de jobs em threads com captura de stdout e progresso.

Segurança: a thread de trabalho NUNCA toca no Tk. Ela apenas acumula
eventos numa fila; a thread principal os entrega via drain_all() (pump).
"""

import re
import sys
import threading
import time
import traceback
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


class _LineWriter:
    """Entrega cada linha assim que é escrita, para o log acompanhar operações longas."""

    def __init__(self, on_line):
        self._on_line = on_line
        self._pending = ""

    def write(self, text):
        self._pending += text.replace("\r", "\n")
        *lines, self._pending = self._pending.split("\n")
        for line in lines:
            self._on_line(line)
        return len(text)

    def finish(self):
        if self._pending:
            self._on_line(self._pending)
            self._pending = ""


class _ThreadOutput:
    """Direciona prints de cada Job para o próprio Job; os demais seguem para a saída real."""

    def __init__(self, real):
        self._real = real

    def write(self, text):
        writer = getattr(_thread_state, "writer", None)
        if writer is not None:
            return writer.write(text)
        if self._real is not None:
            return self._real.write(text)
        return len(text)

    def flush(self):
        if getattr(_thread_state, "writer", None) is None and self._real is not None:
            self._real.flush()

    def isatty(self):
        return False


_thread_state = threading.local()
_active = []
_lock = threading.Lock()


def _install_thread_output():
    if not isinstance(sys.stdout, _ThreadOutput):
        sys.stdout = _ThreadOutput(sys.stdout)
    if not isinstance(sys.stderr, _ThreadOutput):
        sys.stderr = _ThreadOutput(sys.stderr)


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
        _install_thread_output()
        t = threading.Thread(target=self._run, daemon=True)
        with _lock:
            _active.append(self)
        t.start()

    def _emit_line(self, raw):
        line = strip_ansi(raw).strip()
        if not line:
            return
        if self.on_progress:
            p = parse_progress(line)
            if p is not None:
                self._queue.append((self.on_progress, (p,)))
        if self.on_log:
            self._queue.append((self.on_log, (line,)))

    def _run(self):
        writer = _LineWriter(self._emit_line)
        _thread_state.writer = writer
        result, error = None, None
        try:
            result = self.fn()
        except Exception as e:  # noqa: BLE001
            error = e
        finally:
            writer.finish()
            _thread_state.writer = None
            self.duration = time.time() - self.started

        if error is not None:
            if self.on_error:
                self._queue.append((self.on_error, (error,)))
        else:
            if self.on_done:
                self._queue.append((self.on_done, (result,)))
        self._finished = True

    def drain(self):
        """Entrega os eventos acumulados (executar apenas na thread principal)."""
        while self._queue:
            fn, args = self._queue.popleft()
            try:
                fn(*args)
            except Exception:
                # Um erro na interface não pode derrubar a fila, mas também não pode sumir.
                traceback.print_exc()


def drain_all():
    """Processa a fila de todos os jobs ativos (thread principal)."""
    finished = []
    for job in _active:
        # Lê o estado antes de esvaziar a fila para não perder o último evento do Job.
        was_finished = job._finished
        job.drain()
        if was_finished:
            finished.append(job)
    for job in finished:
        try:
            _active.remove(job)
        except ValueError:
            pass

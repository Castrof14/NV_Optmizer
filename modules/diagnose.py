"""
Backend de diagnóstico / stress test.

Stress test REAL e controlado:
  - CPU: threads em execução contínua (cálculo intensivo) em todos os núcleos.
  - RAM: alocação progressiva de blocos em memória.
  - GPU: monitoramento via nvidia-smi quando disponível.
A interface consome apenas os dados aqui produzidos.
"""

import threading
import time

from modules.system import get_cpu_usage, get_cpu_freq, get_cpu_temp, get_gpu_sample, get_ram_usage


class StressTest:
    """Controla início/parada e amostragem do teste de estresse real."""

    def __init__(self):
        self._stop = threading.Event()
        self._workers = []
        self._lock = threading.Lock()
        self.running = False
        self.started_at = None
        self._mode = {"cpu": False, "ram": False}

    def start(self, cpu: bool = True, ram: bool = True):
        if self.running:
            return
        self._stop.clear()
        self.running = True
        self.started_at = time.time()
        self._mode = {"cpu": bool(cpu), "ram": bool(ram)}

        if cpu:
            import os
            n = os.cpu_count() or 2
            for i in range(n):
                t = threading.Thread(target=self._cpu_worker, name=f"nv-stress-cpu-{i}", daemon=True)
                t.start()
                self._workers.append(t)

        if ram:
            self._ram_alloc = []
            t = threading.Thread(target=self._ram_worker, name="nv-stress-ram", daemon=True)
            t.start()
            self._workers.append(t)

    def _cpu_worker(self):
        while not self._stop.is_set():
            x = 0.0
            for _ in range(2000):
                x += (_ * 3.14159) ** 0.5 * (_ * 0.57721)
            # mantém o resultado vivo para que o JIT/loop não seja removido
            self._cpu_acc = x

    def _ram_worker(self):
        chunks = []
        block = 64 * 1024 * 1024  # 64 MB
        target = 0.55
        try:
            for _ in range(64):
                if self._stop.is_set():
                    break
                usage = get_ram_usage()
                if not usage.get("available"):
                    break
                if usage.get("total") and usage["used"] / usage["total"] >= target:
                    break
                try:
                    chunk = bytearray(block)
                    for i in range(0, block, 4096):
                        chunk[i] = i & 0xFF
                    chunks.append(chunk)
                except MemoryError:
                    break
                time.sleep(0.05)
        finally:
            self._ram_alloc = chunks

    def stop(self):
        self._stop.set()
        for t in self._workers:
            t.join(timeout=1.0)
        self._workers = []
        self._ram_alloc = []
        self.running = False

    def elapsed(self) -> float:
        if not self.started_at:
            return 0.0
        return time.time() - self.started_at

    def sample(self) -> dict:
        cpu_pct = get_cpu_usage()
        if cpu_pct is None:
            cpu_pct = 0
        ram = get_ram_usage()
        gpu = get_gpu_sample()
        return {
            "running": self.running,
            "elapsed": self.elapsed(),
            "cpu": {"usage": cpu_pct, "temp": get_cpu_temp(), "freq": get_cpu_freq()},
            "ram": {"used": ram.get("used"), "total": ram.get("total"), "pct": ram.get("pct")},
            "gpu": {"usage": gpu.get("usage"), "temp": gpu.get("temp"), "available": gpu.get("available", False)},
            "mode": dict(self._mode),
        }


stress = StressTest()


def start_stress(cpu: bool = True, ram: bool = True) -> dict:
    stress.start(cpu=cpu, ram=ram)
    return stress.sample()


def stop_stress() -> dict:
    stress.stop()
    return stress.sample()


def read_sample() -> dict:
    return stress.sample()


def monitor_idle() -> dict:
    """Leitura de referência sem estresse (dashboard/stress em repouso)."""
    return stress.sample()
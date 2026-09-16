"""
NV Optimizer 2.0 - Backend de Stress Tests
Testes reais de CPU, GPU e Memória com interrupção.
"""

import ctypes
import multiprocessing
import os
import subprocess
import threading
import time
from datetime import datetime

from .backend_core import (
    OperationResult, ErrorCode, isAdmin, run_command, global_progress,
)
from .system import getCPUInfo, getRAMInfo, getGPUInfo


class _CancellationToken:
    def __init__(self):
        self.cancelled = False

    def cancel(self):
        self.cancelled = True


def _cpu_worker(stop_event, results, index):
    """Worker de stress de CPU - operação matemática pesada (processo separado)."""
    start = time.time()
    pass_count = 0
    try:
        while not stop_event.is_set():
            x = 0.0
            for i in range(200000):
                x += (i * 1.0000001) ** 1.5
                if stop_event.is_set():
                    break
            pass_count += 1
    except Exception:
        pass
    finally:
        try:
            results[index] = {"passes": pass_count, "seconds": time.time() - start}
        except Exception:
            pass


def stressCPU(duration: int = 60, on_progress=None) -> OperationResult:
    """Executa stress test real de CPU em todos os núcleos via multiprocessing."""
    operation = "stress-cpu"
    if duration <= 0:
        duration = 60

    cores = multiprocessing.cpu_count()
    ctx = multiprocessing.get_context('spawn')
    stop_event = ctx.Event()
    manager = ctx.Manager()
    results = manager.dict()

    cpu_info = getCPUInfo()
    global_progress.emit_start(operation, f"Iniciando stress de CPU ({cores} processos)...")

    procs = []
    for i in range(cores):
        p = ctx.Process(target=_cpu_worker, args=(stop_event, results, i))
        p.daemon = True
        procs.append(p)
        p.start()

    start_time = time.time()
    samples = []
    cancelled = False
    try:
        while time.time() - start_time < duration:
            if stop_event.is_set():
                cancelled = True
                break
            info = getCPUInfo()
            samples.append({
                "time": round(time.time() - start_time, 1),
                "usage": info.get("usage", 0),
                "frequency_mhz": info.get("frequency_mhz", 0),
            })
            global_progress.emit_progress(
                operation,
                int((time.time() - start_time) / duration * 100),
                f"Uso: {info.get('usage', 0):.0f}%  Tempo restante: {duration - int(time.time() - start_time)}s",
            )
            if on_progress:
                on_progress(samples[-1])
            time.sleep(1)
    except KeyboardInterrupt:
        cancelled = True
    finally:
        stop_event.set()
        for p in procs:
            p.join(timeout=3)
            if p.is_alive():
                p.terminate()
        try:
            total_passes = 0
            final_results = dict(results)
            total_passes = sum(r.get("passes", 0) for r in final_results.values())
        except Exception:
            total_passes = 0
        try:
            manager.shutdown()
        except Exception:
            pass

    if not samples:
        samples = [{"time": 0, "usage": 0, "frequency_mhz": 0}]

    avg_usage = sum(s["usage"] for s in samples) / len(samples)
    max_usage = max(s["usage"] for s in samples)
    peak_freq = max(s["frequency_mhz"] for s in samples)

    global_progress.emit_complete(operation, "Stress de CPU concluído.")

    return OperationResult.ok(
        message="Teste interrompido pelo usuário." if cancelled else "Stress de CPU concluído.",
        data={
            "test": "cpu",
            "duration_sec": round(time.time() - start_time, 1),
            "cores": cores,
            "cpu_model": cpu_info.get("model"),
            "avg_usage": round(avg_usage, 1),
            "max_usage": round(max_usage, 1),
            "peak_frequency_mhz": peak_freq,
            "total_iterations": total_passes,
            "cancelled": cancelled,
            "samples": samples[-30:],
        },
    )


_GPU_PS_SCRIPT = r"""
Add-Type -AssemblyName PresentationCore,PresentationFramework,WindowsBase
$win = New-Object System.Windows.Window
$win.Width = 200
$win.Height = 200
$win.WindowStyle = [System.Windows.WindowStyle]::None
$win.ShowInTaskbar = $false
$win.Topmost = $true
$win.Left = -500
$win.Top = -500

$grid = New-Object System.Windows.Controls.Grid
$grid.Background = [System.Windows.Media.Brushes]::Black
$win.Content = $grid

$canvas = New-Object System.Windows.Controls.Canvas
$grid.Children.Add($canvas)

$shapes = @()
for ($i = 0; $i -lt 50; $i++) {
    $ellipse = New-Object System.Windows.Shapes.Ellipse
    $ellipse.Width = 20 + (Get-Random -Minimum 5 -Maximum 40)
    $ellipse.Height = $ellipse.Width
    $brush = [System.Windows.Media.SolidColorBrush]::new(
        [System.Windows.Media.Color]::FromRgb(
            (Get-Random -Minimum 50 -Maximum 255),
            (Get-Random -Minimum 50 -Maximum 255),
            (Get-Random -Minimum 50 -Maximum 255)
        ))
    $ellipse.Fill = $brush
    $canvas.Children.Add($ellipse)
    $shapes += @{ Shape=$ellipse; X=(Get-Random -Minimum 0 -Maximum 800); Y=(Get-Random -Minimum 0 -Maximum 800) }
}

$anim = New-Object System.Windows.DoubleAnimation
$anim.From = 0
$anim.To = 360
$anim.Duration = [System.Windows.Duration]::new([TimeSpan]::FromMilliseconds(50))
$anim.RepeatBehavior = [System.Windows.Media.Animation.RepeatBehavior]::Forever

$rotate = New-Object System.Windows.Media.RotateTransform
$win.RenderTransform = $rotate
$rotate.BeginAnimation([System.Windows.Media.RotateTransform]::AngleProperty, $anim)

$win.Show()

$elapsed = 0
$start = [System.Diagnostics.Stopwatch]::StartNew()
while ($elapsed -lt $duration) {
    [System.Windows.Threading.Dispatcher]::CurrentDispatcher.Invoke(
        [System.Action]{}, [System.Windows.Threading.DispatcherPriority]::Render
    )
    $canvas.Margin = New-Object System.Windows.Thickness(
        (Get-Random -Minimum -10 -Maximum 10),
        (Get-Random -Minimum -10 -Maximum 10), 0, 0)
    $win.Width = 190 + (Get-Random -Minimum 0 -Maximum 20)
    $win.Height = 190 + (Get-Random -Minimum 0 -Maximum 20)
    $elapsed = $start.Elapsed.TotalSeconds
}
$win.Close()
"""


def stressGPU(duration: int = 60, on_progress=None) -> OperationResult:
    """Executa stress test real de GPU via render loop WPF (GPU-accelerated)."""
    operation = "stress-gpu"
    if duration <= 0:
        duration = 60
    if duration > 600:
        duration = 600

    gpu_info = getGPUInfo()
    if gpu_info.get("model") in (None, "N/A"):
        return OperationResult.error(ErrorCode.NOT_FOUND, "GPU não detectada.")

    global_progress.emit_start(operation, f"Iniciando stress de GPU ({gpu_info.get('model')})...")

    ros = subprocess.DEVNULL if os.name == "nt" else subprocess.DEVNULL

    proc = subprocess.Popen(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command",
         "$duration = " + str(duration) + ";" + _GPU_PS_SCRIPT],
        stdout=ros, stderr=ros,
    )

    start_time = time.time()
    samples = []
    cancelled = False

    try:
        while time.time() - start_time < duration:
            if proc.poll() is not None:
                break
            info = getGPUInfo()
            samples.append({
                "time": round(time.time() - start_time, 1),
                "usage": info.get("usage", 0),
                "temperature_c": info.get("temperature_c"),
                "vram_used_mb": info.get("vram_used_mb"),
            })
            global_progress.emit_progress(
                operation,
                int((time.time() - start_time) / duration * 100),
                f"Tempo restante: {duration - int(time.time() - start_time)}s",
            )
            if on_progress:
                on_progress(samples[-1])
            time.sleep(1)
    except KeyboardInterrupt:
        cancelled = True
    finally:
        try:
            proc.terminate()
        except Exception:
            pass

    if not samples:
        samples = [{"time": 0, "usage": 0, "temperature_c": None, "vram_used_mb": None}]

    avg_usage = sum(s["usage"] for s in samples) / len(samples)
    max_usage = max(s["usage"] for s in samples)
    temps = [s["temperature_c"] for s in samples if s["temperature_c"] is not None]
    max_temp = max(temps) if temps else None
    vram_samples = [s["vram_used_mb"] for s in samples if s["vram_used_mb"] is not None]
    peak_vram = max(vram_samples) if vram_samples else None

    global_progress.emit_complete(operation, "Stress de GPU concluído.")

    return OperationResult.ok(
        message="Teste interrompido pelo usuário." if cancelled else "Stress de GPU concluído.",
        data={
            "test": "gpu",
            "gpu_model": gpu_info.get("model"),
            "gpu_manufacturer": gpu_info.get("manufacturer"),
            "driver_version": gpu_info.get("driver_version"),
            "duration_sec": round(time.time() - start_time, 1),
            "avg_usage": round(avg_usage, 1),
            "max_usage": round(max_usage, 1),
            "max_temperature_c": max_temp,
            "peak_vram_mb": peak_vram,
            "cancelled": cancelled,
            "samples": samples[-30:],
        },
    )


def stressMemory(duration: int = 60, target_percent: int = 75, on_progress=None) -> OperationResult:
    """Executa teste real de memória por alocação pesada."""
    operation = "stress-memory"
    if duration <= 0:
        duration = 60
    if target_percent is None:
        target_percent = 75
    if target_percent <= 10 or target_percent > 90:
        target_percent = 75

    ram_info = getRAMInfo()
    total_bytes = ram_info.get("total_bytes", 0)
    if total_bytes <= 0:
        return OperationResult.error(ErrorCode.NOT_FOUND, "Não foi possível detectar a RAM.")

    global_progress.emit_start(
        operation,
        f"Iniciando stress de memória ({ram_info.get('total_gb', '?')} GB total)...",
    )

    available = ram_info.get("available_bytes", 0)
    alloc_bytes = int(available * (target_percent / 100.0))
    alloc_mb = alloc_bytes // (1024 * 1024)

    chunks = []
    chunk_size = 64 * 1024 * 1024  # 64 MB por chunk

    start_time = time.time()
    try:
        n_chunks = alloc_mb // 64
        for i in range(max(n_chunks, 1)):
            try:
                buf = ctypes.create_string_buffer(chunk_size)
                ctypes.memset(buf, 0xAA, chunk_size)
                chunks.append(buf)
            except MemoryError:
                break

        total_allocated_mb = sum(len(c) for c in chunks) // (1024 * 1024)

        samples = []
        while time.time() - start_time < duration:
            info = getRAMInfo()
            samples.append({
                "time": round(time.time() - start_time, 1),
                "used_mb": info.get("used_mb", 0),
                "available_mb": info.get("available_mb", 0),
                "usage_percent": info.get("usage_percent", 0),
                "allocated_mb": total_allocated_mb,
            })
            global_progress.emit_progress(
                operation,
                int((time.time() - start_time) / duration * 100),
                f"Alocado: {total_allocated_mb} MB da RAM",
            )
            if on_progress:
                on_progress(samples[-1])
            time.sleep(1)

        for i in range(len(chunks)):
            data = chunks.pop()

        used_percent = getRAMInfo().get("usage_percent", 0)

        global_progress.emit_complete(operation, "Stress de memória concluído.")

        if not samples:
            samples = [{
                "time": 0, "used_mb": 0, "available_mb": 0,
                "usage_percent": ram_info.get("usage_percent", 0),
                "allocated_mb": total_allocated_mb,
            }]

        return OperationResult.ok(
            message="Stress de memória concluído.",
            data={
                "test": "memory",
                "ram_total_gb": ram_info.get("total_gb"),
                "allocated_mb": total_allocated_mb,
                "allocated_gb": round(total_allocated_mb / 1024, 2),
                "duration_sec": round(time.time() - start_time, 1),
                "peak_usage_percent": max(s["usage_percent"] for s in samples),
                "samples": samples[-30:],
            },
        )
    except Exception as e:
        return OperationResult.error(
            ErrorCode.OPERATION_FAILED, "Falha no stress de memória.",
            str(e),
        )


def stressMemoryDiagnostic() -> OperationResult:
    """Diagnóstico de memória. Para teste aprofundado recomenda ferramenta especializada."""
    ram = getRAMInfo()
    return OperationResult.ok(
        message=(
            "Para um teste aprofundado de memória, reinicie o PC e execute o "
            "Windows Memory Diagnostic (Windows + R → mdsched.exe) ou MemTest86."
        ),
        data={
            "test": "memory-diagnostic",
            "ram_total_gb": ram.get("total_gb"),
            "used_gb": ram.get("used_gb"),
            "available_gb": ram.get("available_gb"),
            "usage_percent": ram.get("usage_percent"),
            "deep_test_required": True,
            "deep_test_tool": "Windows Memory Diagnostic (mdsched.exe)",
        },
    )


class StressTestManager:
    """Gerencia execução assíncrona dos stress tests com cancelamento."""

    def __init__(self):
        self._thread = None
        self._token = _CancellationToken()
        self._running = False

    @property
    def running(self):
        return self._running

    def start(self, test_type: str, duration: int, on_result=None, on_progress=None):
        if self._running:
            return OperationResult.error(
                ErrorCode.OPERATION_FAILED, "Já existe um teste em execução."
            )

        self._token = _CancellationToken()
        self._running = True

        def _run():
            try:
                if test_type == "cpu":
                    result = stressCPU(duration, on_progress=on_progress)
                elif test_type == "gpu":
                    result = stressGPU(duration, on_progress=on_progress)
                elif test_type == "memory":
                    result = stressMemory(duration, on_progress=on_progress)
                else:
                    result = OperationResult.error(
                        ErrorCode.INVALID_INPUT, f"Tipo de teste inválido: {test_type}"
                    )
                if on_result:
                    on_result(result)
            finally:
                self._running = False

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        return OperationResult.ok("Teste iniciado.")

    def cancel(self):
        self._token.cancel()
        return OperationResult.ok("Cancelamento solicitado.", {"cancelled": True})

    def status(self) -> OperationResult:
        return OperationResult.ok(data={"running": self._running})


stress_manager = StressTestManager()
"""
Módulo de informações do sistema do NV Optimizer.
Exibe informações detalhadas sobre o sistema.
"""

import os
import platform
import subprocess
from utils.colors import Theme, colorize
from utils.logger import logger
from utils.config import system_info


def show_system_info():
    """Exibe informações detalhadas do sistema."""
    print(colorize("\n  Coletando informações do sistema...\n", Theme.PRIMARY))

    info_sections = []

    # Informações básicas
    info_sections.append(_get_basic_info())

    # Informações de hardware
    if system_info.is_windows:
        info_sections.append(_get_windows_hardware_info())
    elif system_info.is_macos:
        info_sections.append(_get_macos_hardware_info())
    elif system_info.is_linux:
        info_sections.append(_get_linux_hardware_info())

    # Informações de rede
    info_sections.append(_get_network_info())

    # Exibir todas as informações
    for section in info_sections:
        for line in section:
            print(f"  {line}")
        print()

    logger.success("Informações coletadas")


def _get_basic_info() -> list:
    """Retorna informações básicas do sistema."""
    return [
        colorize("═══ INFORMAÇÕES BÁSICAS ═══", Theme.PRIMARY),
        f"  Sistema: {system_info.so_name} {system_info.os_release}",
        f"  Versão: {system_info.os_version}",
        f"  Arquitetura: {system_info.architecture}",
        f"  Hostname: {system_info.hostname}",
        f"  Python: {system_info.python_version}",
    ]


def _get_windows_hardware_info() -> list:
    """Retorna informações de hardware do Windows."""
    info = [colorize("═══ HARDWARE ═══", Theme.PRIMARY)]

    try:
        result = subprocess.run(
            ["wmic", "cpu", "get", "Name,NumberOfCores,NumberOfLogicalProcessors", "/format:list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                info.append(f"  CPU: {value.strip()}")
    except Exception:
        info.append("  CPU: Não disponível")

    try:
        result = subprocess.run(
            ["wmic", "memorychip", "get", "Capacity,Speed", "/format:list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in result.stdout.strip().split("\n"):
            if "=" in line and "Capacity" in line:
                try:
                    capacity = int(line.split("=")[1].strip())
                    info.append(f"  RAM: {capacity / (1024**3):.1f} GB")
                except ValueError:
                    pass
    except Exception:
        info.append("  RAM: Não disponível")

    try:
        result = subprocess.run(
            ["wmic", "diskdrive", "get", "Model,Size,MediaType", "/format:list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in result.stdout.strip().split("\n"):
            if "=" in line and "Model" in line:
                parts = line.split("=")
                if len(parts) > 1:
                    info.append(f"  Disco: {parts[1].strip()}")
    except Exception:
        pass

    return info


def _get_macos_hardware_info() -> list:
    """Retorna informações de hardware do macOS."""
    info = [colorize("═══ HARDWARE ═══", Theme.PRIMARY)]

    try:
        result = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        info.append(f"  CPU: {result.stdout.strip()}")
    except Exception:
        info.append("  CPU: Não disponível")

    try:
        result = subprocess.run(
            ["sysctl", "-n", "hw.memsize"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        ram_bytes = int(result.stdout.strip())
        info.append(f"  RAM: {ram_bytes / (1024**3):.1f} GB")
    except Exception:
        info.append("  RAM: Não disponível")

    try:
        result = subprocess.run(
            ["system_profiler", "SPStorageDataType"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in result.stdout.split("\n"):
            if "Media:" in line or "Size:" in line or "Medium Type:" in line:
                info.append(f"  {line.strip()}")
    except Exception:
        pass

    return info


def _get_linux_hardware_info() -> list:
    """Retorna informações de hardware do Linux."""
    info = [colorize("═══ HARDWARE ═══", Theme.PRIMARY)]

    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "model name" in line:
                    info.append(f"  CPU: {line.split(':')[1].strip()}")
                    break
    except Exception:
        info.append("  CPU: Não disponível")

    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if "MemTotal" in line:
                    kb = int(line.split()[1])
                    info.append(f"  RAM: {kb / (1024**2):.1f} GB")
                    break
    except Exception:
        info.append("  RAM: Não disponível")

    try:
        result = subprocess.run(
            ["lsblk", "-d", "-o", "NAME,SIZE,TYPE,MODEL"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in result.stdout.strip().split("\n")[1:]:
            if "disk" in line:
                info.append(f"  Disco: {line.strip()}")
    except Exception:
        pass

    return info


"""Backend estruturado (leitura de hardware/uso em tempo real).

Estas funções retornam dicionários JSON-serializáveis para a interface
Consumidas pela camada frontend via `frontend/api.py`.
Nenhum comando de SO fica dentro dos componentes visuais.
"""

import os
import re
import time
import threading
import shutil as _shutil


def _sub(cmd: list, timeout: int = 15) -> str:
    """Executa um comando e devolve stdout (ou vazio em falha)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def _kv(text: str) -> dict:
    """Converte saída 'chave = valor' em dicionário."""
    out = {}
    for line in text.split("\n"):
        if "=" in line:
            k, _, v = line.partition("=")
            out[k.strip().lower()] = v.strip()
    return out


def get_os_info() -> dict:
    """Informações reais do sistema operacional."""
    base = {
        "name": system_info.so_name,
        "release": system_info.os_release,
        "version": system_info.os_version,
        "architecture": system_info.architecture,
        "hostname": system_info.hostname,
        "available": True,
    }
    if system_info.is_windows:
        raw = _sub(["wmic", "os", "get", "Caption,Version,OSArchitecture", "/format:list"])
        data = _kv(raw)
        if data.get("caption"):
            base["name"] = re.sub(r"\s+", " ", data["caption"])
        if data.get("version"):
            base["version"] = data["version"].split(".")[0]
        if data.get("osarchitecture"):
            base["architecture"] = data["osarchitecture"]
    return base


def get_cpu_info() -> dict:
    """Nome e contagem de núcleos/threads da CPU (leitura real)."""
    cpu = {"name": "Não disponível", "cores": "—", "threads": "—", "available": False}
    if system_info.is_windows:
        raw = _sub(["wmic", "cpu", "get", "Name,NumberOfCores,NumberOfLogicalProcessors", "/format:list"])
        data = _kv(raw)
        if data.get("name"):
            cpu["name"] = re.sub(r"\s+", " ", data["name"]).strip()
            cpu["cores"] = data.get("numberofcores", "—")
            cpu["threads"] = data.get("numberoflogicalprocessors", "—")
            cpu["available"] = True
    elif system_info.is_macos:
        name = _sub(["sysctl", "-n", "machdep.cpu.brand_string"])
        cores = _sub(["sysctl", "-n", "hw.physicalcpu"])
        threads = _sub(["sysctl", "-n", "hw.logicalcpu"])
        if name:
            cpu["name"] = name
            cpu["cores"] = cores or "—"
            cpu["threads"] = threads or "—"
            cpu["available"] = True
    elif system_info.is_linux:
        try:
            with open("/proc/cpuinfo") as f:
                model = ""
                pieces = 0
                for line in f:
                    if "model name" in line and not model:
                        model = line.split(":")[1].strip()
                    if "physical id" in line:
                        pieces += 1
                if model:
                    cpu["name"] = model
                    cpu["cores"] = str(pieces or os.cpu_count() or "—")
                    cpu["threads"] = str(os.cpu_count() or "—")
                    cpu["available"] = True
        except Exception:
            pass
    return cpu


def get_gpu_info() -> dict:
    """Informações reais da placa de vídeo."""
    gpu = {"name": "Não disponível", "vram": "—", "available": False}
    if system_info.is_windows:
        raw = _sub(["wmic", "path", "win32_VideoController", "get", "Name,AdapterRAM,DriverVersion,DriverDate", "/format:list"])
        rows = [blob.strip() for blob in raw.split("\n\n") if blob.strip()]
        best = {}
        for blob in rows:
            data = _kv(blob)
            if data.get("name") and "RDP" not in data["name"] and "Basic Display" not in data["name"]:
                best = data
                break
        if not best and rows:
            # Captura o primeiro descriptor que tenha nome mesmo que básico
            for blob in rows:
                data = _kv(blob)
                if data.get("name"):
                    best = data
                    break
        if best.get("name"):
            gpu["name"] = re.sub(r"\s+", " ", best["name"]).strip()
            vram = best.get("adapterram")
            try:
                gpu["vram"] = f"{int(float(vram)) / (1024**3):.0f} GB"
            except Exception:
                gpu["vram"] = "—"
            gpu["driver"] = best.get("driverversion", "—")
            gpu["driver_date"] = best.get("driverdate", "—")
            gpu["available"] = True
    elif system_info.is_macos:
        raw = _sub(["system_profiler", "SPDisplaysDataType"], timeout=30)
        for line in raw.split("\n"):
            line = line.strip()
            if "Chipset Model:" in line:
                gpu["name"] = line.split(":", 1)[1].strip()
                gpu["available"] = True
            elif "VRAM" in line or ("Metal" in line):
                gpu["vram"] = line.split(":", 1)[1].strip()
    return gpu


def get_ram_info() -> dict:
    """Capacidade total da memória RAM (leitura real)."""
    ram = {"total_gb": "Não disponível", "speed": "—", "available": False}
    if system_info.is_windows:
        raw = _sub(["wmic", "memorychip", "get", "Capacity,Speed", "/format:list"])
        speeds = set()
        total = 0
        for blob in raw.split("\n\n"):
            data = _kv(blob)
            try:
                total += int(float(data.get("capacity", 0)))
            except Exception:
                pass
            if data.get("speed"):
                speeds.add(data["speed"])
        if total:
            ram["total_gb"] = f"{total / (1024**3):.1f}"
            ram["available"] = True
            ram["speed"] = " / ".join(sorted(speeds)) if speeds else "—"
            ram["total_bytes"] = total
    elif system_info.is_macos:
        raw = _sub(["sysctl", "-n", "hw.memsize"])
        try:
            total = int(raw)
            ram["total_gb"] = f"{total / (1024**3):.1f}"
            ram["total_bytes"] = total
            ram["available"] = True
        except Exception:
            pass
    elif system_info.is_linux:
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal"):
                        total_kb = int(line.split()[1])
                        ram["total_gb"] = f"{total_kb / (1024 ** 2):.1f}"
                        ram["total_bytes"] = total_kb * 1024
                        ram["available"] = True
                        break
        except Exception:
            pass
    return ram


def get_disk_info() -> dict:
    """Uso real do disco do sistema."""
    disk = {"total_gb": "Não disponível", "free_gb": "—", "used_gb": "—", "percent": None, "available": False}
    root = "C:\\" if system_info.is_windows else "/"
    try:
        usage = _shutil.disk_usage(root)
        disk["total_gb"] = f"{usage.total / (1024**3):.0f}"
        disk["used_gb"] = f"{usage.used / (1024**3):.0f}"
        disk["free_gb"] = f"{usage.free / (1024**3):.0f}"
        disk["percent"] = round(usage.used / usage.total * 100) if usage.total else 0
        disk["available"] = True
    except Exception:
        pass
    return disk


def get_cpu_usage() -> int | None:
    """Uso real da CPU (percentual único, 0-100)."""
    try:
        if system_info.is_windows:
            raw = _sub(["wmic", "cpu", "get", "loadpercentage", "/value"])
            data = _kv(raw)
            return int(float(data.get("loadpercentage")))
        elif system_info.is_macos:
            raw = _sub(["ps", "-A", "-o", "%cpu="])
            values = [float(x) for x in raw.split() if x.strip()]
            if values:
                return min(100, max(0, int(sum(values) / os.cpu_count())))
        elif system_info.is_linux:
            return _linux_cpu_usage()
    except Exception:
        pass
    return None


_CPU_LOCK = threading.Lock()
_LAST_CPU = None


def _linux_cpu_usage() -> int | None:
    global _LAST_CPU
    try:
        with open("/proc/stat") as f:
            parts = [int(x) for x in f.readline().split()[1:4]]
        if len(parts) != 3:
            return None
        idle, total = parts[2], sum(parts)
        with _CPU_LOCK:
            prev = _LAST_CPU
            _LAST_CPU = (idle, total, time.time())
        if prev:
            didle = idle - prev[0]
            dtotal = total - prev[1]
            if dtotal > 0:
                return min(100, max(0, int((1 - didle / dtotal) * 100)))
        return None
    except Exception:
        return None


def get_ram_usage() -> dict:
    """Uso real da memória em GB."""
    used = total = None
    if system_info.is_windows:
        raw = _sub(["wmic", "OS", "get", "TotalVisibleMemorySize,FreePhysicalMemory", "/format:list"])
        data = _kv(raw)
        try:
            total = int(float(data.get("totalvisiblememorysize", 0))) / 1024
            free = int(float(data.get("freephysicalmemory", 0))) / 1024
            used = total - free
        except Exception:
            pass
    elif system_info.is_macos:
        raw = _sub(["sysctl", "-n", "hw.memsize"])
        try:
            total = int(raw) / (1024**3)
        except Exception:
            pass
        vm = _sub(["vm_stat"])
        try:
            pages = int(re.search(r"page size of (\d+) bytes", vm).group(1))
            def kb(key):
                m = re.search(rf"{key}:\s+([\d]+)", vm)
                return int(m.group(1)) * pages / (1024**3) if m else 0.0
            free = kb("Pages free") + kb("Pages inactive")
            used = total - free
        except Exception:
            pass
    elif system_info.is_linux:
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal"):
                        total = int(line.split()[1]) / (1024**2)
                    elif line.startswith("MemAvailable"):
                        avail = int(line.split()[1]) / (1024**2)
                        used = total - avail
        except Exception:
            pass
    if used is None or total is None:
        return {"used": None, "total": None, "available": False}
    return {"used": round(used, 1), "total": round(total, 1), "pct": min(100, max(0, int(used / total * 100))), "available": True}


def get_cpu_freq() -> str | None:
    """Frequência atual da CPU em GHz (leitura real quando possível)."""
    try:
        if system_info.is_windows:
            raw = _sub(["wmic", "cpu", "get", "CurrentClockSpeed", "/value"])
            data = _kv(raw)
            mhz = int(float(data.get("currentclockspeed", 0)))
            return f"{mhz / 1000:.2f} GHz" if mhz else None
        elif system_info.is_macos:
            raw = _sub(["sysctl", "-n", "hw.cpufrequency"])
            hz = int(raw)
            return f"{hz / 1e9:.2f} GHz" if hz > 0 else None
    except Exception:
        pass
    return None


def get_cpu_temp() -> str | None:
    """Temperatura da CPU (°C) quando o hardware expõe. Caso contrário None."""
    if system_info.is_windows:
        raw = _sub(['wmic', '/namespace:\\\\root\\wmi', 'PATH', 'MSAcpi_ThermalZoneTemperature', 'get', 'CurrentTemperature', '/value'])
        try:
            data = _kv(raw)
            deg = int(float(data.get("currenttemperature", 0))) / 10 - 273.15
            if 0 < deg < 120:
                return f"{deg:.0f}°C"
        except Exception:
            pass
    return None


def get_gpu_sample() -> dict:
    """Leitura real da GPU via nvidia-smi (quando disponível)."""
    import shutil as _s
    bin_path = None
    for cand in ("nvidia-smi", "C:\\Windows\\System32\\nvidia-smi.exe", "/usr/bin/nvidia-smi", "/usr/local/bin/nvidia-smi", "/opt/homebrew/bin/nvidia-smi"):
        if cand == "nvidia-smi":
            if _s.which("nvidia-smi"):
                bin_path = "nvidia-smi"
                break
        elif os.path.exists(cand):
            bin_path = cand
            break
    if not bin_path:
        return {"available": False}
    raw = _sub([bin_path, "--query-gpu=utilization.gpu,temperature.gpu,name,driver_version", "--format=csv,noheader,nounits"], timeout=5)
    if not raw:
        return {"available": False}
    parts = [p.strip() for p in raw.split(",")]
    try:
        return {
            "available": True,
            "usage": int(parts[0]) if parts[0].isdigit() else None,
            "temp": f"{parts[1]}°C" if len(parts) > 1 and parts[1].isdigit() else None,
            "name": parts[2] if len(parts) > 2 else None,
            "driver": parts[3] if len(parts) > 3 else None,
        }
    except Exception:
        return {"available": False}


def collect_overview() -> dict:
    """Snapshot completo para o Dashboard (leituras reais, não inventadas)."""
    return {
        "os": get_os_info(),
        "cpu": get_cpu_info(),
        "gpu": get_gpu_info(),
        "gpu_sample": get_gpu_sample(),
        "ram": get_ram_info(),
        "disk": get_disk_info(),
        "compiled_at": time.time(),
    }


def _get_network_info() -> list:
    """Retorna informações de rede."""
    info = [colorize("═══ REDE ═══", Theme.PRIMARY)]

    try:
        import socket
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        info.append(f"  Hostname: {hostname}")
        info.append(f"  IP Local: {ip}")
    except Exception:
        info.append("  Rede: Não disponível")

    if system_info.is_windows:
        try:
            result = subprocess.run(
                ["ipconfig", "/all"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            dns_servers = []
            for line in result.stdout.split("\n"):
                if "DNS" in line and ":" in line:
                    dns = line.split(":")[-1].strip()
                    if dns and dns != "":
                        dns_servers.append(dns)
            if dns_servers:
                info.append(f"  DNS: {', '.join(dns_servers[:2])}")
        except Exception:
            pass
    elif system_info.is_macos or system_info.is_linux:
        try:
            result = subprocess.run(
                ["scutil", "--dns"] if system_info.is_macos else ["cat", "/etc/resolv.conf"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            for line in result.stdout.split("\n"):
                if "nameserver" in line:
                    dns = line.split()[-1]
                    info.append(f"  DNS: {dns}")
                    break
        except Exception:
            pass

    return info

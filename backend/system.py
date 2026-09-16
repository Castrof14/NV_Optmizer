"""
NV Optimizer 2.0 - Backend de Sistema
Diagnóstico completo: Windows, CPU, GPU, RAM, Disco.
"""

import os
import platform
import subprocess
from datetime import datetime

from .backend_core import OperationResult, isAdmin, run_command, run_powershell


def getWindowsInfo() -> dict:
    """Detecta versão, build, arquitetura e estado de ativação do Windows."""
    info = {
        "version": platform.version(),
        "release": platform.release(),
        "architecture": platform.machine(),
        "edition": platform.win32_edition() if hasattr(platform, "win32_edition") else "N/A",
        "activation": "unknown",
        "build": platform.version(),
    }

    try:
        result = subprocess.run(
            ["reg", "query", "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
             "/v", "DisplayVersion"],
            capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.split("\n"):
            if "DisplayVersion" in line:
                parts = line.split()
                if parts:
                    info["version"] = parts[-1].strip()
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["reg", "query", "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
             "/v", "CurrentBuild"],
            capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.split("\n"):
            if "CurrentBuild" in line:
                parts = line.split()
                if parts:
                    info["build"] = parts[-1].strip()
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["reg", "query", "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
             "/v", "ProductName"],
            capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.split("\n"):
            if "ProductName" in line:
                parts = line.split()
                if parts:
                    info["edition"] = " ".join(parts[3:]).strip()
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["cscript", "//Nologo", os.path.join(os.environ.get("WINDIR", "C:\\Windows"),
             "System32\\slmgr.vbs"), "/dli"],
            capture_output=True, text=True, timeout=20,
        )
        output = result.stdout + result.stderr
        if "Licensed" in output.upper():
            info["activation"] = "licensed"
        elif "trial" in output.lower() or "grace" in output.lower():
            info["activation"] = "trial"
        else:
            info["activation"] = "not_licensed"
    except Exception:
        pass

    return info


def _sample_cpu_usage_windows() -> float:
    """Amostra uso de CPU no Windows via WMI."""
    try:
        result = subprocess.run(
            ["wmic", "cpu", "get", "LoadPercentage", "/value"],
            capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.strip().split("\n"):
            if "LoadPercentage" in line and "=" in line:
                return float(line.split("=")[1].strip())
    except Exception:
        pass
    return 0.0


def getCPUInfo() -> dict:
    """Detecta modelo, núcleos, threads, uso e frequência do CPU."""
    info = {
        "model": "N/A",
        "cores": 0,
        "threads": 0,
        "usage": 0.0,
        "frequency_mhz": 0,
    }

    if platform.system() != "Windows":
        info["cores"] = os.cpu_count() or 0
        info["threads"] = info["cores"]
        info["model"] = platform.processor() or "N/A"
        info["usage"] = _sample_cpu_usage_unix()
        return info

    try:
        result = subprocess.run(
            ["wmic", "cpu", "get", "Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed",
             "/format:list"],
            capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                value = value.strip()
                if key.strip() == "Name" and value:
                    info["model"] = value
                elif key.strip() == "NumberOfCores" and value:
                    info["cores"] = int(value)
                elif key.strip() == "NumberOfLogicalProcessors" and value:
                    info["threads"] = int(value)
                elif key.strip() == "MaxClockSpeed" and value:
                    info["frequency_mhz"] = int(value)
    except Exception:
        pass

    info["usage"] = _sample_cpu_usage_windows()

    return info


def _sample_cpu_usage_unix() -> float:
    """Amostra uso de CPU em sistemas Unix (macOS/Linux)."""
    try:
        if platform.system() == "Darwin":
            import subprocess as sp
            r = sp.run(["ps", "-A", "-o", "%cpu"], capture_output=True, text=True, timeout=10)
            values = []
            for line in r.stdout.split("\n")[1:]:
                v = line.strip()
                if v:
                    try:
                        values.append(float(v))
                    except ValueError:
                        pass
            if values:
                return min(100.0, sum(values) / len(values))
        elif platform.system() == "Linux":
            with open("/proc/stat", "r") as f:
                fields = f.readline().split()[1:]
                total = sum(int(x) for x in fields)
                idle = int(fields[3])
                with open("/proc/stat", "r") as f2:
                    fields2 = f2.readline().split()[1:]
                    total2 = sum(int(x) for x in fields2)
                    idle2 = int(fields2[3])
                    dtotal = total2 - total
                    didle = idle2 - idle
                    if dtotal > 0:
                        return round((dtotal - didle) / dtotal * 100, 1)
    except Exception:
        pass
    return 0.0


def getGPUInfo() -> dict:
    """Detecta fabricante, modelo, driver, uso, temperatura e VRAM da GPU."""
    info = {
        "manufacturer": "N/A",
        "model": "N/A",
        "driver_version": "N/A",
        "driver_date": "N/A",
        "usage": 0,
        "temperature_c": None,
        "vram_total_mb": None,
        "vram_used_mb": None,
    }

    try:
        result = subprocess.run(
            ["wmic", "path", "win32_VideoController",
             "get", "Name,VideoProcessor,DriverVersion,DriverDate,AdapterRAM",
             "/format:list"],
            capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                value = value.strip()
                if key.strip() == "Name" and value:
                    if value.lower().startswith("nvidia") or "nvidia" in value.lower():
                        info["manufacturer"] = "NVIDIA"
                    elif "amd" in value.lower() or "radeon" in value.lower():
                        info["manufacturer"] = "AMD"
                    elif "intel" in value.lower():
                        info["manufacturer"] = "Intel"
                    else:
                        info["manufacturer"] = value.split()[0] if value.split() else "Unknown"
                    info["model"] = value
                elif key.strip() == "DriverVersion" and value:
                    info["driver_version"] = value
                elif key.strip() == "DriverDate" and value:
                    info["driver_date"] = value[:10] if len(value) >= 10 else value
                elif key.strip() == "AdapterRAM" and value:
                    try:
                        info["vram_total_mb"] = int(int(value) / (1024 * 1024))
                    except ValueError:
                        pass
    except Exception:
        pass

    try:
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command',
             'try { $g=Get-CimInstance Win32_VideoController | Select-Object -First 1; '
             'Add-Type -AssemblyName System.Management; Write-Output "OK" } catch { Write-Output "FAIL" }'],
            capture_output=True, text=True, timeout=15,
        )
    except Exception:
        pass

    return info


def getRAMInfo() -> dict:
    """Detecta RAM total, em uso e disponível."""
    info = {
        "total_bytes": 0,
        "used_bytes": 0,
        "available_bytes": 0,
        "total_gb": 0,
        "used_gb": 0,
        "available_gb": 0,
        "usage_percent": 0,
    }

    if platform.system() == "Darwin":
        try:
            hw = subprocess.run(["sysctl", "-n", "hw.memsize"],
                                capture_output=True, text=True, timeout=10)
            total = int(hw.stdout.strip())
            mem = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=10)
            pages = {}
            for line in mem.stdout.split("\n"):
                if ":" in line:
                    key = line.split(":")[0].strip()
                    value = line.split(":")[1].strip().rstrip(".")
                    pages[key] = value
            page_size = 4096
            try:
                ps_out = subprocess.run(["sysctl", "-n", "hw.pagesize"],
                                        capture_output=True, text=True, timeout=10)
                page_size = int(ps_out.stdout.strip())
            except Exception:
                pass
            free_pages = int(pages.get("Pages free", 0).replace(",", ""))
            inactive_pages = int(pages.get("Pages inactive", 0).replace(",", ""))
            available = (free_pages + inactive_pages) * page_size
            info["total_bytes"] = total
            info["available_bytes"] = available
            info["used_bytes"] = total - available
        except Exception:
            pass
    elif platform.system() == "Linux":
        try:
            info["total_bytes"] = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
            info["available_bytes"] = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_AVPHYS_PAGES")
            info["used_bytes"] = info["total_bytes"] - info["available_bytes"]
        except Exception:
            pass
    else:
        try:
            result = subprocess.run(
                ["wmic", "os", "get", "TotalVisibleMemorySize,FreePhysicalMemory",
                 "/format:list"],
                capture_output=True, text=True, timeout=10,
            )
            total_kb = 0
            free_kb = 0
            for line in result.stdout.strip().split("\n"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    try:
                        if key.strip() == "TotalVisibleMemorySize":
                            total_kb = int(value.strip())
                        elif key.strip() == "FreePhysicalMemory":
                            free_kb = int(value.strip())
                    except ValueError:
                        pass

            if total_kb > 0:
                info["total_bytes"] = total_kb * 1024
                info["available_bytes"] = free_kb * 1024
                info["used_bytes"] = info["total_bytes"] - info["available_bytes"]
        except Exception:
            pass

    if info["total_bytes"] > 0:
        info["total_gb"] = round(info["total_bytes"] / (1024 ** 3), 2)
        info["used_gb"] = round(info["used_bytes"] / (1024 ** 3), 2)
        info["available_gb"] = round(info["available_bytes"] / (1024 ** 3), 2)
        info["used_mb"] = round(info["used_bytes"] / (1024 ** 2), 2)
        info["available_mb"] = round(info["available_bytes"] / (1024 ** 2), 2)
        info["usage_percent"] = round((info["used_bytes"] / info["total_bytes"]) * 100, 1)

    return info


def getDiskInfo() -> list:
    """Detecta informações dos discos."""
    disks = []

    try:
        result = subprocess.run(
            ["wmic", "logicaldisk", "get", "DeviceID,VolumeName,Size,FreeSpace,DriveType",
             "/format:list"],
            capture_output=True, text=True, timeout=10,
        )
        current = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                current[key.strip()] = value.strip()
            elif not line.strip() and current:
                if str(current.get("DriveType", "")) == "3":
                    total = int(current.get("Size", 0) or 0)
                    free = int(current.get("FreeSpace", 0) or 0)
                    disks.append({
                        "drive": current.get("DeviceID", ""),
                        "label": current.get("VolumeName", ""),
                        "total_bytes": total,
                        "free_bytes": free,
                        "total_gb": round(total / (1024 ** 3), 2) if total else 0,
                        "free_gb": round(free / (1024 ** 3), 2) if free else 0,
                        "used_gb": round((total - free) / (1024 ** 3), 2) if total and free else 0,
                        "usage_percent": round(((total - free) / total) * 100, 1) if total and free else 0,
                    })
                current = {}
        if current and str(current.get("DriveType", "")) == "3":
            total = int(current.get("Size", 0) or 0)
            free = int(current.get("FreeSpace", 0) or 0)
            disks.append({
                "drive": current.get("DeviceID", ""),
                "label": current.get("VolumeName", ""),
                "total_bytes": total,
                "free_bytes": free,
                "total_gb": round(total / (1024 ** 3), 2) if total else 0,
                "free_gb": round(free / (1024 ** 3), 2) if free else 0,
                "used_gb": round((total - free) / (1024 ** 3), 2) if total and free else 0,
                "usage_percent": round(((total - free) / total) * 100, 1) if total and free else 0,
            })
    except Exception:
        pass

    return disks


def getSystemInfo() -> dict:
    """Retorna diagnóstico completo do sistema em dados estruturados."""
    info = {
        "platform": {
            "os": platform.system(),
            "release": platform.release(),
            "node": platform.node(),
            "python": platform.python_version(),
            "is_windows": platform.system() == "Windows",
            "isAdmin": isAdmin(),
        },
        "windows": {},
        "cpu": {},
        "gpu": {},
        "ram": {},
        "disk": [],
        "collected_at": datetime.now().isoformat(),
    }

    if platform.system() == "Windows":
        info["windows"] = getWindowsInfo()
        info["cpu"] = getCPUInfo()
        info["gpu"] = getGPUInfo()
        info["ram"] = getRAMInfo()
        info["disk"] = getDiskInfo()

    return info


def checkSystem() -> dict:
    """Verifica compatibilidade entre Windows 10/11."""
    result = {"supported": True, "major_version": 10, "windows_11": False, "build": 0}

    try:
        reg = subprocess.run(
            ["reg", "query", "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
             "/v", "DisplayVersion"],
            capture_output=True, text=True, timeout=10,
        )
        for line in reg.stdout.split("\n"):
            if "DisplayVersion" in line:
                parts = line.split()
                if len(parts) >= 3:
                    version = parts[-1].strip()
                    if "11" in version:
                        result["windows_11"] = True
                        result["major_version"] = 11
    except Exception:
        pass

    try:
        reg = subprocess.run(
            ["reg", "query", "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
             "/v", "CurrentBuild"],
            capture_output=True, text=True, timeout=10,
        )
        for line in reg.stdout.split("\n"):
            if "CurrentBuild" in line:
                parts = line.split()
                if len(parts) >= 3:
                    result["build"] = int(parts[-1].strip())

        if result["build"] >= 22000:
            result["windows_11"] = True
            result["major_version"] = 11
    except Exception:
        pass

    return result
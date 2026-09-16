"""
Módulo de drivers do NV Optimizer.
"""

import subprocess
from utils.colors import Theme, colorize
from utils.logger import logger
from utils.config import system_info


def show_drivers():
    """[60] Mostrar Drivers"""
    print(colorize("\n  Listando drivers...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        result = subprocess.run(
            ["driverquery", "/FO", "TABLE"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        lines = result.stdout.split("\n")
        for line in lines[:30]:
            if line.strip():
                print(f"    {line.strip()}")
        if len(lines) > 30:
            print(f"    ... e mais {len(lines) - 30} drivers")
        logger.success(f"Total de drivers: {len(lines) - 2}")
    except Exception as e:
        logger.error(f"Erro ao listar drivers: {e}")


def export_drivers():
    """[61] Exportar Drivers"""
    print(colorize("\n  Exportando drivers...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        import os
        export_path = os.path.expanduser("~/Desktop\\DriversBackup")
        os.makedirs(export_path, exist_ok=True)
        result = subprocess.run(
            ["dism", "/online", "/export-driver", f"/destination:{export_path}"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        logger.success(f"Drivers exportados para: {export_path}")
    except Exception as e:
        logger.error(f"Erro ao exportar drivers: {e}")


def update_drivers_winget():
    """[62] Atualizar Drivers (Winget)"""
    print(colorize("\n  Atualizando drivers via Winget...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        result = subprocess.run(
            ["winget", "upgrade", "--all"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        logger.success("Drivers e programas atualizados")
    except FileNotFoundError:
        logger.warning("Winget não encontrado. Instale o App Installer do Microsoft Store")
    except Exception as e:
        logger.error(f"Erro ao atualizar drivers: {e}")


def _kv(text: str) -> dict:
    out = {}
    for line in text.split("\n"):
        if "=" in line:
            k, _, v = line.partition("=")
            out[k.strip().lower()] = v.strip()
    return out


def get_gpu_driver() -> dict:
    """Versão real do driver da placa de vídeo."""
    result = {"name": "Não disponível", "driver": "—", "date": "—", "available": False}
    if not system_info.is_windows:
        return result
    import re
    raw = subprocess.run(
        ["wmic", "path", "win32_VideoController", "get", "Name,DriverVersion,DriverDate", "/format:list"],
        capture_output=True, text=True, timeout=15,
    )
    best = {}
    for blob in raw.stdout.strip().split("\n\n"):
        data = _kv(blob)
        if data.get("name") and "RDP" not in data["name"] and "Basic Display" not in data["name"]:
            best = data
            break
    if not best:
        for blob in raw.stdout.strip().split("\n\n"):
            data = _kv(blob)
            if data.get("name"):
                best = data
                break
    if best.get("name"):
        result["name"] = re.sub(r"\s+", " ", best["name"]).strip()
        result["driver"] = best.get("driverversion", "—")
        result["date"] = best.get("driverdate", "—")
        result["available"] = True
    # Complementa com nvidia-smi quando NVIDIA disponível
    if "NVIDIA" in result["name"].upper() or not result["available"]:
        try:
            smi = subprocess.run(
                ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5,
            )
            ver = smi.stdout.strip()
            if ver and "NVIDIA" in result["name"].upper():
                result["driver"] = ver
                result["available"] = True
        except Exception:
            pass
    return result

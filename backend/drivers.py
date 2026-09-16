"""
NV Optimizer 2.0 - Backend de Drivers
Detecção e atualização de drivers de GPU com fontes oficiais.
"""

import os
import re
import subprocess

from .backend_core import (
    OperationResult, ErrorCode, isAdmin, run_command, global_progress,
)


def getGpuDriverInfo() -> dict:
    """Detecta fabricante, modelo, versão e data do driver da GPU."""
    info = {
        "manufacturer": "unknown",
        "model": "N/A",
        "driver_version": "N/A",
        "driver_date": "N/A",
        "download_url": None,
    }

    try:
        result = subprocess.run(
            ["wmic", "path", "win32_VideoController",
             "get", "Name,DriverVersion,DriverDate,Manufacturer", "/format:list"],
            capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                value = value.strip()
                if key.strip() == "Name" and value:
                    info["model"] = value
                elif key.strip() == "DriverVersion" and value:
                    info["driver_version"] = value
                elif key.strip() == "DriverDate" and value:
                    info["driver_date"] = value[:10]
                elif key.strip() == "Manufacturer" and value:
                    manufacturer_raw = value.lower()
                    if "nvidia" in manufacturer_raw:
                        info["manufacturer"] = "NVIDIA"
                    elif "amd" in manufacturer_raw or "advanced micro" in manufacturer_raw:
                        info["manufacturer"] = "AMD"
                    elif "intel" in manufacturer_raw:
                        info["manufacturer"] = "Intel"
    except Exception:
        pass

    if info["manufacturer"] == "NVIDIA":
        info["download_url"] = "https://www.nvidia.com/drivers"
    elif info["manufacturer"] == "AMD":
        info["download_url"] = "https://www.amd.com/en/support"
    elif info["manufacturer"] == "Intel":
        info["download_url"] = "https://www.intel.com/content/www/us/en/download-center/home.html"

    return info


def getDriversList() -> list:
    """Lista todos os drivers do sistema."""
    result = run_command(["driverquery", "/FO", "CSV", "/V"], timeout=30)
    drivers = []
    if result["success"]:
        import csv
        import io
        try:
            reader = csv.DictReader(io.StringIO(result["stdout"]))
            for row in reader:
                drivers.append({
                    "name": row.get("Module Name", ""),
                    "display": row.get("Display Name", ""),
                    "type": row.get("State", ""),
                    "date": row.get("Link Date", ""),
                })
        except Exception:
            pass
    return drivers


def findGpuDriver() -> OperationResult:
    """Encontra driver oficial da GPU."""
    info = getGpuDriverInfo()
    if info["manufacturer"] == "unknown":
        return OperationResult.error(
            ErrorCode.NOT_FOUND, "GPU não detectada."
        )

    return OperationResult.ok(
        message=f"Driver da GPU {info['manufacturer']} encontrado.",
        data=info,
    )


def exportGpuDrivers(destination: str = None) -> OperationResult:
    """Exporta drivers do sistema via DISM."""
    if not isAdmin():
        return OperationResult.admin_required()

    if not destination:
        destination = os.path.join(os.environ.get("USERPROFILE", "~"), "Desktop", "DriversBackup")

    os.makedirs(destination, exist_ok=True)

    result = run_command(
        ["dism", "/online", "/export-driver", f"/destination:{destination}"],
        timeout=600,
    )

    if result["success"]:
        return OperationResult.ok(
            f"Drivers exportados para {destination}."
        )
    return OperationResult.error(
        ErrorCode.OPERATION_FAILED, "Falha ao exportar drivers.",
        result["stderr"].strip() or result["stdout"].strip(),
    )


def getDisplayDrivers() -> OperationResult:
    """API: informação do driver de vídeo."""
    return OperationResult.ok(data=getGpuDriverInfo())


def openGpuDriverDownload() -> OperationResult:
    """Abre a página oficial de download do driver."""
    info = getGpuDriverInfo()
    if info["download_url"] is None:
        return OperationResult.error(
            ErrorCode.NOT_FOUND, "Fabricante da GPU não reconhecido."
        )

    import webbrowser
    webbrowser.open(info["download_url"])

    return OperationResult.ok(
        message=f"Abrindo página oficial: {info['download_url']}",
        data=info,
    )
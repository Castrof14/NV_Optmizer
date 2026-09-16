"""
Módulo de reparo expandido do NV Optimizer.
"""

import subprocess
import time
from utils.colors import Theme, colorize
from utils.logger import logger
from utils.config import system_info
from progress import progress_bar


def run_sfc():
    """[40] SFC /SCANNOW"""
    print(colorize("\n  Executando SFC /SCANNOW...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        result = subprocess.run(
            ["sfc", "/scannow"],
            capture_output=True,
            text=True,
            timeout=600,
        )
        for line in result.stdout.split("\n"):
            if line.strip():
                print(f"    {line.strip()}")
        logger.success("SFC concluído")
    except subprocess.TimeoutExpired:
        logger.warning("SFC timeout - execute manualmente: sfc /scannow")
    except Exception as e:
        logger.error(f"Erro ao executar SFC: {e}")


def run_dism():
    """[41] DISM RestoreHealth"""
    print(colorize("\n  Executando DISM RestoreHealth...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        result = subprocess.run(
            ["DISM", "/Online", "/Cleanup-Image", "/RestoreHealth"],
            capture_output=True,
            text=True,
            timeout=600,
        )
        for line in result.stdout.split("\n"):
            if line.strip():
                print(f"    {line.strip()}")
        logger.success("DISM concluído com sucesso")
    except subprocess.TimeoutExpired:
        logger.warning("DISM timeout - execute manualmente")
    except Exception as e:
        logger.error(f"Erro ao executar DISM: {e}")


def run_chkdsk():
    """[42] CHKDSK"""
    print(colorize("\n  Executando CHKDSK...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        result = subprocess.run(
            ["chkdsk", "C:", "/F", "/R"],
            capture_output=True,
            text=True,
            timeout=600,
        )
        for line in result.stdout.split("\n"):
            if line.strip():
                print(f"    {line.strip()}")
        logger.success("CHKDSK concluído")
    except subprocess.TimeoutExpired:
        logger.warning("CHKDSK timeout - execute manualmente")
    except Exception as e:
        logger.error(f"Erro ao executar CHKDSK: {e}")


def repair_windows_update():
    """[43] Reparar Windows Update"""
    print(colorize("\n  Reparando Windows Update...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    commands = [
        ["net", "stop", "wuauserv"],
        ["net", "stop", "cryptSvc"],
        ["net", "stop", "bits"],
        ["net", "stop", "msiserver"],
    ]

    for cmd in commands:
        try:
            subprocess.run(cmd, capture_output=True, timeout=30)
        except Exception:
            pass

    import os
    import shutil
    try:
        shutil.move(
            os.environ.get("SYSTEMROOT", "") + "\\SoftwareDistribution",
            os.environ.get("SYSTEMROOT", "") + "\\SoftwareDistribution.old"
        )
    except Exception:
        pass

    start_commands = [
        ["net", "start", "wuauserv"],
        ["net", "start", "cryptSvc"],
        ["net", "start", "bits"],
        ["net", "start", "msiserver"],
    ]

    for cmd in start_commands:
        try:
            subprocess.run(cmd, capture_output=True, timeout=30)
        except Exception:
            pass

    logger.success("Windows Update reparado")


def repair_system_files():
    """[44] Reparar Arquivos do Sistema"""
    print(colorize("\n  Reparando arquivos do sistema...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    run_sfc()
    run_dism()

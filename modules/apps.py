"""
Módulo de aplicativos do NV Optimizer.
"""

import subprocess
from utils.colors import Theme, colorize
from utils.logger import logger
from utils.config import system_info


def update_all_programs():
    """[70] Atualizar Todos os Programas"""
    print(colorize("\n  Atualizando todos os programas...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        result = subprocess.run(
            ["winget", "upgrade", "--all"],
            capture_output=True,
            text=True,
            timeout=600,
        )
        logger.success("Programas atualizados")
    except FileNotFoundError:
        logger.warning("Winget não encontrado")
    except Exception as e:
        logger.error(f"Erro ao atualizar: {e}")


def update_winget():
    """[71] Atualizar Winget"""
    print(colorize("\n  Atualizando Winget...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        result = subprocess.run(
            ["powershell", "-Command", "Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        logger.success("Winget atualizado")
    except Exception as e:
        logger.error(f"Erro ao atualizar Winget: {e}")


def update_microsoft_store():
    """[72] Atualizar Microsoft Store"""
    print(colorize("\n  Atualizando Microsoft Store...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-AppxPackage -Name Microsoft.WindowsStore | Foreach {Add-AppxPackage -DisableDevelopmentMode -Register \"$($_.InstallLocation)\\AppXManifest.xml\"}"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        logger.success("Microsoft Store atualizado")
    except Exception as e:
        logger.error(f"Erro ao atualizar Store: {e}")


def quick_uninstall():
    """[73] Desinstalador Rápido"""
    print(colorize("\n  Abrindo lista de programas para desinstalação...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        subprocess.run(["appwiz.cpl"], capture_output=True, timeout=10)
        logger.success("Painel de controle de programas aberto")
    except Exception as e:
        logger.error(f"Erro ao abrir desinstalador: {e}")

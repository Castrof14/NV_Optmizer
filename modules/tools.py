"""
Módulo de ferramentas do NV Optimizer.
"""

import subprocess
from utils.colors import Theme, colorize
from utils.logger import logger
from utils.config import system_info


def open_task_manager():
    """[100] Abrir Gerenciador de Tarefas"""
    print(colorize("\n  Abrindo Gerenciador de Tarefas...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        subprocess.Popen(["taskmgr"])
        logger.success("Gerenciador de Tarefas aberto")
    except Exception as e:
        logger.error(f"Erro ao abrir Gerenciador de Tarefas: {e}")


def open_registry_editor():
    """[101] Abrir Editor de Registro"""
    print(colorize("\n  Abrindo Editor de Registro...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        subprocess.Popen(["regedit"])
        logger.success("Editor de Registro aberto")
    except Exception as e:
        logger.error(f"Erro ao abrir Editor de Registro: {e}")


def open_services():
    """[102] Abrir Serviços"""
    print(colorize("\n  Abrindo Serviços...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        subprocess.Popen(["services.msc"])
        logger.success("Serviços aberto")
    except Exception as e:
        logger.error(f"Erro ao abrir Serviços: {e}")


def open_cmd_admin():
    """[103] Abrir CMD como Admin"""
    print(colorize("\n  Abrindo CMD como Administrador...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        subprocess.Popen(
            ["cmd", "/c", "start", "cmd", "/k", "title NV Optimizer CMD"],
            shell=True,
        )
        logger.success("CMD aberto como Administrador")
    except Exception as e:
        logger.error(f"Erro ao abrir CMD: {e}")


def open_powershell():
    """[104] Abrir PowerShell"""
    print(colorize("\n  Abrindo PowerShell...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        subprocess.Popen(["powershell"])
        logger.success("PowerShell aberto")
    except Exception as e:
        logger.error(f"Erro ao abrir PowerShell: {e}")

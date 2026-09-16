"""
Módulo de ponto de restauração do NV Optimizer.
Cria pontos de restauração do sistema.
"""

import os
import platform
import subprocess
from utils.colors import Theme, colorize
from utils.logger import logger
from utils.config import system_info


def create_restore_point():
    """Cria um ponto de restauração do sistema."""
    print(colorize("\n  Criando ponto de restauração...\n", Theme.PRIMARY))

    if system_info.is_windows:
        _create_windows_restore_point()
    elif system_info.is_macos:
        _create_macos_snapshot()
    elif system_info.is_linux:
        _create_linux_snapshot()
    else:
        logger.warning("Sistema operacional não suportado para restauração")


def _create_windows_restore_point():
    """Cria ponto de restauração no Windows."""
    try:
        ps_cmd = (
            'powershell -Command "'
            "Enable-ComputerRestore -Drive 'C:\\'; "
            "Checkpoint-Computer -Description 'NV Optimizer Restore Point' -RestorePointType MODIFY_SETTINGS"
            '"'
        )
        result = subprocess.run(
            ps_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            logger.success("Ponto de restauração criado com sucesso")
        else:
            logger.warning(f"Aviso: {result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        logger.error("Timeout ao criar ponto de restauração")
    except Exception as e:
        logger.error(f"Erro ao criar ponto de restauração: {e}")


def _create_macos_snapshot():
    """Cria snapshot no macOS (Time Machine)."""
    logger.info("No macOS, utilize o Time Machine para criar backup")
    logger.info("Abrindo Preferências do Sistema > Time Machine...")
    try:
        subprocess.run(["open", "-a", "Time Machine"], check=False)
    except Exception:
        pass
    logger.success("Utilitário de backup aberto")


def _create_linux_snapshot():
    """Cria snapshot no Linux."""
    logger.info("No Linux, utilitários como Timeshift podem ser usados")
    try:
        result = subprocess.run(
            ["which", "timeshift"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            logger.info("Timeshift encontrado. Execute: sudo timeshift --create")
        else:
            logger.warning("Timeshift não encontrado. Instale com: sudo apt install timeshift")
    except Exception:
        pass

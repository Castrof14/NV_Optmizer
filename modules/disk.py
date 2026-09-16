"""
Módulo de otimização de disco expandido do NV Optimizer.
"""

import subprocess
import time
from utils.colors import Theme, colorize
from utils.logger import logger
from utils.config import system_info
from progress import progress_bar


def optimize_disk():
    """[20] Otimizar Disco"""
    print(colorize("\n  Otimizando disco...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    steps = [
        ("Desabilitando indexação de disco...", _disable_disk_indexing),
        ("Otimizando TRIM para SSDs...", _optimize_trim),
        ("Desabilitando Superfetch/SysMain...", _disable_superfetch),
    ]

    for i, (message, callback) in enumerate(steps, 1):
        progress_bar(i, len(steps), prefix="  Otimizando:")
        print(f"\n    {message}")
        callback()
        time.sleep(0.3)

    progress_bar(len(steps), len(steps), prefix="  Otimizando:")
    print()
    logger.success("Disco otimizado com sucesso")


def defrag_hd():
    """[21] Desfragmentar HD"""
    print(colorize("\n  Desfragmentando HD...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        logger.info("Analisando fragmentação...")
        result = subprocess.run(
            ["defrag", "C:", "/A"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        print(result.stdout)
        logger.success("Análise de fragmentação concluída")
    except Exception as e:
        logger.error(f"Erro ao desfragmentar: {e}")


def trim_ssd():
    """[22] TRIM SSD"""
    print(colorize("\n  Executando TRIM no SSD...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        result = subprocess.run(
            ["defrag", "C:", "/L"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        print(result.stdout)
        logger.success("TRIM executado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao executar TRIM: {e}")


def optimize_startup():
    """[23] Otimizar Inicialização"""
    print(colorize("\n  Otimizando inicialização...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        import winreg
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
            i = 0
            apps = []
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    apps.append((name, value))
                    i += 1
                except OSError:
                    break

            print(f"\n  Programas de inicialização encontrados: {len(apps)}")
            for name, value in apps:
                print(f"    • {name}")
    except Exception as e:
        logger.error(f"Erro ao listar inicialização: {e}")


def clean_startup_programs():
    """[24] Limpar Programas de Startup"""
    print(colorize("\n  Limpando Programas de Startup...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    startup_apps = [
        "OneDrive", "Microsoft Teams", "Discord", "Spotify",
        "Steam", "Epic Games Launcher", "Adobe Creative Cloud",
        "Google Update", "Apple Software Update"
    ]

    try:
        import winreg
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"

        removed = 0
        for app in startup_apps:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, app)
                    logger.success(f"Removido: {app}")
                    removed += 1
            except FileNotFoundError:
                pass
            except Exception:
                pass

        logger.success(f"{removed} programas removidos da inicialização")
    except Exception as e:
        logger.error(f"Erro ao limpar startup: {e}")


# Funções auxiliares
def _disable_disk_indexing():
    try:
        subprocess.run(["sc", "config", "WSearch", "start=", "disabled"], capture_output=True, timeout=30)
        logger.success("Indexação de disco desabilitada")
    except Exception:
        logger.warning("Não foi possível desabilitar indexação")


def _optimize_trim():
    try:
        subprocess.run(["fsutil", "behavior", "set", "DisableDeleteNotify", "0"], capture_output=True, timeout=30)
        logger.success("TRIM habilitado")
    except Exception:
        logger.warning("Não foi possível configurar TRIM")


def _disable_superfetch():
    try:
        subprocess.run(["sc", "config", "SysMain", "start=", "disabled"], capture_output=True, timeout=30)
        subprocess.run(["net", "stop", "SysMain"], capture_output=True, timeout=30)
        logger.success("Superfetch/SysMain desabilitado")
    except Exception:
        logger.warning("Não foi possível desabilitar Superfetch")

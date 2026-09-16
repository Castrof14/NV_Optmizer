"""
Módulo de limpeza expandido do NV Optimizer.
Funções de limpeza detalhadas por categoria.
"""

import os
import shutil
import subprocess
import time
from utils.colors import Theme, colorize
from utils.logger import logger
from utils.config import system_info
from progress import progress_bar


def clean_temp_files():
    """[10] Limpar Arquivos Temporários"""
    print(colorize("\n  Limpando arquivos temporários...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    temp_dirs = [
        os.environ.get("TEMP", ""),
        os.environ.get("LOCALAPPDATA", "") + "\\Temp",
        os.environ.get("LOCALAPPDATA", "") + "\\Microsoft\\Windows\\INetCache",
        os.environ.get("LOCALAPPDATA", "") + "\\Microsoft\\Windows\\Explorer",
        os.environ.get("LOCALAPPDATA", "") + "\\D3DSCache",
        os.environ.get("LOCALAPPDATA", "") + "\\Microsoft\\Windows\\WER",
        os.environ.get("SYSTEMROOT", "") + "\\Temp",
    ]

    total_freed = 0
    valid_dirs = [d for d in temp_dirs if d and os.path.exists(d)]

    for i, path in enumerate(valid_dirs, 1):
        progress_bar(i, len(valid_dirs), prefix="  Limpando:")
        size = _get_folder_size(path)
        _safe_remove(path)
        if size > 0:
            total_freed += size
            logger.success(f"Limpo: {path} ({_format_size(size)})")
        time.sleep(0.1)

    progress_bar(len(valid_dirs), len(valid_dirs), prefix="  Limpando:")
    print()
    logger.success(f"Espaço recuperado: {_format_size(total_freed)}")


def clean_recycle_bin():
    """[11] Limpar Lixeira"""
    print(colorize("\n  Limpando Lixeira...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        import ctypes
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
        logger.success("Lixeira esvaziada com sucesso")
    except Exception as e:
        logger.error(f"Erro ao esvaziar lixeira: {e}")


def clean_prefetch():
    """[12] Limpar Prefetch"""
    print(colorize("\n  Limpando Prefetch...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    prefetch_path = os.environ.get("SYSTEMROOT", "") + "\\Prefetch"
    if os.path.exists(prefetch_path):
        size = _get_folder_size(prefetch_path)
        _safe_remove(prefetch_path)
        logger.success(f"Prefetch limpo ({_format_size(size)})")
    else:
        logger.warning("Pasta Prefetch não encontrada")


def clean_windows_update_cache():
    """[13] Limpar Cache do Windows Update"""
    print(colorize("\n  Limpando Cache do Windows Update...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        subprocess.run(["net", "stop", "wuauserv"], capture_output=True, timeout=30)
        download_path = os.environ.get("SYSTEMROOT", "") + "\\SoftwareDistribution\\Download"
        if os.path.exists(download_path):
            size = _get_folder_size(download_path)
            shutil.rmtree(download_path, ignore_errors=True)
            logger.success(f"Cache do Windows Update limpo ({_format_size(size)})")
        subprocess.run(["net", "start", "wuauserv"], capture_output=True, timeout=30)
    except Exception as e:
        logger.error(f"Erro ao limpar cache do Windows Update: {e}")


def clean_logs():
    """[14] Limpar Logs"""
    print(colorize("\n  Limpando Logs...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    log_dirs = [
        os.environ.get("SYSTEMROOT", "") + "\\Logs",
        os.environ.get("SYSTEMROOT", "") + "\\System32\\LogFiles",
        os.environ.get("LOCALAPPDATA", "") + "\\CrashDumps",
    ]

    total_freed = 0
    for path in log_dirs:
        if os.path.exists(path):
            size = _get_folder_size(path)
            _safe_remove(path)
            if size > 0:
                total_freed += size
                logger.success(f"Logs limpos: {path} ({_format_size(size)})")

    logger.success(f"Espaço recuperado: {_format_size(total_freed)}")


def clean_browser_cache():
    """[15] Limpar Cache dos Navegadores"""
    print(colorize("\n  Limpando Cache dos Navegadores...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    local_app_data = os.environ.get("LOCALAPPDATA", "")
    browser_caches = [
        (local_app_data + "\\Google\\Chrome\\User Data\\Default\\Cache", "Chrome"),
        (local_app_data + "\\Google\\Chrome\\User Data\\Default\\Code Cache", "Chrome Code"),
        (local_app_data + "\\Microsoft\\Edge\\User Data\\Default\\Cache", "Edge"),
        (local_app_data + "\\Mozilla\\Firefox\\Profiles", "Firefox"),
    ]

    total_freed = 0
    for path, name in browser_caches:
        if os.path.exists(path):
            size = _get_folder_size(path)
            _safe_remove(path)
            if size > 0:
                total_freed += size
                logger.success(f"Cache {name} limpo ({_format_size(size)})")

    logger.success(f"Espaço recuperado: {_format_size(total_freed)}")


def clean_thumbnails():
    """[16] Limpar Miniaturas (Thumbnail Cache)"""
    print(colorize("\n  Limpando Miniaturas...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    thumb_path = os.environ.get("LOCALAPPDATA", "") + "\\Microsoft\\Windows\\Explorer"
    if os.path.exists(thumb_path):
        for file in os.listdir(thumb_path):
            if file.startswith("thumbcache_"):
                try:
                    os.remove(os.path.join(thumb_path, file))
                except Exception:
                    pass
        logger.success("Cache de miniaturas limpo")
    else:
        logger.warning("Pasta de miniaturas não encontrada")


# Funções auxiliares
def _get_folder_size(path: str) -> int:
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                try:
                    total += os.path.getsize(os.path.join(dirpath, f))
                except (OSError, PermissionError):
                    pass
    except (OSError, PermissionError):
        pass
    return total


def _safe_remove(path: str):
    try:
        if os.path.exists(path):
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                except (OSError, PermissionError):
                    pass
    except (OSError, PermissionError):
        pass


def _format_size(size_bytes: int) -> str:
    if size_bytes >= 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"

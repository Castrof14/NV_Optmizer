"""
Utilitários compartilhados para executar comandos do Windows e guardar backups.
"""

import ctypes
import json
import os
import subprocess

from utils.config import system_info

# Evita abrir janelas de console quando rodando pelo executável sem terminal.
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
CONSOLE_ENCODING = "oem" if os.name == "nt" else "utf-8"


def is_admin() -> bool:
    try:
        if system_info.is_windows:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        return os.geteuid() == 0
    except Exception:
        return False


def require_windows_admin(feature: str):
    """Interrompe a operação com uma mensagem clara quando não pode ser executada."""
    if not system_info.is_windows:
        raise RuntimeError(f"{feature} disponível apenas no Windows.")
    if not is_admin():
        raise RuntimeError(f"{feature} exige executar o NV Optimizer como Administrador.")


def run_hidden(cmd: list, timeout: int = 30) -> subprocess.CompletedProcess:
    """Executa um comando sem janela e sem aguardar nenhuma entrada do usuário."""
    return subprocess.run(
        cmd,
        capture_output=True,
        stdin=subprocess.DEVNULL,
        encoding=CONSOLE_ENCODING,
        errors="replace",
        timeout=timeout,
        creationflags=NO_WINDOW,
    )


def command_error(result: subprocess.CompletedProcess) -> str:
    """Comandos como sc.exe escrevem os erros em stdout."""
    return (result.stderr or "").strip() or (result.stdout or "").strip() or "Erro desconhecido"


def backup_path(filename: str) -> str:
    return os.path.join(os.path.expanduser("~"), "NVOptimizer", filename)


def read_backup(filename: str, default):
    try:
        with open(backup_path(filename), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def write_backup(filename: str, data):
    """Grava em arquivo temporário e troca no final para nunca deixar um backup pela metade."""
    path = backup_path(filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

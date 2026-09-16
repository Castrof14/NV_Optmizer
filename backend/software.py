"""
NV Optimizer 2.0 - Backend de Software
Instalação real de programas com fontes oficiais.
"""

import os
import shutil
import subprocess
import urllib.request
import tempfile

from .backend_core import (
    OperationResult, ErrorCode, isAdmin,
    run_command, global_progress,
)

PROGRAMS = {
    "anydesk": {
        "name": "AnyDesk",
        "winget_id": "AnyDeskSoftwareGmbH.AnyDesk",
        "detect_exe": ["AnyDesk.exe"],
        "detect_name": "AnyDesk",
    },
    "winrar": {
        "name": "WinRAR",
        "winget_id": "RARLab.WinRAR",
        "detect_name": "WinRAR",
    },
    "7zip": {
        "name": "7-Zip",
        "winget_id": "7zip.7zip",
        "detect_name": "7-Zip",
    },
    "notepadpp": {
        "name": "Notepad++",
        "winget_id": "Notepad++.Notepad++",
        "detect_name": "Notepad++",
    },
    "brave": {
        "name": "Brave",
        "winget_id": "Brave.Brave",
        "detect_name": "Brave",
    },
    "chrome": {
        "name": "Google Chrome",
        "winget_id": "Google.Chrome",
        "detect_name": "Google Chrome",
    },
    "steam": {
        "name": "Steam",
        "winget_id": "Valve.Steam",
        "detect_name": "Steam",
    },
    "epic": {
        "name": "Epic Games Launcher",
        "winget_id": "EpicGames.EpicGamesLauncher",
        "detect_name": "Epic Games",
    },
}


def _detect_install_exe(exe_names: list) -> bool:
    """Detecta se executável existe em caminhos comuns de instalação."""
    search_dirs = [
        os.environ.get("PROGRAMFILES", "C:\\Program Files"),
        os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
        os.environ.get("LOCALAPPDATA", ""),
    ]

    for base in search_dirs:
        if not base or not os.path.isdir(base):
            continue
        try:
            for folder in os.listdir(base):
                folder_path = os.path.join(base, folder)
                if not os.path.isdir(folder_path):
                    continue
                for exe in exe_names:
                    candidate = os.path.join(folder_path, exe)
                    if os.path.isfile(candidate):
                        return True
                    # Buscar recursivamente (1 nível)
                    try:
                        for sub in os.listdir(folder_path):
                            sub_candidate = os.path.join(folder_path, sub, exe)
                            if os.path.isfile(sub_candidate):
                                return True
                    except (OSError, PermissionError):
                        pass
        except (OSError, PermissionError):
            pass
    return False


def _detect_install_uninstall_registry(app_name: str) -> bool:
    """Detecta instalação via registro de desinstalação."""
    try:
        import winreg
    except ImportError:
        return False

    reg_paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    ]

    for reg_path in reg_paths:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                for i in range(0, winreg.QueryInfoKey(key)[0]):
                    try:
                        with winreg.OpenKey(key, winreg.EnumKey(key, i)) as subkey:
                            try:
                                display = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                if app_name.lower() in display.lower():
                                    return True
                            except OSError:
                                pass
                    except OSError:
                        pass
        except OSError:
            pass
    return False


def _detect_winget_install(winget_id: str) -> bool:
    """Detecta instalação via winget list."""
    try:
        result = subprocess.run(
            ["winget", "list", "--id", winget_id, "--accept-source-agreements"],
            capture_output=True, text=True, timeout=30,
        )
        return winget_id.lower() in result.stdout.lower()
    except Exception:
        return False


def isInstalled(program_id: str) -> dict:
    """Detecta se programa está instalado. Retorna status + versão se possível."""
    prog = PROGRAMS.get(program_id.lower())
    if not prog:
        return {"installed": False, "version": None}

    installed = False

    if "detect_exe" in prog and prog["detect_exe"]:
        installed = _detect_install_exe(prog["detect_exe"])

    if not installed and "detect_name" in prog:
        installed = _detect_install_uninstall_registry(prog["detect_name"])

    if not installed:
        installed = _detect_winget_install(prog["winget_id"])

    version = None
    if installed:
        try:
            result = subprocess.run(
                ["winget", "list", "--id", prog["winget_id"], "--accept-source-agreements"],
                capture_output=True, text=True, timeout=30,
            )
            for line in result.stdout.split("\n"):
                if prog["winget_id"].lower() in line.lower():
                    parts = line.split()
                    if len(parts) >= 2:
                        version = parts[1]

                    elif len(parts) >= 1:
                        calc = [p for p in parts if p.count(".") >= 1]
                        if calc:
                            version = calc[0]
                    break
        except Exception:
            pass

    return {"installed": installed, "version": version}


def detect_programs() -> dict:
    """Detecta status de todos os programas suportados."""
    result = {}
    for prog_id, prog in PROGRAMS.items():
        status = isInstalled(prog_id)
        result[prog_id] = {
            "name": prog["name"],
            "id": prog_id,
            "installed": status["installed"],
            "version": status.get("version"),
        }
    return result


def installProgram(program_id: str, silent: bool = True) -> OperationResult:
    """Instala programa usando fonte oficial (winget)."""
    prog = PROGRAMS.get(program_id.lower())
    if not prog:
        return OperationResult.error(
            ErrorCode.INVALID_INPUT,
            f"Programa não suportado: {program_id}",
        )

    name = prog["name"]
    operation = f"install-{program_id.lower()}"
    global_progress.emit_start(operation, f"Verificando instalação de {name}...")

    status = isInstalled(program_id)
    if status["installed"]:
        return OperationResult.already_installed(name)

    if not isAdmin():
        return OperationResult.admin_required(
            f"Privilégios administrativos são necessários para instalar {name}."
        )

    global_progress.emit_progress(operation, 15, f"Instalando {name}...")

    cmd = ["winget", "install", "--id", prog["winget_id"],
           "--accept-source-agreements", "--accept-package-agreements"]
    if silent:
        cmd.extend(["--silent", "--disable-interactivity"])

    result = run_command(cmd, timeout=600)

    global_progress.emit_progress(operation, 90, f"Verificando instalação...")

    if result["success"]:
        confirm = isInstalled(program_id)
        if confirm["installed"]:
            global_progress.emit_complete(operation, f"{name} instalado com sucesso.")
            return OperationResult.ok(f"{name} instalado com sucesso.",
                                      {"version": confirm.get("version")})
        global_progress.emit_complete(operation, f"{name} instalado (verificação pendente).")
        return OperationResult.ok(f"{name} instalado com sucesso.")
    else:
        global_progress.emit_error(operation, f"Falha ao instalar {name}.")
        return OperationResult.error(
            ErrorCode.INSTALL_FAILED,
            f"Falha ao instalar {name}.",
            result["stderr"].strip() or result["stdout"].strip() or "Erro desconhecido",
        )


def installPrograms(program_ids: list, silent: bool = True) -> list:
    """Instala múltiplos programas."""
    results = []
    for pid in program_ids:
        results.append(installProgram(pid, silent))
    return results


def getProgramInfo(program_id: str) -> OperationResult:
    """Retorna informações de um programa."""
    prog = PROGRAMS.get(program_id.lower())
    if not prog:
        return OperationResult.error(
            ErrorCode.INVALID_INPUT,
            f"Programa não suportado: {program_id}",
        )

    status = isInstalled(program_id)
    return OperationResult.ok(data={
        "id": program_id.lower(),
        "name": prog["name"],
        "winget_id": prog["winget_id"],
        "installed": status["installed"],
        "version": status.get("version"),
    })


def getProgramsStatus() -> OperationResult:
    """Retorna status de todos os programas."""
    return OperationResult.ok(data=detect_programs())
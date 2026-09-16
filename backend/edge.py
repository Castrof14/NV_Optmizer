"""
NV Optimizer 2.0 - Backend do Microsoft Edge
Detecção e desinstalação segura.
"""

import os
import shutil

from .backend_core import (
    OperationResult, ErrorCode, isAdmin, run_command,
)

EDGE_INSTALL_PATHS = [
    os.path.expandvars(r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe"),
    os.path.expandvars(r"%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe"),
]


def checkEdge() -> dict:
    """Detecta se o Edge está instalado."""
    result = {"installed": False, "version": None, "edition": "stable"}

    path = None
    for candidate in EDGE_INSTALL_PATHS:
        if os.path.isfile(candidate):
            path = candidate
            break

    if not path:
        try:
            res = run_command(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command",
                 "(Get-ItemProperty "
                 "'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\"
                 "msedge.exe' -ErrorAction Stop).'(Default)'"],
                timeout=20,
            )
            if res["success"] and res["stdout"].strip():
                p = res["stdout"].strip()
                if os.path.isfile(p):
                    path = p
        except Exception:
            pass

    if path:
        result["installed"] = True
        result["path"] = path
        try:
            res = run_command(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command",
                 f"(Get-Item '{path}').VersionInfo.ProductVersion"],
                timeout=15,
            )
            if res["success"]:
                result["version"] = res["stdout"].strip()
        except Exception:
            pass

    return result


def getEdgeStatus() -> OperationResult:
    """API: status do Edge."""
    return OperationResult.ok(data=checkEdge())


def uninstallEdge(confirm: bool = False) -> OperationResult:
    """Desinstala o Edge se a versão permitir (Windows 10 com langpack/supersed)."""
    operation = "edge-uninstall"
    from .backend_core import global_progress
    global_progress.emit_start(operation, "Verificando instalação do Edge...")

    if not confirm:
        return OperationResult.error(
            ErrorCode.PERMISSION_DENIED,
            "Confirmação explícita é necessária para remover o Microsoft Edge.",
        )

    if not isAdmin():
        return OperationResult.admin_required()

    edge = checkEdge()
    if not edge["installed"]:
        return OperationResult.ok("Microsoft Edge não está instalado.")

    setup_path = None
    for candidate in EDGE_INSTALL_PATHS:
        base = os.path.dirname(os.path.dirname(candidate))
        setup = os.path.join(base, "Installer", "setup.exe")
        if os.path.isfile(setup):
            setup_path = setup
            break

    if not setup_path:
        return OperationResult.unsupported(
            "Não foi possível encontrar o instalador do Edge. "
            "A desinstalação programática do Edge não é suportada sem o "
            "Installer\\setup.exe do Edge."
        )

    payload = '{"delete_uninstall_data":true,"experiments_for_testing":[],"uninstall":true}'

    global_progress.emit_progress(operation, 40, "Executando desinstalação do Edge...")

    result = run_command(
        [setup_path, "--uninstall", "--system-level", "--verbose-logging",
         "--force-uninstall", f"--msedge-uninstall-payload='{payload}'"],
        timeout=120,
    )

    global_progress.emit_progress(operation, 80, "Verificando resultado...")

    final = checkEdge()
    if not final["installed"] or result["success"]:
        global_progress.emit_complete(operation, "Edge removido.")
        return OperationResult.ok("Microsoft Edge foi desinstalado.")
    else:
        global_progress.emit_error(operation, "Falha ao desinstalar Edge.")
        return OperationResult.error(
            ErrorCode.OPERATION_FAILED,
            "Falha ao desinstalar o Microsoft Edge. "
            "Em versões recentes do Edge, a remoção programática não é suportada.",
            result["stderr"].strip() or result["stdout"].strip(),
        )
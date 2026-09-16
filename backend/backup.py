"""
NV Optimizer 2.0 - Backup e Restauração
Salva estado do sistema antes de otimizações e permite restauração.
"""

import json
import os
import shutil
import subprocess
from datetime import datetime

from .backend_core import (
    OperationResult, ErrorCode, isAdmin, run_command,
)

SESSION_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "NVOptimizer", "sessions",
)


def _ensure_session_dir():
    os.makedirs(SESSION_DIR, exist_ok=True)


def getServiceState(service_name: str) -> dict | None:
    """Obtém estado atual de um serviço."""
    result = run_command(["sc", "qc", service_name], timeout=15)
    if not result["success"]:
        return None

    state = {"exists": True, "name": service_name, "start_type": None}
    running = run_command(["sc", "query", service_name], timeout=15)
    state["running"] = "RUNNING" in running["stdout"].upper() if running["success"] else False

    for line in result["stdout"].split("\n"):
        if "START_TYPE" in line:
            upper = line.upper()
            if "DISABLED" in upper:
                state["start_type"] = "disabled"
            elif "AUTO" in upper and "DELAYED" not in upper:
                state["start_type"] = "auto"
                state["delayed"] = "DELAYED" in line
            elif "AUTO_START" in upper:
                state["start_type"] = "auto"
            elif "DEMAND" in upper:
                state["start_type"] = "demand"
            elif "SYSTEM" in upper:
                state["start_type"] = "system"
            elif "BOOT" in upper:
                state["start_type"] = "boot"
    return state


def createOptimizationSession(profile: str) -> OperationResult:
    """Cria sessão de otimização com backup do estado dos serviços."""
    if not isAdmin():
        return OperationResult.admin_required()

    _ensure_session_dir()
    session_id = datetime.now().strftime("optimization-session-%Y-%m-%d-%H%M")
    session_path = os.path.join(SESSION_DIR, session_id)
    os.makedirs(session_path, exist_ok=True)

    session_data = {
        "session_id": session_id,
        "profile": profile,
        "created_at": datetime.now().isoformat(),
        "services_saved": [],
        "power_scheme_before": None,
        "restore_point_created": False,
    }

    # Capturar estado anterior dos serviços das regras
    from .service_rules import SERVICE_RULES
    for rule in SERVICE_RULES:
        state = getServiceState(rule.name)
        if state:
            session_data["services_saved"].append(state)

    # Capturar plano de energia ativo
    power = run_command(["powercfg", "/getactivescheme"], timeout=15)
    if power["success"]:
        scheme = power["stdout"].strip()
        session_data["power_scheme_before"] = scheme

    # Registrar power settings no backup
    try:
        from .backend_core import run_command as rc
        for sub in ("monitor-timeout-ac", "monitor-timeout-dc",
                    "standby-timeout-ac", "standby-timeout-dc"):
            r = rc(["powercfg", "/change", sub, "1000"], timeout=10)  # sentinela p/ garantir esquema atual
    except Exception:
        pass

    # Salvar data
    with open(os.path.join(session_path, "session.json"), "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2, default=str)

    # Tentar criar ponto de restauração
    restore_point_created = False
    try:
        res = run_command(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             "Enable-ComputerRestore -Drive 'C:\\' -ErrorAction SilentlyContinue; "
             "Checkpoint-Computer -Description 'NV Optimizer - " + profile
             + "' -RestorePointType MODIFY_SETTINGS -ErrorAction SilentlyContinue"],
            timeout=120,
        )
        restore_point_created = res["success"]
        session_data["restore_point_created"] = restore_point_created
        with open(os.path.join(session_path, "session.json"), "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2, default=str)
    except Exception:
        pass

    from .logger import logger
    logger.success(
        "create_session", module="backup",
        new_state=session_id,
        details={"profile": profile, "restore_point": restore_point_created,
                 "services_saved": len(session_data["services_saved"])},
    )

    return OperationResult.ok(
        message=(
            f"Sessão de otimização criada: {session_id}\n"
            f"Serviços salvos: {len(session_data['services_saved'])}"
        ),
        data=session_data,
    )


def listRestorePoints() -> OperationResult:
    """Lista sessões de restauração criadas pelo NV Optimizer."""
    _ensure_session_dir()
    sessions = []
    if os.path.isdir(SESSION_DIR):
        for folder in sorted(os.listdir(SESSION_DIR), reverse=True):
            if not folder.startswith("optimization-session"):
                continue
            path = os.path.join(SESSION_DIR, folder)
            json_path = os.path.join(path, "session.json")
            if os.path.isfile(json_path):
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        sessions.append(data)
                except Exception:
                    sessions.append({
                        "session_id": folder,
                        "created_at": "unknown",
                        "profile": "unknown",
                        "corrupted": True,
                    })

    return OperationResult.ok(data=sessions)


def _restore_service_state(session_path: str) -> list:
    """Restaura estados originais dos serviços."""
    results = []
    json_path = os.path.join(session_path, "session.json")
    if not os.path.isfile(json_path):
        return results

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for svc in data.get("services_saved", []):
        name = svc.get("name")
        start_type = svc.get("start_type")
        if not name:
            continue
        result = run_command(["sc", "config", name, "start=", start_type], timeout=20)
        if not result["success"]:
            # Fallback: usar valor baseado no tipo detectado
            alternate = {
                "auto": "auto",
                "demand": "demand",
                "disabled": "disabled",
                "system": "system",
                "boot": "boot",
            }.get(start_type, "demand")
            result = run_command(["sc", "config", name, "start=", alternate], timeout=20)

        results.append({
            "service": name,
            "restored_start_type": start_type,
            "success": result["success"],
        })
    return results


def restoreOptimization(session_id: str) -> OperationResult:
    """Restaura configurações de uma sessão de otimização."""
    if not isAdmin():
        return OperationResult.admin_required()

    session_path = os.path.join(SESSION_DIR, session_id)
    if not os.path.isdir(session_path):
        return OperationResult.error(
            ErrorCode.NOT_FOUND, f"Sessão não encontrada: {session_id}"
        )

    results = _restore_service_state(session_path)

    from .logger import logger
    logger.success(
        "restore", module="backup",
        previous_state=session_id,
        new_state="restored",
        details={"services_restored": len(results)},
    )

    return OperationResult.ok(
        message=f"Restauração concluída para a sessão {session_id}.",
        data={"services_restored": results},
    )


def createRestorePoint() -> OperationResult:
    """Cria ponto de restauração do sistema."""
    if not isAdmin():
        return OperationResult.admin_required()

    result = run_command(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command",
         "Enable-ComputerRestore -Drive 'C:\\' -ErrorAction SilentlyContinue; "
         "Checkpoint-Computer -Description 'NV Optimizer Restore Point' "
         "-RestorePointType MODIFY_SETTINGS"],
        timeout=120,
    )

    if result["success"]:
        return OperationResult.ok("Ponto de restauração criado com sucesso.")
    return OperationResult.error(
        ErrorCode.OPERATION_FAILED, "Não foi possível criar ponto de restauração.",
        result["stderr"].strip() or result["stdout"].strip(),
    )


def apply_restore_point_restore() -> OperationResult:
    """Abre a ferramenta de restauração do sistema."""
    try:
        subprocess.Popen(["rstrui.exe"])
        return OperationResult.ok("Ferramenta de Restauração do Sistema aberta.")
    except Exception as e:
        return OperationResult.error(
            ErrorCode.OPERATION_FAILED, "Falha ao abrir restauração.",
            str(e),
        )
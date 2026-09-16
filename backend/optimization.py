"""
NV Optimizer 2.0 - Backend de Otimização
Perfis Office e Gaming baseados em regras de serviços.
"""

import subprocess

from .backend_core import (
    OperationResult, ErrorCode, isAdmin, run_command,
    global_progress,
)
from .logger import logger
from .service_rules import SERVICE_RULES, ServiceAction
from .power import setHighPerformance, setBalanced, applyPowerProfile
from .backup import (
    createOptimizationSession, restoreOptimization,
    getServiceState, listRestorePoints,
)

# Serviços que não devem ser desabilitados em nenhum cenário
CRITICAL_SERVICES = {
    "WinDefend", "bfe", "MpsSvc", "wscsvc", "SecurityHealthService",
    "Dhcp", "Dnscache", "NlaSvc", "netprofm", "RpcSs", "EventLog",
    "Schedule", "CryptSvc", "DcomLaunch", "Audiosrv", "AudioEndpointBuilder",
    "WlanSvc", "WdNisSvc", "Sense",
}


def _action_for_profile(rule, profile: str) -> ServiceAction:
    return rule.gamingAction if profile == "gaming" else rule.officeAction


def _query_service_state(rule):
    """Consulta estado atual do serviço."""
    return getServiceState(rule.name)


def _change_service_start_type(service_name: str, start_type: str) -> dict:
    """Altera o start type de um serviço e retorna resultado."""
    result = run_command(
        ["sc", "config", service_name, "start=", start_type],
        timeout=20,
    )
    return {
        "success": result["success"],
        "stderr": result["stderr"].strip() or result["stdout"].strip(),
    }


def _is_service_actually_used(service_name: str) -> str:
    """
    Determina se um serviço está 'em uso'.
    Retorna: running | stopped | not_found
    """
    result = run_command(["sc", "query", service_name], timeout=15)
    if not result["success"]:
        return "not_found"
    state = "STOPPED" if "STOPPED" in result["stdout"].upper() else "RUNNING"
    return state.lower()


def _apply_rule(rule, profile: str, session_id: str, dry_run: bool = False) -> dict:
    """Aplica uma regra a um serviço. Retorna resultado detalhado."""
    entry = {
        "service": rule.name,
        "display": rule.display,
        "previous_state": None,
        "new_state": None,
        "status": "skipped",
        "message": "",
    }

    action = _action_for_profile(rule, profile)

    # Serviços críticos nunca são alterados
    if rule.name in CRITICAL_SERVICES:
        action = ServiceAction.KEEP

    previous = _query_service_state(rule)
    if previous is None:
        entry["status"] = "not_found"
        entry["message"] = "Serviço não encontrado no sistema."
        return entry

    prev_type = previous.get("start_type")
    prev_state_str = f"{prev_type}{'(running)' if previous.get('running') else '(stopped)'}"
    entry["previous_state"] = prev_state_str

    if action == ServiceAction.KEEP:
        entry["status"] = "kept"
        entry["message"] = "Serviço mantido conforme perfil."
        return entry

    if dry_run:
        entry["status"] = "planned"
        entry["message"] = f"Ação planejada: {action.value}"
        entry["planned_action"] = action.value
        return entry

    if action == ServiceAction.DISABLE or action == ServiceAction.DISABLE_IF_UNUSED:
        target = "disabled"
    elif action == ServiceAction.MANUAL or action == ServiceAction.MANUAL_IF_UNUSED:
        target = "demand"
    else:
        target = "auto"

    # DISABLE_IF_UNUSED: só desabilita se o serviço não estiver em uso
    if action == ServiceAction.DISABLE_IF_UNUSED or action == ServiceAction.MANUAL_IF_UNUSED:
        usage = _is_service_actually_used(rule.name)
        if usage == "running" and action == ServiceAction.DISABLE_IF_UNUSED:
            entry["status"] = "in_use"
            entry["message"] = "Serviço em uso. Não alterado."
            return entry
        if usage == "running" and action == ServiceAction.MANUAL_IF_UNUSED:
            # Definir para manual mas não parar
            entry["status"] = "in_use"
            entry["message"] = "Serviço em uso. Definido para manual."
            target = "demand"

    if prev_type == target:
        entry["status"] = "already"
        entry["new_state"] = target
        entry["message"] = "Já está no estado desejado."
        return entry

    change = _change_service_start_type(rule.name, target)

    if change["success"]:
        entry["status"] = "changed"
        entry["new_state"] = target
        entry["message"] = f"Tipo de inicialização alterado para {target}."
    else:
        entry["status"] = "failed"
        entry["message"] = change["stderr"] or "Falha ao alterar."

    # Registrar no log estruturado
    logger.log(
        operation=f"optimization-{profile}",
        module="optimization",
        command=f"sc config {rule.name} start= {target}",
        previous_state=prev_state_str,
        new_state=str(target),
        status=entry["status"],
        error=change["stderr"] if not change["success"] else "",
    )

    return entry


def analyzeOptimization(profile: str) -> OperationResult:
    """Analisa o que seria alterado sem aplicar nada (dry run)."""
    if profile not in ("office", "gaming"):
        return OperationResult.error(ErrorCode.INVALID_INPUT, "Perfil inválido.")

    results = []
    for rule in SERVICE_RULES:
        entry = _apply_rule(rule, profile, None, dry_run=True)
        results.append(entry)

    intended = [r for r in results if r.get("status") == "planned"]

    from .service_rules import get_rules
    return OperationResult.ok(
        message=(
            f"Análise concluída para o perfil {profile}.\n"
            f"{len(intended)} alterações seriam aplicadas."
        ),
        data={
            "profile": profile,
            "planned_changes": intended,
            "rules": get_rules(),
        },
    )


def applyOptimization(profile: str, confirm: bool = False) -> OperationResult:
    """Aplica otimização com backup automático do estado anterior."""
    if profile not in ("office", "gaming"):
        return OperationResult.error(ErrorCode.INVALID_INPUT, "Perfil inválido.")

    if not confirm:
        return OperationResult.error(
            ErrorCode.PERMISSION_DENIED,
            "Confirmação do usuário é necessária para aplicar a otimização.",
        )

    if not isAdmin():
        return OperationResult.admin_required()

    operation = f"optimization-{profile}"

    global_progress.emit_start(operation, f"Criando sessão de backup...")

    backup = createOptimizationSession(profile)
    if not backup.success:
        return backup

    session_id = backup.data["session_id"]

    global_progress.emit_progress(operation, 10, "Analisando serviços...")

    changes = []
    total = len(SERVICE_RULES)
    for i, rule in enumerate(SERVICE_RULES):
        global_progress.emit_progress(
            operation,
            10 + int(i / total * 85),
            f"Processando: {rule.display}",
        )
        entry = _apply_rule(rule, profile, session_id)
        changes.append(entry)

    changed = [c for c in changes if c.get("status") == "changed"]
    failed = [c for c in changes if c.get("status") == "failed"]
    in_use = [c for c in changes if c.get("status") == "in_use"]

    # Aplicar perfil de energia
    if profile == "gaming":
        global_progress.emit_progress(operation, 96, "Aplicando perfil de energia...")
        setHighPerformance()
    else:
        global_progress.emit_progress(operation, 96, "Aplicando perfil de energia...")
        setBalanced()

    global_progress.emit_complete(operation, f"Otimização {profile} aplicada.")

    log_status = "success" if not failed else "partial"

    summary = {
        "session_id": session_id,
        "profile": profile,
        "changes": changes,
        "changed_count": len(changed),
        "failed_count": len(failed),
        "kept_count": len([c for c in changes if c.get("status") == "kept"]),
        "in_use_count": len(in_use),
        "restore_point_created": backup.data.get("restore_point_created", False),
        "status": log_status,
    }

    return OperationResult.ok(
        message=(
            f"Otimização {profile} aplicada.\n"
            f"Alterações: {len(changed)} | Falhas: {len(failed)} | Mantidos: "
            f"{len([c for c in changes if c.get('status') == 'kept'])}\n"
            f"Sessão de restauração: {session_id}"
        ),
        data=summary,
    )


def restoreOptimizationBySession(session_id: str) -> OperationResult:
    """Restaura otimização a partir de uma sessão."""
    return restoreOptimization(session_id)


def generateOptimizationReport(profile: str) -> OperationResult:
    """Gera relatório detalhado da última otimização."""
    sessions = listRestorePoints()
    if not sessions.data:
        return OperationResult.error(
            ErrorCode.NOT_FOUND, "Nenhuma sessão de otimização encontrada."
        )

    from .service_rules import get_rules
    return OperationResult.ok(data={
        "profile": profile,
        "sessions": sessions.data[:5],
        "rules": get_rules(),
    })
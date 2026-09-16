"""
NV Optimizer 2.0 - Backend de Segurança
Windows Defender: status, ativar, desativar (com confirmação explícita).
"""

import subprocess

from .backend_core import (
    OperationResult, ErrorCode, isAdmin, run_command, global_progress,
)
from .logger import logger


def getDefenderStatus() -> dict:
    """Obtém estado atual do Windows Defender."""
    status = {
        "available": False,
        "enabled": None,
        "real_time": None,
        "signatures_up_to_date": None,
        "antivirus_enabled": None,
        "service_running": None,
    }

    result = run_command(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command",
         "Get-MpComputerStatus | ConvertTo-Json"],
        timeout=30,
    )

    if result["success"] and result["stdout"].strip():
        import json
        try:
            data = json.loads(result["stdout"].strip())
            status["available"] = True
            status["antivirus_enabled"] = bool(data.get("AntivirusEnabled"))
            status["real_time"] = bool(data.get("RealTimeProtectionEnabled"))
            status["enabled"] = bool(data.get("AntivirusEnabled"))
            status["signatures_up_to_date"] = bool(
                data.get("AntivirusSignatureLastUpdated") or data.get("SignatureAntivirusStatus")
            )
        except (json.JSONDecodeError, AttributeError):
            pass

    service = run_command(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command",
         "Get-Service -Name WinDefend | Select-Object -ExpandProperty Status"],
        timeout=30,
    )
    if service["success"]:
        status["service_running"] = service["stdout"].strip().upper() == "RUNNING"
        status["service_start_type"] = service["stdout"].strip()

    try:
        svc = run_command(["sc", "qc", "WinDefend"], timeout=20)
        if svc["success"]:
            for line in svc["stdout"].split("\n"):
                if "START_TYPE" in line:
                    if "DISABLED" in line.upper():
                        status["service_running"] = False
                    elif "AUTO" in line.upper():
                        status["service_running"] = True
    except Exception:
        pass

    return status


def _check_defender_registry_policy() -> bool:
    """Verifica se há política que desabilita Defender."""
    try:
        result = run_command(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             "try { Get-ItemProperty "
             "'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows Defender' -Name "
             "'DisableAntiSpyware' | Select-Object -ExpandProperty DisableAntiSpyware"
             " } catch { Write-Output 'NOT_FOUND' }"],
            timeout=20,
        )
        stdout = result["stdout"].strip()
        if stdout and stdout.upper() not in ("0", "NOT_FOUND", ""):
            return True
    except Exception:
        pass
    return False


def enableDefender() -> OperationResult:
    """Reativa o Windows Defender."""
    operation = "defender-enable"
    global_progress.emit_start(operation, "Verificando Windows Defender...")

    if not isAdmin():
        return OperationResult.admin_required()

    current = getDefenderStatus()
    if current.get("antivirus_enabled"):
        global_progress.emit_complete(operation, "Defender já está ativo.")
        return OperationResult.ok("Windows Defender já está ativo.", data=current)

    cmd = (
        "Set-MpPreference -DisableRealtimeMonitoring $false; "
        "Set-MpPreference -DisableAntiSpyware $false; "
        "Set-MpPreference -DisableBehaviorMonitoring $false; "
        "Set-MpPreference -DisableIOAVProtection $false; "
        "Remove-ItemProperty -Path "
        "'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows Defender' -Name "
        "'DisableAntiSpyware' -ErrorAction SilentlyContinue; "
        "Set-Service -Name WinDefend -StartupType Automatic -ErrorAction SilentlyContinue; "
        "sc.exe config WinDefend start= auto"
    )

    global_progress.emit_progress(operation, 40, "Ativando Windows Defender...")
    result = run_command(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
        timeout=120,
    )

    global_progress.emit_progress(operation, 80, "Verificando estado...")
    new_status = getDefenderStatus()

    if new_status.get("antivirus_enabled") or result["success"]:
        global_progress.emit_complete(operation, "Windows Defender ativado.")
        logger.success(
            "enable", module="defender",
            previous_state=str(current.get("antivirus_enabled")),
            new_state="True",
        )
        return OperationResult.ok("Windows Defender ativado.", data=new_status)

    logger.error("enable", result["stderr"].strip(), module="defender")
    return OperationResult.error(
        ErrorCode.OPERATION_FAILED,
        "Não foi possível ativar o Windows Defender.",
        result["stderr"].strip() or result["stdout"].strip(),
    )


def disableDefender(confirm: bool = False) -> OperationResult:
    """Desativa o Windows Defender. Exige confirmação explícita do usuário."""
    operation = "defender-disable"
    global_progress.emit_start(operation, "Verificando Windows Defender...")

    if not confirm:
        return OperationResult.error(
            ErrorCode.PERMISSION_DENIED,
            "Confirmação explícita é necessária para desativar o Windows Defender.",
        )

    if not isAdmin():
        return OperationResult.admin_required()

    current = getDefenderStatus()
    if not current.get("antivirus_enabled") and not current.get("real_time"):
        return OperationResult.ok("Windows Defender já está desativado.", data=current)

    cmd = (
        "Set-MpPreference -DisableRealtimeMonitoring $true; "
        "Set-MpPreference -DisableAntiSpyware $true; "
        "Set-MpPreference -DisableBehaviorMonitoring $true; "
        "Set-MpPreference -DisableIOAVProtection $true; "
        "New-Item -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows Defender' "
        "-Force -ErrorAction SilentlyContinue | Out-Null; "
        "New-ItemProperty -Path "
        "'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows Defender' -Name "
        "'DisableAntiSpyware' -Value 1 -PropertyType DWord -Force "
        "-ErrorAction SilentlyContinue; "
        "sc.exe config WinDefend start= disabled"
    )

    global_progress.emit_progress(operation, 40, "Desativando Windows Defender...")
    result = run_command(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
        timeout=120,
    )

    new_status = getDefenderStatus()

    if not new_status.get("antivirus_enabled"):
        global_progress.emit_complete(operation, "Windows Defender desativado.")
        logger.warning(
            "disable", "Windows Defender desativado por solicitação explícita",
            module="defender",
            previous_state=str(current.get("antivirus_enabled")),
            new_state="False",
        )
        return OperationResult.ok("Windows Defender desativado. Reinicie para aplicar totalmente.", data=new_status)

    logger.error("disable", result["stderr"].strip(), module="defender")
    return OperationResult.error(
        ErrorCode.OPERATION_FAILED,
        "Não foi possível desativar o Windows Defender.",
        result["stderr"].strip() or result["stdout"].strip(),
    )


def updateSignatures() -> OperationResult:
    """Atualiza assinaturas do Windows Defender."""
    operation = "defender-update-signatures"
    global_progress.emit_start(operation, "Atualizando assinaturas...")

    result = run_command(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command",
         "Update-MpSignature"],
        timeout=300,
    )

    if result["success"]:
        global_progress.emit_complete(operation, "Assinaturas atualizadas.")
        return OperationResult.ok("Assinaturas do Windows Defender atualizadas.")
    return OperationResult.error(
        ErrorCode.OPERATION_FAILED, "Falha ao atualizar assinaturas.",
        result["stderr"].strip() or result["stdout"].strip(),
    )


def checkFirewall() -> dict:
    """Verifica estado do Firewall do Windows."""
    result = run_command(["netsh", "advfirewall", "show", "allprofiles"], timeout=30)
    profiles = {}
    current = None
    if result["success"]:
        for line in result.stdout.split("\n"):
            line = line.strip()
            if line.startswith("Profile Name"):
                current = line.split(":")[-1].strip()
                profiles[current] = {"enabled": None}
            elif current and line.startswith("State"):
                state = line.split(":")[-1].strip()
                profiles[current]["enabled"] = state.lower() == "on"
    return profiles
"""
NV Optimizer 2.0 - Backend de Energia
Gerencia planos de energia, tela e suspensão.
"""

import subprocess

from .backend_core import (
    OperationResult, ErrorCode, isAdmin, run_command, global_progress,
)
from .logger import logger

POWER_GUID = {
    "high_performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
    "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
    "power_saver": "a1841308-3541-4fab-bc81-f71556f20b4a",
    "ultimate_performance": "e9a42b02-d5df-448d-aa00-03f14749eb61",
}

SCREEN_TIMEOUT_GUID = {   # nome exibível: powercfg alias
    "ac": "monitor-timeout-ac",
    "dc": "monitor-timeout-dc",
}
SLEEP_TIMEOUT_GUID = {
    "ac": "standby-timeout-ac",
    "dc": "standby-timeout-dc",
}
HIBERNATE_TIMEOUT = {
    "ac": "hibernate-timeout-ac",
    "dc": "hibernate-timeout-dc",
}


def getActivePowerScheme() -> dict:
    """Obtém o plano de energia ativo."""
    try:
        result = subprocess.run(
            ["powercfg", "/getactivescheme"],
            capture_output=True, text=True, timeout=15,
        )
        output = result.stdout.strip()
        if result.returncode == 0 and output:
            match = None
            for line in output.split("\n"):
                if "(" in line and ")" in line:
                    match = line
                    break
            if match:
                guid = match.split("(")[-1].split(")")[0].strip()
                name = match.split(": ")[-1].split(" (")[0].strip()
                return {"guid": guid, "name": name}
    except Exception:
        pass
    return {"guid": None, "name": None}


def getScreenTimeout() -> dict:
    """Obtém timeout da tela para AC/DC."""
    result = {"ac": None, "dc": None}
    try:
        for key, alias in SCREEN_TIMEOUT_GUID.items():
            res = subprocess.run(
                ["powercfg", "/query", "SCHEME_CURRENT",
                 "SUB_VIDEO", "VIDEOIDLE", "/value"],
                capture_output=True, text=True, timeout=15,
            )
            for line in res.stdout.split("\n"):
                if "0x" in line or ("AC" in key.upper() and "Current" in line):
                    pass

        res = subprocess.run(
            ["powercfg", "/query", "SCHEME_CURRENT", "SUB_VIDEO", "VIDEOIDLE"],
            capture_output=True, text=True, timeout=15,
        )
        section = None
        for line in res.stdout.split("\n"):
            line = line.strip()
            if "Index" in line and "AC" in line.upper():
                section = "ac"
            elif "Index" in line and "DC" in line.upper():
                section = "dc"
            if section and "Current AC" in line or (section and "Current " in line and "Power" in line):
                parts = line.split()
                if parts:
                    try:
                        value = int(parts[-1])
                        result[section] = value
                    except (ValueError, IndexError):
                        pass
        return result

    except Exception:
        return result


def getSleepTimeout() -> dict:
    """Obtém timeout de suspensão para AC/DC."""
    result = {"ac": None, "dc": None}
    try:
        for key, alias in SLEEP_TIMEOUT_GUID.items():
            res = subprocess.run(
                ["powercfg", "/query", "SCHEME_CURRENT", "SUB_SLEEP", "STANDBYIDLE"],
                capture_output=True, text=True, timeout=15,
            )
            section = None
            for line in res.stdout.split("\n"):
                line = line.strip()
                if "AC" in line.upper() and "Index" in line:
                    section = "ac"
                elif "DC" in line.upper() and "Index" in line:
                    section = "dc"
                if section and "Current AC" in line or (section and "Current " in line and "Power" in line):
                    parts = line.split()
                    if parts:
                        try:
                            value = int(parts[-1])
                            result[section] = value
                        except (ValueError, IndexError):
                            pass
        result = result
    except Exception:
        pass
    return result


def getPowerSettings() -> OperationResult:
    """API: retorna configurações de energia atuais."""
    scheme = getActivePowerScheme()
    return OperationResult.ok(data={
        "active_scheme": scheme,
        "screen_timeout": getScreenTimeout(),
        "sleep_timeout": getSleepTimeout(),
    })


def setHighPerformance() -> OperationResult:
    """Aplica o plano de Alto Desempenho."""
    return _set_power_scheme("high_performance")


def setBalanced() -> OperationResult:
    """Aplica o plano Equilibrado."""
    return _set_power_scheme("balanced")


def setPowerSaver() -> OperationResult:
    """Aplica o plano de Economia de Energia."""
    return _set_power_scheme("power_saver")


def _set_power_scheme(scheme_key: str) -> OperationResult:
    if not isAdmin():
        return OperationResult.admin_required()

    guid = POWER_GUID.get(scheme_key)
    if not guid:
        return OperationResult.error(ErrorCode.INVALID_INPUT, "Plano de energia inválido.")

    operation = f"power-{scheme_key}"
    global_progress.emit_start(operation, f"Aplicando plano {scheme_key.replace('_', ' ')}...")

    previous = getActivePowerScheme()

    result = run_command(["powercfg", "/setactive", guid], timeout=30)
    if result["success"]:
        global_progress.emit_complete(operation)
        logger.success(
            "set_power_scheme", module="power",
            previous_state=previous.get("name") or "Unknown",
            new_state=scheme_key,
        )
        return OperationResult.ok(
            f"Plano {scheme_key.replace('_', ' ')} ativado.",
            {"previous": previous, "current": getActivePowerScheme()},
        )
    return OperationResult.error(
        ErrorCode.OPERATION_FAILED, "Falha ao aplicar plano de energia.",
        result["stderr"].strip() or result["stdout"].strip(),
    )


def setScreenNever() -> OperationResult:
    """Define tela para nunca desligar (AC e DC)."""
    return _set_timeout("screen", 0)


def setSleepNever() -> OperationResult:
    """Define suspensão para nunca (AC e DC)."""
    return _set_timeout("sleep", 0)


def applyPowerProfile(
    high_performance: bool = True,
    screen_never: bool = True,
    sleep_never: bool = True,
    hibernate_never: bool = True,
) -> OperationResult:
    """Aplica o perfil de energia completo."""
    operation = "power-profile"
    global_progress.emit_start(operation, "Aplicando perfil de energia...")

    if not isAdmin():
        return OperationResult.admin_required()

    previous = getPowerSettings().data if getPowerSettings().success else {}

    steps = []
    if high_performance:
        steps.append(("Alto desempenho", setHighPerformance))
    if screen_never:
        steps.append(("Tela nunca", setScreenNever))
    if sleep_never:
        steps.append(("Suspensão nunca", setSleepNever))

    results = {}
    for i, (label, func) in enumerate(steps, 1):
        global_progress.emit_progress(
            operation, int(i / len(steps) * 90), f"Aplicando: {label}..."
        )
        res = func()
        results[label] = res.to_dict() if hasattr(res, "to_dict") else res

    errors = [r for r in results.values() if isinstance(r, dict) and r.get("success") is False]
    if errors:
        return OperationResult.error(
            ErrorCode.OPERATION_FAILED,
            "Perfil aplicado parcialmente com erros.",
            str(errors),
        )

    global_progress.emit_complete(operation, "Perfil de energia aplicado.")
    logger.success(
        "apply_power_profile", module="power",
        previous_state=str(previous),
        new_state=str({
            "high_performance": high_performance,
            "screen_never": screen_never,
            "sleep_never": sleep_never,
        }),
    )
    return OperationResult.ok("Perfil de energia aplicado.", results)


def _set_timeout(target: str, seconds: int) -> OperationResult:
    if not isAdmin():
        return OperationResult.admin_required()

    operation = f"power-{target}-timeout"
    global_progress.emit_start(operation, f"Definindo timeout de {target}...")

    settings = []
    for mode in ("ac", "dc"):
        if target == "screen":
            settings.append(("monitor-timeout-" + mode, seconds))
        elif target == "sleep":
            settings.append(("standby-timeout-" + mode, seconds))
        elif target == "hibernate":
            settings.append(("hibernate-timeout-" + mode, seconds))

    previous_states = {}
    all_ok = True
    for alias, value in settings:
        prev = {"ac": None, "dc": None}
        if alias.startswith(("monitor", "standby")):
            prev = getScreenTimeout() if target == "screen" else getSleepTimeout()
        previous_states[alias] = prev

        result = run_command(["powercfg", "/change", alias, str(seconds)], timeout=30)
        if not result["success"]:
            all_ok = False

    if all_ok:
        global_progress.emit_complete(operation)
        logger.success(
            "set_timeout", module="power",
            command=", ".join([f"{a}={v}" for a, v in settings]),
            previous_state=str(previous_states),
            new_state=f"{target}=never",
        )
        return OperationResult.ok(
            f"{target} definido para nunca desligar."
        )
    return OperationResult.error(
        ErrorCode.OPERATION_FAILED, f"Falha ao configurar timeout de {target}."
    )


def restoreDefaultsPower() -> OperationResult:
    """Restaura esquemas de energia padrão."""
    if not isAdmin():
        return OperationResult.admin_required()

    result = run_command(["powercfg", "/restoredefaultschemes"], timeout=60)
    if result["success"]:
        return OperationResult.ok("Configurações de energia padrão restauradas.")
    return OperationResult.error(
        ErrorCode.OPERATION_FAILED, "Falha ao restaurar energia padrão.",
        result["stderr"].strip() or result["stdout"].strip(),
    )
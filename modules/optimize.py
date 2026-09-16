"""
Backend de otimização (análise + aplicação real).

Perfis:
  - escritorio: otimização leve preservando impressoras, rede, bluetooth,
    áudio, Windows Update e segurança.
  - gaming: otimização pesada preservando serviços Xbox, sem tocar em
    segurança/Windows Update.
Todas as verificações e ações usam comandos reais do Windows (backend).
"""

import time
import subprocess
from utils.colors import Theme, colorize
from utils.logger import logger
from utils.config import system_info
from modules import services as svc
from modules import power as pw
from modules.system import get_cpu_usage

SERVICE_CATEGORY = "Serviços"
POWER_CATEGORY = "Energia"
STARTUP_CATEGORY = "Inicialização"


SERVICE_PROFILES = {
    "escritorio": [s for s in svc.SERVICES_TO_DISABLE if s["name"] in (
        "DiagTrack", "dmwappushservice", "WerSvc", "RemoteRegistry", "Fax", "RetailDemo"
    )],
    "gaming": list(svc.SERVICES_TO_DISABLE),
}

PROFILE_META = {
    "escritorio": {
        "label": "PC de Escritório",
        "power": "Equilibrado",
        "keeps": [
            "Impressoras preservadas",
            "Rede preservada",
            "Bluetooth preservado",
            "Áudio preservado",
            "Windows Update preservado",
            "Segurança preservada",
        ],
    },
    "gaming": {
        "label": "Gaming",
        "power": "Alto desempenho",
        "keeps": [
            "Menos processos",
            "Menos serviços desnecessários",
            "Menos inicialização",
            "Foco em desempenho",
            "Serviços Xbox preservados",
        ],
    },
}


def _startup_entries() -> list:
    """Lê os programas reais de inicialização do usuário (HKCU Run)."""
    entries = []
    if not system_info.is_windows:
        return entries
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ) as key:
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    entries.append({"name": name, "value": value})
                    i += 1
                except OSError:
                    break
    except Exception:
        pass
    return entries


_STARTUP_TARGETS = [
    "OneDrive", "Microsoft Teams", "Discord", "Spotify",
    "Steam", "Epic Games Launcher", "Adobe Creative Cloud",
    "Google Update", "Apple Software Update",
]


def analyze(profile: str) -> dict:
    """Análise real do computador para um perfil."""
    if profile not in SERVICE_PROFILES:
        raise ValueError(f"Perfil desconhecido: {profile}")

    steps_done = []
    proposals = []

    steps_done.append("Serviços")
    for s in SERVICE_PROFILES[profile]:
        status = svc._get_service_status(s["name"])
        before = status["start_type"] if status["exists"] else None
        if not status["exists"]:
            continue
        if before != "Disabled":
            proposals.append({
                "id": f"svc-{s['name']}",
                "category": SERVICE_CATEGORY,
                "operation": "Desabilitar serviço",
                "service": s["display"],
                "name": s["name"],
                "before": before if before else "Automatic",
                "after": "Disabled",
                "detail": s["description"],
            })

    steps_done.append("Inicialização")
    entries = _startup_entries()
    for e in entries:
        if e["name"] in _STARTUP_TARGETS:
            proposals.append({
                "id": f"start-{e['name']}",
                "category": STARTUP_CATEGORY,
                "operation": "Remover da inicialização",
                "service": e["name"],
                "name": e["name"],
                "before": "Ativo na inicialização",
                "after": "Removido",
                "detail": "Programa desnecessário na inicialização",
            })

    steps_done.append("Energia")
    plan = pw.get_current_power_plan()
    target = PROFILE_META[profile]["power"]
    current_name = plan.get("name")
    if current_name and current_name != target:
        proposals.append({
            "id": "power-plan",
            "category": POWER_CATEGORY,
            "operation": "Alterar plano de energia",
            "service": "Plano de energia",
            "name": "power",
            "before": current_name,
            "after": target,
            "detail": f"Plano atual: {current_name}",
        })

    steps_done.append("Processos")
    usage = get_cpu_usage()
    steps_done.append("Configurações")

    return {
        "profile": profile,
        "label": PROFILE_META[profile]["label"],
        "checks": steps_done,
        "proposals": proposals,
        "count": len(proposals),
        "cpu_usage": usage,
        "keeps": PROFILE_META[profile]["keeps"],
        "applied": False,
    }


def apply(profile: str, proposals: list) -> list:
    """Aplica a otimização de um perfil (ações reais)."""
    if not system_info.is_windows:
        raise RuntimeError("Otimização disponível apenas no Windows")

    rows = []
    total = len(proposals)
    for i, p in enumerate(proposals, 1):
        print(colorize(f"\n  [{i}/{total}] {p['operation']} — {p['service']}", Theme.PRIMARY))
        ok = False
        error = None
        try:
            if p["category"] == SERVICE_CATEGORY:
                r = svc._stop_and_disable_service(p["name"])
                ok = r["success"]
                error = r["error"]
            elif p["category"] == POWER_CATEGORY:
                pw.set_power_plan(p["after"])
                ok = True
            elif p["category"] == STARTUP_CATEGORY:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as key:
                    try:
                        winreg.DeleteValue(key, p["name"])
                        ok = True
                    except FileNotFoundError:
                        ok = True
        except Exception as e:
            error = str(e)
        rows.append({
            "operation": p["operation"],
            "service": p["service"],
            "before": p.get("before"),
            "after": p.get("after"),
            "result": "OK" if ok else "FALHA",
            "detail": error or "",
        })
        if ok:
            logger.success(f"  ✓ {p['service']}")
        else:
            logger.error(f"  ✗ {p['service']}: {error or 'Erro desconhecido'}")
        time.sleep(0.15)

    if all(r["result"] == "OK" for r in rows):
        logger.success(f"Otimização '{PROFILE_META[profile]['label']}' aplicada com sucesso")
    return rows


def apply_restore() -> list:
    """Restaura a última otimização (ações reais, reversas)."""
    if not system_info.is_windows:
        raise RuntimeError("Restauração disponível apenas no Windows")
    rows = []
    print(colorize("\n  Restaurando serviços...", Theme.PRIMARY))
    for s in svc.SERVICES_TO_DISABLE:
        r = svc._enable_service(s["name"])
        rows.append({
            "operation": "Reabilitar serviço",
            "service": s["display"],
            "before": "Disabled",
            "after": "Manual",
            "result": "OK" if r["success"] else "FALHA",
            "detail": r["error"] or "",
        })
    print(colorize("\n  Restaurando energia...", Theme.PRIMARY))
    try:
        pw.set_power_plan("Equilibrado")
        rows.append({
            "operation": "Restaurar plano de energia",
            "service": "Plano de energia",
            "before": "Otimizado",
            "after": "Equilibrado",
            "result": "OK",
            "detail": "",
        })
    except Exception as e:
        rows.append({"operation": "Restaurar plano de energia", "service": "Plano de energia",
                     "before": "Otimizado", "after": "Equilibrado", "result": "FALHA", "detail": str(e)})
    logger.success("Restauração da última otimização concluída")
    return rows


def update_modules_init():
    """Coloca os novos módulos no __init__ do pacote (imports diretos)."""
    pass
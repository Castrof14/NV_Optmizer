"""
Módulo de energia do NV Optimizer.
Inclui leituras estruturadas e configuração real do plano de energia.
"""

import re
import subprocess
from utils.colors import Theme, colorize
from utils.logger import logger
from utils.config import system_info


POWER_SCHEMES = {
    "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c": "Alto desempenho",
    "381b4222-f694-41f0-9685-ff5bb260df2e": "Equilibrado",
    "a1841308-3541-4fab-bc81-f71556f20b4a": "Economia de energia",
    "e9a42b02-d5df-448d-aa00-03f14749eb61": "Alto desempenho (ultimate)",
}


def _sub(cmd: list, timeout: int = 15) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return ""


def scheme_guid(name: str) -> str | None:
    for guid, n in POWER_SCHEMES.items():
        if n.lower() == str(name).lower():
            return guid
    return None


def get_current_power_plan() -> dict:
    """Plano de energia ativo (leitura real via powercfg)."""
    result = {"name": "Não disponível", "guid": None, "available": False}
    if not system_info.is_windows:
        return result
    raw = _sub(["powercfg", "/getactivescheme"])
    m = re.search(r"([0-9a-f-]{36})\s*\((.*?)\)", raw)
    if m:
        result["guid"] = m.group(1)
        result["name"] = m.group(2).strip()
        result["available"] = True
    return result


def list_power_plans() -> list:
    """Lista de planos disponíveis (leitura real)."""
    plans = []
    if not system_info.is_windows:
        return plans
    raw = _sub(["powercfg", "/list"])
    for line in raw.split("\n"):
        m = re.search(r"([0-9a-f-]{36})\s*\((.*?)\)", line)
        if m:
            plans.append({"guid": m.group(1), "name": m.group(2).strip()})
    return plans


MONITOR_TIMEOUT_GUID = "7516b95f-f776-4464-8c53-06167f40cc99"  # SUB_VIDEO
SLEEP_TIMEOUT_GUID = "29f6c1db-86da-48c5-9fdb-f2b67b1f44da"      # SUB_SLEEP


def _query_index(subgroup: str, setting: str) -> int | None:
    """Lê o 'Current AC Power Setting Index' (em segundos) de uma configuração."""
    raw = _sub(["powercfg", "/query", "SCHEME_CURRENT", subgroup, setting])
    m = re.search(r"Current AC Power Setting Index:\s+0x([0-9a-fA-F]+)", raw)
    if not m:
        return None
    try:
        return int(m.group(1), 16)
    except ValueError:
        return None


def get_power_settings() -> dict:
    """Tela e suspensão atuais (minutos). 0 = nunca. Leitura real."""
    result = {"monitor": None, "sleep": None, "available": False}
    if not system_info.is_windows:
        return result
    try:
        mon = _query_index("SUB_VIDEO", MONITOR_TIMEOUT_GUID)
        slp = _query_index("SUB_SLEEP", SLEEP_TIMEOUT_GUID)
    except Exception:
        mon = slp = None
    result["monitor"] = round(mon / 60) if mon is not None else None
    result["sleep"] = round(slp / 60) if slp is not None else None
    result["available"] = True
    return result


def _fmt_minutes(minutes) -> str:
    if minutes is None:
        return "Nunca"
    if int(minutes) <= 0:
        return "Nunca"
    return f"{int(minutes)} min"


def set_power_plan(name: str):
    """Ativa um plano de energia pelo nome (ação real)."""
    if not system_info.is_windows:
        raise RuntimeError("Configuração de energia disponível apenas no Windows")
    guid = scheme_guid(name)
    if not guid:
        raise RuntimeError(f"Plano de energia desconhecido: {name}")
    r = subprocess.run(["powercfg", "/setactive", guid], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or f"Não foi possível ativar o plano {name}")
    logger.success(f"Plano de energia '{name}' ativado")


def set_screen_timeout(minutes: int | None):
    """Tempo de desligamento da tela em minutos (0 = nunca). Ação real."""
    if not system_info.is_windows:
        raise RuntimeError("Configuração de tela disponível apenas no Windows")
    minutes = 0 if minutes is None else int(minutes)
    r = subprocess.run(["powercfg", "/change", "monitor-timeout-ac", str(minutes)], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "Falha ao configurar tempo da tela")


def set_sleep_timeout(minutes: int | None):
    """Tempo de suspensão em minutos (0 = nunca). Ação real."""
    if not system_info.is_windows:
        raise RuntimeError("Configuração de suspensão disponível apenas no Windows")
    minutes = 0 if minutes is None else int(minutes)
    r = subprocess.run(["powercfg", "/change", "standby-timeout-ac", str(minutes)], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "Falha ao configurar tempo de suspensão")


def apply_power_config(plan: str, monitor: int | None, sleep: int | None):
    """Aplica plano + tela + suspensão de uma vez (ação real)."""
    if not system_info.is_windows:
        raise RuntimeError("Configuração de energia disponível apenas no Windows")
    set_power_plan(plan)
    if monitor is not None:
        set_screen_timeout(monitor)
    if sleep is not None:
        set_sleep_timeout(sleep)
    logger.success(f"Configuração de energia aplicada | Plano: {plan} | Tela: {_fmt_minutes(monitor)} | Suspensão: {_fmt_minutes(sleep)}")


def set_high_performance():
    """[80] Alto Desempenho"""
    print(colorize("\n  Configurando plano de Alto Desempenho...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        subprocess.run(
            ["powercfg", "/setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"],
            capture_output=True,
            timeout=30,
        )
        logger.success("Plano de Alto Desempenho ativado")
    except Exception as e:
        logger.error(f"Erro ao configurar energia: {e}")


def set_balanced():
    """[81] Equilibrado"""
    print(colorize("\n  Configurando plano Equilibrado...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        subprocess.run(
            ["powercfg", "/setactive", "381b4222-f694-41f0-9685-ff5bb260df2e"],
            capture_output=True,
            timeout=30,
        )
        logger.success("Plano Equilibrado ativado")
    except Exception as e:
        logger.error(f"Erro ao configurar energia: {e}")


def set_power_saver():
    """[82] Economia de Energia"""
    print(colorize("\n  Configurando plano Economia de Energia...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        subprocess.run(
            ["powercfg", "/setactive", "a1841308-3541-4fab-bc81-f71556f20b4a"],
            capture_output=True,
            timeout=30,
        )
        logger.success("Plano Economia de Energia ativado")
    except Exception as e:
        logger.error(f"Erro ao configurar energia: {e}")

"""
Camada de integração com o backend (respeita a arquitetura existente).

Cada função lê dados reais do sistema via modules/* e devolve dicionários
JSON-serializáveis prontos para a interface. Nenhuma lógica de SO fica aqui.
"""

import sys
from modules.system import collect_overview, get_cpu_usage, get_ram_usage, get_gpu_sample
from modules.power import get_current_power_plan, get_power_settings
from modules.security import get_defender_status
from modules.drivers import get_gpu_driver
from modules.programs import list_programs, check_all
from modules.office import get_status as office_get_status
from modules.diagnose import read_sample, stress
from modules.optimize import analyze as opt_analyze, PROFILE_META
from utils.config import system_info


def _na():
    return {"available": False}


def _map_available(data: dict) -> dict:
    if data.get("available") is None:
        data["available"] = True
    return data


def dashboard_load() -> dict:
    """Snapshot para a página Dashboard (todas as leituras reais)."""
    sys_name = system_info.so_name
    base = collect_overview()
    power = get_current_power_plan()
    defender = get_defender_status()
    driver = get_gpu_driver()
    settings = get_power_settings()
    ram_use = get_ram_usage()
    cpu_pct = get_cpu_usage()
    gpu = get_gpu_sample()

    overview = {
        "os": base.get("os", {"name": sys_name, "architecture": "—"}),
        "cpu": base.get("cpu", _na()),
        "gpu": base.get("gpu", _na()),
        "ram": base.get("ram", _na()),
        "disk": base.get("disk", _na()),
        "power": _map_available(power),
        "power_settings": _map_available(settings),
        "defender": defender,
        "driver": driver,
        "current_profile": None,
        "cpu_pct": cpu_pct,
        "gpu_sample": gpu,
        "ram_used": ram_use,
        "optimized": False,
        "available": True,
    }
    return overview


def programs_load():
    """Catálogo + status real de instalação."""
    cat = list_programs()
    status = check_all()
    by_key = {s["key"]: s["installed"] for s in status}
    for p in cat:
        p["status"] = by_key.get(p["key"])
    return cat


def power_state() -> dict:
    plan = get_current_power_plan()
    settings = get_power_settings()
    return {**plan, "monitor": settings.get("monitor"), "sleep": settings.get("sleep")}


def defender_state() -> dict:
    return get_defender_status()


def drivers_state() -> dict:
    return get_gpu_driver()


def office_state() -> dict:
    return office_get_status()


def stress_sample() -> dict:
    return read_sample()


def analyze(profile: str) -> dict:
    return opt_analyze(profile)
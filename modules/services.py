"""
Módulo de serviços do NV Optimizer.
Gerencia serviços do Windows.
"""

import subprocess
from utils.colors import Theme, colorize
from utils.logger import logger
from utils.config import system_info
from progress import progress_bar


# Serviços para desabilitar
SERVICES_TO_DISABLE = [
    {
        "name": "DiagTrack",
        "display": "Connected User Experiences and Telemetry",
        "description": "Desabilita coleta de telemetria do Windows",
    },
    {
        "name": "dmwappushservice",
        "display": "dmwappushservice",
        "description": "Serviço de envio de dados de diagnóstico",
    },
    {
        "name": "SysMain",
        "display": "SysMain",
        "description": "Desabilita pré-carregamento de aplicativos em segundo plano",
    },
    {
        "name": "MapsBroker",
        "display": "Downloaded Maps Manager",
        "description": "Desabilita mapas offline do Windows",
    },
    {
        "name": "RemoteRegistry",
        "display": "Remote Registry",
        "description": "Desabilita acesso remoto ao Registro do Windows",
    },
    {
        "name": "WerSvc",
        "display": "Windows Error Reporting Service",
        "description": "Desabilita envio automático de relatórios de erro",
    },
    {
        "name": "Fax",
        "display": "Fax",
        "description": "Desabilita serviço de fax",
    },
    {
        "name": "RetailDemo",
        "display": "Retail Demo Service",
        "description": "Desabilita modo demonstração de loja",
    },
    {
        "name": "WSearch",
        "display": "Windows Search",
        "description": "Desabilita indexação de arquivos para economizar recursos",
    },
]


def disable_unnecessary_services():
    """Desabilita serviços desnecessários do Windows."""
    print(colorize("\n  Desabilitando serviços desnecessários...\n", Theme.PRIMARY))

    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    total = len(SERVICES_TO_DISABLE)
    disabled = 0
    failed = 0

    for i, service in enumerate(SERVICES_TO_DISABLE, 1):
        progress_bar(i, total, prefix="  Processando:")
        print(f"\n    {colorize(service['display'], Theme.TEXT)}")
        print(f"    {colorize(service['description'], Theme.MUTED)}")

        result = _stop_and_disable_service(service["name"])
        if result["success"]:
            logger.success(f"  ✓ {service['display']} desabilitado")
            disabled += 1
        else:
            logger.warning(f"  ✗ {service['display']}: {result['error']}")
            failed += 1

    progress_bar(total, total, prefix="  Processando:")

    print()
    print(colorize("  ════════════════════════════════════════════", Theme.SUCCESS))
    print(colorize(f"  Serviços desabilitados: {disabled}/{total}", Theme.SUCCESS))
    if failed > 0:
        print(colorize(f"  Falhas: {failed}", Theme.WARNING))
    print(colorize("  ════════════════════════════════════════════", Theme.SUCCESS))


def list_disabled_services():
    """Lista o status dos serviços."""
    print(colorize("\n  Verificando status dos serviços...\n", Theme.PRIMARY))

    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    print(colorize("  ── SERVIÇOS ──", Theme.PRIMARY))
    print()

    for service in SERVICES_TO_DISABLE:
        status = _get_service_status(service["name"])
        if status["exists"]:
            if status["start_type"] == "Disabled":
                status_text = colorize("DESABILITADO", Theme.SUCCESS)
            elif status["start_type"] == "Running":
                status_text = colorize("EM EXECUÇÃO", Theme.WARNING)
            else:
                status_text = colorize(status["start_type"], Theme.TEXT)

            print(f"  {colorize(service['display'], Theme.TEXT)}")
            print(f"    Nome: {service['name']}")
            print(f"    Status: {status_text}")
            print()
        else:
            print(f"  {colorize(service['display'], Theme.TEXT)}")
            print(f"    {colorize('Não encontrado', Theme.MUTED)}")
            print()


def enable_all_services():
    """Reabilita todos os serviços que foram desabilitados."""
    print(colorize("\n  Reabilitando serviços...\n", Theme.PRIMARY))

    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    total = len(SERVICES_TO_DISABLE)
    enabled = 0

    for i, service in enumerate(SERVICES_TO_DISABLE, 1):
        progress_bar(i, total, prefix="  Reabilitando:")

        result = _enable_service(service["name"])
        if result["success"]:
            logger.success(f"  ✓ {service['display']} reabilitado")
            enabled += 1
        else:
            logger.warning(f"  ✗ {service['display']}: {result['error']}")

    progress_bar(total, total, prefix="  Reabilitando:")
    print()
    logger.success(f"Serviços reabilitados: {enabled}/{total}")


def _stop_and_disable_service(service_name: str) -> dict:
    """Para e desabilita um serviço."""
    try:
        # Parar o serviço
        subprocess.run(
            ["net", "stop", service_name],
            capture_output=True,
            timeout=30,
        )

        # Desabilitar o serviço
        result = subprocess.run(
            ["sc", "config", service_name, "start=", "disabled"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return {"success": True, "error": None}
        else:
            return {"success": False, "error": result.stderr.strip() or "Erro desconhecido"}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _enable_service(service_name: str) -> dict:
    """Reabilita um serviço."""
    try:
        result = subprocess.run(
            ["sc", "config", service_name, "start=", "demand"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return {"success": True, "error": None}
        else:
            return {"success": False, "error": result.stderr.strip() or "Erro desconhecido"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def _get_service_status(service_name: str) -> dict:
    """Obtém o status de um serviço."""
    try:
        result = subprocess.run(
            ["sc", "qc", service_name],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return {"exists": False, "start_type": None}

        start_type = "Unknown"
        for line in result.stdout.split("\n"):
            if "START_TYPE" in line:
                if "DISABLED" in line.upper():
                    start_type = "Disabled"
                elif "AUTO" in line.upper():
                    start_type = "Running"
                elif "DEMAND" in line.upper():
                    start_type = "Manual"
                break

        return {"exists": True, "start_type": start_type}

    except Exception:
        return {"exists": False, "start_type": None}

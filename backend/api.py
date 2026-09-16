"""
NV Optimizer 2.0 - API / IPC Layer
Interface organizada para o frontend consumir o backend.

Todas as operações retornam OperationResult (dict-padronizado) e
emitem eventos de progresso através de ProgressEmitter.

Nenhum comando arbitrário do frontend é executado: somente operações
registradas nesta API são permitidas.
"""

from .backend_core import OperationResult, ErrorCode, global_progress
from . import system as system_module
from . import software
from . import office
from . import security
from . import drivers
from . import power
from . import edge
from . import stress
from . import optimization
from . import backup
from .logger import logger


# =====================================================================
# SISTEMA
# =====================================================================

def get_system_info():
    """GET /system/info"""
    try:
        return OperationResult.ok(data=system_module.getSystemInfo())
    except Exception as e:
        return OperationResult.error(ErrorCode.OPERATION_FAILED, str(e))


def get_system_check():
    """Compatibilidade Windows 10/11"""
    try:
        return OperationResult.ok(data=system_module.checkSystem())
    except Exception as e:
        return OperationResult.error(ErrorCode.OPERATION_FAILED, str(e))


# =====================================================================
# PROGRAMAS
# =====================================================================

def get_programs():
    """GET /programs"""
    try:
        return software.getProgramsStatus()
    except Exception as e:
        return OperationResult.error(ErrorCode.OPERATION_FAILED, str(e))


def install_program(program_id):
    """POST /programs/install"""
    try:
        return software.installProgram(program_id)
    except Exception as e:
        return OperationResult.error(ErrorCode.OPERATION_FAILED, str(e))


# =====================================================================
# OFFICE
# =====================================================================

def get_office_status():
    """GET /office/status"""
    return office.getOfficeStatus()


def install_office():
    """POST /office/install"""
    return office.installOffice()


def check_office():
    """GET /office/check"""
    return OperationResult.ok(data=office.checkOffice())


def get_windows_activation():
    """GET /licensing/windows"""
    try:
        info = system_module.getWindowsInfo()
        return OperationResult.ok(data={
            "activation": info.get("activation", "unknown"),
            "edition": info.get("edition"),
        })
    except Exception as e:
        return OperationResult.error(ErrorCode.OPERATION_FAILED, str(e))


# =====================================================================
# WINDOWS DEFENDER
# =====================================================================

def get_defender_status():
    """GET /defender/status"""
    return OperationResult.ok(data=security.getDefenderStatus())


def enable_defender():
    """POST /defender/enable"""
    return security.enableDefender()


def disable_defender(confirm=False):
    """POST /defender/disable"""
    return security.disableDefender(confirm=confirm)


def update_defender_signatures():
    """POST /defender/update"""
    return security.updateSignatures()


def get_firewall_status():
    """GET /firewall/status"""
    return OperationResult.ok(data=security.checkFirewall())


# =====================================================================
# DRIVERS
# =====================================================================

def get_gpu_driver():
    """GET /drivers/gpu"""
    return drivers.getDisplayDrivers()


def find_gpu_driver():
    """POST /drivers/search"""
    return drivers.findGpuDriver()


def export_drivers():
    """POST /drivers/export"""
    return drivers.exportGpuDrivers()


# =====================================================================
# ENERGIA
# =====================================================================

def get_power_settings():
    """GET /power"""
    return power.getPowerSettings()


def apply_power_profile(high_performance=True, screen_never=True, sleep_never=True):
    """POST /power/apply"""
    return power.applyPowerProfile(
        high_performance=high_performance,
        screen_never=screen_never,
        sleep_never=sleep_never,
    )


def set_power_plan(plan):
    """POST /power/plan {plan: high_performance|balanced|power_saver}"""
    if plan == "high_performance":
        return power.setHighPerformance()
    if plan == "balanced":
        return power.setBalanced()
    if plan == "power_saver":
        return power.setPowerSaver()
    return OperationResult.error(ErrorCode.INVALID_INPUT, "Plano inválido.")


def set_screen_never():
    """POST /power/screen-never"""
    return power.setScreenNever()


def set_sleep_never():
    """POST /power/sleep-never"""
    return power.setSleepNever()


# =====================================================================
# STRESS TESTS
# =====================================================================

def start_stress(test_type, duration):
    """POST /stress/{test_type}"""
    return stress.stress_manager.start(
        test_type, duration,
        on_result=_stress_result_callback,
    )


def _stress_result_callback(result):
    if result.success:
        logger.success(
            f"stress-{result.data.get('test', '')}", module="stress",
            new_state="completed",
            details=result.data,
        )
    else:
        logger.error(
            f"stress", result.message, module="stress"
        )


def cancel_stress():
    """POST /stress/cancel"""
    return stress.stress_manager.cancel()


def get_stress_status():
    """GET /stress/status"""
    return stress.stress_manager.status()


def get_memory_diagnostic():
    """POST /stress/memory-diagnostic"""
    return stress.stressMemoryDiagnostic()


# =====================================================================
# OTIMIZAÇÃO
# =====================================================================

def analyze_optimization(profile):
    """POST /optimization/analyze"""
    return optimization.analyzeOptimization(profile)


def apply_optimization(profile, confirm=False):
    """POST /optimization/apply"""
    return optimization.applyOptimization(profile, confirm=confirm)


def restore_optimization(session_id):
    """POST /optimization/restore"""
    return optimization.restoreOptimizationBySession(session_id)


def list_restore_points():
    """GET /optimization/restore-points"""
    return backup.listRestorePoints()


def create_backup_session(profile):
    """POST /backup/create"""
    return backup.createOptimizationSession(profile)


# =====================================================================
# EDGE
# =====================================================================

def get_edge_status():
    """GET /edge"""
    return edge.getEdgeStatus()


def uninstall_edge(confirm=False):
    """POST /edge/uninstall"""
    return edge.uninstallEdge(confirm=confirm)


# =====================================================================
# LOGS
# =====================================================================

def get_logs(limit=200):
    """GET /logs"""
    return OperationResult.ok(data=logger.get_logs(limit))


def get_log_paths():
    """GET /logs/paths"""
    return OperationResult.ok(data=logger.get_log_paths())


def is_admin():
    """GET /admin/status"""
    return OperationResult.ok(data={
        "isAdmin": system_module.getSystemInfo()["platform"]["isAdmin"] if False else _is_admin(),
    })


def _is_admin():
    from .backend_core import isAdmin as _ia
    return _ia()


# =====================================================================
# ROTEADOR DE OPERAÇÕES (whitelist)
# =====================================================================

OPERATIONS = {
    "system.info": get_system_info,
    "system.check": get_system_check,
    "admin.status": is_admin,

    "programs.list": get_programs,
    "programs.install": install_program,

    "office.status": get_office_status,
    "office.check": check_office,
    "office.install": install_office,
    "licensing.windows": get_windows_activation,

    "defender.status": get_defender_status,
    "defender.enable": enable_defender,
    "defender.disable": disable_defender,
    "defender.update": update_defender_signatures,
    "firewall.status": get_firewall_status,

    "drivers.gpu": get_gpu_driver,
    "drivers.search": find_gpu_driver,
    "drivers.export": export_drivers,

    "power.settings": get_power_settings,
    "power.apply": apply_power_profile,
    "power.plan": set_power_plan,
    "power.screen-never": set_screen_never,
    "power.sleep-never": set_sleep_never,

    "stress.start": start_stress,
    "stress.cancel": cancel_stress,
    "stress.status": get_stress_status,
    "stress.memory-diagnostic": get_memory_diagnostic,

    "optimization.analyze": analyze_optimization,
    "optimization.apply": apply_optimization,
    "optimization.restore": restore_optimization,
    "optimization.restore-points": list_restore_points,
    "backup.create": create_backup_session,

    "edge.status": get_edge_status,
    "edge.uninstall": uninstall_edge,

    "logs.get": get_logs,
    "logs.paths": get_log_paths,
}


def dispatch(operation: str, **kwargs):
    """
    Ponto de entrada único para o frontend.

    Args:
        operation: chave whitelist (ex: 'defender.status', 'programs.install')
        **kwargs: parâmetros da operação

    Returns:
        dict padronizado com success/code/message/data
    """
    func = OPERATIONS.get(operation)
    if func is None:
        return OperationResult.error(
            ErrorCode.INVALID_INPUT,
            f"Operação não registrada: {operation}",
        ).to_dict()

    try:
        result = func(**kwargs)
        if isinstance(result, OperationResult):
            return result.to_dict()
        return OperationResult.ok(data=result).to_dict()
    except TypeError as e:
        return OperationResult.error(
            ErrorCode.INVALID_INPUT,
            f"Parâmetros inválidos para {operation}.",
            str(e),
        ).to_dict()
    except Exception as e:
        return OperationResult.error(
            ErrorCode.OPERATION_FAILED,
            f"Erro ao executar {operation}.",
            str(e),
        ).to_dict()


class BackendAPI:
    """Fachada principal do backend para o frontend."""

    def __init__(self):
        self.progress = global_progress
        self.operations = OPERATIONS

    def call(self, operation: str, **kwargs) -> dict:
        return dispatch(operation, **kwargs)

    def on_progress(self, callback):
        self.progress.on_progress(callback)

    def off_progress(self, callback):
        self.progress.off_progress(callback)

    # Atalhos tipados
    def system_info(self) -> dict:
        return self.call("system.info")

    def programs(self) -> dict:
        return self.call("programs.list")

    def install(self, program_id: str) -> dict:
        return self.call("programs.install", program_id=program_id)

    def office_status(self) -> dict:
        return self.call("office.status")

    def install_office(self) -> dict:
        return self.call("office.install")

    def defender_status(self) -> dict:
        return self.call("defender.status")

    def defender_enable(self) -> dict:
        return self.call("defender.enable")

    def defender_disable(self, confirm: bool = False) -> dict:
        return self.call("defender.disable", confirm=confirm)

    def power_settings(self) -> dict:
        return self.call("power.settings")

    def apply_power(self) -> dict:
        return self.call("power.apply")

    def analyze(self, profile: str) -> dict:
        return self.call("optimization.analyze", profile=profile)

    def apply_optimization(self, profile: str, confirm: bool = False) -> dict:
        return self.call("optimization.apply", profile=profile, confirm=confirm)

    def restore(self, session_id: str) -> dict:
        return self.call("optimization.restore", session_id=session_id)

    def restore_points(self) -> dict:
        return self.call("optimization.restore-points")

    def logs(self, limit: int = 200) -> dict:
        return self.call("logs.get", limit=limit)

    def stress(self, test_type: str, duration: int) -> dict:
        return self.call("stress.start", test_type=test_type, duration=duration)

    def cancel_stress(self) -> dict:
        return self.call("stress.cancel")


backend_api = BackendAPI()
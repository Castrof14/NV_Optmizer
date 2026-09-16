"""
NV Optimizer 2.0 - Core Backend
Funções fundamentais: admin, erros, progresso, segurança.
"""

import os
import sys
import ctypes
import platform
import subprocess
import threading
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional


class ErrorCode(str, Enum):
    SUCCESS = "SUCCESS"
    ADMIN_REQUIRED = "ADMIN_REQUIRED"
    NOT_WINDOWS = "NOT_WINDOWS"
    ALREADY_INSTALLED = "ALREADY_INSTALLED"
    NOT_FOUND = "NOT_FOUND"
    INSTALL_FAILED = "INSTALL_FAILED"
    UNSUPPORTED = "UNSUPPORTED"
    OPERATION_FAILED = "OPERATION_FAILED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"
    INVALID_INPUT = "INVALID_INPUT"


class OperationResult:
    """Resultado padronizado de operações do backend."""

    def __init__(
        self,
        success: bool,
        code: str = ErrorCode.SUCCESS,
        message: str = "",
        data: Any = None,
        details: Optional[str] = None,
    ):
        self.success = success
        self.code = code
        self.message = message
        self.data = data
        self.details = details
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        result = {
            "success": self.success,
            "code": self.code.value if isinstance(self.code, ErrorCode) else str(self.code),
            "message": self.message,
            "timestamp": self.timestamp,
        }
        if self.data is not None:
            result["data"] = self.data
        if self.details:
            result["details"] = self.details
        return result

    @classmethod
    def ok(cls, message: str = "Operação concluída", data: Any = None) -> "OperationResult":
        return cls(success=True, code=ErrorCode.SUCCESS, message=message, data=data)

    @classmethod
    def error(cls, code: str, message: str, details: str = None) -> "OperationResult":
        return cls(success=False, code=code, message=message, details=details)

    @classmethod
    def admin_required(cls, message: str = "Privilégios administrativos são necessários.") -> "OperationResult":
        return cls(success=False, code=ErrorCode.ADMIN_REQUIRED, message=message)

    @classmethod
    def not_windows(cls) -> "OperationResult":
        return cls(success=False, code=ErrorCode.NOT_WINDOWS, message="Esta operação é exclusiva do Windows.")

    @classmethod
    def already_installed(cls, program: str) -> "OperationResult":
        return cls(success=True, code=ErrorCode.ALREADY_INSTALLED, message=f"{program} já está instalado.")

    @classmethod
    def unsupported(cls, reason: str) -> "OperationResult":
        return cls(success=False, code=ErrorCode.UNSUPPORTED, message=reason)


def isAdmin() -> bool:
    """Verifica se o programa está sendo executado como administrador."""
    try:
        if platform.system() == "Windows":
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except Exception:
        return False


def require_admin(func: Callable) -> Callable:
    """Decorator que verifica privilégios de administrador antes de executar."""
    def wrapper(*args, **kwargs):
        if not isAdmin():
            return OperationResult.admin_required()
        return func(*args, **kwargs)
    return wrapper


class ProgressEmitter:
    """Emite eventos de progresso para o frontend."""

    def __init__(self):
        self._listeners: list[Callable] = []
        self._lock = threading.Lock()

    def on_progress(self, callback: Callable):
        with self._lock:
            self._listeners.append(callback)

    def off_progress(self, callback: Callable):
        with self._lock:
            self._listeners = [l for l in self._listeners if l is not callback]

    def emit(self, operation: str, progress: int, status: str, message: str = ""):
        event = {
            "operation": operation,
            "progress": min(max(progress, 0), 100),
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        with self._lock:
            for listener in self._listeners:
                try:
                    listener(event)
                except Exception:
                    pass

    def emit_start(self, operation: str, message: str = "Iniciando..."):
        self.emit(operation, 0, "starting", message)

    def emit_progress(self, operation: str, percent: int, message: str = ""):
        self.emit(operation, percent, "in_progress", message)

    def emit_complete(self, operation: str, message: str = "Concluído"):
        self.emit(operation, 100, "completed", message)

    def emit_error(self, operation: str, message: str = "Erro"):
        self.emit(operation, 0, "error", message)


class SecurityValidator:
    """Valida e sanitiza inputs para operações do backend."""

    ALLOWED_PROGRAMS = {
        "anydesk": "AnyDesk",
        "winrar": "WinRAR",
        "7zip": "7-Zip",
        "notepadpp": "Notepad++",
        "brave": "Brave",
        "chrome": "Google Chrome",
        "steam": "Steam",
        "epic": "Epic Games Launcher",
    }

    ALLOWED_POWERSHELL_COMMANDS = {
        "Get-MpComputerStatus",
        "Update-MpSignature",
        "Get-Service",
        "Set-Service",
        "Get-Process",
        "Get-CimInstance",
        "Get-WmiObject",
        "Get-ItemProperty",
        "Set-ItemProperty",
        "Enable-ComputerRestore",
        "Checkpoint-Computer",
    }

    @classmethod
    def validate_program(cls, program_id: str) -> Optional[str]:
        """Valida ID do programa. Retorna nome legítimo ou None."""
        return cls.ALLOWED_PROGRAMS.get(program_id.lower())

    @classmethod
    def validate_powershell(cls, command: str) -> bool:
        """Verifica se comando PowerShell é permitido."""
        cmd_stripped = command.strip()
        for allowed in cls.ALLOWED_POWERSHELL_COMMANDS:
            if cmd_stripped.startswith(allowed):
                return True
        return False

    @classmethod
    def sanitize_path(cls, path: str) -> str:
        """Remove caracteres perigosos de caminhos."""
        dangerous = ["|", "&", ";", "$", "`"]
        result = path
        for char in dangerous:
            result = result.replace(char, "")
        return result


def run_command(
    cmd: list,
    timeout: int = 60,
    capture: bool = True,
    shell: bool = False,
) -> dict:
    """Executa comando do sistema de forma segura e padronizada."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            timeout=timeout,
            shell=shell,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout if capture else "",
            "stderr": result.stderr if capture else "",
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Timeout",
            "returncode": -1,
        }
    except FileNotFoundError:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Comando não encontrado: {cmd[0] if cmd else 'vazio'}",
            "returncode": -1,
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
        }


def run_powershell(
    command: str,
    timeout: int = 60,
    elevated: bool = False,
) -> dict:
    """Executa comando PowerShell de forma segura."""
    if not SecurityValidator.validate_powershell(command):
        return {
            "success": False,
            "stdout": "",
            "stderr": "Comando PowerShell não autorizado",
            "returncode": -1,
        }

    ps_cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", command]
    return run_command(ps_cmd, timeout=timeout)


def get_wmic_value(query: str, field: str, default: str = "N/A") -> str:
    """Obtém valor de query WMIC de forma padronizada."""
    try:
        result = subprocess.run(
            ["wmic"] + query.split() + ["/format:list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in result.stdout.strip().split("\n"):
            if field.upper() in line.upper() and "=" in line:
                value = line.split("=", 1)[1].strip()
                if value:
                    return value
    except Exception:
        pass
    return default


global_progress = ProgressEmitter()

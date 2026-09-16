"""
Módulo de logging do NV Optimizer.
Fornece funções para registro de ações com cores.
"""

import os
from datetime import datetime
from .colors import Colors, Theme, colorize


class Logger:
    """Logger colorido para o terminal."""

    def __init__(self, log_to_file: bool = False):
        self.log_to_file = log_to_file
        self.log_entries = []

    def _timestamp(self) -> str:
        return datetime.now().strftime("%H:%M:%S")

    def _log(self, message: str, msg_type: str = "INFO", color: str = Colors.WHITE):
        ts = self._timestamp()
        prefix_map = {
            "SUCCESS": "OK",
            "WARNING": "AVISO",
            "ERROR": "ERRO",
            "INFO": "INFO",
        }
        prefix = prefix_map.get(msg_type, "INFO")
        formatted = f"[{ts}] {prefix}: {message}"
        print(colorize(formatted, color))
        self.log_entries.append({"time": ts, "type": msg_type, "message": message})

    def success(self, message: str):
        self._log(message, "SUCCESS", Theme.SUCCESS)

    def warning(self, message: str):
        self._log(message, "WARNING", Theme.WARNING)

    def error(self, message: str):
        self._log(message, "ERROR", Theme.ERROR)

    def info(self, message: str):
        self._log(message, "INFO", Theme.INFO)

    def step(self, current: int, total: int, message: str):
        phase = f"[Fase {current}/{total}]"
        print(colorize(f"{phase} {message}", Theme.PRIMARY))

    def clear(self):
        self.log_entries.clear()

    def get_summary(self) -> list:
        return self.log_entries.copy()


logger = Logger()

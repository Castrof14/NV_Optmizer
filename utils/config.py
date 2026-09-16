"""
Módulo de configuração do NV Optimizer.
Detecta SO e configura o ambiente.
"""

import os
import sys
import platform


class SystemInfo:
    """Informações do sistema detectado."""

    def __init__(self):
        self.os_name = platform.system()
        self.os_release = platform.release()
        self.os_version = platform.version()
        self.architecture = platform.machine()
        self.python_version = platform.python_version()
        self.hostname = platform.node()

    @property
    def is_windows(self) -> bool:
        return self.os_name == "Windows"

    @property
    def is_macos(self) -> bool:
        return self.os_name == "Darwin"

    @property
    def is_linux(self) -> bool:
        return self.os_name == "Linux"

    @property
    def so_name(self) -> str:
        if self.is_windows:
            return "Windows"
        elif self.is_macos:
            return "macOS"
        elif self.is_linux:
            return "Linux"
        return "Desconhecido"

    def display_info(self) -> str:
        return (
            f"{self.so_name} {self.os_release} ({self.os_version})\n"
            f"Arquitetura: {self.architecture}\n"
            f"Python: {self.python_version}\n"
            f"Hostname: {self.hostname}"
        )


class Config:
    """Configurações gerais do aplicativo."""

    APP_NAME = "NV OPTIMIZER"
    VERSION = "1.0.0"
    AUTHOR = "NV"

    # Dimensões
    MENU_WIDTH = 50
    PROGRESS_WIDTH = 30

    # Símbolos
    SYMBOL_CHECK = "✓"
    SYMBOL_CROSS = "✗"
    SYMBOL_ARROW = "►"
    SYMBOL_BULLET = "•"
    SYMBOL_LINE = "═"
    SYMBOL_DOT = "░"
    SYMBOL_FILLED = "█"
    SYMBOL_EMPTY = "░"

    # Caracteres da barra de progresso
    PROGRESS_FILLED = "█"
    PROGRESS_EMPTY = "░"

    # Tempos de espera (segundos)
    WAIT_AFTER_ACTION = 2
    WAIT_ENTER_PROMPT = 0

    # Configurações do sistema
    system = SystemInfo()

    @classmethod
    def clear_screen(cls):
        """Limpa a tela do terminal."""
        os.system("cls" if cls.system.is_windows else "clear")

    @classmethod
    def pause(cls, message: str = "Pressione ENTER para continuar..."):
        """Pausa a execução até o usuário pressionar ENTER."""
        try:
            input(f"\n{message}")
        except (EOFError, KeyboardInterrupt):
            pass

    @classmethod
    def get_input(cls, prompt: str = "Digite a opção: ") -> str:
        """Obtém entrada do usuário."""
        try:
            return input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            return ""


system_info = SystemInfo()
config = Config()

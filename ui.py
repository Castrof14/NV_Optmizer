"""
Módulo de interface do usuário do NV Optimizer.
Fornece funções para exibição de menus, caixas e elementos visuais.
"""

import os
from utils.colors import Colors, Theme, colorize, bold, dim, primary, accent, muted
from utils.config import Config, system_info


def clear_screen():
    """Limpa a tela do terminal."""
    Config.clear_screen()


def print_separator(char: str = "═", length: int = None):
    """Imprime uma linha separadora."""
    if length is None:
        length = Config.MENU_WIDTH
    print(colorize(char * length, Theme.PRIMARY))


def print_header(title: str, width: int = None):
    """Imprime um cabeçalho estilizado."""
    if width is None:
        width = Config.MENU_WIDTH
    print()
    print_separator("═", width)
    print(colorize(f"  {title}", Theme.HEADER))
    print_separator("═", width)
    print()


def print_box(lines: list, width: int = None):
    """Imprime texto dentro de uma caixa."""
    if width is None:
        width = Config.MENU_WIDTH

    print(colorize("╔" + "═" * (width - 2) + "╗", Theme.PRIMARY))

    for line in lines:
        padding = width - 4 - len(line)
        if padding < 0:
            padding = 0
        print(colorize("║", Theme.PRIMARY) + f" {line}" + " " * padding + colorize("║", Theme.PRIMARY))

    print(colorize("╚" + "═" * (width - 2) + "╝", Theme.PRIMARY))


def print_option(number: int, description: str, available: bool = True):
    """Imprime uma opção do menu."""
    num = colorize(f"[{number}]", Theme.ACCENT)
    if available:
        desc = colorize(description, Theme.TEXT)
    else:
        desc = dim(description) + colorize(" (Windows)", Theme.MUTED)
    print(f"  {num} {desc}")


def print_success(message: str):
    """Imprime mensagem de sucesso."""
    icon = colorize(Config.SYMBOL_CHECK, Theme.SUCCESS)
    print(f"  {icon} {colorize(message, Theme.SUCCESS)}")


def print_warning(message: str):
    """Imprime mensagem de aviso."""
    icon = colorize(Config.SYMBOL_CROSS, Theme.WARNING)
    print(f"  {icon} {colorize(message, Theme.WARNING)}")


def print_error(message: str):
    """Imprime mensagem de erro."""
    icon = colorize(Config.SYMBOL_CROSS, Theme.ERROR)
    print(f"  {icon} {colorize(message, Theme.ERROR)}")


def print_info(message: str):
    """Imprime mensagem informativa."""
    icon = colorize(Config.SYMBOL_ARROW, Theme.INFO)
    print(f"  {icon} {colorize(message, Theme.INFO)}")


def print_muted(message: str):
    """Imprime texto secundário."""
    print(f"  {muted(message)}")


def get_system_info_box() -> list:
    """Retorna informações do sistema formatadas."""
    si = system_info
    return [
        colorize("Sistema:", Theme.ACCENT) + f" {si.so_name} {si.os_release}",
        colorize("Arquitetura:", Theme.ACCENT) + f" {si.architecture}",
        colorize("Python:", Theme.ACCENT) + f" {si.python_version}",
    ]


def print_system_info():
    """Imprime informações do sistema em uma caixa."""
    print_header("INFORMAÇÕES DO SISTEMA")
    print_box(get_system_info_box())
    print()

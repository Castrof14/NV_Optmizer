"""
Módulo de cores ANSI para terminal.
Fornece constantes e funções para formatação de texto colorido.
"""


class Colors:
    """Cores ANSI padrão."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Cores de texto
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

    # Cores de fundo
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # Cores brilhantes
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # True Color (24-bit) - Cores personalizadas NV
    NV_BLUE = "\033[38;2;0;17;255m"      # #0011FF
    NV_YELLOW = "\033[38;2;255;238;0m"    # #FFEE00
    BG_NV_BLUE = "\033[48;2;0;17;255m"    # Fundo #0011FF
    BG_NV_YELLOW = "\033[48;2;255;238;0m" # Fundo #FFEE00


class Theme:
    """Tema de cores do NV Optimizer."""
    PRIMARY = Colors.NV_BLUE      # Azul #0011FF
    ACCENT = Colors.NV_YELLOW     # Amarelo #FFEE00
    SUCCESS = Colors.BRIGHT_GREEN
    WARNING = Colors.BRIGHT_YELLOW
    ERROR = Colors.BRIGHT_RED
    INFO = Colors.CYAN
    TEXT = Colors.WHITE
    MUTED = Colors.GRAY
    HEADER = Colors.BOLD + Colors.NV_BLUE
    BOLD = Colors.BOLD


def colorize(text: str, color: str) -> str:
    """Aplica cor a um texto."""
    return f"{color}{text}{Colors.RESET}"


def bold(text: str) -> str:
    """Aplica negrito ao texto."""
    return f"{Colors.BOLD}{text}{Colors.RESET}"


def dim(text: str) -> str:
    """Aplica dim ao texto."""
    return f"{Colors.DIM}{text}{Colors.RESET}"


def success(text: str) -> str:
    """Cor de sucesso (verde)."""
    return colorize(text, Theme.SUCCESS)


def warning(text: str) -> str:
    """Cor de aviso (amarelo)."""
    return colorize(text, Theme.WARNING)


def error(text: str) -> str:
    """Cor de erro (vermelho)."""
    return colorize(text, Theme.ERROR)


def info(text: str) -> str:
    """Cor de informação (ciano)."""
    return colorize(text, Theme.INFO)


def primary(text: str) -> str:
    """Cor primária (azul)."""
    return colorize(text, Theme.PRIMARY)


def accent(text: str) -> str:
    """Cor de destaque (amarelo)."""
    return colorize(text, Theme.ACCENT)


def muted(text: str) -> str:
    """Cor secundária (cinza)."""
    return colorize(text, Theme.MUTED)


def enable_ansi_windows():
    """Habilita suporte ANSI no Windows."""
    try:
        import os
        os.system("")
    except Exception:
        pass


enable_ansi_windows()

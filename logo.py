"""
Módulo de logo ASCII art do NV Optimizer.
Exibe o logo colorido no terminal.
"""

from utils.colors import Colors, colorize


# Logo ASCII art - NV (N azul, V amarelo)
LOGO_LINES = [
    colorize("███╗   ██╗ ", Colors.NV_BLUE) + colorize("██╗   ██╗", Colors.NV_YELLOW),
    colorize("████╗  ██║ ", Colors.NV_BLUE) + colorize("██║   ██║", Colors.NV_YELLOW),
    colorize("██╔██╗ ██║ ", Colors.NV_BLUE) + colorize("██║   ██║", Colors.NV_YELLOW),
    colorize("██║╚██╗██║ ", Colors.NV_BLUE) + colorize("╚██╗ ██╔╝", Colors.NV_YELLOW),
    colorize("██║ ╚████║ ", Colors.NV_BLUE) + colorize(" ╚████╔╝ ", Colors.NV_YELLOW),
    colorize("╚═╝  ╚═══╝ ", Colors.NV_BLUE) + colorize("  ╚═══╝  ", Colors.NV_YELLOW),
]


def get_logo() -> str:
    """Retorna o logo formatado com cores."""
    return "\n".join(LOGO_LINES)


def get_banner() -> str:
    """Retorna o banner completo com logo e informações."""
    from utils.config import Config

    logo = get_logo()
    title = colorize(f"        {Config.APP_NAME}", Colors.NV_BLUE + Colors.BOLD)
    version = colorize(f"        Versão {Config.VERSION}", Colors.NV_YELLOW)
    separator = colorize("=" * 50, Colors.NV_BLUE)

    return f"""
{logo}
{title}
{version}

{separator}
"""


def display_logo():
    """Exibe o logo na tela."""
    print(get_banner())


def display_mini_logo():
    """Exibe uma versão menor do logo."""
    n = colorize("N", Colors.NV_BLUE + Colors.BOLD)
    v = colorize("V", Colors.NV_YELLOW + Colors.BOLD)
    print(f"  ╔══{n}{v}══╗")
    print(f"  ║ {colorize('OPTIMIZER', Colors.NV_YELLOW)} ║")
    print(colorize(f"  ╚═════════╝", Colors.NV_BLUE))

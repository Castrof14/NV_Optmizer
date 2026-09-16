"""
Módulo de barras de progresso do NV Optimizer.
Fornece diferentes estilos de exibição de progresso.
"""

import sys
import time
from utils.colors import Colors, Theme, colorize


def progress_bar(
    current: int,
    total: int,
    width: int = 30,
    prefix: str = "",
    suffix: str = "",
    fill_char: str = "█",
    empty_char: str = "░",
    show_percent: bool = True,
    color: str = None,
):
    """
    Exibe uma barra de progresso.

    Args:
        current: Valor atual
        total: Valor total
        width: Largura da barra em caracteres
        prefix: Texto antes da barra
        suffix: Texto após a barra
        fill_char: Caractere preenchido
        empty_char: Caractere vazio
        show_percent: Mostrar porcentagem
        color: Cor da barra
    """
    if color is None:
        color = Theme.PRIMARY

    percent = float(current) / float(total) if total > 0 else 0
    filled_length = int(width * percent)
    bar = fill_char * filled_length + empty_char * (width - filled_length)

    if show_percent:
        percent_text = f" {int(percent * 100)}%"
    else:
        percent_text = ""

    line = f"\r{prefix} {colorize(bar, color)}{percent_text}{suffix}"
    sys.stdout.write(line)
    sys.stdout.flush()

    if current >= total:
        print()


def progress_bar_block(
    current: int,
    total: int,
    width: int = 30,
    prefix: str = "",
    color: str = None,
):
    """Barra de progresso estilo bloco com porcentagem."""
    progress_bar(
        current=current,
        total=total,
        width=width,
        prefix=prefix,
        fill_char=Config.PROGRESS_FILLED if 'Config' in dir() else "█",
        empty_char=Config.PROGRESS_EMPTY if 'Config' in dir() else "░",
        show_percent=True,
        color=color,
    )


def progress_bar_bracket(
    current: int,
    total: int,
    width: int = 30,
    prefix: str = "",
    color: str = None,
):
    """Barra de progresso estilo colchetes."""
    if color is None:
        color = Theme.PRIMARY

    percent = float(current) / float(total) if total > 0 else 0
    filled_length = int(width * percent)
    bar = "#" * filled_length + "." * (width - filled_length)

    percent_text = f" {int(percent * 100)}%"
    line = f"\r{prefix} [{colorize(bar, color)}]{percent_text}"
    sys.stdout.write(line)
    sys.stdout.flush()

    if current >= total:
        print()


def animated_progress(
    total: int,
    duration: float = 2.0,
    prefix: str = "",
    steps: int = 50,
    color: str = None,
):
    """Exibe uma animação de progresso simulada."""
    if color is None:
        color = Theme.PRIMARY

    step_time = duration / steps

    for i in range(steps + 1):
        progress_bar(
            current=i,
            total=steps,
            width=30,
            prefix=prefix,
            color=color,
        )
        time.sleep(step_time)


def spinner(message: str, duration: float = 1.0):
    """Exibe um spinner animado."""
    spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    start_time = time.time()

    try:
        while time.time() - start_time < duration:
            for char in spinner_chars:
                sys.stdout.write(f"\r  {colorize(char, Theme.PRIMARY)} {message}")
                sys.stdout.flush()
                time.sleep(0.1)
    except KeyboardInterrupt:
        pass

    sys.stdout.write(f"\r  {colorize('✓', Theme.SUCCESS)} {message}\n")
    sys.stdout.flush()


def step_progress(steps: list, step_delay: float = 0.5):
    """
    Exibe progresso passo a passo.

    Args:
        steps: Lista de (mensagem, função_callback)
        step_delay: Delay entre passos
    """
    total = len(steps)
    for i, (message, callback) in enumerate(steps, 1):
        print(colorize(f"\n[Fase {i}/{total}]", Theme.PRIMARY) + f" {message}")
        if callback:
            callback()
        time.sleep(step_delay)


def print_completion_bar(label: str = "Concluído", width: int = 40):
    """Imprime uma barra de conclusão 100%."""
    bar = Config.PROGRESS_FILLED * width if hasattr(Config, 'PROGRESS_FILLED') else "█" * width
    print(f"\n  {colorize(label, Theme.SUCCESS)}: {colorize(bar, Theme.SUCCESS)} 100%")

"""
Módulo avançado do NV Optimizer.
Modos especiais e limpeza completa.
"""

import subprocess
import time
from utils.colors import Theme, colorize
from utils.logger import logger
from utils.config import system_info
from progress import progress_bar, animated_progress
from modules.cleanup import clean_temp_files, clean_prefetch, clean_windows_update_cache, clean_logs, clean_browser_cache, clean_thumbnails
from modules.disk import optimize_disk, trim_ssd, optimize_startup, clean_startup_programs
from modules.network import flush_dns, reset_network, reset_winsock
from modules.repair import run_sfc, run_dism


def run_all_optimizations():
    """[120] Executar Todas as Otimizações"""
    print(colorize("\n  Executando todas as otimizações...\n", Theme.PRIMARY))

    steps = [
        ("Limpando arquivos temporários", clean_temp_files),
        ("Limpando Prefetch", clean_prefetch),
        ("Limpando Cache do Windows Update", clean_windows_update_cache),
        ("Limpando Logs", clean_logs),
        ("Limpando Cache dos Navegadores", clean_browser_cache),
        ("Limpando Miniaturas", clean_thumbnails),
        ("Otimizando Disco", optimize_disk),
        ("Executando TRIM", trim_ssd),
        ("Limpando DNS", flush_dns),
        ("Reparando Sistema", run_sfc),
    ]

    for i, (name, func) in enumerate(steps, 1):
        print()
        print(colorize(f"\n  [{i}/{len(steps)}] {name}...", Theme.PRIMARY))
        try:
            func()
        except Exception as e:
            logger.error(f"Erro em {name}: {e}")
        time.sleep(0.5)

    print()
    print(colorize("  ════════════════════════════════════════════", Theme.SUCCESS))
    print(colorize("  TODAS AS OTIMIZAÇÕES CONCLUÍDAS!", Theme.SUCCESS))
    print(colorize("  ════════════════════════════════════════════", Theme.SUCCESS))


def gamer_mode():
    """[121] Modo Gamer"""
    print(colorize("\n  Ativando Modo Gamer...\n", Theme.PRIMARY))

    steps = [
        ("Configurando plano de Alto Desempenho", _set_high_performance),
        ("Otimizando Disco para jogos", optimize_disk),
        ("Executando TRIM no SSD", trim_ssd),
        ("Otimizando Inicialização", optimize_startup),
        ("Limpando DNS para menor latência", flush_dns),
    ]

    for i, (name, func) in enumerate(steps, 1):
        progress_bar(i, len(steps), prefix="  Configurando:")
        print(f"\n    {name}...")
        try:
            func()
        except Exception as e:
            logger.error(f"Erro: {e}")
        time.sleep(0.3)

    progress_bar(len(steps), len(steps), prefix="  Configurando:")
    print()
    print(colorize("  ════════════════════════════════════════════", Theme.SUCCESS))
    print(colorize("  MODO GAMER ATIVADO!", Theme.SUCCESS))
    print(colorize("  Reinicie para aplicar todas as mudanças", Theme.ACCENT))
    print(colorize("  ════════════════════════════════════════════", Theme.SUCCESS))


def work_mode():
    """[122] Modo Trabalho"""
    print(colorize("\n  Ativando Modo Trabalho...\n", Theme.PRIMARY))

    steps = [
        ("Configurando plano Equilibrado", _set_balanced),
        ("Verificando programas de inicialização", optimize_startup),
        ("Limpando DNS", flush_dns),
    ]

    for i, (name, func) in enumerate(steps, 1):
        progress_bar(i, len(steps), prefix="  Configurando:")
        print(f"\n    {name}...")
        try:
            func()
        except Exception as e:
            logger.error(f"Erro: {e}")
        time.sleep(0.3)

    progress_bar(len(steps), len(steps), prefix="  Configurando:")
    print()
    print(colorize("  ════════════════════════════════════════════", Theme.SUCCESS))
    print(colorize("  MODO TRABALHO ATIVADO!", Theme.SUCCESS))
    print(colorize("  ════════════════════════════════════════════", Theme.SUCCESS))


def restore_defaults():
    """[123] Restaurar Configurações"""
    print(colorize("\n  Restaurando configurações padrão...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        subprocess.run(["powercfg", "/restoredefaultschemes"], capture_output=True, timeout=30)
        logger.success("Configurações de energia restauradas")
    except Exception as e:
        logger.error(f"Erro ao restaurar: {e}")


def full_cleanup():
    """[124] Limpeza Completa"""
    print(colorize("\n  Executando limpeza completa...\n", Theme.PRIMARY))

    steps = [
        ("Limpando Arquivos Temporários", clean_temp_files),
        ("Limpando Lixeira", _clean_recycle_bin),
        ("Limpando Prefetch", clean_prefetch),
        ("Limpando Cache do Windows Update", clean_windows_update_cache),
        ("Limpando Logs", clean_logs),
        ("Limpando Cache dos Navegadores", clean_browser_cache),
        ("Limpando Miniaturas", clean_thumbnails),
    ]

    for i, (name, func) in enumerate(steps, 1):
        progress_bar(i, len(steps), prefix="  Limpando:")
        print(f"\n    {name}...")
        try:
            func()
        except Exception as e:
            logger.error(f"Erro: {e}")
        time.sleep(0.3)

    progress_bar(len(steps), len(steps), prefix="  Limpando:")
    print()
    print(colorize("  ════════════════════════════════════════════", Theme.SUCCESS))
    print(colorize("  LIMPEZA COMPLETA CONCLUÍDA!", Theme.SUCCESS))
    print(colorize("  ════════════════════════════════════════════", Theme.SUCCESS))


def _set_high_performance():
    if system_info.is_windows:
        subprocess.run(["powercfg", "/setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"], capture_output=True, timeout=30)


def _set_balanced():
    if system_info.is_windows:
        subprocess.run(["powercfg", "/setactive", "381b4222-f694-41f0-9685-ff5bb260df2e"], capture_output=True, timeout=30)


def _clean_recycle_bin():
    if system_info.is_windows:
        try:
            import ctypes
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
            logger.success("Lixeira esvaziada")
        except Exception:
            pass

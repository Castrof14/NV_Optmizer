#!/usr/bin/env python3
"""
NV Optimizer 2.0 - Otimizador de Sistema
Ponto de entrada principal do aplicativo.

Uso:
    python main.py          → Interface gráfica (GUI)
    python main.py --cli    → Modo terminal (CLI legado)
"""

import sys
import os

# Adicionar diretório pai ao path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def launch_gui():
    """Inicia a interface gráfica do NV Optimizer 2.0."""
    from frontend.app import NVOptimizerApp
    app = NVOptimizerApp()
    app.mainloop()


def launch_cli():
    """Inicia o modo terminal (legado)."""
    from menu import main_loop
    from logo import display_logo
    from ui import clear_screen, print_header, print_error
    from utils.config import Config, system_info
    from utils.colors import Theme, colorize

    def check_admin():
        try:
            if system_info.is_windows:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except Exception:
            return False

    def print_admin_warning():
        print()
        print(colorize("  ╔══════════════════════════════════════════════╗", Theme.WARNING))
        print(colorize("  ║  AVISO: Execute como Administrador/root      ║", Theme.WARNING))
        print(colorize("  ║  Algumas otimizações podem não funcionar    ║", Theme.WARNING))
        print(colorize("  ║  sem privilégios elevados.                  ║", Theme.WARNING))
        print(colorize("  ╚══════════════════════════════════════════════╝", Theme.WARNING))
        print()

    try:
        clear_screen()
        display_logo()
        if not check_admin():
            print_admin_warning()
        Config.pause("Pressione ENTER para iniciar...")
        main_loop()
    except KeyboardInterrupt:
        print()
        print(colorize("\n  Saindo do NV Optimizer...", Theme.MUTED))
        sys.exit(0)
    except Exception as e:
        print_error(f"Erro fatal: {e}")
        sys.exit(1)


def main():
    """Ponto de entrada principal."""
    if "--cli" in sys.argv:
        launch_cli()
    else:
        launch_gui()


if __name__ == "__main__":
    main()

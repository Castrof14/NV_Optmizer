#!/usr/bin/env python3
"""
Script de build para NV Optimizer 2.0.
Gera executável usando PyInstaller.
"""

import os
import sys
import platform
import subprocess


def build():
    """Gera executável do NV Optimizer."""
    print("=" * 50)
    print("  NV Optimizer 2.0 - Build Script")
    print("=" * 50)
    print()

    # Verificar se PyInstaller está instalado
    try:
        import PyInstaller
        print(f"PyInstaller versão: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller não encontrado. Instalando...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Configurações de build
    system = platform.system()
    app_name = "NV Optimizer"

    if system == "Windows":
        ext = ".exe"
        icon = None
    elif system == "Darwin":
        ext = ""
        icon = None
    else:
        ext = ""
        icon = None

    # Comando PyInstaller
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--clean",
        "--name", app_name,
    ]

    if icon and os.path.exists(icon):
        cmd.extend(["--icon", icon])

    # Adicionar hidden imports necessários
    hidden_imports = [
        # Utils
        "utils", "utils.colors", "utils.config", "utils.logger",
        # Backend modules
        "modules", "modules.system", "modules.power", "modules.security",
        "modules.drivers", "modules.programs", "modules.office",
        "modules.optimize", "modules.diagnose", "modules.services",
        "modules.restore", "modules.cleanup", "modules.disk",
        "modules.network", "modules.repair", "modules.apps",
        "modules.development", "modules.tools", "modules.reports",
        "modules.advanced",
        # Frontend
        "frontend", "frontend.app", "frontend.api", "frontend.jobs",
        "frontend.logs", "frontend.theme", "frontend.modules_bridge",
        "frontend.components", "frontend.pages",
        "frontend.components.button", "frontend.components.card",
        "frontend.components.badge", "frontend.components.progressbar",
        "frontend.components.skeleton", "frontend.components.spinner",
        "frontend.components.modal", "frontend.components.confirm",
        "frontend.components.toast", "frontend.components.loading",
        "frontend.components.error", "frontend.components.sidebar",
        "frontend.components.header",
        "frontend.pages.dashboard", "frontend.pages.programs",
        "frontend.pages.office", "frontend.pages.windows",
        "frontend.pages.drivers", "frontend.pages.diagnosis",
        "frontend.pages.optimization", "frontend.pages.energy",
        "frontend.pages.defender", "frontend.pages.restore",
        "frontend.pages.logs",
    ]

    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])

    cmd.append("main.py")

    print(f"\nExecutando: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))

    if result.returncode == 0:
        print()
        print("=" * 50)
        print("  Build concluído com sucesso!")
        print(f"  Executável: dist/{app_name}{ext}")
        print("=" * 50)
    else:
        print()
        print("  Erro durante o build!")
        sys.exit(1)


if __name__ == "__main__":
    build()

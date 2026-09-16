"""
Módulo de desenvolvimento do NV Optimizer.
"""

import subprocess
import platform
from utils.colors import Theme, colorize
from utils.logger import logger
from utils.config import system_info


def install_git():
    """[90] Instalar Git"""
    print(colorize("\n  Instalando Git...\n", Theme.PRIMARY))

    try:
        if system_info.is_windows:
            subprocess.run(["winget", "install", "Git.Git"], timeout=300)
        elif system_info.is_macos:
            subprocess.run(["brew", "install", "git"], timeout=300)
        else:
            subprocess.run(["sudo", "apt-get", "install", "-y", "git"], timeout=300)
        logger.success("Git instalado com sucesso")
    except FileNotFoundError:
        logger.warning("Gerenciador de pacotes não encontrado")
    except Exception as e:
        logger.error(f"Erro ao instalar Git: {e}")


def install_python():
    """[91] Instalar Python"""
    print(colorize("\n  Instalando Python...\n", Theme.PRIMARY))

    try:
        if system_info.is_windows:
            subprocess.run(["winget", "install", "Python.Python.3.12"], timeout=300)
        elif system_info.is_macos:
            subprocess.run(["brew", "install", "python3"], timeout=300)
        else:
            subprocess.run(["sudo", "apt-get", "install", "-y", "python3"], timeout=300)
        logger.success("Python instalado com sucesso")
    except FileNotFoundError:
        logger.warning("Gerenciador de pacotes não encontrado")
    except Exception as e:
        logger.error(f"Erro ao instalar Python: {e}")


def install_nodejs():
    """[92] Instalar Node.js"""
    print(colorize("\n  Instalando Node.js...\n", Theme.PRIMARY))

    try:
        if system_info.is_windows:
            subprocess.run(["winget", "install", "OpenJS.NodeJS.LTS"], timeout=300)
        elif system_info.is_macos:
            subprocess.run(["brew", "install", "node"], timeout=300)
        else:
            subprocess.run(["sudo", "apt-get", "install", "-y", "nodejs"], timeout=300)
        logger.success("Node.js instalado com sucesso")
    except FileNotFoundError:
        logger.warning("Gerenciador de pacotes não encontrado")
    except Exception as e:
        logger.error(f"Erro ao instalar Node.js: {e}")


def install_vscode():
    """[93] Instalar VS Code"""
    print(colorize("\n  Instalando VS Code...\n", Theme.PRIMARY))

    try:
        if system_info.is_windows:
            subprocess.run(["winget", "install", "Microsoft.VisualStudioCode"], timeout=300)
        elif system_info.is_macos:
            subprocess.run(["brew", "install", "--cask", "visual-studio-code"], timeout=300)
        else:
            subprocess.run(["sudo", "snap", "install", "code", "--classic"], timeout=300)
        logger.success("VS Code instalado com sucesso")
    except FileNotFoundError:
        logger.warning("Gerenciador de pacotes não encontrado")
    except Exception as e:
        logger.error(f"Erro ao instalar VS Code: {e}")


def install_docker():
    """[94] Instalar Docker"""
    print(colorize("\n  Instalando Docker...\n", Theme.PRIMARY))

    try:
        if system_info.is_windows:
            subprocess.run(["winget", "install", "Docker.DockerDesktop"], timeout=300)
        elif system_info.is_macos:
            subprocess.run(["brew", "install", "--cask", "docker"], timeout=300)
        else:
            subprocess.run(["sudo", "apt-get", "install", "-y", "docker.io"], timeout=300)
        logger.success("Docker instalado com sucesso")
    except FileNotFoundError:
        logger.warning("Gerenciador de pacotes não encontrado")
    except Exception as e:
        logger.error(f"Erro ao instalar Docker: {e}")


def install_homebrew():
    """[95] Instalar Homebrew"""
    print(colorize("\n  Instalando Homebrew...\n", Theme.PRIMARY))

    if not system_info.is_macos and not system_info.is_linux:
        logger.warning("Homebrew é para macOS/Linux")
        return

    try:
        subprocess.run(
            ['/bin/bash', '-c', '"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'],
            timeout=300,
        )
        logger.success("Homebrew instalado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao instalar Homebrew: {e}")


def update_homebrew():
    """[96] Atualizar Homebrew"""
    print(colorize("\n  Atualizando Homebrew...\n", Theme.PRIMARY))

    if not system_info.is_macos and not system_info.is_linux:
        logger.warning("Homebrew é para macOS/Linux")
        return

    try:
        subprocess.run(["brew", "update"], timeout=300)
        subprocess.run(["brew", "upgrade"], timeout=300)
        logger.success("Homebrew atualizado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao atualizar Homebrew: {e}")

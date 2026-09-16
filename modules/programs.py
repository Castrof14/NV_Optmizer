"""
Backend de instalação de programas (via winget real).
A interface apenas chama estas funções — nenhum comando fica no frontend.
"""

import subprocess
from utils.colors import Theme, colorize
from utils.logger import logger
from utils.config import system_info

PROGRAMS = [
    {
        "key": "anydesk",
        "name": "AnyDesk",
        "category": "basico",
        "winget": "AnyDeskSoftwareGmbH.AnyDesk",
        "tags": ["remoto", "suporte"],
        "description": "Acesso remoto rápido, seguro e leve.",
    },
    {
        "key": "winrar",
        "name": "WinRAR",
        "category": "basico",
        "winget": "RARLab.WinRAR",
        "tags": ["compactar", "zip"],
        "description": "Compactação e extração de arquivos RAR e ZIP.",
    },
    {
        "key": "7zip",
        "name": "7-Zip",
        "category": "basico",
        "winget": "7zip.7zip",
        "tags": ["compactar", "zip"],
        "description": "Compactador gratuito e de código aberto.",
    },
    {
        "key": "notepadpp",
        "name": "Notepad++",
        "category": "basico",
        "winget": "Notepad++.Notepad++",
        "tags": ["editor", "código"],
        "description": "Editor de texto e código fonte com abas.",
    },
    {
        "key": "brave",
        "name": "Brave",
        "category": "basico",
        "winget": "BraveSoftware.BraveBrowser",
        "tags": ["navegador", "privacidade"],
        "description": "Navegador rápido com bloqueio de anúncios nativo.",
    },
    {
        "key": "chrome",
        "name": "Google Chrome",
        "category": "basico",
        "winget": "Google.Chrome",
        "tags": ["navegador"],
        "description": "Navegador mais utilizado do mundo.",
    },
    {
        "key": "steam",
        "name": "Steam",
        "category": "gaming",
        "winget": "Valve.Steam",
        "tags": ["jogos", "launcher"],
        "description": "Plataforma principal de jogos para PC.",
    },
    {
        "key": "epic",
        "name": "Epic Games Launcher",
        "category": "gaming",
        "winget": "EpicGames.EpicGamesLauncher",
        "tags": ["jogos", "launcher"],
        "description": "Loja e launcher de jogos da Epic Games.",
    },
]


def list_programs() -> list:
    """Catálogo de programas disponíveis."""
    return list(PROGRAMS)


def _is_windows() -> bool:
    if not system_info.is_windows:
        raise RuntimeError("Instalação de programas disponível apenas no Windows")
    return True


def winget_available() -> bool:
    """Verifica se o winget existe (verificação real)."""
    try:
        r = subprocess.run(["winget", "--version"], capture_output=True, text=True, timeout=10)
        return r.returncode == 0
    except Exception:
        return False


def check_installed(key: str) -> bool:
    """Verifica se um programa está instalado (via winget list)."""
    _is_windows()
    entry = next((p for p in PROGRAMS if p["key"] == key), None)
    if not entry:
        return False
    if not winget_available():
        raise RuntimeError("Winget não encontrado no sistema")
    try:
        r = subprocess.run(
            ["winget", "list", "--id", entry["winget"], "--exact"],
            capture_output=True, text=True, timeout=60,
        )
        return entry["winget"].lower() in r.stdout.lower() and r.returncode == 0
    except Exception as e:
        raise RuntimeError(f"Falha ao verificar {entry['name']}: {e}")


def check_all() -> list:
    """Status real de instalação de todos os programas do catálogo."""
    result = []
    if not system_info.is_windows:
        for p in PROGRAMS:
            result.append({"key": p["key"], "installed": None})
        return result
    for p in PROGRAMS:
        try:
            result.append({"key": p["key"], "installed": check_installed(p["key"])})
        except Exception:
            result.append({"key": p["key"], "installed": None})
    return result


def install_program(key: str) -> None:
    """Instala um programa do catálogo por chave (ação real via winget)."""
    _is_windows()
    entry = next((p for p in PROGRAMS if p["key"] == key), None)
    if not entry:
        raise RuntimeError(f"Programa desconhecido: {key}")
    if not winget_available():
        raise RuntimeError("Winget não encontrado. Instale o App Installer pela Microsoft Store.")
    print(colorize(f"\n  Instalando {entry['name']}...\n", Theme.PRIMARY))
    r = subprocess.run(
        ["winget", "install", "--exact", "--id", entry["winget"],
         "--accept-package-agreements", "--accept-source-agreements",
         "--disable-interactivity"],
        capture_output=True, text=True, timeout=1800,
    )
    out = (r.stdout or "") + (r.stderr or "")
    for line in out.split("\n"):
        line = line.strip()
        if line:
            print(f"    {line}")
    if "encontr" in out.lower() and "não" in out.lower() and r.returncode != 0:
        raise RuntimeError(f"Não foi possível instalar {entry['name']}. Verifique os logs.")
    if r.returncode != 0 and "já instalado" not in out.lower():
        raise RuntimeError(f"Falha na instalação de {entry['name']} (código {r.returncode}).")
    logger.success(f"Programa {entry['name']} instalado com sucesso")
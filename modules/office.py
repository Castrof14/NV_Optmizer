"""
Backend de instalação/configuração do Microsoft Office.

Seguindo o padrão do ambiente MS Office Setup (tutorial office tutorial.txt):
  - Pasta "MS Office Setup" na raiz do sistema, com o Office Deployment Tool
    e o arquivo de configuração.
  - Instalação via: Setup.exe /configure <Configuração.xml>
A interface apenas chama estas funções — nenhum comando fica no frontend.
"""

import os
import subprocess
from utils.colors import Theme, colorize
from utils.logger import logger
from utils.config import system_info


def _base_dir() -> str:
    return os.path.join(os.environ.get("SystemDrive", "C:"), "MS Office Setup")


def get_status() -> dict:
    """Status real do Office instalado no sistema."""
    result = {"available": False, "installed": False, "version": None, "path": None, "setup_dir": None, "setup_ready": False}
    if not system_info.is_windows:
        return result
    result["available"] = True
    result["setup_dir"] = _base_dir()
    setup = os.path.join(_base_dir(), "Setup.exe")
    cfg = os.path.join(_base_dir(), "Configuration.xml")
    if not os.path.exists(cfg):
        for name in ("configuração.xml", "Configuracao.xml", "configuration.xml"):
            cand = os.path.join(_base_dir(), name)
            if os.path.exists(cand):
                cfg = cand
                break
    result["setup_ready"] = os.path.exists(setup) and os.path.exists(cfg)
    result["setup_path"] = setup if os.path.exists(setup) else None

    candidates = [
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Microsoft Office", "root", "Office16", "WINWORD.EXE"),
        os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "Microsoft Office", "root", "Office16", "WINWORD.EXE"),
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Microsoft Office", "Office16", "WINWORD.EXE"),
    ]
    for p in candidates:
        if os.path.exists(p):
            result["installed"] = True
            result["path"] = p
            result["version"] = _detect_version(p)
            break
    return result


def _detect_version(winword_path: str) -> str | None:
    try:
        import win32api  # type: ignore
        info = win32api.GetFileVersionInfo(winword_path, "\\")
        ms = info.get("FileVersionMS", 0)
        ls = info.get("FileVersionLS", 0)
        major, minor, build, qfe = ms >> 16, ms & 0xFFFF, ls >> 16, ls & 0xFFFF
        return f"{major}.{minor}.{build}.{qfe}"
    except Exception:
        return None


def get_install_path() -> str | None:
    st = get_status()
    return st.get("setup_path")


def install_office() -> None:
    """Instala/configura o Office usando o Deployment Tool (ação real)."""
    if not system_info.is_windows:
        raise RuntimeError("Instalação do Office disponível apenas no Windows")

    base = _base_dir()
    setup = os.path.join(base, "Setup.exe")
    cfg = None
    for name in ("Configuration.xml", "configuration.xml", "Configuração.xml", "Configuracao.xml"):
        cand = os.path.join(base, name)
        if os.path.exists(cand):
            cfg = cand
            break

    if not os.path.exists(setup) or not cfg:
        raise RuntimeError(
            f"Ambiente de instalação do Office não encontrado. "
            f"Coloque o Office Deployment Tool (Setup.exe) e o arquivo de configuração "
            f"na pasta: {base}"
        )

    status = get_status()
    if status.get("installed"):
        print(colorize("\n  Microsoft Office já detectado no sistema.\n", Theme.WARNING))

    print(colorize("\n  Iniciando instalação/configuração do Office...\n", Theme.PRIMARY))
    print(f"    Setup: {setup}")
    print(f"    Config: {cfg}")

    r = subprocess.run([setup, "/configure", cfg], capture_output=True, text=True, timeout=3600)
    out = (r.stdout or "") + (r.stderr or "")
    for line in out.split("\n"):
        line = line.strip()
        if line:
            print(f"    {line}")
    if r.returncode not in (0, -1073741818):  # 0xC0000005 pode indicar "já instalado / reinício pendente"
        raise RuntimeError(f"Falha ao executar o Office Setup (código {r.returncode}).")

    final = get_status()
    if final.get("installed"):
        logger.success("Microsoft Office instalado/configurado com sucesso")
    else:
        logger.warning("Office Setup executado. Verifique a conclusão da instalação.")
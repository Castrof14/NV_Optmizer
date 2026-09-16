"""
NV Optimizer 2.0 - Backend de Office
Gerencia instalação e status do Microsoft Office conforme office tutorial.txt.
"""

import os
import shutil
import subprocess
import urllib.request

from .backend_core import (
    OperationResult, ErrorCode, isAdmin,
    run_command, global_progress,
)

OFFICE_FOLDER = "C:\\MS Office Setup"

OFFICE_DOWNLOAD_URL = (
    "https://www.microsoft.com/en-us/download/details.aspx?id=49117"
)
OODT_DOWNLOAD_URL = (
    "https://go.microsoft.com/fwlink/?linkid=2073432"
)

CONFIG_XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<Configuration>
  <Add OfficeClientEdition="64" Channel="LTSC" Version="2024">
    <Product ID="ProPlus2024Volume">
      <Language ID="MatchOS" />
      <ExcludeApp ID="Access" />
      <ExcludeApp ID="Groove" />
      <ExcludeApp ID="Lync" />
      <ExcludeApp ID="OneDrive" />
      <ExcludeApp ID="OneNote" />
      <ExcludeApp ID="Outlook" />
      <ExcludeApp ID="Publisher" />
      <ExcludeApp ID="Teams" />
    </Product>
  </Add>
  <Property Name="ACTIVATIONTYPE" Value="KMS" />
  <Property Name="AUTOACTIVATE" Value="0" />
  <Property Name="FORCEAPPSHUTDOWN" Value="False" />
  <Property Name="UPDATEEXPERIENCE" Value="manual" />
  <Property Name="UpdatePath" Value="" />
  <Property Name="UTILITYUPDATEEXPERIENCE" Value="1" />
  <Updates Enabled="TRUE" />
  <Display Level="Full" AcceptEULA="TRUE" />
  <Logging Level="Standard" Path="C:\\MS Office Setup\\Logs" />
  <RemoveMSI />
</Configuration>
"""


def checkOffice() -> dict:
    """Verifica se Office está instalado e retorna informações."""
    result = {
        "installed": False,
        "version": None,
        "edition": None,
        "activated": False,
        "product_name": None,
    }

    try:
        ps_cmd = (
            "Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\"
            "Uninstall\\* | Where-Object { $_.DisplayName -like '*Microsoft Office*' } | "
            "Select-Object -First 1 DisplayName,DisplayVersion"

        )
        res = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=30,
        )
        for line in res.stdout.split("\n"):
            line = line.strip()
            if not line:
                continue
            if "Microsoft Office" in line and "DisplayName" not in line and ":" in line:
                result["product_name"] = line.split(":", 1)[1].strip()
            if "DisplayVersion" in line and ":" in line:
                result["version"] = line.split(":", 1)[1].strip()

        if result["product_name"]:
            result["installed"] = True

            if "LTSC" in result["product_name"] or "2024" in result["product_name"]:
                result["edition"] = "Office LTSC Plus 2024"
            elif "365" in result["product_name"] or "Professional" in result["product_name"]:
                result["edition"] = "Office 365"
    except Exception:
        pass

    result["activated"] = getOfficeActivationStatus()

    return result


def getOfficeActivationStatus() -> bool:
    """Verifica estado de ativação do Office."""
    try:
        ospp_path = os.path.join(
            os.environ.get("ProgramFiles", "C:\\Program Files"),
            "Microsoft Office", "Office16", "OSPP.VBS",
        )
        if not os.path.isfile(ospp_path):
            ospp_path = os.path.join(
                os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
                "Microsoft Office", "Office16", "OSPP.VBS",
            )

        if not os.path.isfile(ospp_path):
            return False

        result = subprocess.run(
            ["cscript", "//Nologo", ospp_path, "/dstatus"],
            capture_output=True, text=True, timeout=30,
        )
        return "LICENSED" in (result.stdout + result.stderr).upper()
    except Exception:
        return False


def getOfficeStatus() -> OperationResult:
    """API: status do Office."""
    data = checkOffice()
    if data["installed"]:
        return OperationResult.ok(data=data)
    return OperationResult.ok(
        message="Microsoft Office não está instalado.",
        data=data,
    )


def _download_official_odt(dest_path: str) -> bool:
    """Baixa o Office Deployment Tool oficial com User-Agent adequado."""
    try:
        request = urllib.request.Request(
            OODT_DOWNLOAD_URL,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        with urllib.request.urlopen(request, timeout=120) as resp:
            with open(dest_path, "wb") as f:
                f.write(resp.read())
        return os.path.isfile(dest_path) and os.path.getsize(dest_path) > 10000
    except Exception:
        return False


def _get_official_setup_exe() -> str:
    """Baixa o Office Deployment Tool oficial."""
    oodt_zip = os.path.join(OFFICE_FOLDER, "OODT.zip")
    os.makedirs(OFFICE_FOLDER, exist_ok=True)

    if not os.path.isfile(oodt_zip) or os.path.getsize(oodt_zip) < 10000:
        if not _download_official_odt(oodt_zip):
            return ""

    import zipfile
    try:
        with zipfile.ZipFile(oodt_zip, "r") as zip_ref:
            zip_ref.extractall(OFFICE_FOLDER)
    except Exception:
        return ""

    setup_exe = os.path.join(OFFICE_FOLDER, "setup.exe")
    return setup_exe if os.path.isfile(setup_exe) else ""


def _write_config_xml() -> bool:
    """Escrita do arquivo de configuração."""
    try:
        os.makedirs(OFFICE_FOLDER, exist_ok=True)
        with open(os.path.join(OFFICE_FOLDER, "Configuração.xml"), "w", encoding="utf-8") as f:
            f.write(CONFIG_XML_TEMPLATE)
        return True
    except Exception:
        return False


def installOffice(edition: str = "standard") -> OperationResult:
    """Instala Microsoft Office LTSC Plus 2024 conforme o tutorial."""
    global_progress.emit_start("office-install", "Preparando instalação do Office...")

    if not isAdmin():
        return OperationResult.admin_required()

    existing = checkOffice()
    if existing["installed"]:
        global_progress.emit_complete("office-install", "Office já está instalado.")
        return OperationResult.already_installed("Microsoft Office")

    global_progress.emit_progress("office-install", 10, "Preparando pasta MS Office Setup...")

    try:
        os.makedirs(OFFICE_FOLDER, exist_ok=True)
    except Exception as e:
        global_progress.emit_error("office-install", "Falha ao criar pasta.")
        return OperationResult.error(
            ErrorCode.OPERATION_FAILED,
            "Falha ao criar pasta MS Office Setup.",
            str(e),
        )

    global_progress.emit_progress("office-install", 20, "Baixando Office Deployment Tool...")

    setup_exe = _get_official_setup_exe()
    if not setup_exe:
        global_progress.emit_error("office-install", "Falha ao baixar ODT.")
        return OperationResult.error(
            ErrorCode.INSTALL_FAILED,
            "Falha ao baixar o Office Deployment Tool. "
            "Baixe manualmente em "
            "https://www.microsoft.com/en-us/download/details.aspx?id=49117 "
            f"e coloque em {OFFICE_FOLDER}.",
            "Download of OODT failed",
        )

    global_progress.emit_progress("office-install", 35, "Gerando arquivo de configuração...")
    if not _write_config_xml():
        global_progress.emit_error("office-install", "Falha ao gerar configuração.")
        return OperationResult.error(
            ErrorCode.OPERATION_FAILED,
            "Falha ao gerar arquivo de configuração.",
        )

    global_progress.emit_progress("office-install", 40, "Executando setup.exe /configure...")

    config_path = os.path.join(OFFICE_FOLDER, "Configuração.xml")
    result = run_command([
        setup_exe, "/configure", config_path,
    ], timeout=3600)

    global_progress.emit_progress("office-install", 85, "Verificando instalação...")

    final = checkOffice()
    if final["installed"] or result["success"]:
        global_progress.emit_progress("office-install", 95, "Verificando ativação...")
        global_progress.emit_complete("office-install", "Office instalado com sucesso.")
        return OperationResult.ok("Microsoft Office instalado com sucesso.", {
            "version": final.get("version"),
            "edition": final.get("edition"),
        })

    global_progress.emit_error("office-install", "Instalação falhou.")
    return OperationResult.error(
        ErrorCode.INSTALL_FAILED,
        "Falha ao instalar Microsoft Office.",
        result["stderr"].strip() or result["stdout"].strip() or "Erro desconhecido",
    )


def setOfficeKey(key: str) -> OperationResult:
    """Define chave de licença (mecanismo legítimo via OSPP)."""
    if not isAdmin():
        return OperationResult.admin_required()

    if not key or len(key) < 10:
        return OperationResult.error(
            ErrorCode.INVALID_INPUT, "Chave de licença inválida."
        )

    ospp_path = os.path.join(
        os.environ.get("ProgramFiles", "C:\\Program Files"),
        "Microsoft Office", "Office16", "OSPP.VBS",
    )
    if not os.path.isfile(ospp_path):
        ospp_path = os.path.join(
            os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
            "Microsoft Office", "Office16", "OSPP.VBS",
        )

    if not os.path.isfile(ospp_path):
        return OperationResult.error(
            ErrorCode.NOT_FOUND, "OSPP.VBS não encontrado. Office não instalado?"
        )

    result = run_command(
        ["cscript", "//Nologo", ospp_path, "/inpkey:" + key],
        timeout=60,
    )

    if result["success"]:
        return OperationResult.ok("Chave de licença registrada.")
    return OperationResult.error(
        ErrorCode.OPERATION_FAILED, "Falha ao registrar chave.",
        result["stderr"].strip() or result["stdout"].strip(),
    )


def activateOffice() -> OperationResult:
    """Ativa o Office via mecanismo legítimo (KMS ou online)."""
    if not isAdmin():
        return OperationResult.admin_required()

    if not checkOffice()["installed"]:
        return OperationResult.error(
            ErrorCode.NOT_FOUND, "Office não está instalado."
        )

    ospp_path = os.path.join(
        os.environ.get("ProgramFiles", "C:\\Program Files"),
        "Microsoft Office", "Office16", "OSPP.VBS",
    )
    if not os.path.isfile(ospp_path):
        ospp_path = os.path.join(
            os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
            "Microsoft Office", "Office16", "OSPP.VBS",
        )

    if not os.path.isfile(ospp_path):
        return OperationResult.error(
            ErrorCode.NOT_FOUND, "OSPP.VBS não encontrado."
        )

    result = run_command(["cscript", "//Nologo", ospp_path, "/act"], timeout=120)
    if result["success"]:
        if getOfficeActivationStatus():
            return OperationResult.ok("Office ativado com sucesso.")
        return OperationResult.ok(
            "Comando de ativação executado. Verifique o estado de ativação.",
        )
    return OperationResult.error(
        ErrorCode.OPERATION_FAILED, "Falha ao ativar Office.",
        result["stderr"].strip() or result["stdout"].strip(),
    )
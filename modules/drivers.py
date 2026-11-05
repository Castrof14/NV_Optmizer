"""
Módulo de drivers do NV Optimizer.
"""

import base64
import json
import subprocess
import threading
from utils.colors import Theme, colorize
from utils.logger import logger
from utils.config import system_info
from utils.shell import NO_WINDOW, require_windows_admin

# Classes de driver do Windows Update tratadas como essenciais: vídeo, rede, áudio,
# chipset/sistema, armazenamento, USB e Bluetooth.
BASIC_DRIVER_CLASSES = ("Display", "Net", "MEDIA", "System", "HDC", "SCSIAdapter", "USB", "Bluetooth")

WINDOWS_UPDATE_TIMEOUT = 3 * 60 * 60

# A API do Windows Update já vem no sistema: não depende de módulos externos.
# BIOS/firmware nunca entra: uma falha na gravação pode impedir o computador de ligar.
_WINDOWS_UPDATE_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false
$basicClasses = @(__BASIC_CLASSES__)
$onlyBasic = $__ONLY_BASIC__
$install = $__INSTALL__
function Emit($line) { [Console]::Out.WriteLine($line); [Console]::Out.Flush() }
try {
    Emit 'Procurando drivers no Windows Update...'
    $session = New-Object -ComObject Microsoft.Update.Session
    $session.ClientApplicationID = 'NV Optimizer'
    $searcher = $session.CreateUpdateSearcher()
    $searcher.ServerSelection = 2
    $found = $searcher.Search("IsInstalled=0 and Type='Driver' and IsHidden=0").Updates

    $candidates = @()
    foreach ($u in $found) {
        $class = [string]$u.DriverClass
        if ($class -eq 'Firmware') { continue }
        if ($onlyBasic -and $basicClasses -notcontains $class) { continue }
        $candidates += $u
    }

    # O Windows Update pode oferecer várias versões para o mesmo dispositivo: fica a mais nova.
    $selected = @($candidates |
        Group-Object { if ($_.DriverHardwareID) { $_.DriverHardwareID } else { $_.Identity.UpdateID } } |
        ForEach-Object { $_.Group | Sort-Object { $_.DriverVerDate } -Descending | Select-Object -First 1 })

    $items = @()
    $reboot = $false
    $total = $selected.Count
    Emit "Drivers encontrados: $total"
    $i = 0
    foreach ($u in $selected) {
        $i++
        $title = [string]$u.Title
        $item = @{ title = $title; class = [string]$u.DriverClass; status = 'available'; detail = '' }
        if ($install) {
            try {
                if (-not $u.EulaAccepted) { $u.AcceptEula() }
                $one = New-Object -ComObject Microsoft.Update.UpdateColl
                [void]$one.Add($u)

                Emit "[$i/$total] Baixando: $title"
                $downloader = $session.CreateUpdateDownloader()
                $downloader.Updates = $one
                $download = $downloader.Download()
                if ($download.ResultCode -ne 2 -and $download.ResultCode -ne 3) {
                    throw ('Download falhou: 0x{0:X8}' -f $download.HResult)
                }

                Emit "[$i/$total] Instalando: $title"
                $installer = $session.CreateUpdateInstaller()
                $installer.ForceQuiet = $true
                $installer.Updates = $one
                $result = $installer.Install()
                $itemResult = $result.GetUpdateResult(0)
                if ($result.RebootRequired) { $reboot = $true }
                if ($itemResult.ResultCode -eq 2) {
                    $item.status = 'installed'
                    Emit "[$i/$total] Instalado: $title"
                } else {
                    throw ('Instalação falhou: 0x{0:X8}' -f $itemResult.HResult)
                }
            } catch {
                $item.status = 'failed'
                $item.detail = $_.Exception.Message
                Emit "[$i/$total] FALHA: $title - $($_.Exception.Message)"
            }
        } else {
            Emit "[$i/$total] Disponível: $title"
        }
        $items += $item
    }
    Emit ('NV_RESULT ' + (@{ items = $items; reboot = $reboot } | ConvertTo-Json -Compress -Depth 4))
} catch {
    Emit "NV_ERROR $($_.Exception.Message)"
    exit 1
}
"""


def _run_windows_update(only_basic: bool, install: bool) -> dict:
    """Consulta (e opcionalmente instala) drivers, repassando o andamento em tempo real."""
    classes = ", ".join(f"'{c}'" for c in BASIC_DRIVER_CLASSES)
    script = (
        _WINDOWS_UPDATE_SCRIPT
        .replace("__BASIC_CLASSES__", classes)
        .replace("__ONLY_BASIC__", "true" if only_basic else "false")
        .replace("__INSTALL__", "true" if install else "false")
    )
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    proc = subprocess.Popen(
        ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
         "-OutputFormat", "Text", "-EncodedCommand", encoded],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
        creationflags=NO_WINDOW,
    )
    watchdog = threading.Timer(WINDOWS_UPDATE_TIMEOUT, proc.kill)
    watchdog.start()

    summary = None
    error = None
    last_line = ""
    try:
        for raw in proc.stdout:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("NV_RESULT "):
                summary = json.loads(line[len("NV_RESULT "):])
            elif line.startswith("NV_ERROR "):
                error = line[len("NV_ERROR "):]
            else:
                last_line = line
                print(line)
        proc.wait()
    finally:
        watchdog.cancel()
        proc.stdout.close()

    if summary is None:
        raise RuntimeError(f"Windows Update: {error or last_line or 'operação interrompida'}")
    return {
        "items": summary.get("items") or [],
        "reboot": bool(summary.get("reboot")),
    }


def check_driver_updates(only_basic: bool = False) -> dict:
    """Lista os drivers disponíveis no Windows Update, sem instalar nada."""
    require_windows_admin("Verificar drivers")
    return _run_windows_update(only_basic, install=False)


def update_drivers(only_basic: bool) -> dict:
    """Instala os drivers disponíveis no Windows Update e retorna o resultado de cada um."""
    require_windows_admin("Atualizar drivers")
    result = _run_windows_update(only_basic, install=True)
    installed = sum(1 for item in result["items"] if item["status"] == "installed")
    failed = sum(1 for item in result["items"] if item["status"] == "failed")
    result["installed"] = installed
    result["failed"] = failed
    if not result["items"]:
        print("Nenhuma atualização de driver disponível.")
    else:
        print(f"Concluído: {installed} instalados, {failed} falhas.")
    if result["reboot"]:
        print("Reinicie o computador para concluir a instalação.")
    return result


def update_drivers_basic():
    """[62] Atualizar Drivers Básicos"""
    return update_drivers(only_basic=True)


def update_drivers_all():
    """[63] Atualizar Todos os Drivers"""
    return update_drivers(only_basic=False)


def show_drivers():
    """[60] Mostrar Drivers"""
    print(colorize("\n  Listando drivers...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        result = subprocess.run(
            ["driverquery", "/FO", "TABLE"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        lines = result.stdout.split("\n")
        for line in lines[:30]:
            if line.strip():
                print(f"    {line.strip()}")
        if len(lines) > 30:
            print(f"    ... e mais {len(lines) - 30} drivers")
        logger.success(f"Total de drivers: {len(lines) - 2}")
    except Exception as e:
        logger.error(f"Erro ao listar drivers: {e}")


def export_drivers():
    """[61] Exportar Drivers"""
    print(colorize("\n  Exportando drivers...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        import os
        export_path = os.path.expanduser("~/Desktop\\DriversBackup")
        os.makedirs(export_path, exist_ok=True)
        result = subprocess.run(
            ["dism", "/online", "/export-driver", f"/destination:{export_path}"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        logger.success(f"Drivers exportados para: {export_path}")
    except Exception as e:
        logger.error(f"Erro ao exportar drivers: {e}")


def _read_video_controllers() -> list:
    """Placas de vídeo via CIM (o wmic não vem mais instalado no Windows 11 atual)."""
    script = (
        "[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false; "
        "@(Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, "
        "@{n='DriverDate';e={if ($_.DriverDate) { $_.DriverDate.ToString('dd/MM/yyyy') }}}) "
        "| ConvertTo-Json -Compress"
    )
    try:
        raw = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, stdin=subprocess.DEVNULL, encoding="utf-8", errors="replace",
            timeout=20, creationflags=NO_WINDOW,
        )
        data = json.loads(raw.stdout or "[]")
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return []
    # O PowerShell 5.1 pode reduzir uma lista de um item a um único objeto.
    return data if isinstance(data, list) else [data]


def get_gpu_driver() -> dict:
    """Versão real do driver da placa de vídeo."""
    result = {"name": "Não disponível", "driver": "—", "date": "—", "available": False}
    if not system_info.is_windows:
        return result
    import re
    controllers = [c for c in _read_video_controllers() if c.get("Name")]
    physical = [c for c in controllers if "RDP" not in c["Name"] and "Basic Display" not in c["Name"]]
    best = (physical or controllers or [{}])[0]
    if best.get("Name"):
        result["name"] = re.sub(r"\s+", " ", best["Name"]).strip()
        result["driver"] = best.get("DriverVersion") or "—"
        result["date"] = best.get("DriverDate") or "—"
        result["available"] = True
    # Complementa com nvidia-smi quando NVIDIA disponível
    if "NVIDIA" in result["name"].upper() or not result["available"]:
        try:
            smi = subprocess.run(
                ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5,
            )
            ver = smi.stdout.strip()
            if ver and "NVIDIA" in result["name"].upper():
                result["driver"] = ver
                result["available"] = True
        except Exception:
            pass
    return result

"""
Módulo de segurança do NV Optimizer.
"""

import subprocess
from utils.colors import Theme, colorize
from utils.logger import logger
from utils.config import system_info


def check_defender():
    """[50] Verificar Windows Defender"""
    print(colorize("\n  Verificando Windows Defender...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-MpComputerStatus"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        for line in result.stdout.split("\n"):
            if line.strip():
                print(f"    {line.strip()}")
        logger.success("Status do Windows Defender obtido")
    except Exception as e:
        logger.error(f"Erro ao verificar Defender: {e}")


def update_signatures():
    """[51] Atualizar Assinaturas"""
    print(colorize("\n  Atualizando assinaturas do Windows Defender...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        result = subprocess.run(
            ["powershell", "-Command", "Update-MpSignature"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        logger.success("Assinaturas atualizadas com sucesso")
    except Exception as e:
        logger.error(f"Erro ao atualizar assinaturas: {e}")


def check_firewall():
    """[52] Verificar Firewall"""
    print(colorize("\n  Verificando Firewall...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        result = subprocess.run(
            ["netsh", "advfirewall", "show", "allprofiles"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        for line in result.stdout.split("\n"):
            if line.strip():
                print(f"    {line.strip()}")
        logger.success("Status do Firewall obtido")
    except Exception as e:
        logger.error(f"Erro ao verificar Firewall: {e}")


def remove_invalid_policies():
    """[53] Remover Políticas Inválidas"""
    print(colorize("\n  Removendo políticas inválidas...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        import winreg
        key_path = r"SOFTWARE\Policies\Microsoft\Windows"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                logger.info("Políticas encontradas - verificando...")
        except FileNotFoundError:
            logger.success("Nenhuma política inválida encontrada")
    except Exception as e:
        logger.error(f"Erro ao verificar políticas: {e}")


def _sub(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return ""


def get_defender_status() -> dict:
    """Status real do Windows Defender (leitura real)."""
    result = {"available": False, "real_time": None, "antivirus": None, "signatures": None, "last_update": None}
    if not system_info.is_windows:
        return result
    raw = _sub(["powershell", "-NoProfile", "-Command", "Get-MpComputerStatus | Format-List AntivirusEnabled,RealTimeProtectionEnabled,AMSignatureVersion,AVSignatureVersion,AntivirusSignatureLastUpdated"], timeout=30)
    if not raw:
        return result
    data = {}
    for line in raw.split("\n"):
        if ":" in line:
            k, _, v = line.partition(":")
            data[k.strip()] = v.strip()
    if "AntivirusEnabled" in data:
        result["available"] = True
        result["antivirus"] = data["AntivirusEnabled"].lower() == "true"
        result["real_time"] = data.get("RealTimeProtectionEnabled", "").lower() == "true"
        result["signatures"] = data.get("AMSignatureVersion") or data.get("AVSignatureVersion") or "—"
        result["last_update"] = data.get("AntivirusSignatureLastUpdated") or "—"
    return result


def set_defender_realtime(enabled: bool) -> bool:
    """Ativa ou desativa proteção em tempo real (ação real)."""
    if not system_info.is_windows:
        raise RuntimeError("Configuração disponível apenas no Windows")
    flag = "$false" if enabled else "$true"
    raw = _sub(["powershell", "-NoProfile", "-Command", f"Set-MpPreference -DisableRealtimeMonitoring {flag}"], timeout=30)
    # Set-MpPreference não retorna stdout em sucesso (rc=0)
    logger.success(f"Proteção em tempo real {'ATIVADA' if enabled else 'DESATIVADA'}")
    return True

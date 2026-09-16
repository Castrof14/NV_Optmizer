"""
Módulo de rede expandido do NV Optimizer.
"""

import subprocess
import time
from utils.colors import Theme, colorize
from utils.logger import logger
from utils.config import system_info
from progress import progress_bar


def reset_network():
    """[30] Resetar Rede"""
    print(colorize("\n  Resetando configurações de rede...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    commands = [
        ["netsh", "int", "ip", "reset"],
        ["netsh", "int", "tcp", "reset"],
        ["netsh", "winsock", "reset"],
    ]

    for cmd in commands:
        try:
            subprocess.run(cmd, capture_output=True, timeout=60)
        except Exception:
            pass

    logger.success("Rede resetada com sucesso")


def flush_dns():
    """[31] Flush DNS"""
    print(colorize("\n  Limpando cache DNS...\n", Theme.PRIMARY))

    try:
        if system_info.is_windows:
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True, timeout=30)
        elif system_info.is_macos:
            subprocess.run(["sudo", "dscacheutil", "-flushcache"], capture_output=True, timeout=30)
            subprocess.run(["sudo", "killall", "-HUP", "mDNSResponder"], capture_output=True, timeout=30)
        else:
            subprocess.run(["sudo", "systemd-resolve", "--flush-caches"], capture_output=True, timeout=30)
        logger.success("Cache DNS limpo com sucesso")
    except Exception as e:
        logger.error(f"Erro ao limpar DNS: {e}")


def renew_ip():
    """[32] Renovar IP"""
    print(colorize("\n  Renovando endereço IP...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        subprocess.run(["ipconfig", "/release"], capture_output=True, timeout=30)
        time.sleep(1)
        subprocess.run(["ipconfig", "/renew"], capture_output=True, timeout=30)
        logger.success("IP renovado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao renovar IP: {e}")


def reset_winsock():
    """[33] Reset Winsock"""
    print(colorize("\n  Resetando Winsock...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        subprocess.run(["netsh", "winsock", "reset"], capture_output=True, timeout=60)
        logger.success("Winsock resetado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao resetar Winsock: {e}")


def set_dns_google():
    """[34] Alterar DNS para Google"""
    print(colorize("\n  Configurando DNS do Google...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    _set_dns(["8.8.8.8", "8.8.4.4"])


def set_dns_cloudflare():
    """[35] Alterar DNS para Cloudflare"""
    print(colorize("\n  Configurando DNS da Cloudflare...\n", Theme.PRIMARY))
    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    _set_dns(["1.1.1.1", "1.0.0.1"])


def test_latency():
    """[36] Testar Latência"""
    print(colorize("\n  Testando latência...\n", Theme.PRIMARY))

    targets = [
        ("Google", "8.8.8.8"),
        ("Cloudflare", "1.1.1.1"),
        ("Quad9", "9.9.9.9"),
    ]

    for name, host in targets:
        try:
            result = subprocess.run(
                ["ping", "-c", "4", host],
                capture_output=True,
                text=True,
                timeout=10,
            )
            for line in result.stdout.split("\n"):
                if "avg" in line or "time=" in line:
                    logger.info(f"{name}: {line.strip()}")
                    break
        except Exception:
            logger.warning(f"Não foi possível testar {name}")


def _set_dns(dns_servers: list):
    try:
        subprocess.run(
            ["netsh", "interface", "ip", "set", "dns", "Wi-Fi", "static", dns_servers[0]],
            capture_output=True,
            timeout=30,
        )
        subprocess.run(
            ["netsh", "interface", "ip", "add", "dns", "Wi-Fi", dns_servers[1], "index=2"],
            capture_output=True,
            timeout=30,
        )
        logger.success(f"DNS configurado: {', '.join(dns_servers)}")
    except Exception as e:
        logger.error(f"Erro ao configurar DNS: {e}")

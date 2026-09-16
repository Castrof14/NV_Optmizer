"""
Módulo de relatórios do NV Optimizer.
"""

import json
import os
import subprocess
import platform
from datetime import datetime
from utils.colors import Theme, colorize
from utils.logger import logger
from utils.config import system_info


def export_system_info():
    """[110] Exportar Informações do Sistema"""
    print(colorize("\n  Exportando informações do sistema...\n", Theme.PRIMARY))

    info = _collect_system_info()
    desktop = os.path.expanduser("~/Desktop")
    filename = os.path.join(desktop, f"NV_Sistema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("NV OPTIMIZER - Informações do Sistema\n")
        f.write("=" * 50 + "\n\n")
        for key, value in info.items():
            f.write(f"{key}: {value}\n")

    logger.success(f"Relatório exportado: {filename}")


def export_html_report():
    """[111] Exportar Relatório HTML"""
    print(colorize("\n  Gerando relatório HTML...\n", Theme.PRIMARY))

    info = _collect_system_info()
    desktop = os.path.expanduser("~/Desktop")
    filename = os.path.join(desktop, f"NV_Relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>NV Optimizer - Relatório</title>
    <style>
        body {{ font-family: Arial; background: #1a1a2e; color: #fff; padding: 20px; }}
        h1 {{ color: #1565C0; }}
        .info {{ background: #16213e; padding: 15px; border-radius: 8px; margin: 10px 0; }}
        .label {{ color: #FBC02D; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>NV Optimizer - Relatório do Sistema</h1>
    <p>Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
    <div class="info">
"""
    for key, value in info.items():
        html += f'        <p><span class="label">{key}:</span> {value}</p>\n'

    html += """    </div>
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    logger.success(f"Relatório HTML exportado: {filename}")


def export_txt_report():
    """[112] Exportar Relatório TXT"""
    export_system_info()


def export_json_report():
    """[113] Exportar Relatório JSON"""
    print(colorize("\n  Gerando relatório JSON...\n", Theme.PRIMARY))

    info = _collect_system_info()
    info["data_geracao"] = datetime.now().isoformat()
    desktop = os.path.expanduser("~/Desktop")
    filename = os.path.join(desktop, f"NV_Relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)

    logger.success(f"Relatório JSON exportado: {filename}")


def _collect_system_info() -> dict:
    info = {
        "Sistema": platform.system(),
        "Versão": platform.version(),
        "Release": platform.release(),
        "Arquitetura": platform.machine(),
        "Hostname": platform.node(),
        "Python": platform.python_version(),
    }

    if system_info.is_windows:
        try:
            result = subprocess.run(["wmic", "cpu", "get", "Name"], capture_output=True, text=True, timeout=10)
            for line in result.stdout.split("\n"):
                if line.strip() and "Name" not in line:
                    info["CPU"] = line.strip()
                    break
        except Exception:
            pass

        try:
            result = subprocess.run(["wmic", "memorychip", "get", "Capacity"], capture_output=True, text=True, timeout=10)
            for line in result.stdout.split("\n"):
                if line.strip() and "Capacity" not in line:
                    try:
                        info["RAM"] = f"{int(line.strip()) / (1024**3):.1f} GB"
                    except ValueError:
                        pass
        except Exception:
            pass

    return info

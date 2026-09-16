"""
Pontes de ação para o backend.

Este módulo é a fronteira "Frontend → Backend". Ele apenas importa e expõe
funções dos módulos reais — nenhum comando de sistema é executado aqui.
As funções chamáveis executam dentro dos Jobs (threads) e o stdout é capturado
para alimentar logs/progresso da interface.
"""

# Programas
from modules.programs import install_program, check_all as check_all_programs, list_programs

# Office
from modules.office import install_office, get_status as office_status

# Energia
from modules.power import apply_power_config, set_power_plan, set_screen_timeout, set_sleep_timeout

# Defender
from modules.security import set_defender_realtime, update_signatures

# Drivers
from modules.drivers import update_drivers_winget

# Restauração / Otimização
from modules.optimize import apply as apply_optimize, apply_restore
from modules.restore import create_restore_point

# Windows (Preparação): limpeza/disco/rede/reparo
from modules.cleanup import (
    clean_temp_files, clean_recycle_bin, clean_prefetch,
    clean_windows_update_cache, clean_logs, clean_browser_cache, clean_thumbnails,
)
from modules.disk import (optimize_disk, defrag_hd, trim_ssd,
                          optimize_startup, clean_startup_programs)
from modules.network import (flush_dns, renew_ip, reset_winsock, reset_network,
                             set_dns_google, set_dns_cloudflare, test_latency)
from modules.repair import (run_sfc, run_dism, run_chkdsk,
                            repair_windows_update, repair_system_files)
from modules.services import disable_unnecessary_services, enable_all_services, list_disabled_services

# Stress test
from modules.diagnose import start_stress, stop_stress


# Mapa para a página Windows (Preparação): ações executáveis pelo frontend
WINDOWS_ACTIONS = {
    "limpeza": [
        ("Temporários", "Limpar arquivos temporários e caches.", clean_temp_files),
        ("Lixeira", "Esvaziar a lixeira.", clean_recycle_bin),
        ("Prefetch", "Limpar cache de inicialização.", clean_prefetch),
        ("Windows Update", "Limpar cache do Windows Update.", clean_windows_update_cache),
        ("Logs", "Limpar logs do sistema.", clean_logs),
        ("Navegadores", "Limpar cache dos navegadores.", clean_browser_cache),
        ("Miniaturas", "Limpar cache de miniaturas.", clean_thumbnails),
    ],
    "disco": [
        ("Otimizar disco", "Desabilitar indexação e otimizar.", optimize_disk),
        ("Desfragmentar HD", "Analisar/desfragmentar disco.", defrag_hd),
        ("TRIM SSD", "Executar TRIM no SSD.", trim_ssd),
        ("Inicialização", "Listar programas de inicialização.", optimize_startup),
        ("Limpar startup", "Remover programas desnecessários.", clean_startup_programs),
    ],
    "rede": [
        ("Flush DNS", "Limpar cache DNS.", flush_dns),
        ("Renovar IP", "Renovar endereço IP.", renew_ip),
        ("Reset Winsock", "Resetar Winsock.", reset_winsock),
        ("Resetar rede", "Resetar rede e TCP.", reset_network),
        ("DNS Google", "Definir DNS 8.8.8.8.", set_dns_google),
        ("DNS Cloudflare", "Definir DNS 1.1.1.1.", set_dns_cloudflare),
        ("Testar latência", "Ping principais servidores.", test_latency),
    ],
    "reparo": [
        ("SFC /SCANNOW", "Reparar integridade do sistema.", run_sfc),
        ("DISM", "Reparação da imagem do sistema.", run_dism),
        ("CHKDSK", "Verificar disco.", run_chkdsk),
        ("Windows Update", "Reparar atualização.", repair_windows_update),
        ("Arquivos do sistema", "SFC + DISM.", repair_system_files),
    ],
}


def windows_action(group: str, index: int):
    return WINDOWS_ACTIONS[group][index][2]
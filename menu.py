"""
Módulo do menu principal do NV Optimizer.
Gerencia o loop principal e a seleção de opções com categorias.
"""

import time
from logo import display_logo
from ui import (
    clear_screen,
    print_header,
    print_option,
    print_separator,
    print_success,
    print_warning,
    print_error,
    print_info,
    print_muted,
)
from progress import animated_progress, spinner
from utils.colors import Theme, colorize
from utils.config import Config, system_info
from utils.logger import logger
from modules import (
    # Restore
    create_restore_point,
    # Cleanup
    clean_temp_files, clean_recycle_bin, clean_prefetch,
    clean_windows_update_cache, clean_logs, clean_browser_cache, clean_thumbnails,
    # Disk
    optimize_disk, defrag_hd, trim_ssd, optimize_startup, clean_startup_programs,
    # Network
    reset_network, flush_dns, renew_ip, reset_winsock,
    set_dns_google, set_dns_cloudflare, test_latency,
    # Repair
    run_sfc, run_dism, run_chkdsk, repair_windows_update, repair_system_files,
    # System
    show_system_info,
    # Security
    check_defender, update_signatures, check_firewall, remove_invalid_policies,
    # Drivers
    show_drivers, export_drivers, update_drivers_winget,
    # Apps
    update_all_programs, update_winget, update_microsoft_store, quick_uninstall,
    # Power
    set_high_performance, set_balanced, set_power_saver,
    # Development
    install_git, install_python, install_nodejs, install_vscode,
    install_docker, install_homebrew, update_homebrew,
    # Tools
    open_task_manager, open_registry_editor, open_services, open_cmd_admin, open_powershell,
    # Reports
    export_system_info, export_html_report, export_txt_report, export_json_report,
    # Advanced
    run_all_optimizations, gamer_mode, work_mode, restore_defaults, full_cleanup,
    # Services
    disable_unnecessary_services, list_disabled_services, enable_all_services,
)


# Mapeamento de opções para funções
OPTIONS = {
    # Restauração
    "1": ("Criar Ponto de Restauração", create_restore_point),

    # Limpeza (10-16)
    "10": ("Limpar Arquivos Temporários", clean_temp_files),
    "11": ("Limpar Lixeira", clean_recycle_bin),
    "12": ("Limpar Prefetch", clean_prefetch),
    "13": ("Limpar Cache do Windows Update", clean_windows_update_cache),
    "14": ("Limpar Logs", clean_logs),
    "15": ("Limpar Cache dos Navegadores", clean_browser_cache),
    "16": ("Limpar Miniaturas (Thumbnail Cache)", clean_thumbnails),

    # Otimização (20-24)
    "20": ("Otimizar Disco", optimize_disk),
    "21": ("Desfragmentar HD", defrag_hd),
    "22": ("TRIM SSD", trim_ssd),
    "23": ("Otimizar Inicialização", optimize_startup),
    "24": ("Limpar Programas de Startup", clean_startup_programs),

    # Rede (30-36)
    "30": ("Resetar Rede", reset_network),
    "31": ("Flush DNS", flush_dns),
    "32": ("Renovar IP", renew_ip),
    "33": ("Reset Winsock", reset_winsock),
    "34": ("Alterar DNS para Google", set_dns_google),
    "35": ("Alterar DNS para Cloudflare", set_dns_cloudflare),
    "36": ("Testar Latência", test_latency),

    # Reparo (40-44)
    "40": ("SFC /SCANNOW", run_sfc),
    "41": ("DISM RestoreHealth", run_dism),
    "42": ("CHKDSK", run_chkdsk),
    "43": ("Reparar Windows Update", repair_windows_update),
    "44": ("Reparar Arquivos do Sistema", repair_system_files),

    # Segurança (50-53)
    "50": ("Verificar Windows Defender", check_defender),
    "51": ("Atualizar Assinaturas", update_signatures),
    "52": ("Verificar Firewall", check_firewall),
    "53": ("Remover Políticas Inválidas", remove_invalid_policies),

    # Drivers (60-62)
    "60": ("Mostrar Drivers", show_drivers),
    "61": ("Exportar Drivers", export_drivers),
    "62": ("Atualizar Drivers (Winget)", update_drivers_winget),

    # Aplicativos (70-73)
    "70": ("Atualizar Todos os Programas", update_all_programs),
    "71": ("Atualizar Winget", update_winget),
    "72": ("Atualizar Microsoft Store", update_microsoft_store),
    "73": ("Desinstalador Rápido", quick_uninstall),

    # Energia (80-82)
    "80": ("Alto Desempenho", set_high_performance),
    "81": ("Equilibrado", set_balanced),
    "82": ("Economia de Energia", set_power_saver),

    # Desenvolvimento (90-96)
    "90": ("Instalar Git", install_git),
    "91": ("Instalar Python", install_python),
    "92": ("Instalar Node.js", install_nodejs),
    "93": ("Instalar VS Code", install_vscode),
    "94": ("Instalar Docker", install_docker),
    "95": ("Instalar Homebrew", install_homebrew),
    "96": ("Atualizar Homebrew", update_homebrew),

    # Ferramentas (100-104)
    "100": ("Abrir Gerenciador de Tarefas", open_task_manager),
    "101": ("Abrir Editor de Registro", open_registry_editor),
    "102": ("Abrir Serviços", open_services),
    "103": ("Abrir CMD como Admin", open_cmd_admin),
    "104": ("Abrir PowerShell", open_powershell),

    # Relatórios (110-113)
    "110": ("Exportar Informações do Sistema", export_system_info),
    "111": ("Exportar Relatório HTML", export_html_report),
    "112": ("Exportar Relatório TXT", export_txt_report),
    "113": ("Exportar Relatório JSON", export_json_report),

    # Avançado (120-124)
    "120": ("Executar Todas as Otimizações", run_all_optimizations),
    "121": ("Modo Gamer", gamer_mode),
    "122": ("Modo Trabalho", work_mode),
    "123": ("Restaurar Configurações", restore_defaults),
    "124": ("Limpeza Completa", full_cleanup),

    # Serviços (130-132)
    "130": ("Desabilitar Serviços Desnecessários", disable_unnecessary_services),
    "131": ("Verificar Status dos Serviços", list_disabled_services),
    "132": ("Reabilitar Todos os Serviços", enable_all_services),
}

# Categorias para exibição no menu
CATEGORIES = [
    ("", [("1", "Criar Ponto de Restauração")]),
    ("LIMPEZA", [
        ("10", "Limpar Arquivos Temporários"),
        ("11", "Limpar Lixeira"),
        ("12", "Limpar Prefetch"),
        ("13", "Limpar Cache do Windows Update"),
        ("14", "Limpar Logs"),
        ("15", "Limpar Cache dos Navegadores"),
        ("16", "Limpar Miniaturas (Thumbnail Cache)"),
    ]),
    ("OTIMIZAÇÃO", [
        ("20", "Otimizar Disco"),
        ("21", "Desfragmentar HD"),
        ("22", "TRIM SSD"),
        ("23", "Otimizar Inicialização"),
        ("24", "Limpar Programas de Startup"),
    ]),
    ("REDE", [
        ("30", "Resetar Rede"),
        ("31", "Flush DNS"),
        ("32", "Renovar IP"),
        ("33", "Reset Winsock"),
        ("34", "Alterar DNS para Google"),
        ("35", "Alterar DNS para Cloudflare"),
        ("36", "Testar Latência"),
    ]),
    ("REPARO", [
        ("40", "SFC /SCANNOW"),
        ("41", "DISM RestoreHealth"),
        ("42", "CHKDSK"),
        ("43", "Reparar Windows Update"),
        ("44", "Reparar Arquivos do Sistema"),
    ]),
    ("SEGURANÇA", [
        ("50", "Verificar Windows Defender"),
        ("51", "Atualizar Assinaturas"),
        ("52", "Verificar Firewall"),
        ("53", "Remover Políticas Inválidas"),
    ]),
    ("DRIVERS", [
        ("60", "Mostrar Drivers"),
        ("61", "Exportar Drivers"),
        ("62", "Atualizar Drivers (Winget)"),
    ]),
    ("APLICATIVOS", [
        ("70", "Atualizar Todos os Programas"),
        ("71", "Atualizar Winget"),
        ("72", "Atualizar Microsoft Store"),
        ("73", "Desinstalador Rápido"),
    ]),
    ("ENERGIA", [
        ("80", "Alto Desempenho"),
        ("81", "Equilibrado"),
        ("82", "Economia de Energia"),
    ]),
    ("DESENVOLVIMENTO", [
        ("90", "Instalar Git"),
        ("91", "Instalar Python"),
        ("92", "Instalar Node.js"),
        ("93", "Instalar VS Code"),
        ("94", "Instalar Docker"),
        ("95", "Instalar Homebrew"),
        ("96", "Atualizar Homebrew"),
    ]),
    ("FERRAMENTAS", [
        ("100", "Abrir Gerenciador de Tarefas"),
        ("101", "Abrir Editor de Registro"),
        ("102", "Abrir Serviços"),
        ("103", "Abrir CMD como Admin"),
        ("104", "Abrir PowerShell"),
    ]),
    ("RELATÓRIOS", [
        ("110", "Exportar Informações do Sistema"),
        ("111", "Exportar Relatório HTML"),
        ("112", "Exportar Relatório TXT"),
        ("113", "Exportar Relatório JSON"),
    ]),
    ("AVANÇADO", [
        ("120", "Executar Todas as Otimizações"),
        ("121", "Modo Gamer"),
        ("122", "Modo Trabalho"),
        ("123", "Restaurar Configurações"),
        ("124", "Limpeza Completa"),
    ]),
    ("SERVIÇOS", [
        ("130", "Desabilitar Serviços Desnecessários"),
        ("131", "Verificar Status dos Serviços"),
        ("132", "Reabilitar Todos os Serviços"),
    ]),
]


def display_main_menu():
    """Exibe o menu principal com categorias."""
    clear_screen()
    display_logo()

    print_separator("═")
    print(colorize("  Selecione uma opção:", Theme.TEXT))
    print_separator("═")
    print()

    for category, items in CATEGORIES:
        if category:
            print(colorize(f"  ── {category} ──", Theme.PRIMARY + Theme.BOLD))
        for num, desc in items:
            print_option(num, desc)
        print()


def get_user_choice() -> str:
    """Obtém a escolha do usuário."""
    return Config.get_input("  Digite a opção: ")


def execute_option(choice: str):
    """Executa a opção escolhida."""
    if choice == "0":
        _exit_program()
        return

    if choice not in OPTIONS:
        print_error("Opção inválida!")
        Config.pause()
        return

    clear_screen()
    name, func = OPTIONS[choice]

    print_header(name.upper())
    spinner("Preparando...", 0.5)

    try:
        func()
    except Exception as e:
        print_error(f"Erro ao executar: {e}")

    print()
    Config.pause()


def _exit_program():
    """Exibe mensagem de saída e encerra."""
    clear_screen()
    print()
    print_separator("═")
    print(colorize("  Obrigado por usar o NV Optimizer!", Theme.PRIMARY))
    print(colorize("  Até a próxima!", Theme.ACCENT))
    print_separator("═")
    print()
    exit(0)


def main_loop():
    """Loop principal do menu."""
    while True:
        try:
            display_main_menu()
            choice = get_user_choice()
            execute_option(choice)
        except KeyboardInterrupt:
            print()
            print_info("Use a opção [0] para sair.")
            Config.pause()
        except EOFError:
            _exit_program()

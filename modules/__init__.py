"""
Pacote de módulos de otimização do NV Optimizer.
"""

from .restore import create_restore_point
from .cleanup import (
    clean_temp_files, clean_recycle_bin, clean_prefetch,
    clean_windows_update_cache, clean_logs, clean_browser_cache, clean_thumbnails
)
from .disk import optimize_disk, defrag_hd, trim_ssd, optimize_startup, clean_startup_programs
from .network import (
    reset_network, flush_dns, renew_ip, reset_winsock,
    set_dns_google, set_dns_cloudflare, test_latency
)
from .repair import run_sfc, run_dism, run_chkdsk, repair_windows_update, repair_system_files
from .system import show_system_info
from .security import check_defender, update_signatures, check_firewall, remove_invalid_policies
from .drivers import show_drivers, export_drivers, update_drivers_winget
from .apps import update_all_programs, update_winget, update_microsoft_store, quick_uninstall
from .power import set_high_performance, set_balanced, set_power_saver
from .development import (
    install_git, install_python, install_nodejs, install_vscode,
    install_docker, install_homebrew, update_homebrew
)
from .tools import open_task_manager, open_registry_editor, open_services, open_cmd_admin, open_powershell
from .reports import export_system_info, export_html_report, export_txt_report, export_json_report
from .advanced import run_all_optimizations, gamer_mode, work_mode, restore_defaults, full_cleanup
from .services import disable_unnecessary_services, list_disabled_services, enable_all_services

# Backend NV Optimizer 2.0
from backend.api import BackendAPI, backend_api

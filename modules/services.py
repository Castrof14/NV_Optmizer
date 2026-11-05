"""
Módulo de serviços do NV Optimizer.
Gerencia serviços do Windows.
"""

import subprocess
from utils.colors import Theme, colorize
from utils.logger import logger
from utils.config import system_info
from utils.shell import (
    command_error, read_backup, require_windows_admin, run_hidden, write_backup,
)
from progress import progress_bar


BACKUP_FILE = "services_backup.json"

# Nunca são alterados por nenhuma função deste módulo, independentemente do nível.
PROTECTED_SERVICES = frozenset(name.lower() for name in (
    # Windows Defender e Segurança do Windows
    "WinDefend", "WdNisSvc", "WdNisDrv", "WdFilter", "WdBoot", "Sense", "MDCoreSvc",
    "SecurityHealthService", "wscsvc", "SgrmBroker", "SgrmAgent",
    "webthreatdefsvc", "webthreatdefusersvc",
    # Firewall e criptografia
    "MpsSvc", "BFE", "CryptSvc", "BDESVC", "KeyIso", "VaultSvc", "SamSs", "EFS",
    # Windows Update (usado também para atualizar os drivers)
    "wuauserv", "UsoSvc", "BITS", "WaaSMedicSvc", "TrustedInstaller", "DoSvc",
    # Rede, áudio e Bluetooth
    "Dhcp", "Dnscache", "NlaSvc", "netprofm", "nsi", "WlanSvc", "LanmanWorkstation",
    "iphlpsvc", "Audiosrv", "AudioEndpointBuilder", "bthserv", "BTAGService",
    # Núcleo do Windows, ponto de restauração e Microsoft Store
    "RpcSs", "RpcEptMapper", "DcomLaunch", "EventLog", "Schedule", "gpsvc", "Winmgmt",
    "PlugPlay", "Power", "ProfSvc", "LSM", "VSS", "swprv", "defragsvc",
    "AppXSvc", "ClipSVC", "InstallService", "LicenseManager", "StateRepository", "wlidsvc",
    # Xbox e Game Pass
    "XblAuthManager", "XblGameSave", "XboxNetApiSvc", "XboxGipSvc", "GamingServices",
    "GamingServicesNet",
))

# Níveis acumulativos: "Alto" inclui o Básico e "Gamer" inclui o Alto.
SERVICE_TIERS = {
    "basico": {
        "label": "Serviços Básicos",
        "badge": "Seguro",
        "description": "Telemetria e serviços que quase ninguém usa. Indicado para qualquer computador.",
        "warning": "Sem impacto no uso normal do computador.",
        "includes": None,
        "services": [
            ("DiagTrack", "Telemetria do Windows", "Coleta e envio de dados de uso"),
            ("dmwappushservice", "Roteamento WAP Push", "Envio de dados de diagnóstico"),
            ("WerSvc", "Relatório de Erros do Windows", "Envio automático de relatórios de erro"),
            ("wercplsupport", "Relatórios de Problemas", "Painel de relatórios de problemas"),
            ("MapsBroker", "Gerenciador de Mapas Baixados", "Atualização de mapas offline"),
            ("RemoteRegistry", "Registro Remoto", "Acesso ao Registro pela rede"),
            ("Fax", "Fax", "Envio e recebimento de fax"),
            ("RetailDemo", "Demonstração de Loja", "Modo de demonstração de loja"),
            ("AJRouter", "Roteador AllJoyn", "Comunicação com dispositivos AllJoyn"),
            ("wisvc", "Programa Windows Insider", "Versões de teste do Windows"),
            ("WalletService", "Carteira", "Serviço de carteira do Windows"),
            ("WMPNetworkSvc", "Compartilhamento do Windows Media Player", "Compartilhamento de mídia na rede"),
        ],
    },
    "alto": {
        "label": "Serviços Alto",
        "badge": "Avançado",
        "description": "Inclui o Básico e desativa indexação, pré-carregamento e acesso remoto.",
        "warning": (
            "Deixam de funcionar: Área de Trabalho Remota do Windows, hotspot móvel, localização, "
            "cartão inteligente, Arquivos Offline e controle dos pais. "
            "A busca de arquivos fica mais lenta e, em HD, os programas podem demorar mais para abrir."
        ),
        "includes": "basico",
        "services": [
            ("SysMain", "SysMain (Superfetch)", "Pré-carregamento de aplicativos"),
            ("WSearch", "Windows Search", "Indexação de arquivos"),
            ("lfsvc", "Geolocalização", "Localização e fuso horário automático"),
            ("TrkWks", "Cliente de Rastreamento de Links", "Rastreamento de atalhos na rede"),
            ("icssvc", "Hotspot Móvel", "Compartilhamento de internet por Wi-Fi"),
            ("SCardSvr", "Cartão Inteligente", "Leitura de cartão inteligente"),
            ("ScDeviceEnum", "Enumeração de Cartão Inteligente", "Detecção de cartão inteligente"),
            ("SCPolicySvc", "Política de Cartão Inteligente", "Política de remoção de cartão"),
            ("UmRdpService", "Redirecionador da Área de Trabalho Remota", "Redirecionamento de dispositivos"),
            ("SessionEnv", "Configuração da Área de Trabalho Remota", "Configuração de sessões remotas"),
            ("TermService", "Área de Trabalho Remota", "Conexões remotas ao computador"),
            ("RasAuto", "Conexão Automática de Acesso Remoto", "Discagem automática de conexões"),
            ("WpcMonSvc", "Controle dos Pais", "Restrições de contas infantis"),
            ("PhoneSvc", "Telefonia", "Chamadas pelo computador"),
            ("SEMgrSvc", "Pagamentos e NFC", "Pagamentos por aproximação"),
            ("PeerDistSvc", "BranchCache", "Cache de conteúdo em redes corporativas"),
            ("CscService", "Arquivos Offline", "Arquivos de rede disponíveis offline"),
            ("Wecsvc", "Coletor de Eventos", "Coleta de eventos de outros computadores"),
            ("WinRM", "Gerenciamento Remoto", "Administração remota via WS-Management"),
            ("AxInstSV", "Instalador ActiveX", "Instalação de controles ActiveX"),
            ("wcncsvc", "Windows Connect Now", "Configuração automática por Wi-Fi Protected Setup"),
            ("TroubleshootingSvc", "Solução de Problemas Recomendada", "Correções automáticas sugeridas"),
            ("diagnosticshub.standardcollector.service", "Hub de Diagnóstico", "Coletor usado por ferramentas de desenvolvimento"),
            ("NcdAutoSetup", "Configuração Automática de Dispositivos de Rede", "Instalação automática de dispositivos de rede"),
            ("MSiSCSI", "Iniciador iSCSI", "Acesso a discos iSCSI"),
            ("SNMPTRAP", "Interceptação SNMP", "Mensagens de gerenciamento de rede"),
        ],
    },
    "gamer": {
        "label": "Serviços Gamer",
        "badge": "Máximo",
        "description": "Inclui o Alto e desativa impressão, scanner, sensores e diagnóstico. Serviços Xbox são mantidos.",
        "warning": (
            "Além do nível Alto, deixam de funcionar: impressoras (incluindo imprimir em PDF), scanner, "
            "rotação automática de tela, histórico de arquivos e solução de problemas do Windows."
        ),
        "includes": "alto",
        "services": [
            ("PrintNotify", "Notificações de Impressora", "Extensões e avisos de impressora"),
            ("Spooler", "Spooler de Impressão", "Filas de impressão"),
            ("stisvc", "Aquisição de Imagens", "Scanners e câmeras WIA"),
            ("SensorService", "Sensores", "Gerenciamento de sensores"),
            ("SensrSvc", "Monitoramento de Sensores", "Brilho e rotação automáticos"),
            ("SensorDataService", "Dados de Sensores", "Entrega de dados dos sensores"),
            ("WdiServiceHost", "Host do Serviço de Diagnóstico", "Diagnóstico do Windows"),
            ("WdiSystemHost", "Host do Sistema de Diagnóstico", "Diagnóstico do Windows"),
            ("DPS", "Política de Diagnóstico", "Detecção de problemas do Windows"),
            ("fhsvc", "Histórico de Arquivos", "Backup automático de arquivos"),
            ("lltdsvc", "Mapeador de Topologia de Rede", "Mapa de dispositivos da rede"),
        ],
    },
}


def is_protected(service_name: str) -> bool:
    return service_name.lower() in PROTECTED_SERVICES


def get_tier_services(tier: str) -> list:
    """Serviços de um nível, incluindo os dos níveis anteriores."""
    if tier not in SERVICE_TIERS:
        raise ValueError(f"Nível de serviços desconhecido: {tier}")
    meta = SERVICE_TIERS[tier]
    inherited = get_tier_services(meta["includes"]) if meta["includes"] else []
    own = [
        {"name": name, "display": display, "description": description}
        for name, display, description in meta["services"]
    ]
    return inherited + own


def get_services_state() -> dict:
    """Situação real de cada nível de serviços neste computador."""
    state = {}
    for tier, meta in SERVICE_TIERS.items():
        services = []
        for service in get_tier_services(tier):
            status = _get_service_status(service["name"])
            services.append({**service, "exists": status["exists"], "start_type": status["start_type"]})
        state[tier] = {
            "label": meta["label"],
            "badge": meta["badge"],
            "description": meta["description"],
            "warning": meta["warning"],
            "services": services,
            "total": sum(1 for s in services if s["exists"]),
            "disabled": sum(1 for s in services if s["start_type"] == "Disabled"),
        }
    return state


def disable_service_tier(tier: str) -> list:
    """Desativa os serviços de um nível, guardando o estado anterior de cada um."""
    require_windows_admin("Desativar serviços")
    services = get_tier_services(tier)
    label = SERVICE_TIERS[tier]["label"]
    total = len(services)
    rows = []

    print(f"Desativando {label}...")
    for i, service in enumerate(services, 1):
        status = _get_service_status(service["name"])
        row = {
            "operation": f"Desativar ({label})",
            "service": service["display"],
            "before": status["start_type"],
            "after": "Disabled",
            "result": "IGNORADO",
            "detail": "",
        }
        if not status["exists"]:
            row["detail"] = "Não existe neste Windows"
        elif status["start_type"] == "Disabled":
            row["detail"] = "Já estava desativado"
        else:
            result = _stop_and_disable_service(service["name"])
            row["result"] = "OK" if result["success"] else "FALHA"
            row["detail"] = result["error"] or ""
            mark = "OK" if result["success"] else f"FALHA: {result['error']}"
            print(f"[{i}/{total}] {service['display']}: {mark}")
        rows.append(row)

    changed = sum(1 for r in rows if r["result"] == "OK")
    failed = sum(1 for r in rows if r["result"] == "FALHA")
    print(f"Concluído: {changed} desativados, {failed} falhas. Reinicie o computador para aplicar tudo.")
    return rows


def restore_services() -> list:
    """Devolve os serviços ao estado anterior à otimização."""
    require_windows_admin("Restaurar serviços")
    backup = read_backup(BACKUP_FILE, {})
    displays = {s["name"]: s["display"] for s in SERVICES_TO_DISABLE}
    for meta in SERVICE_TIERS.values():
        displays.update({name: display for name, display, _ in meta["services"]})

    rows = []
    for name in dict.fromkeys([*backup, *displays]):
        status = _get_service_status(name)
        # Sem backup, só reabilita o que está desativado; o restante não foi alterado.
        if not status["exists"] or (name not in backup and status["start_type"] != "Disabled"):
            continue
        result = _enable_service(name)
        rows.append({
            "operation": "Restaurar serviço",
            "service": displays.get(name, name),
            "before": status["start_type"],
            "after": result.get("start"),
            "result": "OK" if result["success"] else "FALHA",
            "detail": result["error"] or "",
        })
        print(f"{displays.get(name, name)}: {'OK' if result['success'] else 'FALHA'}")
    print(f"Serviços restaurados: {sum(1 for r in rows if r['result'] == 'OK')}/{len(rows)}")
    return rows


def disable_services_basic():
    """[133] Desativar Serviços Básicos"""
    disable_service_tier("basico")


def disable_services_high():
    """[134] Desativar Serviços Alto"""
    disable_service_tier("alto")


def disable_services_gamer():
    """[135] Desativar Serviços Gamer"""
    disable_service_tier("gamer")


# Serviços para desabilitar
SERVICES_TO_DISABLE = [
    {
        "name": "DiagTrack",
        "display": "Connected User Experiences and Telemetry",
        "description": "Desabilita coleta de telemetria do Windows",
    },
    {
        "name": "dmwappushservice",
        "display": "dmwappushservice",
        "description": "Serviço de envio de dados de diagnóstico",
    },
    {
        "name": "SysMain",
        "display": "SysMain",
        "description": "Desabilita pré-carregamento de aplicativos em segundo plano",
    },
    {
        "name": "MapsBroker",
        "display": "Downloaded Maps Manager",
        "description": "Desabilita mapas offline do Windows",
    },
    {
        "name": "RemoteRegistry",
        "display": "Remote Registry",
        "description": "Desabilita acesso remoto ao Registro do Windows",
    },
    {
        "name": "WerSvc",
        "display": "Windows Error Reporting Service",
        "description": "Desabilita envio automático de relatórios de erro",
    },
    {
        "name": "Fax",
        "display": "Fax",
        "description": "Desabilita serviço de fax",
    },
    {
        "name": "RetailDemo",
        "display": "Retail Demo Service",
        "description": "Desabilita modo demonstração de loja",
    },
    {
        "name": "WSearch",
        "display": "Windows Search",
        "description": "Desabilita indexação de arquivos para economizar recursos",
    },
]


def disable_unnecessary_services():
    """Desabilita serviços desnecessários do Windows."""
    print(colorize("\n  Desabilitando serviços desnecessários...\n", Theme.PRIMARY))

    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    total = len(SERVICES_TO_DISABLE)
    disabled = 0
    failed = 0

    for i, service in enumerate(SERVICES_TO_DISABLE, 1):
        progress_bar(i, total, prefix="  Processando:")
        print(f"\n    {colorize(service['display'], Theme.TEXT)}")
        print(f"    {colorize(service['description'], Theme.MUTED)}")

        result = _stop_and_disable_service(service["name"])
        if result["success"]:
            logger.success(f"  ✓ {service['display']} desabilitado")
            disabled += 1
        else:
            logger.warning(f"  ✗ {service['display']}: {result['error']}")
            failed += 1

    progress_bar(total, total, prefix="  Processando:")

    print()
    print(colorize("  ════════════════════════════════════════════", Theme.SUCCESS))
    print(colorize(f"  Serviços desabilitados: {disabled}/{total}", Theme.SUCCESS))
    if failed > 0:
        print(colorize(f"  Falhas: {failed}", Theme.WARNING))
    print(colorize("  ════════════════════════════════════════════", Theme.SUCCESS))


def list_disabled_services():
    """Lista o status dos serviços."""
    print(colorize("\n  Verificando status dos serviços...\n", Theme.PRIMARY))

    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    print(colorize("  ── SERVIÇOS ──", Theme.PRIMARY))
    print()

    for service in SERVICES_TO_DISABLE:
        status = _get_service_status(service["name"])
        if status["exists"]:
            if status["start_type"] == "Disabled":
                status_text = colorize("DESABILITADO", Theme.SUCCESS)
            else:
                status_text = colorize(status["start_type"], Theme.TEXT)

            print(f"  {colorize(service['display'], Theme.TEXT)}")
            print(f"    Nome: {service['name']}")
            print(f"    Status: {status_text}")
            print()
        else:
            print(f"  {colorize(service['display'], Theme.TEXT)}")
            print(f"    {colorize('Não encontrado', Theme.MUTED)}")
            print()


def enable_all_services():
    """Reabilita todos os serviços que foram desabilitados."""
    print(colorize("\n  Reabilitando serviços...\n", Theme.PRIMARY))

    if not system_info.is_windows:
        logger.warning("Esta função é exclusiva do Windows")
        return

    try:
        rows = restore_services()
    except RuntimeError as e:
        logger.warning(str(e))
        return
    enabled = sum(1 for r in rows if r["result"] == "OK")
    logger.success(f"Serviços reabilitados: {enabled}/{len(rows)}")


def _stop_and_disable_service(service_name: str) -> dict:
    """Guarda o tipo de inicialização atual, para e desabilita um serviço."""
    if is_protected(service_name):
        return {"success": False, "error": "Serviço protegido: não pode ser desativado."}

    status = _get_service_status(service_name)
    if not status["exists"]:
        return {"success": False, "error": "Serviço não encontrado."}

    try:
        if status["sc_start"] != "disabled":
            backup = read_backup(BACKUP_FILE, {})
            # Mantém o primeiro valor gravado: é o original, anterior a qualquer otimização.
            backup.setdefault(service_name, status["sc_start"])
            write_backup(BACKUP_FILE, backup)

        # sc stop falha na hora se houver dependentes; net stop ficaria aguardando confirmação.
        run_hidden(["sc", "stop", service_name])

        result = run_hidden(["sc", "config", service_name, "start=", "disabled"])
        if result.returncode == 0:
            return {"success": True, "error": None}
        return {"success": False, "error": command_error(result)}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _enable_service(service_name: str) -> dict:
    """Devolve um serviço ao tipo de inicialização original (Manual, se não houver backup)."""
    backup = read_backup(BACKUP_FILE, {})
    start = backup.get(service_name, "demand")
    try:
        result = run_hidden(["sc", "config", service_name, "start=", start])
        if result.returncode != 0:
            return {"success": False, "error": command_error(result), "start": start}

        if start in ("auto", "delayed-auto"):
            run_hidden(["sc", "start", service_name])
        if service_name in backup:
            del backup[service_name]
            write_backup(BACKUP_FILE, backup)
        return {"success": True, "error": None, "start": start}

    except Exception as e:
        return {"success": False, "error": str(e), "start": start}


def _get_service_status(service_name: str) -> dict:
    """Lê o tipo de inicialização no Registro: é rápido e não depende do idioma do Windows."""
    missing = {"exists": False, "start_type": None, "sc_start": None}
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            rf"SYSTEM\CurrentControlSet\Services\{service_name}",
        ) as key:
            start = winreg.QueryValueEx(key, "Start")[0]
            try:
                delayed = winreg.QueryValueEx(key, "DelayedAutostart")[0]
            except OSError:
                delayed = 0
    except (ImportError, OSError):
        return missing

    if start == 2:
        start_type, sc_start = "Automatic", "delayed-auto" if delayed else "auto"
    elif start == 3:
        start_type, sc_start = "Manual", "demand"
    elif start == 4:
        start_type, sc_start = "Disabled", "disabled"
    else:
        # Boot/System: drivers carregados pelo próprio kernel.
        start_type, sc_start = "System", "boot" if start == 0 else "system"
    return {"exists": True, "start_type": start_type, "sc_start": sc_start}

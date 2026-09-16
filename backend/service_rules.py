"""
NV Optimizer 2.0 - Sistema de Regras de Serviços
Estrutura organizada para otimizações de Office e Gaming.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum


class ServiceAction(str, Enum):
    KEEP = "KEEP"
    DISABLE_IF_UNUSED = "DISABLE_IF_UNUSED"
    DISABLE = "DISABLE"
    MANUAL_IF_UNUSED = "MANUAL_IF_UNUSED"
    MANUAL = "MANUAL"
    AUTO = "AUTO"


@dataclass
class ServiceRule:
    name: str                       # Nome do serviço (ex: spooler)
    display: str                    # Nome amigável
    description: str                # Descrição do que o serviço faz
    officeAction: ServiceAction     # Ação no perfil Office
    gamingAction: ServiceAction     # Ação no perfil Gaming
    requiresConfirmation: bool = False
    canRestore: bool = True

    def to_dict(self) -> dict:
        data = asdict(self)
        data["officeAction"] = self.officeAction.value
        data["gamingAction"] = self.gamingAction.value
        return data


# Regras de serviços do sistema
SERVICE_RULES: list[ServiceRule] = [
    # === Segurança (sempre KEEP) ===
    ServiceRule(
        "WinDefend", "Windows Defender",
        "Proteção antivírus do Windows. Manter ativo por segurança.",
        ServiceAction.KEEP, ServiceAction.KEEP, requiresConfirmation=True,
    ),
    ServiceRule(
        "SecurityHealthService", "Windows Security Health Service",
        "Serviço de saúde da segurança do Windows.",
        ServiceAction.KEEP, ServiceAction.KEEP,
    ),
    ServiceRule(
        "bfe", "Base Filtering Engine",
        "Firewall e filtro de pacotes. Necessário para segurança de rede.",
        ServiceAction.KEEP, ServiceAction.KEEP,
    ),
    ServiceRule(
        "wscsvc", "Windows Security Center",
        "Central de segurança do Windows.",
        ServiceAction.KEEP, ServiceAction.KEEP,
    ),
    ServiceRule(
        "MpsSvc", "Windows Defender Firewall",
        "Firewall do Windows. Manter por segurança.",
        ServiceAction.KEEP, ServiceAction.KEEP,
    ),
    ServiceRule(
        "WdNisSvc", "Windows Defender Network Inspection Service",
        "Inspeção de rede do Defender.",
        ServiceAction.KEEP, ServiceAction.KEEP,
    ),
    ServiceRule(
        "Sense", "Windows Defender Advanced Threat Protection",
        "Proteção avançada contra ameaças.",
        ServiceAction.KEEP, ServiceAction.KEEP,
    ),

    # === Windows Update (KEEP para Office, MANUAL para Gaming) ===
    ServiceRule(
        "wuauserv", "Windows Update",
        "Serviço de atualização do Windows. Manter para segurança e correções.",
        ServiceAction.KEEP, ServiceAction.MANUAL_IF_UNUSED, requiresConfirmation=True,
    ),
    ServiceRule(
        "Bits", "Background Intelligent Transfer (BITS)",
        "Transferência em segundo plano usada por Windows Update e outros.",
        ServiceAction.KEEP, ServiceAction.MANUAL_IF_UNUSED,
    ),
    ServiceRule(
        "UsoSvc", "Update Orchestrator Service",
        "Orquestrador de atualizações do Windows.",
        ServiceAction.KEEP, ServiceAction.MANUAL_IF_UNUSED,
    ),

    # === Rede (KEEP sempre) ===
    ServiceRule(
        "Dhcp", "DHCP Client",
        "Obtém endereço IP dinâmico. Necessário para rede.",
        ServiceAction.KEEP, ServiceAction.KEEP,
    ),
    ServiceRule(
        "Dnscache", "DNS Client",
        "Cache de resolução DNS. Necessário para navegação.",
        ServiceAction.KEEP, ServiceAction.KEEP,
    ),
    ServiceRule(
        "NlaSvc", "Network Location Awareness",
        "Detecção de rede e conexão.",
        ServiceAction.KEEP, ServiceAction.KEEP,
    ),
    ServiceRule(
        "netprofm", "Network List Service",
        "Lista de redes e conexões.",
        ServiceAction.KEEP, ServiceAction.KEEP,
    ),
    ServiceRule(
        "LanmanServer", "Server",
        "Compartilhamento de arquivos na rede (SMB).",
        ServiceAction.MANUAL_IF_UNUSED, ServiceAction.MANUAL_IF_UNUSED,
    ),
    ServiceRule(
        "LanmanWorkstation", "Workstation",
        "Acesso a compartilhamentos de rede.",
        ServiceAction.KEEP, ServiceAction.MANUAL_IF_UNUSED,
    ),
    ServiceRule(
        "WlanSvc", "WLAN AutoConfig",
        "Conexão Wi-Fi. Manter se usar Wi-Fi.",
        ServiceAction.KEEP, ServiceAction.KEEP,
    ),
    # === Impressora (KEEP para Office, MANUAL para Gaming) ===
    ServiceRule(
        "Spooler", "Print Spooler",
        "Gerencia filas de impressão. Necessário para impressoras.",
        ServiceAction.KEEP, ServiceAction.DISABLE_IF_UNUSED, canRestore=True,
    ),
    ServiceRule(
        "PrintNotify", "Printer Extensions and Notifications",
        "Extensões de impressora.",
        ServiceAction.KEEP, ServiceAction.MANUAL_IF_UNUSED,
    ),

    # === Bluetooth / Áudio (KEEP) ===
    ServiceRule(
        "bthserv", "Bluetooth Support Service",
        "Suporte a dispositivos Bluetooth.",
        ServiceAction.KEEP, ServiceAction.MANUAL_IF_UNUSED,
    ),
    ServiceRule(
        "BTAGService", "Bluetooth Audio Gateway Service",
        "Áudio via Bluetooth.",
        ServiceAction.KEEP, ServiceAction.MANUAL_IF_UNUSED,
    ),
    ServiceRule(
        "Audiosrv", "Windows Audio",
        "Serviço de áudio do Windows. Necessário para som.",
        ServiceAction.KEEP, ServiceAction.KEEP,
    ),
    ServiceRule(
        "AudioEndpointBuilder", "Windows Audio Endpoint Builder",
        "Gerencia dispositivos de áudio.",
        ServiceAction.KEEP, ServiceAction.KEEP,
    ),

    # === Telemetria (desabilitar) ===
    ServiceRule(
        "DiagTrack", "Connected User Experiences and Telemetry",
        "Coleta de telemetria do Windows.",
        ServiceAction.DISABLE_IF_UNUSED, ServiceAction.DISABLE,
    ),
    ServiceRule(
        "dmwappushservice", "Diagnostic Policy Service (dmwappush)",
        "Serviço de envio de dados de diagnóstico.",
        ServiceAction.DISABLE_IF_UNUSED, ServiceAction.DISABLE,
    ),
    ServiceRule(
        "WerSvc", "Windows Error Reporting",
        "Relatórios de erro do Windows.",
        ServiceAction.DISABLE_IF_UNUSED, ServiceAction.DISABLE,
    ),
    ServiceRule(
        "diagnosticshub.standardcollector.service",
        "Diagnostics Hub Standard Collector",
        "Coletor de diagnóstico.",
        ServiceAction.MANUAL_IF_UNUSED, ServiceAction.DISABLE,
    ),

    # === Busca / Indexação ===
    ServiceRule(
        "WSearch", "Windows Search",
        "Indexação de arquivos. Pode consumir recursos.",
        ServiceAction.MANUAL_IF_UNUSED, ServiceAction.DISABLE_IF_UNUSED,
    ),

    # === Softwares / SysMain ===
    ServiceRule(
        "SysMain", "SysMain (Superfetch)",
        "Pré-carregamento de aplicativos. Em SSDs tem pouco benefício.",
        ServiceAction.MANUAL_IF_UNUSED, ServiceAction.DISABLE_IF_UNUSED,
    ),

    # === Xbox / Game Pass (KEEP no Gaming) ===
    ServiceRule(
        "XblAuthManager", "Xbox Live Auth Manager",
        "Autenticação Xbox. Necessário para Game Pass e Xbox.",
        ServiceAction.MANUAL_IF_UNUSED, ServiceAction.KEEP,
    ),
    ServiceRule(
        "XblGameSave", "Xbox Live Game Save",
        "Save games na nuvem do Xbox.",
        ServiceAction.MANUAL_IF_UNUSED, ServiceAction.KEEP,
    ),
    ServiceRule(
        "XboxNetApiSvc", "Xbox Live Networking Service",
        "Rede Xbox Live.",
        ServiceAction.MANUAL_IF_UNUSED, ServiceAction.KEEP,
    ),
    ServiceRule(
        "XboxGipSvc", "Xbox Accessory Management Service",
        "Gerenciamento de acessórios Xbox.",
        ServiceAction.MANUAL_IF_UNUSED, ServiceAction.KEEP,
    ),
    ServiceRule(
        "GamingServices", "Gaming Services",
        "Serviços de jogos do Microsoft Store/Game Pass.",
        ServiceAction.MANUAL_IF_UNUSED, ServiceAction.KEEP,
    ),

    # === Outros serviços de sistema ===
    ServiceRule(
        "MapsBroker", "Downloaded Maps Manager",
        "Gerenciador de mapas offline.",
        ServiceAction.DISABLE_IF_UNUSED, ServiceAction.DISABLE_IF_UNUSED,
    ),
    ServiceRule(
        "RemoteRegistry", "Remote Registry",
        "Acesso remoto ao registro. Risco de segurança.",
        ServiceAction.DISABLE_IF_UNUSED, ServiceAction.DISABLE,
        requiresConfirmation=True,
    ),
    ServiceRule(
        "Fax", "Fax",
        "Serviço de fax. Raramente utilizado.",
        ServiceAction.DISABLE_IF_UNUSED, ServiceAction.DISABLE,
    ),
    ServiceRule(
        "RetailDemo", "Retail Demo Service",
        "Modo demonstração de loja.",
        ServiceAction.DISABLE_IF_UNUSED, ServiceAction.DISABLE,
    ),
    ServiceRule(
        "Themes", "Themes",
        "Temas visuais do Windows.",
        ServiceAction.KEEP, ServiceAction.MANUAL_IF_UNUSED,
    ),
    ServiceRule(
        "gpsvc", "Group Policy Client",
        "Política de grupo. Necessário para configurações.",
        ServiceAction.KEEP, ServiceAction.KEEP,
    ),
    ServiceRule(
        "Schedule", "Task Scheduler",
        "Agendador de tarefas. Necessário para muitas funções.",
        ServiceAction.KEEP, ServiceAction.KEEP,
    ),
    ServiceRule(
        "EventLog", "Windows Event Log",
        "Registro de eventos do sistema.",
        ServiceAction.KEEP, ServiceAction.KEEP,
    ),
    ServiceRule(
        "RpcSs", "Remote Procedure Call (RPC)",
        "Núcleo do Windows. Não desabilitar nunca.",
        ServiceAction.KEEP, ServiceAction.KEEP,
    ),
    ServiceRule(
        "CryptSvc", "Cryptographic Services",
        "Serviços criptográficos.",
        ServiceAction.KEEP, ServiceAction.KEEP,
    ),
    ServiceRule(
        "DcomLaunch", "DCOM Server Process Launcher",
        "Obrigatório para o Windows.",
        ServiceAction.KEEP, ServiceAction.KEEP,
    ),
]

# Filtra duplicatas preservando a primeira ocorrência
_SEEN = set()
SERVICE_RULES_UNIQUE = []
for rule in SERVICE_RULES:
    if rule.name not in _SEEN:
        _SEEN.add(rule.name)
        SERVICE_RULES_UNIQUE.append(rule)
SERVICE_RULES = SERVICE_RULES_UNIQUE


def get_rules() -> list:
    return [r.to_dict() for r in SERVICE_RULES]


def get_rule(name: str) -> ServiceRule | None:
    for rule in SERVICE_RULES:
        if rule.name == name:
            return rule
    return None
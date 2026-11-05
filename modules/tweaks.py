"""
Otimizações adicionais do Windows (Registro e comandos do sistema).

Antes de alterar um valor, o conteúdo original é guardado em um backup, permitindo
desfazer tudo depois. Nenhuma otimização mexe no Windows Defender, no firewall, no
Windows Update nem nas proteções de segurança do sistema (como o Core Isolation).
"""

from dataclasses import dataclass

from utils.shell import command_error, read_backup, require_windows_admin, run_hidden, write_backup

BACKUP_FILE = "tweaks_backup.json"

DWORD = "dword"
TEXT = "sz"
BINARY = "binary"

_DESKTOP = r"Control Panel\Desktop"
_CURRENT = r"Software\Microsoft\Windows\CurrentVersion"
_SUGGESTIONS = rf"{_CURRENT}\ContentDeliveryManager"
_MULTIMEDIA = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"


def _task(name: str) -> tuple:
    """Comando para desativar/reativar uma tarefa agendada (pode não existir em todo Windows)."""
    return (
        ["schtasks", "/Change", "/TN", name, "/Disable"],
        ["schtasks", "/Change", "/TN", name, "/Enable"],
        False,
    )


@dataclass(frozen=True)
class Tweak:
    id: str
    label: str
    description: str
    values: tuple = ()      # (raiz, caminho, nome, tipo, dado)
    commands: tuple = ()    # (comando, comando para desfazer, obrigatório)
    recommended: bool = True


TWEAKS = (
    Tweak(
        "game_mode", "Ativar Modo de Jogo",
        "Prioriza o jogo aberto em relação às tarefas em segundo plano.",
        values=(
            ("HKCU", r"Software\Microsoft\GameBar", "AutoGameModeEnabled", DWORD, 1),
            ("HKCU", r"Software\Microsoft\GameBar", "AllowAutoGameMode", DWORD, 1),
        ),
    ),
    Tweak(
        "game_dvr", "Desativar gravação em segundo plano",
        "Desliga a captura do Xbox Game Bar, que consome CPU e GPU durante os jogos.",
        values=(
            ("HKCU", r"System\GameConfigStore", "GameDVR_Enabled", DWORD, 0),
            ("HKCU", rf"{_CURRENT}\GameDVR", "AppCaptureEnabled", DWORD, 0),
        ),
    ),
    Tweak(
        "game_priority", "Priorizar jogos no agendador",
        "Dá mais prioridade de CPU e GPU para jogos e remove o limite de rede para multimídia.",
        values=(
            ("HKLM", _MULTIMEDIA, "SystemResponsiveness", DWORD, 10),
            ("HKLM", _MULTIMEDIA, "NetworkThrottlingIndex", DWORD, 0xFFFFFFFF),
            ("HKLM", rf"{_MULTIMEDIA}\Tasks\Games", "GPU Priority", DWORD, 8),
            ("HKLM", rf"{_MULTIMEDIA}\Tasks\Games", "Priority", DWORD, 6),
            ("HKLM", rf"{_MULTIMEDIA}\Tasks\Games", "Scheduling Category", TEXT, "High"),
            ("HKLM", rf"{_MULTIMEDIA}\Tasks\Games", "SFIO Priority", TEXT, "High"),
        ),
    ),
    Tweak(
        "visual_effects", "Reduzir efeitos visuais",
        "Remove animações e transparências. Saia e entre na conta para aplicar por completo.",
        values=(
            ("HKCU", rf"{_CURRENT}\Explorer\VisualEffects", "VisualFXSetting", DWORD, 2),
            ("HKCU", _DESKTOP, "UserPreferencesMask", BINARY, "9012038010000000"),
            ("HKCU", _DESKTOP, "MenuShowDelay", TEXT, "0"),
            ("HKCU", rf"{_DESKTOP}\WindowMetrics", "MinAnimate", TEXT, "0"),
            ("HKCU", rf"{_CURRENT}\Themes\Personalize", "EnableTransparency", DWORD, 0),
            ("HKCU", r"Software\Microsoft\Windows\DWM", "EnableAeroPeek", DWORD, 0),
        ),
    ),
    Tweak(
        "startup_delay", "Remover atraso na inicialização",
        "Abre mais cedo os programas configurados para iniciar com o Windows.",
        values=(("HKCU", rf"{_CURRENT}\Explorer\Serialize", "StartupDelayInMSec", DWORD, 0),),
    ),
    Tweak(
        "background_apps", "Desativar apps em segundo plano",
        "Impede apps da Microsoft Store de rodar fechados. Alguns podem deixar de enviar notificações.",
        values=(("HKCU", rf"{_CURRENT}\BackgroundAccessApplications", "GlobalUserDisabled", DWORD, 1),),
    ),
    Tweak(
        "telemetry", "Reduzir telemetria",
        "Reduz o envio de dados, desativa o ID de publicidade e as tarefas de coleta.",
        values=(
            ("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry", DWORD, 0),
            ("HKCU", rf"{_CURRENT}\AdvertisingInfo", "Enabled", DWORD, 0),
        ),
        commands=(
            _task(r"\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser"),
            _task(r"\Microsoft\Windows\Application Experience\ProgramDataUpdater"),
            _task(r"\Microsoft\Windows\Customer Experience Improvement Program\Consolidator"),
            _task(r"\Microsoft\Windows\Customer Experience Improvement Program\UsbCeip"),
        ),
    ),
    Tweak(
        "suggestions", "Remover sugestões e anúncios",
        "Desliga dicas, apps sugeridos e instalações silenciosas de apps promocionais.",
        values=tuple(
            ("HKCU", _SUGGESTIONS, name, DWORD, 0)
            for name in (
                "SilentInstalledAppsEnabled", "SystemPaneSuggestionsEnabled", "SoftLandingEnabled",
                "SubscribedContent-338388Enabled", "SubscribedContent-338389Enabled",
                "SubscribedContent-353694Enabled", "SubscribedContent-353696Enabled",
            )
        ),
    ),
    Tweak(
        "web_search", "Remover resultados da web na busca",
        "O menu Iniciar passa a buscar somente no computador.",
        values=(
            ("HKCU", r"Software\Policies\Microsoft\Windows\Explorer", "DisableSearchBoxSuggestions", DWORD, 1),
            ("HKCU", rf"{_CURRENT}\Search", "BingSearchEnabled", DWORD, 0),
        ),
    ),
    Tweak(
        "widgets", "Desativar widgets",
        "Remove o painel de notícias e widgets e seus processos em segundo plano.",
        values=(("HKLM", r"SOFTWARE\Policies\Microsoft\Dsh", "AllowNewsAndInterests", DWORD, 0),),
    ),
    Tweak(
        "last_access", "Reduzir gravações no disco",
        "Deixa de gravar a data do último acesso de cada arquivo.",
        commands=((
            ["fsutil", "behavior", "set", "disablelastaccess", "1"],
            ["fsutil", "behavior", "set", "disablelastaccess", "2"],
            True,
        ),),
    ),
    # Opcionais: dependem do uso de cada pessoa, por isso ficam fora do "aplicar recomendadas".
    Tweak(
        "mouse_acceleration", "Desativar aceleração do mouse",
        "Deixa a mira mais consistente em jogos. Muda a sensação do mouse.",
        values=(
            ("HKCU", r"Control Panel\Mouse", "MouseSpeed", TEXT, "0"),
            ("HKCU", r"Control Panel\Mouse", "MouseThreshold1", TEXT, "0"),
            ("HKCU", r"Control Panel\Mouse", "MouseThreshold2", TEXT, "0"),
        ),
        recommended=False,
    ),
    Tweak(
        "hibernation", "Desativar hibernação",
        "Libera vários GB em disco. Remove a hibernação e a inicialização rápida do Windows.",
        commands=((["powercfg", "/hibernate", "off"], ["powercfg", "/hibernate", "on"], True),),
        recommended=False,
    ),
)

_TWEAKS_BY_ID = {tweak.id: tweak for tweak in TWEAKS}


def _hive(winreg, root: str):
    return winreg.HKEY_CURRENT_USER if root == "HKCU" else winreg.HKEY_LOCAL_MACHINE


def _read_original(winreg, root: str, path: str, name: str) -> dict:
    """Valor atual em formato que pode ser gravado no backup."""
    try:
        with winreg.OpenKey(_hive(winreg, root), path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            data, kind = winreg.QueryValueEx(key, name)
    except OSError:
        return {"exists": False}
    if isinstance(data, bytes):
        return {"exists": True, "kind": kind, "hex": data.hex()}
    return {"exists": True, "kind": kind, "data": data}


def _write_value(winreg, root: str, path: str, name: str, kind: int, data):
    access = winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY
    with winreg.CreateKeyEx(_hive(winreg, root), path, 0, access) as key:
        winreg.SetValueEx(key, name, 0, kind, data)


def _delete_value(winreg, root: str, path: str, name: str):
    access = winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY
    try:
        with winreg.OpenKey(_hive(winreg, root), path, 0, access) as key:
            winreg.DeleteValue(key, name)
    except FileNotFoundError:
        pass


def _apply(tweak: Tweak):
    """Aplica uma otimização, guardando antes o estado original."""
    import winreg

    kinds = {DWORD: winreg.REG_DWORD, TEXT: winreg.REG_SZ, BINARY: winreg.REG_BINARY}
    backup = read_backup(BACKUP_FILE, {"values": {}, "commands": []})

    for root, path, name, kind, data in tweak.values:
        # Mantém o primeiro valor gravado: é o original, anterior a qualquer otimização.
        backup["values"].setdefault(
            "|".join((root, path, name)),
            _read_original(winreg, root, path, name),
        )
    if tweak.commands and tweak.id not in backup["commands"]:
        backup["commands"].append(tweak.id)
    write_backup(BACKUP_FILE, backup)

    for root, path, name, kind, data in tweak.values:
        value = bytes.fromhex(data) if kind == BINARY else data
        _write_value(winreg, root, path, name, kinds[kind], value)

    for command, _undo, required in tweak.commands:
        result = run_hidden(command, timeout=60)
        if result.returncode != 0 and required:
            raise RuntimeError(command_error(result))


def apply_tweak(tweak_id: str):
    """Aplica uma única otimização."""
    require_windows_admin("Esta otimização")
    tweak = _TWEAKS_BY_ID[tweak_id]
    print(tweak.description)
    _apply(tweak)
    print(f"{tweak.label}: OK")


def apply_recommended_tweaks():
    """Cria um ponto de restauração e aplica todas as otimizações recomendadas."""
    require_windows_admin("Aplicar otimizações")
    from modules.restore import create_restore_point
    create_restore_point()

    tweaks = [tweak for tweak in TWEAKS if tweak.recommended]
    failures = []
    for i, tweak in enumerate(tweaks, 1):
        try:
            _apply(tweak)
            print(f"[{i}/{len(tweaks)}] {tweak.label}: OK")
        except (OSError, RuntimeError, ValueError) as e:
            failures.append(tweak.label)
            print(f"[{i}/{len(tweaks)}] {tweak.label}: FALHA - {e}")

    if failures:
        raise RuntimeError(f"Não foi possível aplicar: {', '.join(failures)}")
    print("Otimizações aplicadas. Reinicie o computador para aplicar tudo.")


def undo_tweaks():
    """Devolve os valores originais de tudo o que foi alterado por este módulo."""
    require_windows_admin("Desfazer otimizações")
    import winreg

    backup = read_backup(BACKUP_FILE, {"values": {}, "commands": []})
    if not backup["values"] and not backup["commands"]:
        print("Nenhuma otimização para desfazer.")
        return

    failures = []
    for entry, original in list(backup["values"].items()):
        root, path, name = entry.split("|", 2)
        try:
            if not original["exists"]:
                _delete_value(winreg, root, path, name)
            elif "hex" in original:
                _write_value(winreg, root, path, name, original["kind"], bytes.fromhex(original["hex"]))
            else:
                _write_value(winreg, root, path, name, original["kind"], original["data"])
            del backup["values"][entry]
        except OSError as e:
            failures.append(f"{name}: {e}")

    for tweak_id in list(backup["commands"]):
        tweak_failed = False
        for _command, undo, required in _TWEAKS_BY_ID[tweak_id].commands:
            result = run_hidden(undo, timeout=60)
            if result.returncode != 0 and required:
                tweak_failed = True
                failures.append(f"{tweak_id}: {command_error(result)}")
        if not tweak_failed:
            backup["commands"].remove(tweak_id)

    write_backup(BACKUP_FILE, backup)
    if failures:
        raise RuntimeError(f"Não foi possível desfazer: {'; '.join(failures)}")
    print("Otimizações desfeitas. Reinicie o computador para aplicar tudo.")


def clean_component_store():
    """Remove versões antigas de componentes do Windows (WinSxS)."""
    require_windows_admin("Limpeza de componentes")
    print("Limpando componentes antigos do Windows. Pode levar vários minutos...")
    result = run_hidden(["dism", "/online", "/cleanup-image", "/startcomponentcleanup"], timeout=60 * 60)
    if result.returncode != 0:
        raise RuntimeError(command_error(result))
    print("Limpeza de componentes concluída.")

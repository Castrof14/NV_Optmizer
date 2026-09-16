"""
NV Optimizer 2.0 - Interface Gráfica
GUI moderna com CustomTkinter usando tema azul e amarelo.
Backend integrado via BackendAPI para operações reais do Windows.
"""

import customtkinter as ctk
import threading
import io
import sys
import json
from datetime import datetime

from utils.config import Config, system_info

# --- Módulos legados (v1.0) ---
from modules.restore import create_restore_point
from modules.cleanup import (
    clean_temp_files, clean_recycle_bin, clean_prefetch,
    clean_windows_update_cache, clean_logs, clean_browser_cache, clean_thumbnails
)
from modules.disk import optimize_disk, defrag_hd, trim_ssd, optimize_startup, clean_startup_programs
from modules.network import (
    reset_network, flush_dns, renew_ip, reset_winsock,
    set_dns_google, set_dns_cloudflare, test_latency
)
from modules.repair import run_sfc, run_dism, run_chkdsk, repair_windows_update, repair_system_files
from modules.security import check_defender, update_signatures, check_firewall, remove_invalid_policies
from modules.drivers import show_drivers, export_drivers, update_drivers_winget
from modules.apps import update_all_programs, update_winget, update_microsoft_store, quick_uninstall
from modules.power import set_high_performance, set_balanced, set_power_saver
from modules.development import (
    install_git, install_python, install_nodejs, install_vscode,
    install_docker, install_homebrew, update_homebrew
)
from modules.tools import open_task_manager, open_registry_editor, open_services, open_cmd_admin, open_powershell
from modules.reports import export_system_info, export_html_report, export_txt_report, export_json_report
from modules.advanced import run_all_optimizations, gamer_mode, work_mode, restore_defaults, full_cleanup
from modules.services import disable_unnecessary_services, list_disabled_services, enable_all_services

# --- Backend 2.0 ---
from backend.api import backend_api

ctk.set_appearance_mode("dark")

NV_BLUE = "#0011FF"
NV_YELLOW = "#FFEE00"
NV_DARK = "#0a0a2e"
NV_DARK2 = "#12123a"
NV_DARK3 = "#1a1a4e"
NV_BTN_HOVER = "#0022cc"
NV_YELLOW_DIM = "#ccbb00"
NV_RED = "#ff3333"
NV_GREEN = "#33cc55"
NV_LOG_BG = "#080820"

CATEGORIES = {
    # =================================================================
    # CATEGORIAS DO BACKEND 2.0 (operam via BackendAPI)
    # =================================================================
    "Diagnóstico": [
        ("Status do Sistema", "api:system.info"),
        ("Verificar Compatibilidade", "api:system.check"),
        ("Verificar Ativação Windows", "api:licensing.windows"),
    ],
    "Programas": [
        ("Listar Programas", "api:programs.list"),
        ("Instalar AnyDesk", "api:programs.install:anydesk"),
        ("Instalar WinRAR", "api:programs.install:winrar"),
        ("Instalar 7-Zip", "api:programs.install:7zip"),
        ("Instalar Notepad++", "api:programs.install:notepadpp"),
        ("Instalar Brave", "api:programs.install:brave"),
        ("Instalar Chrome", "api:programs.install:chrome"),
        ("Instalar Steam", "api:programs.install:steam"),
        ("Instalar Epic Games", "api:programs.install:epic"),
    ],
    "Office": [
        ("Status do Office", "api:office.status"),
        ("Instalar Office LTSC 2024", "api:office.install"),
        ("Verificar Office", "api:office.check"),
    ],
    "Defender": [
        ("Status do Defender", "api:defender.status"),
        ("Ativar Defender", "api:defender.enable"),
        ("Desativar Defender", "api:defender.disable"),
        ("Atualizar Assinaturas", "api:defender.update"),
        ("Status Firewall", "api:firewall.status"),
    ],
    "GPU": [
        ("Info da GPU", "api:drivers.gpu"),
        ("Buscar Driver Oficial", "api:drivers.search"),
        ("Exportar Drivers", "api:drivers.export"),
    ],
    "Energia 2.0": [
        ("Ver Configurações", "api:power.settings"),
        ("Perfil Completo (Gaming)", "api:power.apply"),
        ("Plano Alto Desempenho", "api:power.plan:high_performance"),
        ("Tela Nunca Desligar", "api:power.screen-never"),
        ("Suspensão Nunca", "api:power.sleep-never"),
    ],
    "Stress Test": [
        ("Teste CPU 60s", "api:stress.cpu:60"),
        ("Teste GPU 60s", "api:stress.gpu:60"),
        ("Teste Memória 60s", "api:stress.memory:60"),
        ("Diagnóstico de Memória", "api:stress.memory-diagnostic"),
        ("Parar Teste", "api:stress.cancel"),
    ],
    "Otimização 2.0": [
        ("Analisar Perfil Office", "api:optimization.analyze:office"),
        ("Aplicar Perfil Office", "api:optimization.apply:office"),
        ("Analisar Perfil Gaming", "api:optimization.analyze:gaming"),
        ("Aplicar Perfil Gaming", "api:optimization.apply:gaming"),
        ("Ver Sessões de Restauração", "api:optimization.restore-points"),
    ],
    "Edge": [
        ("Status do Edge", "api:edge.status"),
        ("Desinstalar Edge", "api:edge.uninstall"),
    ],
    "Logs": [
        ("Ver Logs da Sessão", "api:logs.get"),
        ("Caminho dos Logs", "api:logs.paths"),
    ],
    # =================================================================
    # CATEGORIAS DO MÓDULO LEGADO (v1.0) — preservadas
    # =================================================================
    "Restauração": [
        ("Criar Ponto de Restauração", create_restore_point),
    ],
    "Limpeza": [
        ("Limpar Arquivos Temporários", clean_temp_files),
        ("Limpar Lixeira", clean_recycle_bin),
        ("Limpar Prefetch", clean_prefetch),
        ("Limpar Cache do Windows Update", clean_windows_update_cache),
        ("Limpar Logs", clean_logs),
        ("Limpar Cache dos Navegadores", clean_browser_cache),
        ("Limpar Miniaturas", clean_thumbnails),
    ],
    "Otimização": [
        ("Otimizar Disco", optimize_disk),
        ("Desfragmentar HD", defrag_hd),
        ("TRIM SSD", trim_ssd),
        ("Otimizar Inicialização", optimize_startup),
        ("Limpar Programas de Startup", clean_startup_programs),
    ],
    "Rede": [
        ("Resetar Rede", reset_network),
        ("Flush DNS", flush_dns),
        ("Renovar IP", renew_ip),
        ("Reset Winsock", reset_winsock),
        ("DNS Google", set_dns_google),
        ("DNS Cloudflare", set_dns_cloudflare),
        ("Testar Latência", test_latency),
    ],
    "Reparo": [
        ("SFC /SCANNOW", run_sfc),
        ("DISM RestoreHealth", run_dism),
        ("CHKDSK", run_chkdsk),
        ("Reparar Windows Update", repair_windows_update),
        ("Reparar Arquivos do Sistema", repair_system_files),
    ],
    "Segurança": [
        ("Windows Defender", check_defender),
        ("Atualizar Assinaturas", update_signatures),
        ("Verificar Firewall", check_firewall),
        ("Remover Políticas Inválidas", remove_invalid_policies),
    ],
    "Drivers": [
        ("Mostrar Drivers", show_drivers),
        ("Exportar Drivers", export_drivers),
        ("Atualizar Drivers", update_drivers_winget),
    ],
    "Aplicativos": [
        ("Atualizar Todos os Programas", update_all_programs),
        ("Atualizar Winget", update_winget),
        ("Atualizar Microsoft Store", update_microsoft_store),
        ("Desinstalador Rápido", quick_uninstall),
    ],
    "Energia": [
        ("Alto Desempenho", set_high_performance),
        ("Equilibrado", set_balanced),
        ("Economia de Energia", set_power_saver),
    ],
    "Desenvolvimento": [
        ("Instalar Git", install_git),
        ("Instalar Python", install_python),
        ("Instalar Node.js", install_nodejs),
        ("Instalar VS Code", install_vscode),
        ("Instalar Docker", install_docker),
        ("Instalar Homebrew", install_homebrew),
        ("Atualizar Homebrew", update_homebrew),
    ],
    "Ferramentas": [
        ("Gerenciador de Tarefas", open_task_manager),
        ("Editor de Registro", open_registry_editor),
        ("Serviços", open_services),
        ("CMD (Admin)", open_cmd_admin),
        ("PowerShell", open_powershell),
    ],
    "Relatórios": [
        ("Exportar Info do Sistema", export_system_info),
        ("Relatório HTML", export_html_report),
        ("Relatório TXT", export_txt_report),
        ("Relatório JSON", export_json_report),
    ],
    "Avançado": [
        ("Executar Todas Otimizações", run_all_optimizations),
        ("Modo Gamer", gamer_mode),
        ("Modo Trabalho", work_mode),
        ("Restaurar Configurações", restore_defaults),
        ("Limpeza Completa", full_cleanup),
    ],
    "Serviços": [
        ("Desabilitar Serviços", disable_unnecessary_services),
        ("Verificar Status", list_disabled_services),
        ("Reabilitar Serviços", enable_all_services),
    ],
}

CATEGORY_ICONS = {
    "Diagnóstico": "",
    "Programas": "",
    "Office": "",
    "Defender": "",
    "GPU": "",
    "Energia 2.0": "",
    "Stress Test": "",
    "Otimização 2.0": "",
    "Edge": "",
    "Logs": "",
    "Restauração": "",
    "Limpeza": "",
    "Otimização": "",
    "Rede": "",
    "Reparo": "",
    "Segurança": "",
    "Drivers": "",
    "Aplicativos": "",
    "Energia": "",
    "Desenvolvimento": "",
    "Ferramentas": "",
    "Relatórios": "",
    "Avançado": "",
    "Serviços": "",
}


class NVOptimizerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{Config.APP_NAME} v{Config.VERSION}")
        self.geometry("1100x750")
        self.minsize(900, 600)
        self.configure(fg_color=NV_DARK)

        self._build_header()
        self._build_body()
        self._build_footer()

        self.current_category = None
        self._select_category("Avançado")

        self._is_running = False

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=NV_DARK2, corner_radius=0, height=90)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.pack(side="left", padx=30, pady=10)

        n_label = ctk.CTkLabel(
            logo_frame, text="N", font=ctk.CTkFont(size=42, weight="bold"),
            text_color=NV_BLUE
        )
        n_label.pack(side="left")

        v_label = ctk.CTkLabel(
            logo_frame, text="V", font=ctk.CTkFont(size=42, weight="bold"),
            text_color=NV_YELLOW
        )
        v_label.pack(side="left")

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=15, pady=10)

        ctk.CTkLabel(
            title_frame, text="OPTIMIZER",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=NV_YELLOW
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame, text=f"v{Config.VERSION}",
            font=ctk.CTkFont(size=12),
            text_color="#888899"
        ).pack(anchor="w")

        info_frame = ctk.CTkFrame(header, fg_color="transparent")
        info_frame.pack(side="right", padx=30, pady=10)

        os_text = system_info.so_name
        ctk.CTkLabel(
            info_frame, text=os_text,
            font=ctk.CTkFont(size=13),
            text_color=NV_YELLOW
        ).pack(anchor="e")

        arch_text = system_info.architecture
        ctk.CTkLabel(
            info_frame, text=arch_text,
            font=ctk.CTkFont(size=11),
            text_color="#666688"
        ).pack(anchor="e")

        sep = ctk.CTkFrame(self, fg_color=NV_BLUE, height=2, corner_radius=0)
        sep.pack(fill="x")

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=0, pady=0)

        self._build_sidebar(body)
        self._build_main_area(body)

    def _build_sidebar(self, parent):
        sidebar = ctk.CTkFrame(parent, fg_color=NV_DARK2, corner_radius=0, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        cat_label = ctk.CTkLabel(
            sidebar, text="CATEGORIAS",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=NV_YELLOW
        )
        cat_label.pack(pady=(15, 10), padx=15, anchor="w")

        self.cat_buttons = {}
        self.current_cat_btn = None

        for cat_name in CATEGORIES:
            icon = CATEGORY_ICONS.get(cat_name, "•")
            btn = ctk.CTkButton(
                sidebar,
                text=f"  {icon}  {cat_name}",
                anchor="w",
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                hover_color=NV_DARK3,
                text_color="#ccccdd",
                height=36,
                corner_radius=6,
                command=lambda c=cat_name: self._select_category(c),
            )
            btn.pack(fill="x", padx=8, pady=2)
            self.cat_buttons[cat_name] = btn

    def _build_main_area(self, parent):
        main = ctk.CTkFrame(parent, fg_color=NV_DARK, corner_radius=0)
        main.pack(side="right", fill="both", expand=True)

        self.actions_frame = ctk.CTkScrollableFrame(
            main, fg_color=NV_DARK, corner_radius=0,
            scrollbar_button_color=NV_BLUE,
            scrollbar_button_hover_color=NV_YELLOW_DIM,
        )
        self.actions_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        log_label = ctk.CTkLabel(
            main, text="SAÍDA",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=NV_YELLOW, anchor="w"
        )
        log_label.pack(padx=15, pady=(2, 0), anchor="w")

        self.log_textbox = ctk.CTkTextbox(
            main,
            fg_color=NV_LOG_BG,
            text_color="#aaaacc",
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=6,
            height=180,
            border_width=1,
            border_color=NV_BLUE,
            wrap="word",
        )
        self.log_textbox.pack(fill="x", padx=10, pady=(0, 10))
        self.log_textbox.configure(state="disabled")

    def _build_footer(self):
        sep = ctk.CTkFrame(self, fg_color=NV_BLUE, height=1, corner_radius=0)
        sep.pack(fill="x")

        footer = ctk.CTkFrame(self, fg_color=NV_DARK2, corner_radius=0, height=35)
        footer.pack(fill="x")
        footer.pack_propagate(False)

        ctk.CTkLabel(
            footer, text=f"  NV Optimizer v{Config.VERSION}  •  {Config.AUTHOR}",
            font=ctk.CTkFont(size=11),
            text_color="#555577"
        ).pack(side="left", padx=10, pady=5)

        self.status_label = ctk.CTkLabel(
            footer, text="Pronto",
            font=ctk.CTkFont(size=11),
            text_color=NV_GREEN
        )
        self.status_label.pack(side="right", padx=15, pady=5)

    def _select_category(self, cat_name):
        if self.current_cat_btn:
            self.current_cat_btn.configure(fg_color="transparent", text_color="#ccccdd")

        self.current_category = cat_name
        btn = self.cat_buttons[cat_name]
        btn.configure(fg_color=NV_DARK3, text_color=NV_YELLOW)
        self.current_cat_btn = btn

        self._build_action_buttons(cat_name)

    def _build_action_buttons(self, cat_name):
        for widget in self.actions_frame.winfo_children():
            widget.destroy()

        cat_label = ctk.CTkLabel(
            self.actions_frame,
            text=f"{CATEGORY_ICONS.get(cat_name, '')}  {cat_name}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=NV_YELLOW,
            anchor="w",
        )
        cat_label.pack(fill="x", padx=5, pady=(5, 12))

        items = CATEGORIES[cat_name]

        grid_frame = ctk.CTkFrame(self.actions_frame, fg_color="transparent")
        grid_frame.pack(fill="x")

        cols = 3
        if len(items) <= 2:
            cols = 2
        if cat_name in ("Avançado", "Otimização 2.0", "Stress Test"):
            cols = 2

        for idx, (label, func_or_cmd) in enumerate(items):
            row = idx // cols
            col = idx % cols

            # Botões de ação perigosa com confirmação
            danger = False
            is_api_call = isinstance(func_or_cmd, str) and func_or_cmd.startswith("api:")
            if is_api_call and ("apply:" in func_or_cmd or "disable" in func_or_cmd.lower()):
                danger = True

            border = NV_RED if danger else NV_BLUE

            btn = ctk.CTkButton(
                grid_frame,
                text=label,
                font=ctk.CTkFont(size=13),
                fg_color=NV_DARK2,
                hover_color=NV_BTN_HOVER,
                text_color="#ddddff",
                border_width=1,
                border_color=border,
                height=50,
                corner_radius=8,
                anchor="center",
                command=lambda f=func_or_cmd, l=label: self._run_action(f, l),
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        for c in range(cols):
            grid_frame.columnconfigure(c, weight=1)

    def _log(self, msg, color="#aaaacc"):
        self.log_textbox.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_textbox.insert("end", f"[{timestamp}] {msg}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def _clear_log(self):
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

    def _set_status(self, text, color=NV_GREEN):
        self.status_label.configure(text=text, text_color=color)

    def _set_buttons_state(self, state):
        state_val = "normal" if state == "normal" else "disabled"
        for widget in self.actions_frame.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                widget.configure(state=state_val)
            elif isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkButton):
                        child.configure(state=state_val)

    def _run_action(self, func_or_cmd, label):
        if self._is_running:
            self._log("Aguarde a ação atual finalizar...", NV_YELLOW)
            return

        self._is_running = True
        self._set_buttons_state("disabled")
        self._set_status(f"Executando: {label}", NV_YELLOW)
        self._log(f"Iniciando: {label}", NV_BLUE)

        thread = threading.Thread(
            target=self._execute_action, args=(func_or_cmd, label), daemon=True
        )
        thread.start()

    def _execute_action(self, func_or_cmd, label):
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()

        try:
            if isinstance(func_or_cmd, str) and func_or_cmd.startswith("api:"):
                result = self._execute_api_call(func_or_cmd)
            else:
                func_or_cmd()
                result = {
                    "success": True,
                    "message": buffer.getvalue().strip() or "Concluído",
                }
            output = buffer.getvalue().strip()
            if result.get("message"):
                output = f"{output}\n{result['message']}".strip() if output else result["message"]
            self.after(0, self._on_action_done, label, result.get("success", False), output)
        except Exception as e:
            output = buffer.getvalue().strip()
            error_msg = f"{output}\nERRO: {e}" if output else f"ERRO: {e}"
            self.after(0, self._on_action_done, label, False, error_msg)
        finally:
            sys.stdout = old_stdout

    def _execute_api_call(self, cmd):
        """Executa chamada da API do backend e retorna dict padronizado."""
        parts = cmd[len("api:"):].split(":", 1)
        operation = parts[0]
        param = parts[1] if len(parts) > 1 else None

        # Operações que exigem confirmação do usuário
        confirm_required = {"optimization.apply", "defender.disable", "edge.uninstall"}
        confirm = False
        if operation in confirm_required:
            confirm = self._confirm_dialog()
            if not confirm:
                return {"success": False, "message": "Operação cancelada pelo usuário."}

        kwargs = {}
        if operation == "programs.install":
            kwargs["program_id"] = param
        elif operation == "optimization.analyze":
            kwargs["profile"] = param
        elif operation == "optimization.apply":
            kwargs["profile"] = param
            kwargs["confirm"] = True
        elif operation in ("stress.start", "stress.cpu", "stress.gpu", "stress.memory"):
            # Mapear atalhos: stress.cpu:60 → stress.start(test_type=cpu, duration=60)
            if operation.startswith("stress.") and operation != "stress.start":
                test_type = operation.split(".", 1)[1]
                duration = param
            else:
                test_type, _, duration = (param or "").partition(":")
            operation = "stress.start"
            kwargs["test_type"] = test_type
            kwargs["duration"] = int(duration or 60)
        elif operation == "power.plan":
            kwargs["plan"] = param
        elif operation == "defender.disable":
            kwargs["confirm"] = True
        elif operation == "edge.uninstall":
            kwargs["confirm"] = True

        return backend_api.call(operation, **kwargs)

    def _confirm_dialog(self):
        """Diálogo de confirmação para operações destrutivas."""
        try:
            dialog = ctk.CTkToplevel(self)
            dialog.title("Confirmação")
            dialog.geometry("420x200")
            dialog.transient(self)
            dialog.grab_set()
            dialog.configure(fg_color=NV_DARK2)

            ctk.CTkLabel(
                dialog,
                text="⚠  ATENÇÃO",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=NV_RED,
            ).pack(pady=(15, 5))

            ctk.CTkLabel(
                dialog,
                text=(
                    "Esta operação altera configurações importantes do sistema.\n"
                    "Deseja continuar?"
                ),
                font=ctk.CTkFont(size=13),
                text_color="#ccccdd",
            ).pack(pady=(0, 15))

            confirmed = {"value": False}

            def on_yes():
                confirmed["value"] = True
                dialog.destroy()

            def on_no():
                dialog.destroy()

            btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            btn_frame.pack(pady=10)

            ctk.CTkButton(
                btn_frame, text="Sim, continuar",
                command=on_yes, fg_color=NV_RED,
                hover_color="#cc2222", width=140, corner_radius=8,
            ).pack(side="left", padx=10)

            ctk.CTkButton(
                btn_frame, text="Cancelar",
                command=on_no, fg_color=NV_DARK3,
                hover_color="#2a2a5e", width=140, corner_radius=8,
            ).pack(side="left", padx=10)

            self.wait_window(dialog)
            return confirmed["value"]
        except Exception:
            return False

    def _on_action_done(self, label, success, output):
        self._is_running = False
        self._set_buttons_state("normal")

        if success:
            self._log(f"Concluído: {label}", NV_GREEN)
            self._set_status("Pronto", NV_GREEN)
        else:
            self._log(f"Falha: {label}", NV_RED)
            self._set_status("Erro", NV_RED)

        if output:
            for line in output.split("\n"):
                if line.strip():
                    self._log(f"  {line}", "#8888aa" if success else NV_RED)


def run_gui():
    app = NVOptimizerGUI()
    app.mainloop()


if __name__ == "__main__":
    run_gui()

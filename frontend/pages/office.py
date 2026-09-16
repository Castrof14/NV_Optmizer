"""Office — instalação/configuração do Microsoft Office (backend real)."""

import customtkinter as ctk

import frontend.api as api
import frontend.modules_bridge as backend
from frontend.pages import PageBase
from frontend.theme import Theme
from frontend.components import (Card, Button, Badge, PulseBar, LoadingState, ErrorState)
from frontend.jobs import strip_ansi


class OfficePage(PageBase):
    page_id = "office"
    title = "Office"
    subtitle = "Instale e configure o Microsoft Office pelo Deployment Tool."
    badge_text = None

    def _build(self):
        self._running = False
        self._render_status()

    def _render_status(self):
        for w in self.winfo_children():
            w.destroy()

        head = Card(self, title="MICROSOFT OFFICE", badge="Office")
        head.pack(fill="x", pady=(0, 20))

        status = api.office_state()

        if status.get("available"):
            if status.get("installed"):
                Badge(head.body, text="INSTALADO", tone="green").pack(anchor="w")
                if status.get("version"):
                    ctk.CTkLabel(head.body, text=f"Versão: {status['version']}",
                                 font=Theme.font(13, mono=True), text_color=Theme.TEXT_SOFT).pack(anchor="w", pady=(6, 0))
            else:
                Badge(head.body, text="NÃO INSTALADO", tone="orange").pack(anchor="w")
            if status.get("setup_path"):
                ctk.CTkLabel(head.body, text=f"Setup: {status['setup_path']}",
                             font=Theme.font(12, mono=True), text_color=Theme.BODY).pack(anchor="w", pady=(8, 0))
            if not status.get("setup_ready"):
                ctk.CTkLabel(
                    head.body,
                    text=("Ambiente de instalação não localizado. Configure a pasta "
                          "'MS Office Setup' na raiz do sistema (Setup.exe + arquivo de configuração)."),
                    font=Theme.font(12), text_color=Theme.WARNING, wraplength=520,
                    justify="left", anchor="w").pack(anchor="w", pady=(8, 0))
        else:
            Badge(head.body, text="DISPONÍVEL APENAS NO WINDOWS", tone="red").pack(anchor="w")

        btns = ctk.CTkFrame(head.body, fg_color="transparent")
        btns.pack(anchor="w", pady=(16, 0))
        Button(btns, text="INSTALAR / CONFIGURAR", variant="primary",
               command=self._install).pack(side="left", padx=(0, 8))
        Button(btns, text="Verificar status", variant="secondary",
               command=self._render_status).pack(side="left")

        prog = ctk.CTkFrame(head.body, fg_color="transparent")
        prog.pack(fill="x", pady=(20, 0))
        self._status_label = ctk.CTkLabel(prog, text="Status: Pronto para instalar",
                                          font=Theme.font(14, weight="bold"),
                                          text_color=Theme.SUCCESS, anchor="w")
        self._status_label.pack(anchor="w")
        self._bar = PulseBar(prog, height=8, color=Theme.NV_BLUE)
        self._bar.pack(fill="x", pady=(10, 0))
        self._pause_bar()

        self._btn_bar = 0
        self._stage = ctk.CTkLabel(head.body, text="", font=Theme.font(13),
                                   text_color=Theme.TEXT_SOFT, anchor="w")
        self._stage.pack(anchor="w", pady=(10, 0))

        logs = ctk.CTkTextbox(self, fg_color=Theme.SURFACE_ELEV, text_color=Theme.BODY,
                              font=Theme.font(12, mono=True), corner_radius=Theme.R_LG,
                              border_width=1, border_color=Theme.HAIRLINE, height=220,
                              wrap="word")
        logs.pack(fill="x", pady=(0, 20))
        self._logs = logs
        self._log(f"Office · status lido em {status.get('available', False)}")

    def _log(self, msg):
        self._logs.configure(state="normal")
        self._logs.insert("end", f"  {msg}\n")
        self._logs.see("end")
        self._logs.configure(state="disabled")

    def _pause_bar(self):
        self._bar.pack_forget()

    def _install(self):
        if self._running:
            return
        self._running = True
        self._bar.pack(fill="x", pady=(10, 0))
        self._bar.start()
        self._status_label.configure(text="Status: Instalando componentes...", text_color=Theme.NV_YELLOW)
        self._stage.configure(text="")

        def run():
            backend.install_office()
        self._action("Instalar Office",
                     fn=run,
                     on_log=self._on_log,
                     on_done=lambda _: self._done(True, None),
                     on_error=lambda e: self._done(False, e))

    def _on_log(self, line):
        line = strip_ansi(line)
        if line:
            self._stage.configure(text=line)
            self._log(line)

    def _done(self, ok, err):
        self._running = False
        self._bar.stop()
        self._pause_bar()
        if ok:
            self._status_label.configure(text="Status: Instalação concluída", text_color=Theme.SUCCESS)
            self._toast("success", "Microsoft Office instalado com sucesso.")
            self._log(operation="Instalar Office", result="OK")
        else:
            self._status_label.configure(text="Status: Não foi possível concluir", text_color=Theme.DANGER)
            self._toast("error", f"Falha na instalação do Office. Verifique os logs.")
            self._log(operation="Instalar Office", result="FALHA", detail=str(err))
            self._stage.configure(text=str(err))
        self.after(420, self._render_status)
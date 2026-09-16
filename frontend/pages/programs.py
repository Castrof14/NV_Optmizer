"""Programas — instalação de aplicativos (dados reais via winget)."""

import customtkinter as ctk

import frontend.api as api
import frontend.modules_bridge as backend
from frontend.pages import PageBase
from frontend.theme import Theme
from frontend.components import (Card, Button, Badge, PulseBar, LoadingState, ErrorState)

GROUPS = [("basico", "Programas básicos"), ("gaming", "Gaming")]


class _ProgramRow:
    def __init__(self, page, parent, program):
        self.page = page
        self.program = program
        self.var = ctk.BooleanVar(value=False)

        row = ctk.CTkFrame(parent, fg_color=Theme.SURFACE_ELEV, corner_radius=Theme.R_LG,
                           border_width=1, border_color=Theme.HAIRLINE)
        row.pack(fill="x", pady=6)
        row.grid_columnconfigure(1, weight=1)

        self.check = ctk.CTkCheckBox(row, text="", variable=self.var, width=24,
                                     corner_radius=Theme.R_SM,
                                     fg_color=Theme.NV_BLUE, hover_color=Theme.NV_BLUE_HOVER,
                                     checkmark_color="#ffffff", border_color=Theme.MUTED)
        self.check.grid(row=0, column=0, rowspan=2, padx=(18, 6), pady=18)

        name = ctk.CTkFrame(row, fg_color="transparent")
        name.grid(row=0, column=1, sticky="w", pady=(12, 0))
        ctk.CTkLabel(name, text=program["name"], font=Theme.font(15, weight="bold"),
                     text_color=Theme.TEXT, anchor="w").pack(side="left")
        self.progress = PulseBar(row, height=6, color=Theme.NV_YELLOW)
        self.progress.pack(fill="x", padx=8, pady=(8, 0))
        self.progress.pack_forget()

        ctk.CTkLabel(row, text=program["description"], font=Theme.font(12),
                     text_color=Theme.BODY, anchor="w", wraplength=480,
                     justify="left").grid(row=1, column=1, sticky="w", pady=(2, 12))

        meta = ctk.CTkFrame(name, fg_color="transparent")
        meta.pack(side="left", padx=(10, 0))
        for tag in program.get("tags", [])[:2]:
            Badge(meta, text=tag, tone="neutral", size=10).pack(side="left", padx=2)

        self.badge = Badge(row, text="Verificando", tone="neutral")
        self.badge.grid(row=0, column=3, sticky="e", padx=(6, 16), pady=(10, 0))

    def set_status(self, status: str):
        self.badge.configure(text=status)
        if status == "Instalado":
            self.badge.set_tone("green")
        elif status == "Não instalado":
            self.badge.set_tone("gray")
        elif status == "Instalando":
            self.badge.set_tone("yellow")
            self.progress.pack(fill="x", padx=8, pady=(8, 0))
        elif status == "Erro":
            self.badge.set_tone("red")
            self.progress.pack_forget()
        else:
            self.badge.set_tone("neutral")
        self.badge.grid_configure(row=0, column=3)

    def set_running(self, running):
        st = "disabled" if running else "normal"
        try:
            self.check.configure(state=st)
        except Exception:
            pass


class ProgramsPage(PageBase):
    page_id = "programas"
    title = "Programas"
    subtitle = "Instale os principais programas do seu computador de uma só vez."
    badge_text = None

    def _build(self):
        self.rows = []
        self._running = False
        self._load()

    def on_show(self):
        pass

    def _load(self):
        for w in self.winfo_children():
            w.destroy()
        LoadingState(self, message="Verificando programas instalados...").pack(fill="both", expand=True)
        self._action("Verificando programas", fn=api.programs_load,
                     on_done=self._render, on_error=self._fail)

    def _fail(self, err):
        for w in self.winfo_children():
            w.destroy()
        ErrorState(self, message=f"{err}", on_retry=self._load).pack(fill="both", expand=True)

    def _render(self, catalog):
        for w in self.winfo_children():
            w.destroy()

        for cat, label in GROUPS:
            group = Card(self, title=label)
            group.pack(fill="x", pady=(0, 20))
            items = [p for p in catalog if p.get("category") == cat]
            for p in items:
                row = _ProgramRow(self, group.body, p)
                st = p.get("status")
                row.set_status("Instalado" if st is True else
                               ("Não instalado" if st is False else "Verificando"))
                self.rows.append(row)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", pady=(4, 0))
        Button(bottom, text="INSTALAR SELECIONADOS", variant="primary", icon="⬇",
               command=self._install_selected).pack(side="left")

    def _selected(self):
        return [r for r in self.rows if r.var.get()]

    def _install_selected(self):
        if self._running:
            return
        sel = self._selected()
        if not sel:
            self._toast("warning", "Selecione ao menos um programa para instalar.")
            return
        self._running = True

        names = [r.program["name"] for r in sel]
        self._log(operation="Instalar programas", service=", ".join(names), result="pendente")
        self.app.set_busy(True, "Instalando programas")

        for r in sel:
            r.set_running(True)
            r.set_status("Instalando")

        def run():
            for r in sel:
                print(f"[NV:INSTALANDO] {r.program['name']}")
                backend.install_program(r.program["key"])
                print(f"[NV:INSTALADO] {r.program['name']}")

        self._action("Instalar programas",
                     fn=run,
                     on_log=self._on_install_log,
                     on_done=lambda _: self._install_done(True, None),
                     on_error=lambda e: self._install_done(False, e))

    def _on_install_log(self, line):
        if line.startswith("[NV:INSTALANDO] "):
            name = line.replace("[NV:INSTALANDO] ", "").strip()
            for r in self.rows:
                if r.program["name"] == name:
                    r.set_status("Instalando")
        elif line.startswith("[NV:INSTALADO] "):
            name = line.replace("[NV:INSTALADO] ", "").strip()
            for r in self.rows:
                if r.program["name"] == name:
                    r.set_status("Instalado")

    def _install_done(self, ok, err):
        self._running = False
        self.app.set_busy(False)
        for r in self.rows:
            r.set_running(False)
        if ok:
            self._toast("success", "Programas instalados com sucesso.")
            self._log(operation="Instalar programas", result="OK")
        else:
            self._toast("error", f"Não foi possível concluir a instalação: {err}")
            self._log(operation="Instalar programas", result="FALHA", detail=str(err))
            for r in self.rows:
                if r.badge.cget("text") == "Instalando":
                    r.set_status("Erro")
        self._refresh_statuses()

    def _refresh_statuses(self):
        self._action("Atualizando status",
                     fn=backend.check_all_programs,
                     on_done=self._apply_statuses,
                     on_error=lambda e: None)

    def _apply_statuses(self, rows):
        try:
            for p in rows:
                key = p["key"]
                installed = p["installed"]
                for r in self.rows:
                    if r.program["key"] == key and installed is True:
                        r.set_status("Instalado")
        except Exception:
            pass
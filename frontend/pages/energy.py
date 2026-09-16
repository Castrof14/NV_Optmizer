"""Energia — configuração real do plano de energia do Windows."""

import customtkinter as ctk

import frontend.api as api
import frontend.modules_bridge as backend
from frontend.pages import PageBase
from frontend.theme import Theme
from frontend.components import (Card, Button, Badge, PulseBar, LoadingState, ErrorState)

PRESETS = [
    ("Equilibrado", "Equilibrado", 15, 15),
    ("Alto desempenho", "Alto desempenho", 0, 0),
    ("Economia de energia", "Economia de energia", 10, 15),
]


class EnergyPage(PageBase):
    page_id = "energia"
    title = "Energia"
    subtitle = "Plano de energia, tempo de tela e suspensão."
    badge_text = None

    def _build(self):
        self._monitor = 15
        self._sleep = 15
        self._plan = "Equilibrado"
        self._load()

    def _load(self):
        for w in self.winfo_children():
            w.destroy()
        LoadingState(self, message="Carregando configurações de energia...").pack(fill="both", expand=True)
        self._action("Ler energia", fn=api.power_state, on_done=self._render, on_error=lambda e: self._fail(str(e)))

    def _fail(self, msg):
        for w in self.winfo_children():
            w.destroy()
        ErrorState(self, message=str(msg), on_retry=self._load).pack(fill="both", expand=True)

    def _render(self, data):
        for w in self.winfo_children():
            w.destroy()

        avail = data.get("available", False)

        # Status
        status = Card(self, title="Estado atual")
        status.pack(fill="x", pady=(0, 20))
        plan_name = data.get("name") or "Não disponível"
        ctk.CTkLabel(status.body, text=plan_name, font=Theme.display_font(24),
                     text_color=Theme.NV_YELLOW if avail else Theme.MUTED, anchor="w").pack(anchor="w")
        mon = data.get("monitor")
        slp = data.get("sleep")
        ctk.CTkLabel(status.body,
                     text=f"Tela: {self._fmt(mon)}  ·  Suspensão: {self._fmt(slp)}",
                     font=Theme.font(14), text_color=Theme.BODY, anchor="w").pack(anchor="w", pady=(6, 0))

        if not avail:
            Badge(status.body, text="Plano de energia não disponível nesta máquina",
                  tone="neutral").pack(anchor="w", pady=(12, 0))

        # Presets
        presets = Card(self, title="Configurações")
        presets.pack(fill="x", pady=(0, 20))

        self._btns_frame = ctk.CTkFrame(presets.body, fg_color="transparent")
        self._btns_frame.pack(fill="x")
        for i, (label, plan, mon, slp) in enumerate(PRESETS):
            btn = Button(self._btns_frame, text=label.upper(), variant="secondary",
                         command=lambda p=plan, m=mon, s=slp, b=label: self._apply_preset(p, m, s, b))
            btn.pack(side="left", padx=(0, 8))

        # Monitor/Sleep controls
        ctl = ctk.CTkFrame(presets.body, fg_color="transparent")
        ctl.pack(fill="x", pady=(18, 0))
        self._mon_slider = self._make_slider(ctl, "TELA (MIN)", 0, 120, data.get("monitor") or 15, 0)
        self._slp_slider = self._make_slider(ctl, "SUSPENSÃO (MIN)", 0, 120, data.get("sleep") or 15, 1)

        self._apply_btn = Button(presets.body, text="APLICAR", variant="primary", command=self._apply_custom)
        self._apply_btn.pack(anchor="w", pady=(18, 0))

        # Status
        status2 = Card(self, title="Status")
        status2.pack(fill="x")
        self._status_label = ctk.CTkLabel(status2.body, text="", font=Theme.font(13),
                                          text_color=Theme.SUCCESS, anchor="w")
        self._status_label.pack(anchor="w")
        self._bar = PulseBar(status2.body, height=8, color=Theme.NV_BLUE)
        self._bar.pack_forget()

    def _make_slider(self, parent, label, from_, to, value, row):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(8, 0))
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text=label, font=Theme.font(11, weight="bold"),
                     text_color=Theme.MUTED).grid(row=0, column=0, sticky="w")
        slider = ctk.CTkSlider(frame, from_=from_, to=to, number_of_steps=12,
                               fg_color=Theme.SURFACE_STRONG, progress_color=Theme.NV_BLUE,
                               button_color=Theme.NV_BLUE, button_hover_color=Theme.NV_BLUE_HOVER,
                               command=lambda v, lbl=None: None)
        slider.set(value)
        slider.grid(row=1, column=0, sticky="ew")
        val_label = ctk.CTkLabel(frame, text=self._fmt(value),
                                 font=Theme.num_font(13), text_color=Theme.TEXT_SOFT)
        val_label.grid(row=0, column=1, rowspan=2, padx=(10, 0))
        slider.configure(command=lambda v, lbl=val_label: lbl.configure(text=self._fmt(int(v))))
        return slider

    @staticmethod
    def _fmt(minutes):
        if minutes is None or int(minutes) <= 0:
            return "Nunca"
        return f"{int(minutes)} min"

    def _apply_preset(self, plan, monitor, sleep, label):
        self.app.confirm(
            f"APLICAR PRESET {label.upper()}?",
            f"O plano de energia será alterado para {label}.",
            danger=False,
            on_confirm=lambda: self._run_apply(plan, monitor, sleep),
        )

    def _apply_custom(self):
        monitor = int(self._mon_slider.get())
        sleep = int(self._slp_slider.get())
        self._plan = "Equilibrado"
        self.app.confirm(
            "APLICAR CONFIGURAÇÕES DE ENERGIA?",
            f"Plano Equilibrado · Tela: {self._fmt(monitor)} · Suspensão: {self._fmt(sleep)}",
            danger=False,
            on_confirm=lambda: self._run_apply(self._plan, monitor, sleep),
        )

    def _run_apply(self, plan, monitor, sleep):
        self._apply_btn.configure(state="disabled")
        self._bar.pack(fill="x", pady=(12, 0))
        self._bar.start()
        self._status_label.configure(text="Aplicando configurações...", text_color=Theme.NV_YELLOW)
        self.app.set_busy(True, "Configurando energia")

        def run():
            backend.apply_power_config(plan, monitor, sleep)

        self._action("Aplicar energia", fn=run,
                     on_done=lambda _: self._apply_done(),
                     on_error=lambda e: self._apply_fail(str(e)))

    def _apply_done(self):
        self.app.set_busy(False)
        self._bar.stop(); self._bar.pack_forget()
        self._apply_btn.configure(state="normal")
        self._status_label.configure(text="Configurações aplicadas.", text_color=Theme.SUCCESS)
        self._toast("success", "Configurações de energia aplicadas.")
        self._log(operation="Energia", result="OK")
        self.after(500, self._load)

    def _apply_fail(self, msg):
        self.app.set_busy(False)
        self._bar.stop(); self._bar.pack_forget()
        self._apply_btn.configure(state="normal")
        self._status_label.configure(text="Falha ao aplicar.", text_color=Theme.DANGER)
        self._toast("error", f"Falha ao aplicar energia: {msg}")
        self._log(operation="Energia", result="FALHA", detail=str(msg))
"""Diagnóstico — Stress Test com monitoramento em tempo real."""

import time
import customtkinter as ctk

import frontend.api as api
import frontend.modules_bridge as backend
from frontend.pages import PageBase
from frontend.theme import Theme
from frontend.components import Card, Button, Badge, Bar, PulseBar

PRESETS = [("1:00", 60), ("5:00", 300), ("10:00", 600)]


class DiagnosisPage(PageBase):
    page_id = "diagnostico"
    title = "Stress Test"
    subtitle = "Avalie o desempenho real de CPU, GPU e memória sob carga."
    badge_text = None

    def _build(self):
        self._running_test = False
        self._polling = False
        self._duration = 60
        self._started = None
        self._alive = True

        # ---- Cartão de controle ----
        top = Card(self, title="Stress Test", subtitle="Use com moderação.")
        top.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(top.body, text="DURAÇÃO DO TESTE", font=Theme.font(11, weight="bold"),
                     text_color=Theme.MUTED).pack(anchor="w")
        sel = ctk.CTkFrame(top.body, fg_color="transparent")
        sel.pack(fill="x", pady=(8, 0))
        self.seg = ctk.CTkSegmentedButton(
            sel,
            values=[p[0] for p in PRESETS] + ["Personalizado"],
            fg_color=Theme.SURFACE_STRONG,
            selected_color=Theme.SURFACE_ELEV2,
            selected_hover_color=Theme.SURFACE_ELEV2,
            unselected_color=Theme.SURFACE_STRONG,
            unselected_hover_color=Theme.SURFACE_ELEV2,
            text_color=Theme.TEXT_SOFT,
            font=Theme.font(13),
            corner_radius=Theme.R_PILL,
            command=self._on_preset,
        )
        self.seg.set("5:00")
        self._duration = 300
        sel.grid_columnconfigure(0, weight=1)
        self.seg.pack(fill="x")

        self._custom = ctk.CTkFrame(top.body, fg_color="transparent")
        self._custom.pack(fill="x", pady=(10, 0))
        self._custom.pack_forget()
        self._slider = ctk.CTkSlider(self._custom, from_=30, to=1800, number_of_steps=60,
                                     fg_color=Theme.SURFACE_STRONG, progress_color=Theme.NV_BLUE,
                                     button_color=Theme.NV_BLUE, button_hover_color=Theme.NV_BLUE_HOVER)
        self._slider.set(300)
        self._slider.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self._slider_val = ctk.CTkLabel(self._custom, text="5 min", font=Theme.num_font(13),
                                        text_color=Theme.TEXT_SOFT)
        self._slider_val.grid(row=0, column=1, sticky="e")
        self._custom.grid_columnconfigure(0, weight=1)
        self._slider.configure(command=lambda v: self._slider_val.configure(
            text=f"{int(v // 60)} min {int(v % 60):02d}s"))

        self._cpu_ck = ctk.BooleanVar(value=True)
        self._ram_ck = ctk.BooleanVar(value=True)
        toggles = ctk.CTkFrame(top.body, fg_color="transparent")
        toggles.pack(anchor="w", pady=(12, 0))
        ctk.CTkCheckBox(toggles, text="CPU", variable=self._cpu_ck, corner_radius=Theme.R_SM,
                        fg_color=Theme.NV_BLUE, hover_color=Theme.NV_BLUE_HOVER,
                        checkmark_color="#ffffff", border_color=Theme.MUTED).pack(side="left", padx=(0, 16))
        ctk.CTkCheckBox(toggles, text="RAM", variable=self._ram_ck, corner_radius=Theme.R_SM,
                        fg_color=Theme.NV_BLUE, hover_color=Theme.NV_BLUE_HOVER,
                        checkmark_color="#ffffff", border_color=Theme.MUTED).pack(side="left")

        btnrow = ctk.CTkFrame(top.body, fg_color="transparent")
        btnrow.pack(fill="x", pady=(18, 0))
        self.start_btn = Button(btnrow, text="INICIAR TESTE", variant="primary", icon="▶",
                                command=self._confirm_start)
        self.start_btn.pack(side="left")
        self.stop_btn = Button(btnrow, text="Parar", variant="danger", icon="■", command=self._stop_test)
        self.stop_btn.pack(side="left", padx=(8, 0))
        self.stop_btn.configure(state="disabled")

        # ---- Monitor ----
        mon = ctk.CTkFrame(self, fg_color="transparent")
        mon.pack(fill="x", pady=(0, 20))
        mon.grid_columnconfigure(0, weight=1)
        mon.grid_columnconfigure(1, weight=1)
        mon.grid_columnconfigure(2, weight=1)

        self.cpu_card = Card(mon, title="CPU", badge="uso")
        self.cpu_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.gpu_card = Card(mon, title="GPU", badge="uso")
        self.gpu_card.grid(row=0, column=1, sticky="nsew", padx=10)
        self.ram_card = Card(mon, title="RAM", badge="uso")
        self.ram_card.grid(row=0, column=2, sticky="nsew", padx=(10, 0))

        self._big = {}
        for key in ("cpu", "gpu", "ram"):
            lb = ctk.CTkLabel(self.__dict__[f"{key}_card"].body, text="—",
                              font=Theme.display_font(40), text_color=Theme.TEXT, anchor="w")
            lb.pack(fill="x", pady=(14, 0))
            self._big[key] = lb
            bar = Bar(self.__dict__[f"{key}_card"].body, value=0, show_pct=False,
                      color=Theme.NV_BLUE, height=8)
            bar.pack(fill="x", pady=(16, 0))
            self.__dict__[f"_{key}_bar"] = bar
            sub = ctk.CTkLabel(self.__dict__[f"{key}_card"].body, text="Carregando...",
                               font=Theme.font(13), text_color=Theme.BODY, anchor="w")
            sub.pack(fill="x", pady=(8, 0))
            self.__dict__[f"_{key}_sub"] = sub

        # ---- Progresso do teste ----
        prog = Card(self, title="Tempo")
        prog.pack(fill="x", pady=(0, 20))
        self.time_label = ctk.CTkLabel(prog.body, text="00:00 / 05:00",
                                       font=Theme.num_font(18), text_color=Theme.TEXT_SOFT, anchor="w")
        self.time_label.pack(anchor="w")
        self.prog = Bar(prog.body, value=0, color=Theme.NV_BLUE, height=10)
        self.prog.pack(fill="x", pady=(10, 0))

        # ---- Status ----
        status = Card(self, title="Status")
        status.pack(fill="x")
        self.status_badge = Badge(status.body, text="Pronto", tone="neutral")
        self.status_badge.pack(anchor="w")

        self._poll()

    # ---------- Controles ----------
    def _on_preset(self, value):
        if value == "Personalizado":
            self._custom.pack(fill="x", pady=(10, 0))
            self._duration = int(self._slider.get())
        else:
            self._custom.pack_forget()
            for name, secs in PRESETS:
                if name == value:
                    self._duration = secs

    def _minutes_label(self):
        m, s = divmod(self._duration, 60)
        return f"{m:02d}:{s:02d}"

    @staticmethod
    def _fmt(seconds: float) -> str:
        seconds = max(0, int(seconds))
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def _confirm_start(self):
        self.app.confirm(
            "INICIAR O TESTE DE ESTRESSE?",
            "Este teste pode aumentar o consumo, o uso e a temperatura do computador.",
            detail=f"Duração: {self._minutes_label()}  ·  Carga: "
                   + ", ".join(x for x, v in [("CPU", self._cpu_ck.get()), ("RAM", self._ram_ck.get())] if v),
            danger=True,
            on_confirm=self._start_test,
        )

    def _start_test(self):
        if self._running_test:
            return
        self._running_test = True
        self._started = time.time()
        self._log(operation="Stress Test", service="Iniciar", result="pendente")
        backend.start_stress(cpu=self._cpu_ck.get(), ram=self._ram_ck.get())
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_badge.configure(text="TESTANDO", text_color=Theme.NV_YELLOW)
        self.status_badge.set_tone("yellow")
        self._toast("info", f"Teste de estresse iniciado ({self._minutes_label()}).")
        self._log(operation="Stress Test", result="OK", service="Iniciado")
        self._poll()

    def _stop_test(self):
        if not self._running_test:
            return
        backend.stop_stress()
        self._running_test = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_badge.configure(text="Encerrado", text_color=Theme.TEXT_SOFT)
        self.status_badge.set_tone("neutral")
        self._toast("info", "Teste de estresse encerrado.")
        self._log(operation="Stress Test", result="OK", service="Encerrado")
        self._poll()

    # ---------- Monitoramento ----------
    def on_show(self):
        self._alive = True
        self._poll()

    def on_hide(self):
        self._alive = False

    def _poll(self):
        if not self._alive:
            return
        try:
            s = api.stress_sample()
            self._apply_sample(s)
        except Exception:
            pass
        try:
            if self.winfo_exists():
                self.after(1000, self._poll)
        except Exception:
            pass

    def _apply_sample(self, s):
        cpu = s.get("cpu") or {}
        ram = s.get("ram") or {}
        gpu = s.get("gpu") or {}

        u = cpu.get("usage")
        self._cpu_bar.set((u or 0) / 100)
        self._big["cpu"].configure(text=f"{u}%" if u is not None else "—")
        cpu_sub = f"{(cpu.get('temp') or 'Temp —')}  ·  {(cpu.get('freq') or 'Freq —')}"
        self._cpu_sub.configure(text=cpu_sub if cpu.get("temp") or cpu.get("freq") else "Dados não disponíveis")

        gu = gpu.get("usage")
        if gpu.get("available"):
            self._gpu_bar.set((gu or 0) / 100)
            self._big["gpu"].configure(text=f"{gu}%" if gu is not None else "—")
            self._gpu_sub.configure(text=f"{(gpu.get('temp') or 'Temp —')}  ·  nvidia-smi")
        else:
            self._gpu_bar.set(0)
            self._big["gpu"].configure(text="—")
            self._gpu_sub.configure(text="GPU não suportada para monitoramento")

        if ram.get("used") is not None and ram.get("total"):
            self._ram_bar.set((ram.get("pct") or 0) / 100)
            self._big["ram"].configure(text=f"{ram.get('pct')}%")
            self._ram_sub.configure(text=f"{ram.get('used')} / {ram.get('total')} GB")
        else:
            self._ram_bar.set(0)
            self._big["ram"].configure(text="—")
            self._ram_sub.configure(text="Dados não disponíveis")

        if self._running_test:
            elapsed = time.time() - self._started
            pct = min(1.0, elapsed / self._duration)
            self.prog.set(pct)
            self.time_label.configure(text=f"{self._fmt(elapsed)} / {self._minutes_label()}")
            if elapsed >= self._duration:
                self._stop_test()
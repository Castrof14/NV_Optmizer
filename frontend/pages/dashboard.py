"""Dashboard — visão geral do computador com dados reais."""

import customtkinter as ctk

import frontend.api as api
from frontend.pages import PageBase
from frontend.theme import Theme
from frontend.components import (
    Card, HardwareCard, StatusCard, Button, Badge, Bar,
    LoadingState, ErrorState,
)


def _tone_for(value: str) -> str:
    v = value.upper()
    if any(x in v for x in ("ATIVO", "ATUALIZADO", "ALTO DESEMPENHO", "PROTEGIDO", "SIM")):
        return "green"
    if any(x in v for x in ("NÃO APLICADA", "DESATIVADO", "NÃO")):
        return "orange"
    return "neutral"


class DashboardPage(PageBase):
    page_id = "dashboard"
    title = "Dashboard"
    subtitle = "Visão geral do seu computador, com informações reais do sistema."
    badge_text = None

    def _build(self):
        self.content = None
        self._load()

    def on_show(self):
        pass

    def _load(self):
        for w in self.winfo_children():
            w.destroy()
        LoadingState(self, message="Coletando informações do sistema...").pack(fill="both", expand=True)
        self._action("Carregando dashboard",
                     fn=api.dashboard_load,
                     on_done=self._render,
                     on_error=self._fail)
        self.app.set_busy(True, "Lendo hardware do sistema")

    def _fail(self, err):
        self.app.set_busy(False)
        for w in self.winfo_children():
            w.destroy()
        ErrorState(self, message=f"{err}",
                   on_retry=self._load).pack(fill="both", expand=True)

    def _render(self, data):
        self.app.set_busy(False)
        for w in self.winfo_children():
            w.destroy()

        # ---- Hero: identificação do PC ----
        hero = Card(self, title="Seu computador",
                    subtitle="Status geral do sistema em tempo real.")
        hero.pack(fill="x", pady=(0, 20))
        hero_body = hero.body

        os_info = data.get("os") or {}
        cpu = data.get("cpu") or {}
        ram = data.get("ram") or {}
        disk = data.get("disk") or {}

        inner = ctk.CTkFrame(hero_body, fg_color="transparent")
        inner.pack(fill="x")
        inner.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(inner, text="Windows" if os_info.get("name", "").lower().startswith("windows")
                     else (os_info.get("name") or "Não disponível"),
                     font=Theme.display_font(30), text_color=Theme.TEXT,
                     anchor="w").grid(row=0, column=0, sticky="w")

        _status = data.get("status_geral", "Carregando...")
        ba = Badge(inner, text="Status geral")
        ba.grid(row=0, column=1, sticky="e")

        # Uso em tempo real
        cpu_pct = data.get("cpu_pct")
        line = ctk.CTkFrame(hero_body, fg_color="transparent")
        line.pack(fill="x", pady=(22, 0))
        line.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(line, text="CPU", font=Theme.font(13, weight="bold"),
                     text_color=Theme.BODY).grid(row=0, column=0, sticky="w", padx=(0, 12))
        bar = Bar(line, value=(cpu_pct / 100 if cpu_pct is not None else 0),
                  color=Theme.NV_BLUE, show_pct=False, height=8)
        bar.grid(row=0, column=1, sticky="ew")
        if cpu_pct is not None:
            ctk.CTkLabel(line, text=f"{cpu_pct}%", font=Theme.font(12, weight="bold", mono=True),
                         text_color=Theme.TEXT_SOFT).grid(row=0, column=2, sticky="e", padx=(12, 0))
        else:
            ctk.CTkLabel(line, text="Não disponível", font=Theme.font(12),
                         text_color=Theme.MUTED).grid(row=0, column=2, sticky="e", padx=(12, 0))

        # ---- Hardware ----
        hw = ctk.CTkFrame(self, fg_color="transparent")
        hw.pack(fill="x", pady=(0, 20))
        hw.grid_columnconfigure(0, weight=1)

        cpu_card = HardwareCard(hw, icon="◈", title="CPU",
                                value=cpu.get("name") or "Não disponível",
                                sub=f"{cpu.get('cores', '—')} núcleos · {cpu.get('threads', '—')} threads",
                                value_small=len((cpu.get("name") or "")) > 28)
        ram_card = HardwareCard(hw, icon="◈", title="RAM",
                                value=f"{ram.get('total_gb', '—')} GB",
                                sub="Memória instalada")
        gpu_card = HardwareCard(hw, icon="◈", title="GPU",
                                value=(data.get("gpu") or {}).get("name") or "Não disponível",
                                sub=f"{(data.get('gpu') or {}).get('vram', '—')} VRAM",
                                value_small=True)
        disk_card = HardwareCard(hw, icon="◈", title="Disco",
                                 value=f"{disk.get('total_gb', '—')} GB" if disk.get("total_gb") != "Não disponível" else "Não disponível",
                                 sub=f"{disk.get('free_gb', '—')} GB livres · {disk.get('percent', 0)}% em uso",
                                 tone={"label": f"{disk.get('percent', 0)}%", "tone": "blue"} if disk.get("percent") is not None else None)

        cpu_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ram_card.grid(row=0, column=1, sticky="nsew", padx=10)
        gpu_card.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(20, 0))
        disk_card.grid(row=1, column=1, sticky="nsew", padx=10, pady=(20, 0))
        hw.grid_columnconfigure(0, weight=1)
        hw.grid_columnconfigure(1, weight=1)

        # ---- Status ----
        self._render_status(data)

    def _render_status(self, data):
        stat = ctk.CTkFrame(self, fg_color="transparent")
        stat.pack(fill="x")

        ctk.CTkLabel(stat, text="STATUS", font=Theme.font(11, weight="bold"),
                     text_color=Theme.MUTED).pack(anchor="w", pady=(0, 10))

        defender = data.get("defender") or {}
        def_val = "Verificando..."
        def_tone = "neutral"
        if defender.get("available"):
            def_val = "ATIVO" if defender.get("real_time") else "DESATIVADO"
            def_tone = "green" if defender.get("real_time") else "red"

        power = data.get("power") or {}
        power_val = power.get("name") or "Carregando..."
        drv = data.get("driver") or {}
        drv_val = "ATUALIZADO" if drv.get("driver") and drv.get("driver") != "—" else "NÃO VERIFICADO"
        if not drv.get("available"):
            drv_val = "NÃO DISPONÍVEL"

        profile_val = getattr(self.app, "current_profile", None)
        if profile_val == "escritorio":
            profile_val = "ESCRITÓRIO"
        elif profile_val == "gaming":
            profile_val = "GAMING"
        else:
            profile_val = "NÃO APLICADA"
        data["status_geral"] = profile_val

        StatusCard(stat, "Windows Defender", def_val, tone=def_tone).pack(fill="x", pady=5)
        StatusCard(stat, "Energia", power_val, tone=_tone_for(power_val)).pack(fill="x", pady=5)
        StatusCard(stat, "Driver GPU", drv_val, tone=_tone_for(drv_val)).pack(fill="x", pady=5)
        StatusCard(stat, "Perfil de otimização", profile_val, tone=_tone_for(profile_val)).pack(fill="x", pady=5)

        okay = all(x in "ATIVOATUALIZADO" for x in (def_val, power_val, drv_val)) and profile_val not in ("NÃO",)
        total = ctk.CTkFrame(stat, fg_color="transparent")
        total.pack(fill="x", pady=(18, 0))
        Badge(total, text="SISTEMA SAUDÁVEL" if okay else "ATENÇÃO NECESSÁRIA",
              tone="green" if okay else "orange", size=12).pack(side="left")
        Button(total, text="Atualizar", variant="secondary", command=self._load, icon="↻").pack(side="right")
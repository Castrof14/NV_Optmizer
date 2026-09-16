"""Drivers — placa de vídeo e versão real do driver."""

import customtkinter as ctk

import frontend.api as api
import frontend.modules_bridge as backend
from frontend.pages import PageBase
from frontend.theme import Theme
from frontend.components import (Card, Button, Badge, PulseBar, LoadingState, ErrorState)


class DriversPage(PageBase):
    page_id = "drivers"
    title = "Drivers"
    subtitle = "Placa de vídeo, versão do driver e atualização via Windows."
    badge_text = None

    def _build(self):
        self._running = False
        self._load()

    def _load(self):
        for w in self.winfo_children():
            w.destroy()
        LoadingState(self, message="Lendo placa de vídeo e drivers...").pack(fill="both", expand=True)
        self._action("Lendo drivers", fn=api.drivers_state,
                     on_done=self._render, on_error=lambda e: self._fail(str(e)))

    def _fail(self, msg):
        for w in self.winfo_children():
            w.destroy()
        ErrorState(self, message=f"{msg}", on_retry=self._load).pack(fill="both", expand=True)

    def _render(self, data):
        for w in self.winfo_children():
            w.destroy()

        card = Card(self, title="PLACA DE VÍDEO")
        card.pack(fill="x", pady=(0, 20))

        name = data.get("name") or "Não disponível"
        ctk.CTkLabel(card.body, text=name, font=Theme.display_font(26),
                     text_color=Theme.TEXT, anchor="w").pack(anchor="w")

        rows = ctk.CTkFrame(card.body, fg_color="transparent")
        rows.pack(fill="x", pady=(18, 0))
        ctk.CTkLabel(rows, text="DRIVER", font=Theme.font(11, weight="bold"),
                     text_color=Theme.MUTED).pack(anchor="w")
        ctk.CTkLabel(rows, text=data.get("driver", "—") if data.get("available") else "Não disponível",
                     font=Theme.num_font(17), text_color=Theme.TEXT_SOFT).pack(anchor="w", pady=(4, 0))
        if data.get("available") and data.get("date"):
            ctk.CTkLabel(rows, text=f"Data: {data['date']}", font=Theme.font(12),
                         text_color=Theme.BODY).pack(anchor="w", pady=(2, 0))

        st = ctk.CTkFrame(card.body, fg_color="transparent")
        st.pack(fill="x", pady=(14, 0))
        ctk.CTkLabel(st, text="STATUS", font=Theme.font(11, weight="bold"),
                     text_color=Theme.MUTED).pack(side="left")
        is_updated = bool(data.get("available") and data.get("driver") and data.get("driver") != "—")
        Badge(st, text="Atualizado" if is_updated else "Não verificado",
              tone="green" if is_updated else "orange").pack(side="left", padx=(12, 0))

        btns = ctk.CTkFrame(card.body, fg_color="transparent")
        btns.pack(anchor="w", pady=(18, 0))
        Button(btns, text="PROCURAR DRIVER", variant="primary", icon="🔍",
               command=self._search).pack(side="left", padx=(0, 8))
        Button(btns, text="Atualizar via Winget", variant="secondary",
               command=self._update_winget).pack(side="left", padx=(0, 8))
        Button(btns, text="Verificar novamente", variant="ghost",
               command=self._load).pack(side="left")

        self._status = ctk.CTkLabel(card.body, text="", font=Theme.font(13),
                                    text_color=Theme.SUCCESS, anchor="w")
        self._status.pack(anchor="w", pady=(16, 0))
        self._bar = PulseBar(card.body, height=8, color=Theme.NV_BLUE)
        self._bar.pack_forget()

        logs = ctk.CTkTextbox(self, fg_color=Theme.SURFACE_ELEV, text_color=Theme.BODY,
                              font=Theme.font(12, mono=True), corner_radius=Theme.R_LG,
                              border_width=1, border_color=Theme.HAIRLINE, height=200, wrap="word")
        logs.pack(fill="x")
        self._logs = logs

    def _log(self, msg):
        self._logs.configure(state="normal")
        self._logs.insert("end", f"  {msg}\n")
        self._logs.see("end")
        self._logs.configure(state="disabled")

    def _search(self):
        if self._running:
            return
        self.app.confirm(
            "ATUALIZAR DRIVER DA PLACA DE VÍDEO?",
            "O NV irá verificar e atualizar os drivers do sistema via Windows Update/Winget.",
            danger=False, on_confirm=self._update_winget)

    def _update_winget(self):
        if self._running:
            return
        self._running = True
        self._bar.pack(fill="x", pady=(12, 0))
        self._bar.start()
        self._status.configure(text="Atualizando drivers... Pode levar alguns minutos.", text_color=Theme.NV_YELLOW)
        self._log("Iniciando atualização de drivers...")

        self._action("Atualizar driver",
                     fn=backend.update_drivers_winget,
                     on_log=self._log,
                     on_done=lambda _: self._finish(True, None),
                     on_error=lambda e: self._finish(False, str(e)))

    def _finish(self, ok, err):
        self._running = False
        self._bar.stop()
        self._bar.pack_forget()
        if ok:
            self._status.configure(text="Atualização finalizada.", text_color=Theme.SUCCESS)
            self._toast("success", "Verificação de drivers concluída.")
            self._log(operation="Atualizar driver", result="OK")
        else:
            self._status.configure(text="Não foi possível concluir a atualização.", text_color=Theme.DANGER)
            self._toast("error", f"Falha ao atualizar drivers: {err}")
            self._log(operation="Atualizar driver", result="FALHA", detail=str(err))
        self.after(600, self._load)
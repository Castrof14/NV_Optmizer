"""Defender — status e toggle da proteção em tempo real."""

import customtkinter as ctk

import frontend.api as api
import frontend.modules_bridge as backend
from frontend.pages import PageBase
from frontend.theme import Theme
from frontend.components import (Card, Button, Badge, PulseBar, LoadingState, ErrorState)


class DefenderPage(PageBase):
    page_id = "defender"
    title = "Windows Defender"
    subtitle = "Status do antivírus, proteção em tempo real e assinaturas."
    badge_text = None

    def _build(self):
        self._load()

    def _load(self):
        for w in self.winfo_children():
            w.destroy()
        LoadingState(self, message="Lendo status do Windows Defender...").pack(fill="both", expand=True)
        self._action("Ler Defender", fn=api.defender_state, on_done=self._render, on_error=lambda e: self._fail(str(e)))

    def _fail(self, msg):
        for w in self.winfo_children():
            w.destroy()
        ErrorState(self, message=str(msg), on_retry=self._load).pack(fill="both", expand=True)

    def _render(self, data):
        for w in self.winfo_children():
            w.destroy()

        avail = data.get("available", False)

        # Status geral
        status = Card(self, title="STATUS DO DEFENDER")
        status.pack(fill="x", pady=(0, 20))
        Badge(status.body,
              text="ATIVO" if avail else "Não disponível",
              tone="green" if avail else "neutral").pack(anchor="w")

        if not avail:
            ctk.CTkLabel(status.body, text="O Windows Defender não foi detectado nesta máquina.",
                         font=Theme.font(14), text_color=Theme.BODY, anchor="w").pack(anchor="w", pady=(12, 0))
            return

        # Proteção em tempo real
        rt = data.get("real_time")
        rt_card = Card(self, title="Proteção em tempo real")
        rt_card.pack(fill="x", pady=(0, 20))
        rt_badge = Badge(rt_card.body,
                         text="ATIVADA" if rt else "DESATIVADA",
                         tone="green" if rt else "red")
        rt_badge.pack(anchor="w")

        self._rt_btn = Button(rt_card.body,
                              text="DESATIVAR" if rt else "ATIVAR",
                              variant="danger" if rt else "primary",
                              command=self._toggle_rt)
        self._rt_btn.pack(anchor="w", pady=(12, 0))

        ctk.CTkLabel(rt_card.body,
                     text="A proteção em tempo real monitora ameaças continuamente.",
                     font=Theme.font(13), text_color=Theme.BODY, anchor="w").pack(anchor="w", pady=(8, 0))

        self._status = ctk.CTkLabel(rt_card.body, text="", font=Theme.font(13),
                                    text_color=Theme.SUCCESS, anchor="w")
        self._status.pack(anchor="w", pady=(10, 0))
        self._bar = PulseBar(rt_card.body, height=8, color=Theme.NV_BLUE)
        self._bar.pack_forget()

        # Assinaturas
        sig = Card(self, title="ASSINATURAS")
        sig.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(sig.body, text=f"Versão: {data.get('signatures', '—')}",
                     font=Theme.font(14), text_color=Theme.TEXT_SOFT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(sig.body, text=f"Última atualização: {data.get('last_update', '—')}",
                     font=Theme.font(14), text_color=Theme.BODY, anchor="w").pack(anchor="w", pady=(4, 0))

        Button(sig.body, text="ATUALIZAR ASSINATURAS", variant="secondary",
               command=self._update_signatures).pack(anchor="w", pady=(14, 0))

    def _toggle_rt(self):
        data = api.defender_state()
        new_val = not data.get("real_time", False)
        action = "DESATIVAR" if new_val is False else "ATIVAR"
        self.app.confirm(
            f"{action} PROTEÇÃO EM TEMPO REAL?",
            "Esta ação afeta a segurança do computador em tempo real.",
            danger=not new_val,
            on_confirm=lambda: self._run_toggle(new_val),
        )

    def _run_toggle(self, enabled):
        self._rt_btn.configure(state="disabled")
        self._bar.pack(fill="x", pady=(10, 0))
        self._bar.start()
        self._status.configure(text="Alterando proteção em tempo real...", text_color=Theme.NV_YELLOW)
        self.app.set_busy(True, "Configurando Windows Defender")

        def run():
            backend.set_defender_realtime(enabled)

        self._action("Alterar Defender", fn=run,
                     on_done=lambda _: self._done(enabled),
                     on_error=lambda e: self._fail_toggle(str(e)))

    def _done(self, enabled):
        self.app.set_busy(False)
        self._bar.stop(); self._bar.pack_forget()
        self._status.configure(
            text=f"Proteção em tempo real {'ATIVADA' if enabled else 'DESATIVADA'}.",
            text_color=Theme.SUCCESS if enabled else Theme.WARNING,
        )
        label = "ATIVADA" if enabled else "DESATIVADA"
        self._toast("success", f"Proteção em tempo real {label}.")
        self._log(operation="Defender", result="OK", detail=f"Real time {label}")
        self.after(600, self._load)

    def _fail_toggle(self, msg):
        self.app.set_busy(False)
        self._bar.stop(); self._bar.pack_forget()
        self._rt_btn.configure(state="normal")
        self._status.configure(text="Falha ao alterar proteção.", text_color=Theme.DANGER)
        self._toast("error", f"Falha ao alterar Defender: {msg}")

    def _update_signatures(self):
        self.app.confirm(
            "ATUALIZAR ASSINATURAS DO DEFENDER?",
            "O Windows irá baixar as assinaturas mais recentes.",
            danger=False,
            on_confirm=self._run_update_sig,
        )

    def _run_update_sig(self):
        self._bar.pack(fill="x", pady=(10, 0))
        self._bar.start()
        self._status.configure(text="Atualizando assinaturas...", text_color=Theme.NV_YELLOW)
        self.app.set_busy(True, "Atualizando assinaturas do Defender")

        def run():
            backend.update_signatures()

        self._action("Atualizar assinaturas", fn=run,
                     on_done=lambda _: self._sig_done(),
                     on_error=lambda e: self._sig_fail(str(e)))

    def _sig_done(self):
        self.app.set_busy(False)
        self._bar.stop(); self._bar.pack_forget()
        self._status.configure(text="Assinaturas atualizadas.", text_color=Theme.SUCCESS)
        self._toast("success", "Assinaturas do Windows Defender atualizadas.")
        self._log(operation="Atualizar assinaturas", result="OK")
        self.after(600, self._load)

    def _sig_fail(self, msg):
        self.app.set_busy(False)
        self._bar.stop(); self._bar.pack_forget()
        self._status.configure(text="Falha ao atualizar assinaturas.", text_color=Theme.DANGER)
        self._toast("error", f"Falha ao atualizar assinaturas: {msg}")
        self._log(operation="Atualizar assinaturas", result="FALHA", detail=str(msg))
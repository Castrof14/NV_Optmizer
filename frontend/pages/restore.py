"""Restauração — ponto de restauração e reversão da última otimização."""

import customtkinter as ctk

import frontend.modules_bridge as backend
from frontend.pages import PageBase
from frontend.theme import Theme
from frontend.components import (Card, Button, Badge, PulseBar)


class RestorePage(PageBase):
    page_id = "restauracao"
    title = "Restauração"
    subtitle = "Ponto de restauração do sistema e reversão de otimizações."
    badge_text = None

    def _build(self):
        # Ponto de restauração
        card = Card(self, title="Ponto de restauração")
        card.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(card.body,
                     text="Crie um ponto de restauração antes de alterações importantes no sistema.",
                     font=Theme.font(14), text_color=Theme.BODY, anchor="w", justify="left",
                     wraplength=560).pack(anchor="w")
        Button(card.body, text="CRIAR PONTO DE RESTAURAÇÃO", variant="primary",
               icon="↻", command=self._confirm_create).pack(anchor="w", pady=(14, 0))

        self._create_status = ctk.CTkLabel(card.body, text="", font=Theme.font(13),
                                           text_color=Theme.SUCCESS, anchor="w")
        self._create_status.pack(anchor="w", pady=(12, 0))
        self._create_bar = PulseBar(card.body, height=8, color=Theme.NV_BLUE)
        self._create_bar.pack_forget()

        # Restaurar otimização
        card2 = Card(self, title="Restaurar otimização", badge="Última otimização")
        card2.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(card2.body,
                     text="Reabilita os serviços e o plano de energia alterados pela última otimização.",
                     font=Theme.font(14), text_color=Theme.BODY, anchor="w", justify="left",
                     wraplength=560).pack(anchor="w")
        Button(card2.body, text="RESTAURAR OTIMIZAÇÃO", variant="secondary",
               icon="↺", command=self._confirm_restore).pack(anchor="w", pady=(14, 0))

        self._restore_status = ctk.CTkLabel(card2.body, text="", font=Theme.font(13),
                                            text_color=Theme.SUCCESS, anchor="w")
        self._restore_status.pack(anchor="w", pady=(12, 0))
        self._restore_bar = PulseBar(card2.body, height=8, color=Theme.NV_YELLOW)
        self._restore_bar.pack_forget()

        tip = Card(self, title="Sobre")
        tip.pack(fill="x")
        ctk.CTkLabel(tip.body,
                     text="• A criação do ponto de restauração depende do Sistema de "
                          "Proteção do Windows estar habilitado.\n"
                          "• No Windows a restauração pode exigir elevação (administrador).",
                     font=Theme.font(13), text_color=Theme.MUTED, anchor="w", justify="left",
                     wraplength=560).pack(anchor="w")

    def _confirm_create(self):
        self.app.confirm(
            "CRIAR PONTO DE RESTAURAÇÃO?",
            "Recomendado antes de aplicar otimizações ou alterações no sistema.",
            danger=True, on_confirm=self._create_point,
        )

    def _create_point(self):
        self._create_bar.pack(fill="x", pady=(10, 0))
        self._create_bar.start()
        self._create_status.configure(text="Criando ponto de restauração...", text_color=Theme.NV_YELLOW)
        self.app.set_busy(True, "Criando ponto de restauração")

        def run():
            backend.create_restore_point()

        self._action("Criar ponto de restauração", fn=run,
                     on_done=lambda _: self._create_done(),
                     on_error=lambda e: self._create_fail(str(e)))

    def _create_done(self):
        self.app.set_busy(False)
        self._create_bar.stop(); self._create_bar.pack_forget()
        self._create_status.configure(text="Ponto de restauração criado.", text_color=Theme.SUCCESS)
        self._toast("success", "Ponto de restauração criado.")
        self._log(operation="Ponto de restauração", result="OK")

    def _create_fail(self, msg):
        self.app.set_busy(False)
        self._create_bar.stop(); self._create_bar.pack_forget()
        self._create_status.configure(text="Falha ao criar ponto de restauração.", text_color=Theme.DANGER)
        self._toast("error", f"Falha: {msg}")
        self._log(operation="Ponto de restauração", result="FALHA", detail=str(msg))

    def _confirm_restore(self):
        self.app.confirm(
            "RESTAURAR A ÚLTIMA OTIMIZAÇÃO?",
            "Os serviços desabilitados serão reabilitados e o plano de energia restaurado.",
            danger=True, on_confirm=self._restore_optimization,
        )

    def _restore_optimization(self):
        self._restore_bar.pack(fill="x", pady=(10, 0))
        self._restore_bar.start()
        self._restore_status.configure(text="Restaurando otimização...", text_color=Theme.NV_YELLOW)
        self.app.set_busy(True, "Restaurando otimização")

        def run():
            return backend.apply_restore()

        def done(rows):
            self.app.set_busy(False)
            self._restore_bar.stop(); self._restore_bar.pack_forget()
            ok = all(r["result"] == "OK" for r in rows)
            self._restore_status.configure(
                text="Restauração concluída." if ok else "Concluída com falhas.",
                text_color=Theme.SUCCESS if ok else Theme.WARNING,
            )
            self._toast("success" if ok else "warning",
                        "Restauração concluída." if ok else "Restauração com falhas nas etapas.")
            self.app.current_profile = None
            for r in rows:
                self._log(operation=r["operation"], service=r["service"],
                          before=r["before"], after=r["after"], result=r["result"],
                          detail=r["detail"])

        self._action("Restaurar otimização", fn=run,
                     on_done=done, on_error=lambda e: self._restore_fail(str(e)))

    def _restore_fail(self, msg):
        self.app.set_busy(False)
        self._restore_bar.stop(); self._restore_bar.pack_forget()
        self._restore_status.configure(text="Falha ao restaurar otimização.", text_color=Theme.DANGER)
        self._toast("error", f"Falha: {msg}")
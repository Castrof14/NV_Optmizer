"""Confirmações para operações importantes/perigosas."""

import customtkinter as ctk

from frontend.theme import Theme
from .modal import Modal


class ConfirmDialog(Modal):
    """Modal de confirmação com mensagem, detalhe opcional e ações."""

    def confirm(self, title, message, detail=None, danger=False,
                confirm_label="Continuar", cancel_label="Cancelar",
                on_confirm=None, on_cancel=None, icon=None):
        def build(body):
            ctk.CTkLabel(
                body,
                text=message,
                font=Theme.font(15),
                text_color=Theme.TEXT_SOFT,
                justify="left",
                wraplength=560,
                anchor="w",
            ).pack(fill="x", pady=(4, 8))
            if detail:
                detail_box = ctk.CTkTextbox(
                    body,
                    fg_color=Theme.SURFACE_STRONG,
                    text_color=Theme.BODY,
                    font=Theme.font(12),
                    corner_radius=Theme.R_MD,
                    height=84,
                    wrap="word",
                )
                detail_box.pack(fill="x", pady=(6, 0))
                detail_box.insert("1.0", detail)
                detail_box.configure(state="disabled")

        self.show(
            title=title,
            icon=icon,
            body_builder=build,
            danger=danger,
            primary={"label": confirm_label, "command": on_confirm},
            secondary={"label": cancel_label, "command": on_cancel},
        )
"""Estado de erro com ação Retry / Ver Log."""

import customtkinter as ctk

from frontend.theme import Theme
from .button import Button


class ErrorState(ctk.CTkFrame):
    def __init__(self, master, title="Não foi possível concluir a operação", message=None,
                 on_retry=None, on_log=None, **kw):
        super().__init__(master, fg_color=Theme.SURFACE_ELEV, corner_radius=Theme.R_XL, **kw)
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.place(relx=0.5, rely=0.45, anchor="center")
        ctk.CTkLabel(inner, text="✗", font=Theme.display_font(44), text_color=Theme.DANGER).pack()
        ctk.CTkLabel(inner, text=title, font=Theme.display_font(20), text_color=Theme.TEXT).pack(pady=(10, 4))
        if message:
            ctk.CTkLabel(inner, text=message, font=Theme.font(13), text_color=Theme.BODY,
                         wraplength=420, justify="center").pack(pady=(0, 10))
        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(pady=(6, 0))
        if on_retry:
            Button(btns, text="Tentar novamente", variant="primary", command=on_retry).pack(side="left", padx=4)
        if on_log:
            Button(btns, text="Ver Log", variant="secondary", command=on_log).pack(side="left", padx=4)
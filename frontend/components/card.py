"""Cards: contêineres com canto xl, hairline e elevação única."""

import customtkinter as ctk

from frontend.theme import Theme
from .badge import Badge


class Card(ctk.CTkFrame):
    """Card padrão com cabeçalho opcional (título + subtítulo + badge)."""

    def __init__(self, master, title=None, subtitle=None, badge=None, hover=False,
                 body_pad=Theme.CARD_PAD, **kw):
        super().__init__(
            master,
            fg_color=Theme.SURFACE_ELEV,
            corner_radius=Theme.R_XL,
            border_width=1,
            border_color=Theme.HAIRLINE,
            **kw,
        )
        self.hover = hover
        grid = 0
        if title or subtitle or badge:
            head = ctk.CTkFrame(self, fg_color="transparent")
            head.grid(row=0, column=0, sticky="ew", padx=Theme.CARD_PAD, pady=(Theme.CARD_PAD, 0))
            head.grid_columnconfigure(0, weight=1)
            right = 1
            if title:
                ctk.CTkLabel(head, text=title, font=Theme.display_font(20),
                             text_color=Theme.TEXT, anchor="w").grid(row=0, column=0, sticky="w")
            if badge:
                Badge(head, text=badge).grid(row=0, column=right, sticky="e", padx=(8, 0))
                right += 1
            if subtitle:
                ctk.CTkLabel(head, text=subtitle, font=Theme.font(13),
                             text_color=Theme.BODY, anchor="w").grid(row=1, column=0, columnspan=right, sticky="w", pady=(2, 0))
            grid = 1

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=grid, column=0, sticky="nsew", padx=body_pad, pady=(0, body_pad))
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(grid, weight=1)

        if hover:
            self.bind("<Enter>", lambda e: self.configure(border_color=Theme.HAIRLINE, fg_color=Theme.SURFACE_ELEV2))
            self.bind("<Leave>", lambda e: self.configure(border_color=Theme.HAIRLINE, fg_color=Theme.SURFACE_ELEV))


class HardwareCard(ctk.CTkFrame):
    """Card de métrica/spec de hardware: ícone, rótulo, valor grande, status."""

    def __init__(self, master, icon, title, value="—", sub=None, tone=None, value_small=False, **kw):
        super().__init__(
            master,
            fg_color=Theme.SURFACE_ELEV,
            corner_radius=Theme.R_XL,
            border_width=1,
            border_color=Theme.HAIRLINE,
            **kw,
        )
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=Theme.CARD_PAD, pady=Theme.CARD_PAD)

        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=icon, font=Theme.font(16), text_color=Theme.TEXT_SOFT).pack(side="left")
        ctk.CTkLabel(top, text=title, font=Theme.font(12, weight="bold"), text_color=Theme.BODY).pack(side="left", padx=(8, 0))

        val = ctk.CTkLabel(
            inner,
            text=value if value else "—",
            font=Theme.num_font(size=20) if not value_small else Theme.num_font(size=15),
            text_color=Theme.TEXT,
            anchor="w",
            justify="left",
            wraplength=300,
        )
        val.pack(fill="x", pady=(14, 0))
        if sub:
            ctk.CTkLabel(inner, text=sub, font=Theme.font(12), text_color=Theme.MUTED,
                         anchor="w", justify="left", wraplength=300).pack(fill="x", pady=(4, 0))
        if tone:
            Badge(inner, text=tone["label"], tone=tone["tone"]).pack(anchor="w", pady=(12, 0))


class StatusCard(ctk.CTkFrame):
    """Linha de status: rótulo à esquerda, valor + selo semântico à direita."""

    def __init__(self, master, label, value, tone="neutral", action_text=None, action_command=None, **kw):
        super().__init__(
            master,
            fg_color=Theme.SURFACE_ELEV,
            corner_radius=Theme.R_LG,
            border_width=1,
            border_color=Theme.HAIRLINE,
            height=58,
            **kw,
        )
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=label, font=Theme.font(14), text_color=Theme.BODY,
                     anchor="w").grid(row=0, column=0, sticky="w", padx=(18, 8))
        if action_text and action_command:
            from .button import Button
            b = Button(self, text=action_text, variant="ghost", command=action_command, small=True, height=30)
            b.grid(row=0, column=1, sticky="e", padx=(4, 8))
        Badge(self, text=value, tone=tone).grid(row=0, column=2, sticky="e", padx=(0, 14))
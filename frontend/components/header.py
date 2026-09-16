"""Cabeçalho da página (título, subtítulo, badge lateral, system chip)."""

import customtkinter as ctk

from frontend.theme import Theme
from .badge import Badge


class Header(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=Theme.SURFACE, corner_radius=0, height=Theme.HEADER_H, **kw)
        self.pack_propagate(False)
        self.grid_columnconfigure(1, weight=1)

        # Linha azul NV sutil no topo
        ctk.CTkFrame(self, fg_color=Theme.NV_BLUE, height=2, corner_radius=0).grid(
            row=0, column=0, columnspan=3, sticky="new"
        )

        self.title = ctk.CTkLabel(self, text="", font=Theme.display_font(24),
                                  text_color=Theme.TEXT, anchor="w")
        self.title.grid(row=1, column=0, sticky="w", padx=(Theme.CONTENT_PAD, 0), pady=(6, 0))

        self.subtitle = ctk.CTkLabel(self, text="", font=Theme.font(13),
                                     text_color=Theme.BODY, anchor="w")
        self.subtitle.grid(row=2, column=0, sticky="w", padx=(Theme.CONTENT_PAD, 0))

        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=1, column=2, rowspan=2, sticky="ne", padx=Theme.CONTENT_PAD, pady=(0, 4))

    def set_page(self, title: str, subtitle: str = "", badge_text: str = None):
        self.title.configure(text=title)
        self.subtitle.configure(text=subtitle)
        chip = None
        for w in self.right_frame.winfo_children():
            if getattr(w, "_nv_system", False):
                try:
                    chip = w.cget("text")
                except Exception:
                    chip = None
                break
        for w in self.right_frame.winfo_children():
            w.destroy()
        Badge(self.right_frame, text="NV", tone="blue", size=11).pack(side="right")
        if badge_text:
            Badge(self.right_frame, text=badge_text, tone="green", size=11).pack(side="right", padx=(0, 8))
        if chip:
            self.set_system(chip)

    def set_system(self, text: str):
        for w in self.right_frame.winfo_children():
            if getattr(w, "_nv_system", False):
                w.destroy()
        chip = Badge(self.right_frame, text=text, tone="neutral", size=11)
        chip._nv_system = True
        chip.pack(side="right", padx=(0, 6))
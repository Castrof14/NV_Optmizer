"""Badge pill semântico (geometria pill, texto caption-strong)."""

import customtkinter as ctk

from frontend.theme import Theme


class Badge(ctk.CTkLabel):
    TONES = {
        "neutral": {"fg": Theme.SURFACE_STRONG, "text": Theme.TEXT_SOFT},
        "blue": {"fg": "#0d1b4d", "text": "#9db4ff"},
        "yellow": {"fg": "#3a3400", "text": Theme.NV_YELLOW},
        "green": {"fg": "#0a2b20", "text": Theme.SUCCESS},
        "red": {"fg": "#3d0f14", "text": "#ff7c87"},
        "orange": {"fg": "#3a2a08", "text": Theme.WARNING},
        "gray": {"fg": Theme.SURFACE_STRONG, "text": Theme.MUTED},
        "white": {"fg": "#ffffff", "text": "#0a0b0d"},
    }

    def __init__(self, master, text="", tone="neutral", size=12, **kw):
        t = self.TONES.get(tone, self.TONES["neutral"])
        super().__init__(
            master,
            text=text,
            font=Theme.font(size=size, weight="bold"),
            text_color=t["text"],
            fg_color=t["fg"],
            corner_radius=Theme.R_PILL,
            padx=12,
            pady=5,
            **kw,
        )

    def set_tone(self, tone):
        t = self.TONES.get(tone, self.TONES["neutral"])
        self.configure(text_color=t["text"], fg_color=t["fg"])
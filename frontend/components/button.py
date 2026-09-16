"""Botões pill (geometria editorial do design system)."""

import customtkinter as ctk

from frontend.theme import Theme


class Button(ctk.CTkButton):
    VARIANTS = {
        "primary": {"fg": Theme.NV_BLUE, "hover": Theme.NV_BLUE_HOVER, "text": "#ffffff", "border": None},
        "secondary": {"fg": Theme.SURFACE_STRONG, "hover": Theme.SURFACE_ELEV2, "text": Theme.TEXT, "border": None},
        "ghost": {"fg": "transparent", "hover": Theme.SURFACE_ELEV2, "text": Theme.TEXT_SOFT, "border": None},
        "outline": {"fg": "transparent", "hover": Theme.SURFACE_ELEV2, "text": Theme.TEXT, "border": Theme.HAIRLINE},
        "yellow": {"fg": Theme.NV_YELLOW, "hover": Theme.NV_YELLOW_DIM, "text": "#131400", "border": None},
        "danger": {"fg": Theme.DANGER, "hover": "#a31924", "text": "#ffffff", "border": None},
        "success": {"fg": Theme.SUCCESS, "hover": "#048c55", "text": "#ffffff", "border": None},
    }

    def __init__(self, master, text="", variant="primary", command=None, height=42,
                 width=None, icon=None, small=False, **kw):
        v = self.VARIANTS.get(variant, self.VARIANTS["primary"])
        self._busy_text = None
        if width is None:
            width = -1  # tamanho automático do conteúdo
            auto_width = True
        else:
            auto_width = False
        label = (f"{icon}  {text}" if icon else text)
        super().__init__(
            master,
            text=label,
            command=command,
            height=28 if small else height,
            width=width,
            corner_radius=Theme.R_PILL,
            fg_color=v["fg"],
            hover_color=v["hover"],
            text_color=v["text"],
            border_width=1 if v["border"] else 0,
            border_color=v["border"],
            font=Theme.font(size=13, weight="bold") if small else Theme.font(size=14, weight="bold"),
        )
        self._auto_width = auto_width
        self._base_label = label

    def set_loading(self, loading: bool, busy_text: str = "Processando..."):
        if loading:
            self.configure(state="disabled", text=f"◌  {busy_text}")
        else:
            self.configure(state="normal", text=self._base_label)


class GhostButton(Button):
    def __init__(self, master, text="", command=None, **kw):
        super().__init__(master, text=text, variant="ghost", command=command, width=1, **kw)
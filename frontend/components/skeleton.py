"""Skeletons (loading) com pulso sutil."""

import customtkinter as ctk

from frontend.theme import Theme


class SkeletonLine(ctk.CTkFrame):
    """Retângulo cinza pulsante que simula conteúdo carregando."""

    def __init__(self, master, width=200, height=16, radius=Theme.R_SM, **kw):
        super().__init__(
            master,
            width=width, height=height,
            fg_color=Theme.SURFACE_STRONG,
            corner_radius=radius,
            **kw,
        )
        self._pulse()

    def _pulse(self):
        try:
            if self.winfo_exists():
                current = self.cget("fg_color")
                new = Theme.SURFACE_ELEV2 if current == Theme.SURFACE_STRONG else Theme.SURFACE_STRONG
                self.configure(fg_color=new)
                self.after(450, self._pulse)
        except Exception:
            pass


class SkeletonCard(ctk.CTkFrame):
    """Card skeleton: título + várias linhas pulsando."""

    def __init__(self, master, lines=4, **kw):
        super().__init__(
            master,
            fg_color=Theme.SURFACE_ELEV,
            corner_radius=Theme.R_XL,
            border_width=1,
            border_color=Theme.HAIRLINE,
            **kw,
        )
        SkeletonLine(self, width=140, height=14).pack(anchor="w", pady=(4, 14), padx=24)
        for i in range(lines):
            SkeletonLine(self, width=240 - (i * 18), height=12).pack(anchor="w", pady=5, padx=24)
        ctk.CTkFrame(self, fg_color="transparent", height=6).pack()
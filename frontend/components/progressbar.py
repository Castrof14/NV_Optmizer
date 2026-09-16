"""Barras de progresso (determinada + pulsante para operações em andamento)."""

import customtkinter as ctk

from frontend.theme import Theme


class Bar(ctk.CTkFrame):
    """Barra determinada com rótulo percentual opcional."""

    def __init__(self, master, value=0.0, height=10, show_pct=True, color=Theme.NV_BLUE, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.height = height
        self.color = color
        row = 0
        if show_pct:
            self.pct = ctk.CTkLabel(self, text="0%", font=Theme.font(12, weight="bold", mono=True),
                                    text_color=Theme.TEXT_SOFT, anchor="e")
            self.pct.grid(row=0, column=0, sticky="e")
            self.grid_columnconfigure(0, weight=1)
            row = 1
        self.bar = ctk.CTkProgressBar(
            self,
            width=140, height=self.height,
            corner_radius=Theme.R_PILL,
            fg_color=Theme.SURFACE_STRONG,
            progress_color=self.color,
            mode="determinate",
        )
        self.bar.grid(row=row, column=0, sticky="ew", pady=(6, 0))
        self.set(value)

    def set(self, value):
        v = max(0.0, min(1.0, float(value)))
        self.bar.set(v)
        if hasattr(self, "pct"):
            self.pct.configure(text=f"{int(round(v * 100))}%")


class PulseBar(ctk.CTkFrame):
    """Barra indeterminada animada — representa trabalho em andamento."""

    def __init__(self, master, height=10, color=Theme.NV_BLUE, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.bar = ctk.CTkProgressBar(
            master=self,
            width=160, height=height,
            corner_radius=Theme.R_PILL,
            fg_color=Theme.SURFACE_STRONG,
            progress_color=color,
            mode="indeterminate",
            indeterminate_speed=0.8,
        )
        self.bar.pack(fill="x")
        self.bar.start()

    def start(self):
        try:
            self.bar.start()
        except Exception:
            pass

    def stop(self):
        self.bar.stop()
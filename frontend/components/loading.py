"""Estado de carregamento fullscreen (replaces page while loading)."""

import customtkinter as ctk

from frontend.theme import Theme
from .spinner import Spinner
from .skeleton import SkeletonCard


class LoadingState(ctk.CTkFrame):
    def __init__(self, master, message="Carregando dados...", skeleton=True, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.place(relx=0.5, rely=0.45, anchor="center")
        self.spinner = Spinner(center, text=message, size=14)
        self.spinner.pack(pady=(0, 14))
        self.spinner.start()
        if skeleton:
            wrap = ctk.CTkFrame(center, fg_color="transparent")
            wrap.pack(pady=(8, 0))
            for _ in range(3):
                SkeletonCard(wrap, lines=3).pack(pady=8)

    def set_message(self, msg):
        self.spinner.set_text(msg)

    def stop(self):
        self.spinner.stop()
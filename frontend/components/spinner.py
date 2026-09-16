"""Spinner discreto (rotação braille) para estados de espera."""

import customtkinter as ctk

from frontend.theme import Theme

_CHARS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class Spinner(ctk.CTkLabel):
    def __init__(self, master, text="", color=Theme.NV_BLUE, size=14, **kw):
        super().__init__(master, text="", text_color=color, font=Theme.font(size=size), **kw)
        self._spinner_msg = text
        self._running = False
        self._i = 0

    def start(self):
        self._running = True
        self._tick()

    def stop(self):
        self._running = False
        self.configure(text=self._spinner_msg)

    def set_text(self, text):
        self._spinner_msg = text

    def _tick(self):
        if not self._running:
            return
        ch = _CHARS[self._i % len(_CHARS)]
        self.configure(text=f"{ch} {self._spinner_msg}")
        self._i += 1
        try:
            self.after(80, self._tick)
        except Exception:
            pass
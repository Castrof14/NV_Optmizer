"""Notificações toast (sucesso, erro, aviso, informação)."""

import customtkinter as ctk

from frontend.theme import Theme


class ToastManager:
    ICONS = {"success": "✓", "error": "✗", "warning": "!", "info": "i"}

    def __init__(self, root: ctk.CTk):
        self.root = root
        self._toasts = []  # [(frame, kind)]

    def show(self, kind: str, message: str, duration: float = 3.8):
        kind = kind if kind in self.ICONS else "info"
        toast = ctk.CTkFrame(
            self.root,
            fg_color=Theme.SURFACE_ELEV2,
            corner_radius=Theme.R_LG,
            border_width=1,
            border_color=Theme.HAIRLINE,
            width=380,
        )
        toast.pack_propagate(False)

        icon = ctk.CTkLabel(toast, text=self.ICONS[kind], font=Theme.font(15, weight="bold"),
                            text_color=Theme._toast_color(kind), width=34)
        icon.pack(side="left", padx=(16, 4), pady=14)
        ctk.CTkLabel(toast, text=message, font=Theme.font(13), text_color=Theme.TEXT_SOFT,
                     wraplength=300, justify="left", anchor="w").pack(side="left", fill="x", pady=14, padx=(0, 14))

        self._toasts.append((toast, kind))
        self._relayout()
        self._animate_in(toast, kind)
        self.root.after(int(duration * 1000), lambda: self._dismiss(toast))

    def _relayout(self):
        y = 90
        for toast, _ in self._toasts:
            if toast.winfo_exists():
                toast.place(relx=1.0, x=-24, y=-y, anchor="se")
                y += 84

    def _animate_in(self, toast, kind):
        try:
            start = 320
            end = -24
            steps = 14
            y = self._current_y(toast)
            def step(i=0):
                if not toast.winfo_exists():
                    return
                x = int(start + (end - start) * (i / steps))
                toast.place(relx=1.0, x=x, y=-y, anchor="se")
                if i < steps:
                    toast.after(12, lambda: step(i + 1))
            step()
        except Exception:
            pass

    def _current_y(self, toast):
        idx = next((i for i, (t, _) in enumerate(self._toasts) if t is toast), 0)
        return 90 + idx * 84

    def _dismiss(self, toast):
        if not toast.winfo_exists():
            return
        try:
            toast.configure(fg_color=Theme.SURFACE)
            toast.border_color = Theme.SURFACE
        except Exception:
            pass
        try:
            self.root.after(160, lambda: self._finish(toast))
        except Exception:
            self._finish(toast)

    def _finish(self, toast):
        if toast in [t for t, _ in self._toasts]:
            self._toasts = [(t, k) for t, k in self._toasts if t is not toast]
        try:
            if toast.winfo_exists():
                toast.destroy()
        except Exception:
            pass
        self._relayout()
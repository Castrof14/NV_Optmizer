"""Modal: overlay escuro + painel central com fade-in."""

import customtkinter as ctk

from frontend.theme import Theme
from .button import Button


class Modal:
    """Janela modal sobre toda a aplicação (backdrop + painel xl)."""

    def __init__(self, root: ctk.CTk):
        self.root = root
        self._open = False
        self._overlay = None
        self._panel = None
        self._primary = {}

    @property
    def is_open(self) -> bool:
        return self._open

    def show(self, title, icon=None, body_builder=None, primary=None, secondary=None, danger=False, wide=False):
        """Abre o modal.

        body_builder(frame) -> preenche o conteúdo; pode devolver altura desejada.
        primary/secondary: dicts {"label","command","variant"}.
        """
        self.close()

        overlay = ctk.CTkFrame(self.root, fg_color="#07080a", corner_radius=0)
        overlay.place(relwidth=1, relheight=1, x=0, y=0)
        self._overlay = overlay

        panel = ctk.CTkFrame(
            overlay,
            fg_color=Theme.SURFACE_ELEV,
            corner_radius=Theme.R_XL,
            border_width=1,
            border_color=Theme.HAIRLINE,
            width=520 if not wide else 680,
        )
        panel.pack_propagate(False)
        panel.place(relx=0.5, rely=0.5, anchor="center")
        self._panel = panel

        # Cabeçalho
        head = ctk.CTkFrame(panel, fg_color="transparent")
        head.pack(fill="x", padx=Theme.CARD_PAD, pady=(Theme.CARD_PAD, 0))
        title_label = ctk.CTkLabel(
            head, text=(f"{icon}  {title}" if icon else title),
            font=Theme.display_font(22), text_color=Theme.TEXT, anchor="w", justify="left",
        )
        title_label.pack(side="left")
        if danger:
            from .badge import Badge
            Badge(head, text="ATENÇÃO", tone="red").pack(side="right")

        # Corpo
        body = ctk.CTkScrollableFrame(panel, fg_color="transparent", scrollbar_fg_color="transparent")
        body.pack(fill="both", expand=True, padx=Theme.CARD_PAD, pady=Theme.CARD_PAD)
        self.body = body

        if body_builder:
            body_builder(body)

        # Ações
        actions = ctk.CTkFrame(panel, fg_color="transparent")
        actions.pack(fill="x", padx=Theme.CARD_PAD, pady=(0, Theme.CARD_PAD))

        if secondary:
            Button(actions, text=secondary.get("label", "Cancelar"),
                   variant=secondary.get("variant", "secondary"),
                   command=lambda: (self.close(), secondary["command"]() if secondary.get("command") else None)
                   ).pack(side="right", padx=(0, 8))
        if primary:
            Button(actions, text=primary.get("label", "Continuar"),
                   variant=primary.get("variant", "danger" if danger else "primary"),
                   command=lambda: (self._keep_primary(primary), primary.get("command")() if primary.get("command") else None)
                   ).pack(side="right")

        overlay.bind("<Escape>", lambda e: self.close())
        overlay.focus_set()
        self._open = True
        self.fade_in()

    def _keep_primary(self, primary):
        # mantém referência ao primary para ações longas
        self._primary = primary

    def fade_in(self):
        steps = [("#0a0b0d", 0.92), ("#07080a", 1.0)]
        def run(i=0):
            if not self._open:
                return
            if i < len(steps):
                color, _ = steps[i]
                self._overlay.configure(fg_color=color)
                self._overlay.after(40, lambda: run(i + 1))
        run()

    def set_loading(self, loading: bool, text="Processando..."):
        if self._primary and "button" in self._primary:
            self._primary["button"].set_loading(loading, text)

    def close(self):
        if self._overlay is not None:
            try:
                self._overlay.destroy()
            except Exception:
                pass
        self._overlay = None
        self._panel = None
        self._open = False
        self._primary = {}
"""Sidebar de navegação com grupos e estado ativo."""

import customtkinter as ctk

from frontend.theme import Theme


class Sidebar(ctk.CTkFrame):
    """
    Barra lateral fixa: logo NV (N azul / V amarelo) + nav groups/items.
    Segue o padrão dark hero (fundo escuro, itens brancos/muted).
    """

    NAV = [
        {"label": "Dashboard", "icon": "◆", "page": "dashboard"},
        {"label": "Preparação", "icon": None, "page": None, "group": [
            {"label": "Programas", "icon": "▣", "page": "programas"},
            {"label": "Office", "icon": "❒", "page": "office"},
            {"label": "Windows", "icon": "▤", "page": "windows"},
            {"label": "Drivers", "icon": "▦", "page": "drivers"},
        ]},
        {"label": "Diagnóstico", "icon": None, "page": None, "group": [
            {"label": "Stress Test", "icon": "◉", "page": "diagnostico"},
        ]},
        {"label": "Otimização", "icon": None, "page": None, "group": [
            {"label": "Escritório", "icon": "▣", "page": "otimizacao_escritorio"},
            {"label": "Gaming", "icon": "▲", "page": "otimizacao_gaming"},
        ]},
        {"label": "Sistema", "icon": None, "page": None, "group": [
            {"label": "Energia", "icon": "◐", "page": "energia"},
            {"label": "Defender", "icon": "⛨", "page": "defender"},
            {"label": "Restauração", "icon": "↻", "page": "restauracao"},
            {"label": "Logs", "icon": "≡", "page": "logs"},
        ]},
    ]

    def __init__(self, master, on_navigate=None, **kw):
        super().__init__(master, fg_color=Theme.SURFACE, corner_radius=0, width=Theme.SIDEBAR_W, **kw)
        self.on_navigate = on_navigate
        self._buttons = {}
        self._active = None

        # Logo
        logo = ctk.CTkFrame(self, fg_color="transparent", height=64)
        logo.pack(fill="x", padx=24, pady=(28, 0))
        logo.pack_propagate(False)
        ctk.CTkLabel(logo, text="N", font=Theme.display_font(34), text_color=Theme.NV_BLUE, anchor="w").pack(side="left")
        ctk.CTkLabel(logo, text="V", font=Theme.display_font(34), text_color=Theme.NV_YELLOW, anchor="w").pack(side="left")
        ctk.CTkLabel(logo, text="  OPTIMIZER", font=Theme.font(14, weight="bold"), text_color=Theme.TEXT_SOFT, anchor="w").pack(side="left")
        ctk.CTkLabel(logo, text="v2.0", font=Theme.font(10, weight="bold", mono=True), text_color=Theme.MUTED, anchor="w").pack(side="left", padx=(6, 0))

        sep = ctk.CTkFrame(self, fg_color=Theme.HAIRLINE, height=1, corner_radius=0)
        sep.pack(fill="x", padx=24, pady=(18, 0))

        # Itens
        wrap = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_fg_color="transparent")
        wrap.pack(fill="both", expand=True, pady=(12, 0), padx=0)

        for item in self.NAV:
            if item.get("group"):
                ctk.CTkLabel(wrap, text=item["label"].upper(), font=Theme.font(11, weight="bold"),
                             text_color=Theme.MUTED, anchor="w").pack(fill="x", padx=28, pady=(16, 6))
                for sub in item["group"]:
                    self._add_item(wrap, sub["label"], sub["page"], icon=sub["icon"], indent=True)
            else:
                self._add_item(wrap, item["label"], item["page"], icon=item["icon"], top=True)

        # NV branding footer
        ctk.CTkLabel(self, text="NV SOFTWARE", font=Theme.font(9, weight="bold", mono=True),
                     text_color=Theme.DISABLED_TEXT).pack(pady=(0, 10))

    def _add_item(self, parent, label, page, icon=None, indent=False, top=False):
        text = f"  {icon}  {label}" if icon else f"      {label}"
        btn = ctk.CTkButton(
            parent,
            text=text,
            anchor="w",
            height=36,
            corner_radius=Theme.R_SM,
            fg_color="transparent",
            hover_color=Theme.SURFACE_ELEV2,
            text_color=Theme.TEXT_SOFT if not top else Theme.TEXT,
            font=Theme.font(13, weight="bold") if top else Theme.font(13),
            command=lambda p=page, l=label: self._navigate(p, l),
        )
        btn.pack(fill="x", padx=24 if not indent else 44, pady=2)
        self._buttons[page] = (btn, label, top)

    def _navigate(self, page, label):
        if self.on_navigate:
            self.on_navigate(page)

    def set_active(self, page: str):
        # desativa anterior
        if self._active and self._active in self._buttons:
            prev = self._buttons[self._active][0]
            prev.configure(fg_color="transparent", text_color=Theme.TEXT_SOFT)
            # remove indicador amarelo se existir
            prev.configure(border_width=0)
        if page in self._buttons:
            btn, label, top = self._buttons[page]
            btn.configure(fg_color=Theme.SURFACE_ELEV2, text_color=Theme.NV_YELLOW if top else Theme.NV_YELLOW_DIM)
            btn.configure(border_width=0)
            self._active = page
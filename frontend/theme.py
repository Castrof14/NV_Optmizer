"""
NV Optimizer 2.0 — Design Tokens.

Paleta baseada nos princípios de DESIGN-coinbase.md (canvas escuro, azul escasso,
geometria pill/card, tipografia display 400, mono para números) com identidade
NV preservada: logo N azul + V amarelo.
"""

import platform

import customtkinter as ctk


class Theme:
    # --- Marca NV (identidade inegociável) ---
    NV_BLUE = "#0011FF"
    NV_BLUE_HOVER = "#0a1ce0"
    NV_BLUE_PRESS = "#000B8F"
    NV_YELLOW = "#FFEE00"
    NV_YELLOW_DIM = "#C9BB00"

    # --- Canvas escuro (assinatura Coinbase dark hero) ---
    INK = "#0a0b0d"
    SURFACE = "#0a0b0d"            # página
    SURFACE_ELEV = "#16181c"       # cards
    SURFACE_ELEV2 = "#1d2128"      # cards hover / headers internos
    SURFACE_STRONG = "#23272e"     # campos / placas de ícones
    HAIRLINE = "#2a2e35"           # bordas em fundo escuro
    HAIRLINE_SOFT = "#1b1e24"

    # --- Texto ---
    TEXT = "#ffffff"
    TEXT_SOFT = "#b3b9c2"
    BODY = "#8b929c"
    MUTED = "#5c626b"
    DISABLED_TEXT = "#3a3f46"

    # --- Semântica (texto, nunca fundo) ---
    SUCCESS = "#05b169"
    DANGER = "#cf202f"
    WARNING = "#f4b000"
    INFO = "#4d8dff"

    # --- Radii (design system) ---
    R_PILL = 100
    R_XL = 24
    R_LG = 16
    R_MD = 12
    R_SM = 8
    R_FULL = 9999

    # --- Dimensões ---
    SIDEBAR_W = 264
    HEADER_H = 76
    FOOTER_H = 34
    CONTENT_PAD = 32
    CARD_PAD = 24

    # --- Fontes locais seguras (substitutos documentados de Coinbase Sans/Mono) ---
    _FONT_FAMILY = "Segoe UI"
    _MONO_FAMILY = "Consolas"
    _CACHE = {}

    @classmethod
    def _setup_families(cls):
        if platform.system() == "Darwin":
            cls._FONT_FAMILY = "Helvetica Neue"
            cls._MONO_FAMILY = "Menlo"
        elif platform.system() == "Linux":
            cls._FONT_FAMILY = "Noto Sans"
            cls._MONO_FAMILY = "DejaVu Sans Mono"

    @classmethod
    def font(cls, size=14, weight="normal", mono=False):
        if not cls._CACHE:
            cls._setup_families()
        key = (size, weight, mono)
        if key not in cls._CACHE:
            family = cls._MONO_FAMILY if mono else cls._FONT_FAMILY
            cls._CACHE[key] = ctk.CTkFont(family=family, size=size, weight=weight)
        return cls._CACHE[key]

    @classmethod
    def display_font(cls, size):
        """Display usa peso 400 (calma editorial, nunca 700)."""
        return cls.font(size=size, weight="normal")

    @classmethod
    def num_font(cls, size=18):
        return cls.font(size=size, weight="normal", mono=True)

    @staticmethod
    def _toast_color(kind: str) -> str:
        return {
            "success": Theme.SUCCESS,
            "error": Theme.DANGER,
            "warning": Theme.WARNING,
            "info": Theme.INFO,
        }.get(kind, Theme.INFO)


# Atalhos de uso comum
C = Theme
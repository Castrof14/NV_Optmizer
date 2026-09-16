"""Logs — histórico de operações da sessão."""

import customtkinter as ctk

import frontend.logs as flogs
from frontend.pages import PageBase
from frontend.theme import Theme
from frontend.components import Card, Button, Badge

RESULT_TONE = {"OK": "green", "FALHA": "red", "INFO": "blue"}


class LogsPage(PageBase):
    page_id = "logs"
    title = "Logs"
    subtitle = "Histórico de operações realizadas nesta sessão."
    badge_text = None

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 16))
        self._count_label = ctk.CTkLabel(header, text="", font=Theme.font(13),
                                         text_color=Theme.BODY, anchor="w")
        self._count_label.pack(side="left")
        Button(header, text="Limpar", variant="ghost", command=self._clear).pack(side="right")

        box = Card(self, title="Operações")
        box.pack(fill="x")
        self._list = ctk.CTkScrollableFrame(box.body, fg_color="transparent",
                                            scrollbar_fg_color="transparent")
        self._list.pack(fill="both", expand=True)
        self._render()

    def on_show(self):
        self._render()

    def _render(self):
        if not hasattr(self, "_list") or not self._list.winfo_exists():
            return
        for w in self._list.winfo_children():
            w.destroy()
        entries = flogs.store.snapshot()
        self._count_label.configure(text=f"{len(entries)} operação(ões) registrada(s).")
        if not entries:
            placeholder = ctk.CTkLabel(self._list, text="Nenhuma operação registrada ainda.",
                                       font=Theme.font(14), text_color=Theme.MUTED)
            placeholder.pack(anchor="w", pady=(10, 0))
            return
        for e in reversed(entries):
            row = ctk.CTkFrame(self._list, fg_color="transparent")
            row.pack(fill="x", pady=3)
            row.grid_columnconfigure(1, weight=1)

            Badge(row, text=e.result, tone=RESULT_TONE.get(e.result, "neutral"),
                  size=10).grid(row=0, column=0, sticky="w", padx=(0, 10))
            ctk.CTkLabel(row, text=f"{e.hour}  {e.operation}",
                         font=Theme.font(13, weight="bold"), text_color=Theme.TEXT,
                         anchor="w").grid(row=0, column=1, sticky="w")
            sub = f"{e.service}"
            if e.before != "—" or e.after != "—":
                sub += f"   {e.before} → {e.after}"
            ctk.CTkLabel(row, text=sub, font=Theme.font(12), text_color=Theme.BODY,
                         anchor="w").grid(row=1, column=1, sticky="w")
            if e.detail:
                ctk.CTkLabel(row, text=e.detail, font=Theme.font(12), text_color=Theme.MUTED,
                             anchor="w", wraplength=560, justify="left").grid(row=2, column=1, sticky="w")

    def _clear(self):
        flogs.store.clear()
        self._render()
        self._toast("info", "Logs limpos.")
        self._log(operation="Logs", service="Limpar", result="OK")
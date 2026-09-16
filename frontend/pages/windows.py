"""Windows (Preparação) — limpeza, disco, rede e reparo (ações reais)."""

import customtkinter as ctk

import frontend.modules_bridge as backend
from frontend.pages import PageBase
from frontend.theme import Theme
from frontend.components import Card, Button, Badge, PulseBar


class WindowsPage(PageBase):
    page_id = "windows"
    title = "Windows"
    subtitle = "Preparação do sistema: limpeza, disco, rede e reparo."
    badge_text = None

    def _build(self):
        self._running = False
        self._load()

    def _load(self):
        for w in self.winfo_children():
            w.destroy()

        groups = [
            ("limpeza", "Limpeza", "🧹"),
            ("disco", "Disco", "💽"),
            ("rede", "Rede", "🌐"),
            ("reparo", "Reparo", "🔧"),
        ]
        for key, label, icon in groups:
            group = Card(self, title=f"{icon}  {label}")
            group.pack(fill="x", pady=(0, 18))
            body = group.body
            i = 0
            for name, desc, fn in backend.WINDOWS_ACTIONS[key]:
                btn = ctk.CTkButton(
                    body,
                    text=name,
                    height=44,
                    corner_radius=Theme.R_MD,
                    fg_color=Theme.SURFACE_STRONG,
                    hover_color=Theme.SURFACE_ELEV2,
                    text_color=Theme.TEXT_SOFT,
                    font=Theme.font(13),
                    command=lambda k=key, n=name, f=fn: self._run(k, n, f),
                )
                btn.grid(row=i, column=0, sticky="ew", padx=(0, 8), pady=4)
                i += 1
            for c in range(1):
                body.grid_columnconfigure(c, weight=1)

        # Console
        console = Card(self, title="Console de execução", subtitle="Saída real das operações")
        console.pack(fill="x")
        self._status = ctk.CTkLabel(console.body, text="Pronto.", font=Theme.font(13, weight="bold"),
                                    text_color=Theme.BODY, anchor="w")
        self._status.pack(anchor="w")
        self._bar = PulseBar(console.body, height=8, color=Theme.NV_BLUE)
        self._bar.pack_forget()
        self._box = ctk.CTkTextbox(console.body, fg_color=Theme.SURFACE, text_color=Theme.BODY,
                                   font=Theme.font(12, mono=True), corner_radius=Theme.R_MD,
                                   border_width=1, border_color=Theme.HAIRLINE, height=190, wrap="word")
        self._box.pack(fill="x", pady=(12, 0))

    def _run(self, group, name, fn):
        if self._running:
            self._toast("warning", "Aguarde a operação em andamento.")
            return
        self._running = True
        self._status.configure(text=f"Executando: {name}...", text_color=Theme.NV_YELLOW)
        self._bar.pack(fill="x", pady=(12, 0))
        self._bar.start()
        self._append(f"» {name}")
        self._log(operation=name, result="pendente")

        def wrap():
            fn()
        self._action(f"Windows · {name}",
                     fn=wrap,
                     on_log=self._append,
                     on_done=lambda _: self._finish(name, True, None),
                     on_error=lambda e: self._finish(name, False, str(e)))

    def _append(self, line):
        self._box.configure(state="normal")
        self._box.insert("end", f"  {line}\n")
        self._box.see("end")
        self._box.configure(state="disabled")

    def _finish(self, name, ok, err):
        self._running = False
        self._bar.stop()
        self._bar.pack_forget()
        if ok:
            self._status.configure(text=f"Concluído: {name}", text_color=Theme.SUCCESS)
            self._toast("success", f"{name} concluído.")
            self._log(operation=name, result="OK")
        else:
            self._status.configure(text=f"Falha: {name}", text_color=Theme.DANGER)
            self._toast("error", f"Não foi possível concluir '{name}'. {err}")
            self._log(operation=name, result="FALHA", detail=err)
            self._append(f"! {err}")
"""Serviços — desativação por níveis (Básico, Alto e Gamer) com restauração."""

import customtkinter as ctk

import frontend.api as api
import frontend.modules_bridge as backend
from frontend.pages import PageBase
from frontend.theme import Theme
from frontend.components import Card, Button, Badge, PulseBar, LoadingState, ErrorState


class ServicesPage(PageBase):
    page_id = "servicos"
    title = "Serviços"
    subtitle = "Desative serviços por nível. Cada nível inclui os anteriores."
    badge_text = None

    def _build(self):
        self._running = False
        self._state = {}
        self._count_labels = {}
        self._load()

    def _load(self):
        for w in self.winfo_children():
            w.destroy()
        LoadingState(self, message="Lendo serviços do Windows...").pack(fill="both", expand=True)
        self._action("Ler serviços", fn=api.services_state,
                     on_done=self._render, on_error=lambda e: self._fail(str(e)))

    def _fail(self, msg):
        for w in self.winfo_children():
            w.destroy()
        ErrorState(self, message=str(msg), on_retry=self._load).pack(fill="both", expand=True)

    def _render(self, state):
        self._state = state
        for w in self.winfo_children():
            w.destroy()

        for tier, meta in state.items():
            card = Card(self, title=meta["label"], badge=meta["badge"])
            card.pack(fill="x", pady=(0, 18))
            ctk.CTkLabel(card.body, text=meta["description"], font=Theme.font(14),
                         text_color=Theme.BODY, anchor="w", justify="left",
                         wraplength=640).pack(anchor="w")
            count = ctk.CTkLabel(card.body, text=self._count_text(meta), font=Theme.font(12, mono=True),
                                 text_color=Theme.MUTED, anchor="w")
            count.pack(anchor="w", pady=(8, 0))
            self._count_labels[tier] = count

            buttons = ctk.CTkFrame(card.body, fg_color="transparent")
            buttons.pack(anchor="w", pady=(14, 0))
            Button(buttons, text="DESATIVAR", variant="primary",
                   command=lambda t=tier: self._confirm_disable(t)).pack(side="left", padx=(0, 8))
            Button(buttons, text="Ver lista", variant="ghost",
                   command=lambda t=tier: self._show_list(t)).pack(side="left")

        safe = Card(self, title="Sempre preservados")
        safe.pack(fill="x", pady=(0, 18))
        badges = ctk.CTkFrame(safe.body, fg_color="transparent")
        badges.pack(anchor="w")
        for label in ("Windows Defender", "Firewall", "Windows Update", "Rede e Wi-Fi",
                      "Áudio e Bluetooth", "Xbox"):
            Badge(badges, text=label, tone="green", size=11).pack(side="left", padx=(0, 6))

        console = Card(self, title="Execução")
        console.pack(fill="x")
        self._status = ctk.CTkLabel(console.body, text="Pronto.", font=Theme.font(13, weight="bold"),
                                    text_color=Theme.BODY, anchor="w")
        self._status.pack(anchor="w")
        self._bar = PulseBar(console.body, height=8, color=Theme.NV_YELLOW)
        self._bar.pack_forget()
        self._box = ctk.CTkTextbox(console.body, fg_color=Theme.SURFACE, text_color=Theme.BODY,
                                   font=Theme.font(12, mono=True), corner_radius=Theme.R_MD,
                                   border_width=1, border_color=Theme.HAIRLINE, height=180, wrap="word")
        self._box.pack(fill="x", pady=(12, 0))
        self._box.configure(state="disabled")
        Button(console.body, text="RESTAURAR SERVIÇOS", variant="secondary", icon="↺",
               command=self._confirm_restore).pack(anchor="w", pady=(14, 0))

    @staticmethod
    def _count_text(meta):
        return f"{meta['total']} serviços neste computador · {meta['disabled']} já desativados"

    def _show_list(self, tier):
        meta = self._state[tier]

        def build(body):
            for service in meta["services"]:
                row = ctk.CTkFrame(body, fg_color="transparent")
                row.pack(fill="x", pady=4)
                ctk.CTkLabel(row, text=service["display"], font=Theme.font(13, weight="bold"),
                             text_color=Theme.TEXT, anchor="w").pack(anchor="w")
                state = service["start_type"] or "Não existe neste Windows"
                ctk.CTkLabel(row, text=f"{service['description']} · {state}", font=Theme.font(12),
                             text_color=Theme.MUTED, anchor="w", justify="left",
                             wraplength=600).pack(anchor="w")

        self.app.modal.show(title=meta["label"].upper(), body_builder=build,
                            primary={"label": "Fechar", "variant": "secondary"},
                            secondary=None, wide=True)

    def _confirm_disable(self, tier):
        if self._running:
            self._toast("warning", "Aguarde a operação em andamento.")
            return
        meta = self._state[tier]
        self.app.confirm(
            f"DESATIVAR {meta['label'].upper()}?",
            "Um ponto de restauração será criado e o estado atual de cada serviço será guardado.",
            detail=meta["warning"],
            danger=True,
            confirm_label="Desativar",
            on_confirm=lambda: self._disable(tier),
        )

    def _disable(self, tier):
        label = self._state[tier]["label"]

        def run():
            backend.create_restore_point()
            return backend.disable_service_tier(tier)

        self._start(f"Desativar {label}", run)

    def _confirm_restore(self):
        if self._running:
            self._toast("warning", "Aguarde a operação em andamento.")
            return
        self.app.confirm(
            "RESTAURAR SERVIÇOS?",
            "Os serviços voltam ao tipo de inicialização que tinham antes de serem desativados.",
            confirm_label="Restaurar",
            on_confirm=self._restore,
        )

    def _restore(self):
        self._start("Restaurar serviços", backend.restore_services)

    def _start(self, name, fn):
        self._running = True
        self._status.configure(text=f"Executando: {name}...", text_color=Theme.NV_YELLOW)
        self._bar.pack(fill="x", pady=(12, 0))
        self._bar.start()
        self.app.set_busy(True, name)
        self._append(f"» {name}")
        self._action(name, fn=fn, on_log=self._append,
                     on_done=lambda rows: self._finish(name, rows),
                     on_error=lambda e: self._finish_error(name, str(e)))

    def _append(self, line):
        self._box.configure(state="normal")
        self._box.insert("end", f"  {line}\n")
        self._box.see("end")
        self._box.configure(state="disabled")

    def _end_running(self):
        self._running = False
        self._bar.stop()
        self._bar.pack_forget()
        self.app.set_busy(False)

    def _finish(self, name, rows):
        self._end_running()
        failed = [r for r in rows if r["result"] == "FALHA"]
        for row in rows:
            if row["result"] != "IGNORADO":
                self._log(operation=row["operation"], service=row["service"], before=row["before"],
                          after=row["after"], result=row["result"], detail=row["detail"])
        if failed:
            self._status.configure(text=f"{name}: concluído com {len(failed)} falhas.", text_color=Theme.WARNING)
            self._toast("warning", f"{name}: {len(failed)} serviços não foram alterados.")
        else:
            self._status.configure(text=f"{name}: concluído. Reinicie o computador.", text_color=Theme.SUCCESS)
            self._toast("success", f"{name}: concluído.")
        self._action("Ler serviços", fn=api.services_state, on_done=self._refresh_counts)

    def _finish_error(self, name, message):
        self._end_running()
        self._status.configure(text=f"Falha: {name}", text_color=Theme.DANGER)
        self._append(f"! {message}")
        self._toast("error", message)
        self._log(operation=name, result="FALHA", detail=message)

    def _refresh_counts(self, state):
        self._state = state
        for tier, meta in state.items():
            self._count_labels[tier].configure(text=self._count_text(meta))

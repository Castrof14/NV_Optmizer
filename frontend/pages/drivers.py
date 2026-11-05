"""Drivers — placa de vídeo e atualização real pelo Windows Update."""

import customtkinter as ctk

import frontend.api as api
import frontend.modules_bridge as backend
from frontend.pages import PageBase
from frontend.theme import Theme
from frontend.components import (Card, Button, Badge, PulseBar, LoadingState, ErrorState)


class DriversPage(PageBase):
    page_id = "drivers"
    title = "Drivers"
    subtitle = "Placa de vídeo e atualização de drivers pelo Windows Update."
    badge_text = None

    def _build(self):
        self._running = False
        self._load()

    def _load(self):
        for w in self.winfo_children():
            w.destroy()
        LoadingState(self, message="Lendo placa de vídeo e drivers...").pack(fill="both", expand=True)
        self._action("Lendo drivers", fn=api.drivers_state,
                     on_done=self._render, on_error=lambda e: self._fail(str(e)))

    def _fail(self, msg):
        for w in self.winfo_children():
            w.destroy()
        ErrorState(self, message=f"{msg}", on_retry=self._load).pack(fill="both", expand=True)

    def _render(self, data):
        for w in self.winfo_children():
            w.destroy()

        card = Card(self, title="PLACA DE VÍDEO")
        card.pack(fill="x", pady=(0, 20))

        name = data.get("name") or "Não disponível"
        ctk.CTkLabel(card.body, text=name, font=Theme.display_font(26),
                     text_color=Theme.TEXT, anchor="w").pack(anchor="w")

        rows = ctk.CTkFrame(card.body, fg_color="transparent")
        rows.pack(fill="x", pady=(18, 0))
        ctk.CTkLabel(rows, text="DRIVER", font=Theme.font(11, weight="bold"),
                     text_color=Theme.MUTED).pack(anchor="w")
        ctk.CTkLabel(rows, text=data.get("driver", "—") if data.get("available") else "Não disponível",
                     font=Theme.num_font(17), text_color=Theme.TEXT_SOFT).pack(anchor="w", pady=(4, 0))
        if data.get("available") and data.get("date"):
            ctk.CTkLabel(rows, text=f"Data: {data['date']}", font=Theme.font(12),
                         text_color=Theme.BODY).pack(anchor="w", pady=(2, 0))

        update = Card(self, title="ATUALIZAR DRIVERS", subtitle="Fonte oficial: Windows Update")
        update.pack(fill="x", pady=(0, 20))

        options = ctk.CTkFrame(update.body, fg_color="transparent")
        options.pack(fill="x", pady=(10, 0))
        options.grid_columnconfigure((0, 1), weight=1, uniform="scope")
        self._scope_option(options, 0, "Drivers Básicos",
                           "Vídeo, rede, áudio, chipset, armazenamento, USB e Bluetooth.",
                           "primary", lambda: self._confirm_update(True))
        self._scope_option(options, 1, "Todos os Drivers",
                           "Tudo que o Windows Update oferecer, incluindo periféricos. BIOS/firmware fica de fora.",
                           "secondary", lambda: self._confirm_update(False))

        secondary = ctk.CTkFrame(update.body, fg_color="transparent")
        secondary.pack(anchor="w", pady=(14, 0))
        Button(secondary, text="Verificar disponíveis", variant="secondary",
               command=self._check).pack(side="left", padx=(0, 8))
        Button(secondary, text="Reler placa de vídeo", variant="ghost",
               command=self._reload).pack(side="left")

        self._status = ctk.CTkLabel(update.body, text="", font=Theme.font(13),
                                    text_color=Theme.SUCCESS, anchor="w", justify="left", wraplength=640)
        self._status.pack(anchor="w", pady=(16, 0))
        self._bar = PulseBar(update.body, height=8, color=Theme.NV_BLUE)
        self._bar.pack_forget()

        self._box = ctk.CTkTextbox(self, fg_color=Theme.SURFACE_ELEV, text_color=Theme.BODY,
                                   font=Theme.font(12, mono=True), corner_radius=Theme.R_LG,
                                   border_width=1, border_color=Theme.HAIRLINE, height=200, wrap="word")
        self._box.pack(fill="x")
        self._box.configure(state="disabled")

    @staticmethod
    def _scope_option(parent, column, title, description, variant, command):
        box = ctk.CTkFrame(parent, fg_color=Theme.SURFACE, corner_radius=Theme.R_LG)
        box.grid(row=0, column=column, sticky="nsew", padx=(0, 10) if column == 0 else (0, 0))
        ctk.CTkLabel(box, text=title, font=Theme.font(15, weight="bold"), text_color=Theme.TEXT,
                     anchor="w").pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkLabel(box, text=description, font=Theme.font(12), text_color=Theme.BODY, anchor="w",
                     justify="left", wraplength=280).pack(anchor="w", padx=16)
        Button(box, text="ATUALIZAR", variant=variant, command=command).pack(anchor="w", padx=16, pady=14)

    def _append(self, msg):
        self._box.configure(state="normal")
        self._box.insert("end", f"  {msg}\n")
        self._box.see("end")
        self._box.configure(state="disabled")

    def _reload(self):
        if self._running:
            self._toast("warning", "Aguarde a operação em andamento.")
            return
        self._load()

    def _confirm_update(self, only_basic):
        if self._running:
            self._toast("warning", "Aguarde a operação em andamento.")
            return
        scope = "os drivers básicos" if only_basic else "todos os drivers"
        self.app.confirm(
            f"ATUALIZAR {scope.upper()}?",
            f"O NV vai baixar e instalar {scope} disponíveis no Windows Update.",
            detail=("Um ponto de restauração será criado antes. A tela pode piscar durante "
                    "a instalação de drivers de vídeo, e o computador pode precisar reiniciar."),
            confirm_label="Atualizar",
            on_confirm=lambda: self._update(only_basic),
        )

    def _start(self, status, fn, on_done):
        self._running = True
        self._bar.pack(fill="x", pady=(12, 0))
        self._bar.start()
        self._status.configure(text=status, text_color=Theme.NV_YELLOW)
        self.app.set_busy(True, status)
        self._action(status, fn=fn, on_log=self._append, on_done=on_done,
                     on_error=lambda e: self._finish_error(str(e)))

    def _end_running(self):
        self._running = False
        self._bar.stop()
        self._bar.pack_forget()
        self.app.set_busy(False)

    def _check(self):
        if self._running:
            self._toast("warning", "Aguarde a operação em andamento.")
            return
        self._start("Procurando drivers disponíveis...", backend.check_driver_updates, self._check_done)

    def _check_done(self, result):
        self._end_running()
        total = len(result["items"])
        basic_classes = {c.lower() for c in backend.BASIC_DRIVER_CLASSES}
        basic = sum(1 for item in result["items"] if item["class"].lower() in basic_classes)
        self._status.configure(
            text=f"{total} drivers disponíveis, sendo {basic} básicos." if total
                 else "Nenhuma atualização de driver disponível.",
            text_color=Theme.SUCCESS,
        )

    def _update(self, only_basic):
        def run():
            backend.create_restore_point()
            return backend.update_drivers(only_basic)

        scope = "básicos" if only_basic else "todos"
        self._operation = f"Atualizar drivers ({scope})"
        self._start("Atualizando drivers. Pode levar vários minutos...", run, self._update_done)

    def _update_done(self, result):
        self._end_running()
        items = result["items"]
        installed = result["installed"]
        failed = result["failed"]
        reboot = " Reinicie o computador para concluir." if result["reboot"] else ""

        for item in items:
            self._log(operation=self._operation, service=item["title"],
                      result="OK" if item["status"] == "installed" else "FALHA", detail=item["detail"])

        if not items:
            self._status.configure(text="Nenhuma atualização de driver disponível.", text_color=Theme.SUCCESS)
            self._toast("success", "Os drivers já estão em dia no Windows Update.")
        elif failed:
            self._status.configure(text=f"{installed} instalados e {failed} com falha.{reboot}",
                                   text_color=Theme.WARNING)
            self._toast("warning", f"{failed} drivers não foram instalados. Veja os detalhes no console.")
        else:
            self._status.configure(text=f"{installed} drivers instalados.{reboot}", text_color=Theme.SUCCESS)
            self._toast("success", f"{installed} drivers instalados.")

    def _finish_error(self, message):
        self._end_running()
        self._status.configure(text="Não foi possível concluir a operação.", text_color=Theme.DANGER)
        self._append(f"! {message}")
        self._toast("error", message)
        self._log(operation="Drivers", result="FALHA", detail=message)

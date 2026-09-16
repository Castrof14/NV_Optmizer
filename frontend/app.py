"""Shell principal do NV Optimizer 2.0."""

import customtkinter as ctk

from frontend.theme import Theme
from frontend.components import (
    Sidebar, Header, Modal, ConfirmDialog, ToastManager, PulseBar,
)
from utils.config import system_info

from frontend.pages.dashboard import DashboardPage
from frontend.pages.programs import ProgramsPage
from frontend.pages.office import OfficePage
from frontend.pages.drivers import DriversPage
from frontend.pages.windows import WindowsPage
from frontend.pages.diagnosis import DiagnosisPage
from frontend.pages.optimization import OptimizationPage
from frontend.pages.energy import EnergyPage
from frontend.pages.defender import DefenderPage
from frontend.pages.restore import RestorePage
from frontend.pages.logs import LogsPage

# Rotas → (classe, kwargs) e metadados padrão de cabeçalho.
ROUTE_META = {
    "dashboard": (DashboardPage, {}, "Dashboard", "Visão geral do seu computador com dados reais."),
    "programas": (ProgramsPage, {}, "Programas", "Catálogo de programas essenciais e instalados."),
    "office": (OfficePage, {}, "Office", "Instalação e status do Microsoft Office."),
    "windows": (WindowsPage, {}, "Windows", "Limpeza, disco, rede e reparos do sistema."),
    "drivers": (DriversPage, {}, "Drivers", "Placa de vídeo e versão do driver."),
    "diagnostico": (DiagnosisPage, {}, "Diagnóstico", "Stress test com monitoramento em tempo real."),
    "otimizacao_escritorio": (OptimizationPage, {"profile": "escritorio"},
                              "Otimização · Escritório", "Perfil leve para trabalho e uso diário."),
    "otimizacao_gaming": (OptimizationPage, {"profile": "gaming"},
                          "Otimização · Gaming", "Perfil de desempenho máximo para jogos."),
    "energia": (EnergyPage, {}, "Energia", "Plano de energia, tela e suspensão."),
    "defender": (DefenderPage, {}, "Windows Defender", "Proteção em tempo real e assinaturas."),
    "restauracao": (RestorePage, {}, "Restauração", "Ponto de restauração e reversão."),
    "logs": (LogsPage, {}, "Logs", "Histórico de operações da sessão."),
}


class NVOptimizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("NV Optimizer 2.0")
        self.configure(fg_color=Theme.SURFACE)
        self.geometry("1180x780")
        self.minsize(1024, 680)

        self.current_profile = None
        self._pages = {}
        self._current_page = None

        # Serviços globais de UI
        self.toasts = ToastManager(self)
        self.modal = Modal(self)
        self._confirm_dlg = ConfirmDialog(self)

        # Layout base
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = Sidebar(self, on_navigate=self.navigate)
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        right = ctk.CTkFrame(self, fg_color=Theme.SURFACE, corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(2, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self.header = Header(right)
        self.header.grid(row=0, column=0, sticky="ew")

        # Barra de operação em andamento
        self._busy = ctk.CTkFrame(right, fg_color=Theme.SURFACE_ELEV, height=34, corner_radius=0)
        self._busy.grid(row=1, column=0, sticky="ew")
        self._busy.grid_columnconfigure(1, weight=1)
        self._busy_label = ctk.CTkLabel(self._busy, text="Trabalhando...", font=Theme.font(12),
                                        text_color=Theme.TEXT_SOFT, anchor="w")
        self._busy_label.grid(row=0, column=0, sticky="w", padx=(Theme.CONTENT_PAD, 8))
        self._busy_bar = PulseBar(self._busy, height=4, color=Theme.NV_BLUE)
        self._busy_bar.grid(row=0, column=2, sticky="ew", padx=(8, Theme.CONTENT_PAD))
        self._busy.grid_remove()

        self.container = ctk.CTkFrame(right, fg_color=Theme.SURFACE, corner_radius=0)
        self.container.grid(row=2, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.navigate("dashboard")
        self._system_chip()
        self._pump()

    # ---------- Navegação ----------
    def navigate(self, route):
        if route not in ROUTE_META:
            route = "dashboard"
        page = self._pages.get(route)
        if page is None:
            cls, kw, _, _ = ROUTE_META[route]
            page = cls(self, self.container, **kw)
            self._pages[route] = page
            page.grid(row=0, column=0, sticky="nsew")

        if self._current_page is not None and self._current_page is not page:
            try:
                self._current_page.on_hide()
            except Exception:
                pass
            self._current_page.grid_forget()

        self._current_page = page
        page.grid(row=0, column=0, sticky="nsew")
        page.lift()
        try:
            page.on_show()
        except Exception:
            pass

        _, _, title, subtitle = ROUTE_META[route]
        self.header.set_page(
            getattr(page, "title", title),
            getattr(page, "subtitle", subtitle),
            getattr(page, "badge_text", None),
        )
        self.sidebar.set_active(route)

    # ---------- Confirmação / ocupado ----------
    def confirm(self, title, message="", **kw):
        return self._confirm_dlg.confirm(title=title, message=message or "Confirmar operação?", **kw)

    @property
    def confirm_dialog(self):
        return self._confirm_dlg

    def set_busy(self, busy: bool, msg: str = ""):
        if busy:
            if msg:
                self._busy_label.configure(text=msg)
            self._busy.grid()
            self._busy_bar.start()
        else:
            self._busy_bar.stop()
            self._busy.grid_remove()

    # ---------- Extras ----------
    def _system_chip(self):
        arch = system_info.architecture
        text = system_info.so_name + (f" · {arch}" if arch else "")
        self.header.set_system(text)

    def _pump(self):
        try:
            from frontend.jobs import drain_all
            drain_all()
        except Exception:
            pass
        try:
            if self.winfo_exists():
                self.after(90, self._pump)
        except Exception:
            pass

    def _on_close(self):
        try:
            import frontend.modules_bridge as backend
            backend.stop_stress()
        except Exception:
            pass
        self.destroy()


def main():
    app = NVOptimizerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
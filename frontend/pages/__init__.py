"""Páginas do NV Optimizer 2.0."""

import customtkinter as ctk

from frontend.theme import Theme


class PageBase(ctk.CTkScrollableFrame):
    """Base de todas as páginas — dá acesso ao app e conveniently build."""

    page_id: str = ""
    title = ""
    subtitle = ""
    badge_text = None

    def __init__(self, app, container, **kw):
        self.app = app
        super().__init__(
            container,
            fg_color=Theme.SURFACE,
            corner_radius=0,
            scrollbar_button_color=Theme.HAIRLINE,
            scrollbar_button_hover_color=Theme.MUTED,
            **kw,
        )
        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        """Preenche o conteúdo da página (override em subclasses)."""
        pass

    def on_show(self):
        """Chamado quando a página fica visível."""
        pass

    def on_hide(self):
        """Chamado quando a página deixa de estar visível."""
        pass

    def _action(self, label, fn, on_start=None, on_done=None, on_error=None, on_progress=None, on_log=None):
        """Helper: cria e dispara um Job vinculado à UI da página.

        O Job começa apenas quando o loop de eventos estiver rodando
        (thread de trabalho nunca toca no Tk — entrega via fila/pump).
        """
        from frontend.jobs import Job
        import logging
        job = Job(
            label=label,
            fn=fn,
            on_start=on_start,
            on_done=on_done,
            on_error=on_error,
            on_progress=on_progress,
            on_log=on_log,
        )

        def _go():
            try:
                job.start()
            except Exception:
                pass
        try:
            self.after(0, _go)
        except Exception:
            _go()
        return job

    def _toast(self, kind, message):
        self.app.toasts.show(kind, message)

    def _log(self, **kw):
        from frontend.logs import store
        store.add(**kw)


# Mapeamento de rotas → classes de página (import lazy)
ROUTES = {}


def register(route: str, cls):
    ROUTES[cls.page_id] = (route, cls)
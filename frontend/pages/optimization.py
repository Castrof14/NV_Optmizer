"""Otimização — perfis Escritório / Gaming com análise e aplicação reais."""

import customtkinter as ctk

import frontend.api as api
import frontend.modules_bridge as backend
from frontend.pages import PageBase
from frontend.theme import Theme
from frontend.components import (Card, Button, Badge, Bar, PulseBar, LoadingState, ErrorState)

PROFILES = {
    "escritorio": {
        "title": "PC DE ESCRITÓRIO",
        "desc": "Otimização leve para trabalho, estudos e uso diário.",
        "tag": "Leve",
    },
    "gaming": {
        "title": "GAMING",
        "desc": "Otimização pesada focada em desempenho para jogos.",
        "tag": "Desempenho",
    },
}


class OptimizationPage(PageBase):
    page_id = "otimizacao"
    title = "Otimização"
    subtitle = "Analisamos seu computador e aplicamos as mudanças recomendadas."
    badge_text = None

    def __init__(self, app, container, profile="escritorio", **kw):
        self.profile = profile
        self.meta = PROFILES.get(profile, PROFILES["escritorio"])
        self.analysis = None
        self.applied = False
        super().__init__(app, container, **kw)
        if self.profile == "gaming":
            self.title = "Otimização · Gaming"
            self.subtitle = "Perfil Gaming — desempenho máximo focado em jogos."
        else:
            self.title = "Otimização · Escritório"
            self.subtitle = "Perfil Escritório — leve e equilibrado para o dia a dia."

    def on_show(self):
        pass

    def _build(self):
        self._analyze()

    def _analyze(self):
        for w in self.winfo_children():
            w.destroy()
        loading = LoadingState(self, message="ANALISANDO COMPUTADOR...")
        loading.pack(fill="both", expand=True)
        self._action("Analisando sistema",
                     fn=lambda: api.analyze(self.profile),
                     on_done=self._render,
                     on_error=lambda e: self._fail(str(e)))

    def _fail(self, msg):
        for w in self.winfo_children():
            w.destroy()
        ErrorState(self, message=f"{msg}", on_retry=self._analyze).pack(fill="both", expand=True)

    def _render(self, analysis):
        self.analysis = analysis
        for w in self.winfo_children():
            w.destroy()

        # Hero do perfil
        hero = Card(self, title=self.meta["title"], badge=self.meta["tag"])
        hero.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(hero.body, text=self.meta["desc"], font=Theme.font(14),
                     text_color=Theme.BODY, justify="left", anchor="w", wraplength=560).pack(anchor="w")

        if self.applied or analysis.get("applied"):
            Badge(hero.body, text="OTIMIZAÇÃO APLICADA", tone="green").pack(anchor="w", pady=(12, 0))

        # Checklist de análise
        checks = analysis.get("checks", [])
        check_row = ctk.CTkFrame(hero.body, fg_color="transparent")
        check_row.pack(anchor="w", pady=(16, 0))
        for i, name in enumerate(checks):
            Badge(check_row, text=f"✓ {name}", tone="green").pack(side="left", padx=(0, 6))

        # Preservações
        keeps = analysis.get("keeps", [])
        if keeps:
            kf = ctk.CTkFrame(hero.body, fg_color="transparent")
            kf.pack(fill="x", pady=(10, 0))
            ctk.CTkLabel(kf, text="PRESERVADO:", font=Theme.font(10, weight="bold"),
                         text_color=Theme.MUTED).pack(side="left", padx=(0, 8))
            for k in keeps:
                Badge(kf, text="• " + k, tone="neutral", size=10).pack(side="left", padx=(0, 6), pady=2)

        # Número de alterações
        count = analysis.get("count", 0)
        number = ctk.CTkFrame(hero.body, fg_color="transparent")
        number.pack(fill="x", pady=(18, 0))
        ctk.CTkLabel(number, text=f"{count}", font=Theme.num_font(44),
                     text_color=Theme.NV_YELLOW).pack(side="left")
        ctk.CTkLabel(number, text=f"  alterações recomendadas",
                     font=Theme.font(15), text_color=Theme.TEXT_SOFT, anchor="w").pack(side="left")

        # Ações
        actions = ctk.CTkFrame(hero.body, fg_color="transparent")
        actions.pack(fill="x", pady=(20, 0))
        self.apply_btn = Button(actions, text="APLICAR", variant="primary", icon="⚡",
                                command=self._confirm_apply)
        self.apply_btn.pack(side="left", padx=(0, 8))
        Button(actions, text="VER ALTERAÇÕES", variant="secondary",
               command=self._show_changes).pack(side="left", padx=(0, 8))
        Button(actions, text="Reanalisar", variant="ghost", command=self._analyze).pack(side="left")

        # Progresso
        prog_wrap = ctk.CTkFrame(hero.body, fg_color="transparent")
        prog_wrap.pack(fill="x", pady=(16, 0))
        self._op_status = ctk.CTkLabel(prog_wrap, text="", font=Theme.font(13),
                                       text_color=Theme.SUCCESS, anchor="w")
        self._op_status.pack(anchor="w")
        self._op_bar = PulseBar(prog_wrap, height=8, color=Theme.NV_YELLOW)
        self._op_bar.pack_forget()
        self._op_detail = ctk.CTkLabel(prog_wrap, text="", font=Theme.font(12, mono=True),
                                       text_color=Theme.BODY, anchor="w", justify="left", wraplength=560)
        self._op_detail.pack(anchor="w", pady=(6, 0))

    # ---------- Alterações ----------
    def _show_changes(self):
        if not self.analysis:
            return
        props = self.analysis.get("proposals", [])

        def build(body):
            if not props:
                ctk.CTkLabel(body, text="Nenhuma alteração recomendada.",
                             font=Theme.font(14), text_color=Theme.SUCCESS).pack(anchor="w")
                return
            for p in props:
                row = ctk.CTkFrame(body, fg_color="transparent")
                row.pack(fill="x", pady=4)
                row.grid_columnconfigure(0, weight=1)
                Badge(row, text=p["category"], tone="blue", size=10).grid(row=0, column=0, sticky="w")
                ctk.CTkLabel(row, text=f"{p['service']}", font=Theme.font(13, weight="bold"),
                             text_color=Theme.TEXT, anchor="w").grid(row=1, column=0, sticky="w")
                ctk.CTkLabel(row, text=f"{p['before']}  →  {p['after']}",
                             font=Theme.font(12, mono=True), text_color=Theme.BODY,
                             anchor="w").grid(row=2, column=0, sticky="w")
                if p.get("detail"):
                    ctk.CTkLabel(row, text=p["detail"], font=Theme.font(12),
                                 text_color=Theme.MUTED, anchor="w", justify="left").grid(row=3, column=0, sticky="w")

        self.app.modal.show(
            title="ALTERAÇÕES RECOMENDADAS",
            icon="⚙",
            body_builder=build,
            primary={"label": "Fechar", "variant": "secondary"},
            secondary=None,
            wide=True,
        )

    # ---------- Aplicação ----------
    def _confirm_apply(self):
        if not self.analysis:
            return
        self.app.confirm(
            f"APLICAR OTIMIZAÇÃO {self.meta['title']}?",
            "Esta configuração irá alterar serviços e configurações do Windows.",
            detail="Um ponto de restauração será criado quando possível.",
            danger=True,
            on_confirm=self._apply,
        )

    def _apply(self):
        if self.applied:
            return
        self.applied = True
        self.apply_btn.configure(state="disabled")
        self._op_bar.pack(fill="x", pady=(10, 0))
        self._op_bar.start()
        self._op_status.configure(text="Aplicando otimização...", text_color=Theme.NV_YELLOW)
        self.app.set_busy(True, f"Aplicando {self.meta['title']}")
        proposals = self.analysis.get("proposals", [])
        profile = self.profile

        def run():
            try:
                backend.create_restore_point()
            except Exception:
                pass
            return backend.apply_optimize(profile, proposals)

        self._action(f"Aplicar otimização {profile}",
                     fn=run,
                     on_log=self._apply_log,
                     on_done=lambda rows: self._apply_done(rows),
                     on_error=lambda e: self._apply_fail(str(e)))

    def _apply_log(self, line):
        line = line.strip()
        if not line:
            return
        self._op_detail.configure(text=line)
        if "[i/n]" in line.lower() or "/" in line and "!" not in line:
            pass

    def _apply_done(self, rows):
        self.app.set_busy(False)
        self._op_bar.stop()
        self._op_bar.pack_forget()
        ok = bool(rows) and all(r["result"] == "OK" for r in rows)
        if ok:
            self._op_status.configure(text="Otimização aplicada com sucesso.", text_color=Theme.SUCCESS)
            self._toast("success", "Otimização aplicada com sucesso.")
            self.app.current_profile = self.profile
        else:
            self._op_status.configure(text="Concluído com falhas. Verifique os logs.", text_color=Theme.WARNING)
            self._toast("warning", "Otimização concluída com falhas em algumas etapas.")
        for r in rows:
            self._log(operation=r["operation"], service=r["service"],
                      before=r["before"], after=r["after"],
                      result=r["result"], detail=r["detail"])
        self.after(700, self._analyze)

    def _apply_fail(self, msg):
        self.app.set_busy(False)
        self._op_bar.stop()
        self._op_bar.pack_forget()
        self.applied = False
        self.apply_btn.configure(state="normal")
        self._op_status.configure(text="Não foi possível concluir a operação.", text_color=Theme.DANGER)
        self._op_detail.configure(text=str(msg))
        self._toast("error", f"Não foi possível aplicar a otimização: {msg}")
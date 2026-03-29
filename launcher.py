"""
launcher.py — Ponto de entrada unificado do Star Fishing Bot.

Uso:
    python launcher.py        (modo source)
    StarFishingBot.exe        (modo executável)
"""

import sys
import os
import tkinter as tk

# Garante que src/ seja encontrado
_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from i18n import set_language, t
from config import ConfigManager

# ── Paleta de cores (consistente com o resto do projeto) ──────────────────────
CLR_BG      = "#0d0d0d"
CLR_PANEL   = "#111827"
CLR_CARD    = "#1a1a1a"
CLR_BTN     = "#252535"
CLR_BTN_HV  = "#353550"
CLR_BLUE    = "#1a5fa8"
CLR_BLUE_HV = "#2272c3"
CLR_TEXT    = "#e0e0e0"
CLR_DIM     = "#666680"
CLR_OK      = "#00e676"
CLR_WARN    = "#ffb74d"
CLR_ERR     = "#ef5350"
CLR_GOLD    = "#f0c040"
# ─────────────────────────────────────────────────────────────────────────────


class LauncherWindow(tk.Tk):
    """Janela principal do launcher — escolha entre configurar ou iniciar o bot."""

    def __init__(self):
        super().__init__()
        self.result = None  # "configure" | "start" | None (fechou)

        # Carrega config e idioma
        self._cfg = ConfigManager()
        set_language(self._cfg.get("language", "en"))

        self.title("Star Fishing Bot")
        self.configure(bg=CLR_BG)
        self.resizable(False, False)

        W, H = 440, 430
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw - W) // 2}+{(sh - H) // 2}")

        self._build()
        self.protocol("WM_DELETE_WINDOW", self._quit)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _has(self, key):
        return self._cfg.get(key) is not None

    def _make_btn(self, parent, text, cmd, bg, bg_hover, state="normal"):
        btn = tk.Button(
            parent, text=text, command=cmd,
            font=("Segoe UI", 10, "bold"),
            bg=bg, fg=CLR_TEXT,
            activebackground=bg_hover, activeforeground=CLR_TEXT,
            disabledforeground="#44445a",
            relief="flat", bd=0, cursor="hand2", state=state,
            anchor="center",
        )
        btn._bg, btn._bgh = bg, bg_hover
        btn.bind("<Enter>", lambda e, b=btn: b.config(bg=b._bgh) if str(b["state"]) == "normal" else None)
        btn.bind("<Leave>", lambda e, b=btn: b.config(bg=b._bg)  if str(b["state"]) == "normal" else None)
        return btn

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build(self):
        # Header
        header = tk.Frame(self, bg=CLR_PANEL, height=68)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="★  Star Fishing Bot",
                 font=("Segoe UI", 17, "bold"),
                 bg=CLR_PANEL, fg=CLR_GOLD).pack(side="left", padx=22, pady=16)

        # Status card
        card = tk.Frame(self, bg=CLR_CARD, padx=20, pady=16)
        card.pack(fill="x", padx=20, pady=(18, 0))

        tk.Label(card, text=t("launcher_config_status"),
                 font=("Segoe UI", 9, "bold"),
                 bg=CLR_CARD, fg=CLR_DIM).pack(anchor="w", pady=(0, 10))

        rois = [
            ("roi",             t("launcher_roi_fishing"),   True),
            ("sell_button_roi", t("launcher_roi_sell"),      True),
            ("inventory_roi",   t("launcher_roi_inventory"), False),
        ]

        for key, label, required in rois:
            configured = self._has(key)
            if configured:
                icon, color = "✔", CLR_OK
                badge, badge_color = "", CLR_DIM
            elif required:
                icon, color = "✘", CLR_ERR
                badge, badge_color = t("launcher_required_badge"), CLR_ERR
            else:
                icon, color = "–", CLR_WARN
                badge, badge_color = t("launcher_optional_badge"), CLR_DIM

            row = tk.Frame(card, bg=CLR_CARD)
            row.pack(fill="x", pady=3)

            tk.Label(row, text=icon, font=("Segoe UI", 11, "bold"),
                     bg=CLR_CARD, fg=color, width=2).pack(side="left")
            tk.Label(row, text=label, font=("Segoe UI", 9),
                     bg=CLR_CARD, fg=CLR_TEXT).pack(side="left", padx=(6, 0))
            if badge:
                tk.Label(row, text=f"  {badge}", font=("Segoe UI", 8),
                         bg=CLR_CARD, fg=badge_color).pack(side="left")

        # Warning if required ROIs missing
        required_missing = not self._has("roi") or not self._has("sell_button_roi")

        warn_frame = tk.Frame(self, bg=CLR_BG)
        warn_frame.pack(fill="x", padx=20, pady=(10, 0))
        if required_missing:
            tk.Label(warn_frame, text=t("launcher_missing_warn"),
                     font=("Segoe UI", 8), bg=CLR_BG, fg=CLR_WARN,
                     wraplength=400, justify="left").pack(anchor="w")

        # Buttons
        btn_frame = tk.Frame(self, bg=CLR_BG)
        btn_frame.pack(fill="x", padx=20, pady=(16, 0))

        cfg_btn = self._make_btn(btn_frame, t("launcher_configure_btn"),
                                  self._open_configure, CLR_BTN, CLR_BTN_HV)
        cfg_btn.pack(fill="x", ipady=8, pady=(0, 8))

        start_btn = self._make_btn(btn_frame, t("launcher_start_btn"),
                                    self._start, CLR_BLUE, CLR_BLUE_HV,
                                    state="disabled" if required_missing else "normal")
        start_btn.pack(fill="x", ipady=8)

        # Footer
        tk.Label(self, text=t("launcher_footer_hint"),
                 font=("Segoe UI", 8), bg=CLR_BG, fg=CLR_DIM).pack(pady=(14, 0))

    # ── actions ───────────────────────────────────────────────────────────────

    def _open_configure(self):
        self.result = "configure"
        self.destroy()

    def _start(self):
        self.result = "start"
        self.destroy()

    def _quit(self):
        self.result = None
        self.destroy()


# ── Runner functions ──────────────────────────────────────────────────────────

def _run_roi_selector():
    """Abre a ferramenta de configuração de regiões. Bloqueia até fechar."""
    # roi_selector.py está na mesma pasta que launcher.py
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)
    from roi_selector import MainMenu
    app = MainMenu()
    app.mainloop()


def _run_bot():
    """Inicia o bot e abre o Painel de Controle. Bloqueia até o painel fechar."""
    from main import run_bot
    run_bot()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    while True:
        launcher = LauncherWindow()
        launcher.mainloop()

        if launcher.result == "configure":
            _run_roi_selector()
            # Volta para o launcher com status atualizado

        elif launcher.result == "start":
            _run_bot()
            # Após fechar o painel, volta para o launcher
            # (usuário pode reconfigurar ou reiniciar)

        else:
            # Fechou a janela — sai
            break


if __name__ == "__main__":
    main()

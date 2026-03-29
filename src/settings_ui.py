import tkinter as tk
from tkinter import messagebox
import json
import os
from i18n import t, set_language

# ── Color palette (matches roi_selector) ──────────────────────────────────────
CLR_BG          = "#0F0F0F"
CLR_CARD        = "#1A1A1A"
CLR_BTN         = "#222222"
CLR_BTN_HOVER   = "#333333"
CLR_BTN_BLUE    = "#0066CC"
CLR_BTN_BLUE_HV = "#0088FF"
CLR_TEXT        = "#FFFFFF"
CLR_TEXT_DIM    = "#AAAAAA"
CLR_ACCENT      = "#00FF88"
CLR_ACCENT_DIM  = "#00CC66"
CLR_SEP         = "#2a2a2a"
# ───────────────────────────────────────────────────────────────────────────────


class ModernButton(tk.Button):
    def __init__(self, parent, text, command, width=35, bg=CLR_BTN):
        super().__init__(
            parent, text=text, command=command, width=width,
            font=("Segoe UI", 10, "bold"), bg=bg, fg=CLR_TEXT,
            activebackground=CLR_BTN_HOVER, activeforeground=CLR_TEXT,
            relief="flat", bd=0, pady=12, cursor="hand2",
        )
        self._bg = bg
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        if str(self["state"]) == "normal":
            self.config(bg=CLR_BTN_HOVER if self._bg == CLR_BTN else CLR_BTN_BLUE_HV)

    def _on_leave(self, e):
        if str(self["state"]) == "normal":
            self.config(bg=self._bg)


class ModernEntry(tk.Frame):
    def __init__(self, parent, label_text, default_value, on_change=None):
        super().__init__(parent, bg=CLR_CARD)
        tk.Label(self, text=label_text, bg=CLR_CARD, fg=CLR_TEXT_DIM,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 2))
        self.entry = tk.Entry(
            self, bg=CLR_BTN, fg=CLR_TEXT, insertbackground=CLR_TEXT,
            relief="flat", font=("Segoe UI", 10), highlightthickness=1,
            highlightbackground="#333333", highlightcolor=CLR_BTN_BLUE,
        )
        self.entry.pack(fill="x", ipady=4, padx=1)
        self.entry.insert(0, str(default_value))
        if on_change:
            self.entry.bind("<KeyRelease>", lambda e: on_change())

    def get(self):
        return self.entry.get()


class ModernToggle(tk.Frame):
    def __init__(self, parent, label_text, default_state, on_change=None):
        super().__init__(parent, bg=CLR_CARD)
        self.state = default_state
        self.on_change = on_change

        tk.Label(self, text=label_text, bg=CLR_CARD, fg=CLR_TEXT_DIM,
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 10))

        self.btn = tk.Button(
            self,
            text="ON" if self.state else "OFF",
            bg=CLR_ACCENT if self.state else CLR_BTN,
            fg="#000000" if self.state else CLR_TEXT,
            activebackground=CLR_ACCENT_DIM if self.state else CLR_BTN_HOVER,
            activeforeground="#000000" if self.state else CLR_TEXT,
            relief="flat", bd=0, font=("Segoe UI", 9, "bold"),
            width=6, cursor="hand2", command=self.toggle,
        )
        self.btn.pack(side="right")

    def toggle(self):
        self.state = not self.state
        if self.state:
            self.btn.config(text="ON",  bg=CLR_ACCENT,  fg="#000000",
                            activebackground=CLR_ACCENT_DIM, activeforeground="#000000")
        else:
            self.btn.config(text="OFF", bg=CLR_BTN,     fg=CLR_TEXT,
                            activebackground=CLR_BTN_HOVER,  activeforeground=CLR_TEXT)
        if self.on_change:
            self.on_change()

    def get(self):
        return self.state


class HotkeyDialog(tk.Toplevel):
    def __init__(self, parent, action_name, current_key):
        super().__init__(parent)
        self.title("Hotkey Setting")
        self.geometry("280x130")
        self.configure(bg="#F0F0F0")
        self.resizable(False, False)
        self.result = current_key

        # Center relative to parent
        self.geometry("+{}+{}".format(
            parent.winfo_x() + 150,
            parent.winfo_y() + 200,
        ))

        top_frame = tk.Frame(self, bg="#F0F0F0")
        top_frame.pack(pady=(20, 15))

        tk.Label(top_frame, text=action_name, bg="#FFFFFF", fg="#0033CC",
                 font=("Arial", 10), width=12, relief="groove", bd=2
                 ).pack(side="left", padx=(0, 10), ipady=4)

        self.lbl_key = tk.Label(
            top_frame, text=str(self.result).upper(), bg="#FFFFFF", fg="#000000",
            font=("Arial", 12), width=8, relief="solid", bd=1,
        )
        self.lbl_key.pack(side="left", ipady=4)

        btn_frame = tk.Frame(self, bg="#F0F0F0")
        btn_frame.pack()

        tk.Button(btn_frame, text="Ok",     width=8, bg="#FFFFFF", relief="solid", bd=1,
                  command=self.confirm).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Cancel", width=8, bg="#FFFFFF", relief="solid", bd=1,
                  command=self.cancel).pack(side="left", padx=10)

        self.bind("<Key>", self.on_key)
        self.transient(parent)
        self.grab_set()
        self.focus_force()
        self.wait_window(self)

    def on_key(self, event):
        sym = event.keysym
        if sym in ("Shift_L", "Shift_R", "Control_L", "Control_R",
                   "Alt_L", "Alt_R", "Caps_Lock", "Tab"):
            return
        if len(sym) == 1:
            sym = sym.lower()
        elif sym == "Return":
            sym = "enter"
        elif sym == "Escape":
            sym = "esc"
        elif sym == "Prior":
            sym = "page_up"
        elif sym == "Next":
            sym = "page_down"
        self.result = sym
        self.lbl_key.config(text=str(self.result).upper())

    def confirm(self):
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()


class ModernHotkeyButton(tk.Frame):
    def __init__(self, parent, action_name, label_text, default_value, on_change=None):
        super().__init__(parent, bg=CLR_CARD)
        self.action_name = action_name
        self.on_change   = on_change
        self.current_key = default_value

        tk.Label(self, text=label_text, bg=CLR_CARD, fg=CLR_TEXT_DIM,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 2))

        self.btn = tk.Button(
            self, text=str(self.current_key).upper(),
            bg=CLR_BTN, fg=CLR_ACCENT,
            activebackground=CLR_BTN_HOVER, activeforeground=CLR_ACCENT,
            relief="flat", font=("Segoe UI", 10, "bold"), bd=0,
            cursor="hand2", command=self.open_dialog,
        )
        self.btn.pack(fill="x", ipady=4, padx=1)
        self.btn.bind("<Enter>", lambda e: self.btn.config(bg=CLR_BTN_HOVER))
        self.btn.bind("<Leave>", lambda e: self.btn.config(bg=CLR_BTN))

    def open_dialog(self):
        dialog = HotkeyDialog(self.winfo_toplevel(), self.action_name, self.current_key)
        if dialog.result and dialog.result != self.current_key:
            self.current_key = dialog.result
            self.btn.config(text=str(self.current_key).upper())
            if self.on_change:
                self.on_change()

    def get(self):
        return self.current_key


class LanguageSelector(tk.Frame):
    def __init__(self, parent, current_lang, on_change):
        super().__init__(parent, bg=CLR_CARD)
        self.current_lang = current_lang
        self.on_change    = on_change

        self.btn_pt = tk.Button(self, text="PT", font=("Segoe UI", 8, "bold"), width=5,
                                relief="flat", bd=0, cursor="hand2",
                                command=lambda: self.select("pt"))
        self.btn_pt.pack(side="left", padx=(0, 1), ipady=2)

        self.btn_en = tk.Button(self, text="EN", font=("Segoe UI", 8, "bold"), width=5,
                                relief="flat", bd=0, cursor="hand2",
                                command=lambda: self.select("en"))
        self.btn_en.pack(side="left", ipady=2)

        self.update_ui()

    def select(self, lang):
        if self.current_lang != lang:
            self.current_lang = lang
            self.update_ui()
            self.on_change(lang)

    def update_ui(self):
        if self.current_lang == "pt":
            self.btn_pt.config(bg=CLR_ACCENT,  fg="#000000",
                               activebackground=CLR_ACCENT_DIM, activeforeground="#000000")
            self.btn_en.config(bg=CLR_BTN,     fg="#666666",
                               activebackground=CLR_BTN_HOVER,  activeforeground="#888888")
        else:
            self.btn_en.config(bg=CLR_ACCENT,  fg="#000000",
                               activebackground=CLR_ACCENT_DIM, activeforeground="#000000")
            self.btn_pt.config(bg=CLR_BTN,     fg="#666666",
                               activebackground=CLR_BTN_HOVER,  activeforeground="#888888")


def _card(parent, title):
    """Creates a dark card frame with a bold title label. Returns the frame."""
    frame = tk.Frame(parent, bg=CLR_CARD, padx=15, pady=15)
    frame.pack(fill="x", pady=(0, 12))
    tk.Label(frame, text=title, font=("Segoe UI", 10, "bold"),
             bg=CLR_CARD, fg=CLR_TEXT).pack(anchor="w", pady=(0, 10))
    return frame


class SettingsApp(tk.Tk):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.title(f"Star Fishing — {t('ctrl_panel_title')}")
        self.configure(bg=CLR_BG)
        self.resizable(False, True)

        # Dynamic window height — never taller than screen allows
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        WIN_W = 660
        WIN_H = min(700, screen_h - 80)
        x = max(0, (screen_w - WIN_W) // 2)
        y = max(0, (screen_h - WIN_H) // 2)
        self.geometry(f"{WIN_W}x{WIN_H}+{x}+{y}")
        self.minsize(WIN_W, 400)

        self.lang = self.bot.config.get("language", "en")
        set_language(self.lang)

        # ── Fixed header ──────────────────────────────────────────────────────
        header_frame = tk.Frame(self, bg=CLR_BG)
        header_frame.pack(fill="x", pady=(20, 0), padx=20)

        self.lang_selector = LanguageSelector(header_frame, self.lang, self.change_language)
        self.lang_selector.pack(side="right")

        tk.Label(header_frame, text=t("ctrl_panel_title"),
                 font=("Segoe UI", 14, "bold"), bg=CLR_BG, fg=CLR_TEXT
                 ).pack(side="left")

        tk.Label(self, text=t("ctrl_panel_subtitle"),
                 font=("Segoe UI", 9), bg=CLR_BG, fg="#888888"
                 ).pack(pady=(4, 8))

        tk.Frame(self, bg=CLR_SEP, height=1).pack(fill="x", padx=20, pady=(0, 8))

        # ── Fixed footer ──────────────────────────────────────────────────────
        footer = tk.Frame(self, bg=CLR_BG)
        footer.pack(fill="x", side="bottom", pady=(8, 16))

        self.save_status = tk.Label(footer, text=t("auto_save_hint"),
                                    font=("Segoe UI", 8), bg=CLR_BG, fg="#444444")
        self.save_status.pack(pady=(0, 4))

        # ── Scrollable content area ───────────────────────────────────────────
        wrapper = tk.Frame(self, bg=CLR_BG)
        wrapper.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(wrapper, bg=CLR_BG, highlightthickness=0)
        scrollbar    = tk.Scrollbar(wrapper, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(self._canvas, bg=CLR_BG)
        self._canvas_window = self._canvas.create_window((0, 0), window=inner, anchor="nw")

        inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self.bind_all("<MouseWheel>", self._on_mousewheel)

        # ── Two-column content ────────────────────────────────────────────────
        c = self.bot.config

        def auto_save():
            self.save_settings(silent=True)

        main_frame = tk.Frame(inner, bg=CLR_BG)
        main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        left_col  = tk.Frame(main_frame, bg=CLR_BG)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 8))

        right_col = tk.Frame(main_frame, bg=CLR_BG)
        right_col.pack(side="right", fill="both", expand=True, padx=(8, 0))

        # ── LEFT: Hotkeys ─────────────────────────────────────────────────────
        card_keys = _card(left_col, t("hotkeys_group"))

        self.start_key = ModernHotkeyButton(
            card_keys, t("start_stop_lbl"), t("start_key"), c.get("start_key", "F6"), auto_save)
        self.start_key.pack(fill="x", pady=4)

        self.stop_key = ModernHotkeyButton(
            card_keys, t("stop_forced_lbl"), t("stop_key"), c.get("stop_key", "F7"), auto_save)
        self.stop_key.pack(fill="x", pady=4)

        # ── LEFT: Times & Delays ──────────────────────────────────────────────
        card_times = _card(left_col, t("times_delays_group"))

        self.hold_time = ModernEntry(
            card_times, t("hold_time_lbl"), c.get("hold_time", 0.58), auto_save)
        self.hold_time.pack(fill="x", pady=4)

        self.post_cast = ModernEntry(
            card_times, t("post_cast_lbl"), c.get("post_cast_delay", 0.1), auto_save)
        self.post_cast.pack(fill="x", pady=4)

        # ── LEFT: Automation ──────────────────────────────────────────────────
        card_auto = _card(left_col, t("automation_group"))

        self.auto_sell = ModernToggle(
            card_auto, t("auto_sell_lbl"), c.get("auto_sell_enabled", True), auto_save)
        self.auto_sell.pack(fill="x", pady=4)

        # ── RIGHT: Smart Pause ────────────────────────────────────────────────
        card_pause = _card(right_col, t("smart_pause_group"))

        self.pause_enabled = ModernToggle(
            card_pause, t("enable_smart_pause"), c.get("inactive_pause_enabled", False), auto_save)
        self.pause_enabled.pack(fill="x", pady=4)

        self.pause_triggers = ModernEntry(
            card_pause, t("casts_to_pause"), c.get("inactive_pause_triggers", 4), auto_save)
        self.pause_triggers.pack(fill="x", pady=4)

        self.pause_duration = ModernEntry(
            card_pause, t("pause_duration"), c.get("inactive_pause_duration", 15.0), auto_save)
        self.pause_duration.pack(fill="x", pady=4)

        self.pause_thresh = ModernEntry(
            card_pause, t("spam_threshold"), c.get("inactive_cast_time_threshold", 5.0), auto_save)
        self.pause_thresh.pack(fill="x", pady=4)

        # ── RIGHT: Detection ──────────────────────────────────────────────────
        card_adv = _card(right_col, t("detection_group"))

        self.green_thresh = ModernEntry(
            card_adv, t("green_pixels_lbl"), c.get("green_threshold", 10), auto_save)
        self.green_thresh.pack(fill="x", pady=4)

        self.poll_interval = ModernEntry(
            card_adv, t("poll_interval_lbl"), c.get("poll_interval", 0.1), auto_save)
        self.poll_interval.pack(fill="x", pady=4)

    # ── Scroll helpers ────────────────────────────────────────────────────────

    def _on_inner_configure(self, event):
        bbox = self._canvas.bbox("all")
        if bbox:
            # Only enable scrollregion when content is actually taller than the viewport
            content_h = bbox[3] - bbox[1]
            canvas_h  = self._canvas.winfo_height()
            if content_h > canvas_h:
                self._canvas.configure(scrollregion=bbox)
            else:
                self._canvas.configure(scrollregion=(0, 0, bbox[2], canvas_h))

    def _on_canvas_configure(self, event):
        # Keep the inner frame as wide as the canvas
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        # Only scroll if content actually overflows the viewport
        bbox = self._canvas.bbox("all")
        if bbox and (bbox[3] - bbox[1]) > self._canvas.winfo_height():
            try:
                self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass

    # ── Language ──────────────────────────────────────────────────────────────

    def change_language(self, new_lang):
        self.lang = new_lang
        self.bot.config.set("language", new_lang)
        self.bot.config.save()
        self.bot.wants_restart = True
        self.destroy()

    # ── Save ──────────────────────────────────────────────────────────────────

    def save_settings(self, silent=False):
        try:
            c = self.bot.config

            new_start = str(self.start_key.get()).strip()
            new_stop  = str(self.stop_key.get()).strip()

            if not new_start or not new_stop:
                if not silent:
                    messagebox.showwarning("Atenção", "As teclas de atalho não podem ser vazias.", parent=self)
                return

            c.config["start_key"] = new_start
            c.config["stop_key"]  = new_stop

            c.config["hold_time"]       = float(self.hold_time.get())
            c.config["post_cast_delay"] = float(self.post_cast.get())

            c.config["auto_sell_enabled"] = bool(self.auto_sell.get())

            c.config["inactive_pause_enabled"]       = bool(self.pause_enabled.get())
            c.config["inactive_pause_triggers"]       = int(self.pause_triggers.get())
            c.config["inactive_pause_duration"]       = float(self.pause_duration.get())
            c.config["inactive_cast_time_threshold"]  = float(self.pause_thresh.get())

            c.config["green_threshold"] = int(self.green_thresh.get())
            c.config["poll_interval"]   = float(self.poll_interval.get())

            c.save()

            # Apply new hotkeys live
            self.bot.inputs.set_keys(new_start, new_stop)

            self.save_status.config(text=t("saved_success"), fg=CLR_ACCENT)
            self.after(2000, lambda: self.save_status.config(text="", fg=CLR_BG))

            if not silent:
                messagebox.showinfo("Sucesso", "Configurações salvas!", parent=self)

        except ValueError as e:
            if not silent:
                messagebox.showerror("Erro de Valor",
                                     f"Certifique-se de digitar números válidos.\nErro: {e}",
                                     parent=self)

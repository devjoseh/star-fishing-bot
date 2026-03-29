"""
roi_selector.py — Ferramenta visual para configurar as regiões e templates.
"""

import tkinter as tk
from tkinter import messagebox
import json
import time
import ctypes
import sys
import os

# Adds src/ to python path so i18n and config can be imported easily
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from i18n import t, set_language

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

try:
    import mss
    import mss.tools
    from PIL import Image, ImageTk
except ImportError as e:
    print(f"Dependência faltando: {e}")
    print("Execute: pip install -r requirements.txt")
    sys.exit(1)

def _base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


CONFIG_FILE = os.path.join(_base_dir(), "config.json")
ASSETS_DIR  = os.path.join(_base_dir(), "assets")

if not os.path.exists(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)

# ── Color palette ──────────────────────────────────────────────────────────────
CLR_BG          = "#0d0d0d"
CLR_BG_PANEL    = "#111111"
CLR_BG_FOOTER   = "#161625"
CLR_BTN         = "#252535"
CLR_BTN_HOVER   = "#353550"
CLR_BTN_BLUE    = "#1a5fa8"
CLR_BTN_BLUE_HV = "#2272c3"
CLR_TEXT        = "#e0e0e0"
CLR_TEXT_DIM    = "#666680"
CLR_ACCENT      = "#00ccff"
CLR_SUCCESS     = "#00e676"
CLR_GOLD        = "#f0c040"
# ───────────────────────────────────────────────────────────────────────────────


def load_existing_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                c = json.load(f)
                set_language(c.get("language", "en"))
                return c
        except Exception:
            pass
    set_language("en")
    return {}


def save_config(key, roi, screenshot_pil=None):
    config = load_existing_config()
    config[key] = roi

    if screenshot_pil is not None:
        if key == "inventory_roi":
            x, y, w, h = roi["x"], roi["y"], roi["width"], roi["height"]
            cropped = screenshot_pil.crop((x, y, x + w, y + h))
            template_path = os.path.join(ASSETS_DIR, "inv_full_template.png")
            cropped.save(template_path)
            print(f"Template de texto salvo em: {template_path}")

    config.setdefault("hold_time",                    0.58)
    config.setdefault("start_key",                    "F6")
    config.setdefault("stop_key",                     "F7")
    config.setdefault("toggle_pause_key",             "F8")
    config.setdefault("green_threshold",              10)
    config.setdefault("poll_interval",                0.1)
    config.setdefault("post_cast_delay",              0.1)
    config.setdefault("language",                     "en")
    config.setdefault("inactive_pause_enabled",       False)
    config.setdefault("inactive_pause_triggers",      4)
    config.setdefault("inactive_pause_duration",      15.0)
    config.setdefault("inactive_cast_time_threshold", 5.0)

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

    print(f"✅  {t('roi_saved_title')} '{key}' -> {CONFIG_FILE}")


class ROISelector(tk.Toplevel):
    """Full-screen region picker that adapts to any screen resolution."""

    # Space (px) reserved outside the canvas area
    _FOOTER_H  = 62   # fixed footer bar
    _CHROME_H  = 38   # window title bar + borders
    _TASKBAR_H = 52   # system taskbar
    _MARGIN_W  = 16   # horizontal window margin

    def __init__(self, parent, screenshot_pil, target_key):
        super().__init__(parent)
        self.parent        = parent
        self.screenshot_pil = screenshot_pil
        self.target_key    = target_key

        self.title(t("select_area", target=target_key))
        self.resizable(True, True)
        self.configure(bg="#000000")

        # ── Dynamic sizing ────────────────────────────────────────────────────
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        max_canvas_w = screen_w  - self._MARGIN_W
        max_canvas_h = screen_h  - self._FOOTER_H - self._CHROME_H - self._TASKBAR_H

        orig_w, orig_h = screenshot_pil.size
        scale    = min(max_canvas_w / orig_w, max_canvas_h / orig_h, 1.0)
        self.scale = scale
        disp_w   = int(orig_w * scale)
        disp_h   = int(orig_h * scale)

        # Visible viewport size (never larger than available space)
        view_w = min(disp_w, max_canvas_w)
        view_h = min(disp_h, max_canvas_h)

        display_img  = screenshot_pil.resize((disp_w, disp_h), Image.LANCZOS)
        self.tk_img  = ImageTk.PhotoImage(display_img)

        # ── Canvas + scrollbars ───────────────────────────────────────────────
        canvas_frame = tk.Frame(self, bg="#000000")
        canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            canvas_frame,
            width=view_w, height=view_h,
            cursor="crosshair", bg="#000000",
            highlightthickness=0,
        )

        v_scroll = tk.Scrollbar(canvas_frame, orient="vertical",   command=self.canvas.yview)
        h_scroll = tk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)

        self.canvas.configure(
            xscrollcommand=h_scroll.set,
            yscrollcommand=v_scroll.set,
            scrollregion=(0, 0, disp_w, disp_h),
        )

        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

        # ── Footer (always visible, never scrolls away) ───────────────────────
        footer = tk.Frame(self, bg=CLR_BG_FOOTER, height=self._FOOTER_H)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        inner = tk.Frame(footer, bg=CLR_BG_FOOTER)
        inner.pack(fill="both", expand=True, padx=12, pady=8)

        self.info_label = tk.Label(
            inner,
            text=t("select_area", target=target_key),
            bg=CLR_BG_FOOTER, fg=CLR_TEXT,
            font=("Segoe UI", 9),
        )
        self.info_label.pack(side="left", fill="y")

        btn_frame = tk.Frame(inner, bg=CLR_BG_FOOTER)
        btn_frame.pack(side="right")

        tk.Label(
            btn_frame, text="[R] Reset   [S / Enter] Salvar",
            bg=CLR_BG_FOOTER, fg=CLR_TEXT_DIM,
            font=("Segoe UI", 8),
        ).pack(side="left", padx=(0, 14))

        self.reset_btn = self._make_btn(btn_frame, t("reset_btn"),     self.reset,        CLR_BTN,      CLR_BTN_HOVER)
        self.reset_btn.pack(side="left", padx=4)

        self.save_btn  = self._make_btn(btn_frame, t("save_roi_btn"),  self.confirm_save, CLR_BTN_BLUE, CLR_BTN_BLUE_HV,
                                        disabled_fg="#6aaee0", state="disabled")
        self.save_btn.pack(side="left", padx=4)

        # ── Bindings ──────────────────────────────────────────────────────────
        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        self.bind("<KeyPress-s>", lambda e: self.confirm_save())
        self.bind("<KeyPress-S>", lambda e: self.confirm_save())
        self.bind("<KeyPress-r>", lambda e: self.reset())
        self.bind("<KeyPress-R>", lambda e: self.reset())
        self.bind("<Return>",     lambda e: self.confirm_save())

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # ── Center window on screen ───────────────────────────────────────────
        self.update_idletasks()
        win_w = view_w + 20           # +20 for potential scrollbar width
        win_h = view_h + self._FOOTER_H + 20
        x = max(0, (screen_w - win_w) // 2)
        y = max(0, (screen_h - win_h) // 2)
        self.geometry(f"+{x}+{y}")

        self._rect_id = None
        self._start   = None
        self._end     = None

    # ── Button factory ────────────────────────────────────────────────────────
    def _make_btn(self, parent, text, cmd, bg, bg_hover, disabled_fg=None, state="normal"):
        kw = dict(
            text=text, command=cmd,
            bg=bg, fg=CLR_TEXT,
            activebackground=bg_hover, activeforeground=CLR_TEXT,
            relief="flat", bd=0, font=("Segoe UI", 9, "bold"),
            padx=16, pady=6, cursor="hand2", state=state,
        )
        if disabled_fg:
            kw["disabledforeground"] = disabled_fg
        btn = tk.Button(parent, **kw)
        btn._bg      = bg
        btn._bg_hover = bg_hover
        btn.bind("<Enter>", lambda e, b=btn: b.config(bg=b._bg_hover) if str(b["state"]) == "normal" else None)
        btn.bind("<Leave>", lambda e, b=btn: b.config(bg=b._bg)       if str(b["state"]) == "normal" else None)
        return btn

    # ── Event handlers ────────────────────────────────────────────────────────
    def on_close(self):
        self.destroy()

    def _on_press(self, event):
        self._start = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        self._end   = self._start
        if self._rect_id:
            self.canvas.delete(self._rect_id)
            self._rect_id = None
        self.save_btn.config(state="disabled")

    def _on_drag(self, event):
        if self._start is None:
            return
        self._end = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        if self._rect_id:
            self.canvas.delete(self._rect_id)
        self._rect_id = self.canvas.create_rectangle(
            *self._start, *self._end,
            outline=CLR_ACCENT, width=2, dash=(4, 2),
        )
        self._update_info(confirmed=False)

    def _on_release(self, event):
        if self._start is None:
            return
        self._end = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        if self._rect_id:
            self.canvas.delete(self._rect_id)
        self._rect_id = self.canvas.create_rectangle(
            *self._start, *self._end,
            outline=CLR_SUCCESS, width=2,
        )
        self._update_info(confirmed=True)
        self.save_btn.config(state="normal")

    def _update_info(self, confirmed):
        if self._start and self._end:
            roi    = self._compute_roi()
            status = t("ready_to_save") if confirmed else t("selecting")
            self.info_label.config(
                text=f"{status}  |  x={roi['x']} y={roi['y']}  w={roi['width']} h={roi['height']}",
                fg=CLR_SUCCESS if confirmed else CLR_ACCENT,
            )

    def _compute_roi(self):
        x1 = int(min(self._start[0], self._end[0]) / self.scale)
        y1 = int(min(self._start[1], self._end[1]) / self.scale)
        x2 = int(max(self._start[0], self._end[0]) / self.scale)
        y2 = int(max(self._start[1], self._end[1]) / self.scale)
        return {"x": x1, "y": y1, "width": max(1, x2 - x1), "height": max(1, y2 - y1)}

    def reset(self):
        if self._rect_id:
            self.canvas.delete(self._rect_id)
            self._rect_id = None
        self._start = None
        self._end   = None
        self.save_btn.config(state="disabled")
        self.info_label.config(text=t("select_area", target=self.target_key), fg=CLR_TEXT)

    def confirm_save(self):
        if self._start is None or self._end is None:
            messagebox.showwarning("Atenção", t("no_region_warn"))
            return
        if self._start == self._end:
            messagebox.showwarning("Atenção", t("empty_region_warn"))
            return
        roi = self._compute_roi()
        save_config(self.target_key, roi, self.screenshot_pil)
        messagebox.showinfo(t("roi_saved_title"), t("roi_saved_msg", target=self.target_key))
        self.destroy()


class ModernButton(tk.Button):
    """Dark-themed flat button with hover effect."""

    def __init__(self, parent, text, command, accent=False):
        bg       = CLR_BTN_BLUE    if accent else CLR_BTN
        bg_hover = CLR_BTN_BLUE_HV if accent else CLR_BTN_HOVER
        super().__init__(
            parent,
            text=text, command=command,
            font=("Segoe UI", 10, "bold"),
            bg=bg, fg=CLR_TEXT,
            activebackground=bg_hover, activeforeground=CLR_TEXT,
            relief="flat", bd=0,
            pady=10, padx=20,
            cursor="hand2",
            anchor="center",
        )
        self._bg       = bg
        self._bg_hover = bg_hover
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        if str(self["state"]) == "normal":
            self.config(bg=self._bg_hover)

    def _on_leave(self, e):
        if str(self["state"]) == "normal":
            self.config(bg=self._bg)


class MainMenu(tk.Tk):
    def __init__(self):
        super().__init__()
        load_existing_config()

        self.title("Star Fishing Setup")
        self.configure(bg=CLR_BG)
        self.resizable(False, False)

        # Center on screen
        W, H = 440, 370
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw - W) // 2}+{(sh - H) // 2}")

        # ── Header ────────────────────────────────────────────────────────────
        header = tk.Frame(self, bg="#111827", height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="★  Star Fishing",
            font=("Segoe UI", 16, "bold"),
            bg="#111827", fg=CLR_GOLD,
        ).pack(side="left", padx=20, pady=14)

        tk.Label(
            header, text="· Setup",
            font=("Segoe UI", 11),
            bg="#111827", fg=CLR_TEXT_DIM,
        ).pack(side="left", pady=14)

        # ── Content ───────────────────────────────────────────────────────────
        content = tk.Frame(self, bg=CLR_BG)
        content.pack(expand=True, fill="both", padx=28, pady=16)

        tk.Label(
            content,
            text=t("vision_setup_title"),
            font=("Segoe UI", 9, "bold"),
            bg=CLR_BG, fg=CLR_TEXT_DIM,
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        ModernButton(
            content,
            text=t("start_fishing_btn"),
            command=lambda: self.start_capture("roi"),
        ).pack(pady=5, fill="x")

        ModernButton(
            content,
            text=t("inventory_full_btn"),
            command=lambda: self.start_capture("inventory_roi"),
        ).pack(pady=5, fill="x")

        ModernButton(
            content,
            text=t("sell_all_btn"),
            command=lambda: self.start_capture("sell_button_roi"),
        ).pack(pady=5, fill="x")

        tk.Label(
            content,
            text=t("vision_setup_hint"),
            fg=CLR_TEXT_DIM, bg=CLR_BG,
            font=("Segoe UI", 8),
            wraplength=380, justify="center",
        ).pack(pady=(16, 0))

    def start_capture(self, target_key):
        self.withdraw()
        print(f"\n[Atenção] Focando no jogo em 2 segundos para capturar '{target_key}'...")
        time.sleep(2)
        print("Capturando tela...")
        with mss.mss() as sct:
            monitor    = sct.monitors[1]
            raw        = sct.grab(monitor)
            screenshot = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

        selector = ROISelector(self, screenshot, target_key)
        self.wait_window(selector)
        self.deiconify()


if __name__ == "__main__":
    app = MainMenu()
    app.mainloop()

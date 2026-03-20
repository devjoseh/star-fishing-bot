"""
roi_selector.py — Ferramenta visual para configurar as regiões e templates.
"""

import tkinter as tk
from tkinter import messagebox
import json
import os
import sys
import time
import ctypes

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

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

if not os.path.exists(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)

MAX_DISPLAY_W = 1400
MAX_DISPLAY_H = 850


def load_existing_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(key, roi, screenshot_pil=None):
    config = load_existing_config()
    config[key] = roi
    
    # Se for inventory_roi, salvar um template da imagem
    if screenshot_pil is not None:
        if key == "inventory_roi":
            x, y, w, h = roi["x"], roi["y"], roi["width"], roi["height"]
            cropped = screenshot_pil.crop((x, y, x + w, y + h))
            template_path = os.path.join(ASSETS_DIR, "inv_full_template.png")
            cropped.save(template_path)
            print(f"Template de texto salvo em: {template_path}")

    # Preservar chaves extras
    config.setdefault("hold_time",       0.58)
    config.setdefault("start_key",       "F6")
    config.setdefault("stop_key",        "F7")
    config.setdefault("toggle_pause_key","F8")
    config.setdefault("green_threshold", 10)
    config.setdefault("poll_interval",   0.1)
    config.setdefault("post_cast_delay", 0.1)
    config.setdefault("inactive_pause_enabled",       False)
    config.setdefault("inactive_pause_triggers",      4)
    config.setdefault("inactive_pause_duration",      15.0)
    config.setdefault("inactive_cast_time_threshold", 5.0)

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

    print(f"✅  ROI '{key}' salva em {CONFIG_FILE}")


class ROISelector(tk.Toplevel):
    def __init__(self, parent, screenshot_pil, target_key):
        super().__init__(parent)
        self.parent = parent
        self.screenshot_pil = screenshot_pil
        self.target_key = target_key
        
        self.title(f"Selecionando: {target_key}")
        self.resizable(False, False)

        orig_w, orig_h = screenshot_pil.size
        scale = min(MAX_DISPLAY_W / orig_w, MAX_DISPLAY_H / orig_h, 1.0)
        self.scale = scale
        disp_w = int(orig_w * scale)
        disp_h = int(orig_h * scale)

        display_img = screenshot_pil.resize((disp_w, disp_h), Image.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(display_img)

        self.canvas = tk.Canvas(self, width=disp_w, height=disp_h, cursor="crosshair")
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

        footer = tk.Frame(self, bg="#1e1e1e")
        footer.pack(fill="x")

        self.info_label = tk.Label(
            footer, text=f"Alvo: {target_key.upper()}  |  Selecione a área",
            bg="#1e1e1e", fg="#aaaaaa", font=("Segoe UI", 10), padx=10
        )
        self.info_label.pack(side="left", pady=6)

        btn_frame = tk.Frame(footer, bg="#1e1e1e")
        btn_frame.pack(side="right", padx=8, pady=4)

        self.reset_btn = tk.Button(
            btn_frame, text="Resetar (R)", command=self.reset,
            bg="#333333", fg="white", activebackground="#444444", activeforeground="white",
            relief="flat", font=("Segoe UI", 9, "bold"), padx=12, pady=4, cursor="hand2", bd=0
        )
        self.reset_btn.pack(side="left", padx=4)

        self.save_btn = tk.Button(
            btn_frame, text="Salvar ROI (Enter)", command=self.confirm_save,
            bg="#0066cc", fg="white", activebackground="#0088ff", activeforeground="white",
            relief="flat", font=("Segoe UI", 9, "bold"), padx=12, pady=4, cursor="hand2", bd=0,
            state="disabled"
        )
        self.save_btn.pack(side="left", padx=4)

        self.reset_btn.bind("<Enter>", lambda e: self.reset_btn.config(bg="#444444") if self.reset_btn['state'] == 'normal' else None)
        self.reset_btn.bind("<Leave>", lambda e: self.reset_btn.config(bg="#333333") if self.reset_btn['state'] == 'normal' else None)
        self.save_btn.bind("<Enter>", lambda e: self.save_btn.config(bg="#0088ff") if self.save_btn['state'] == 'normal' else None)
        self.save_btn.bind("<Leave>", lambda e: self.save_btn.config(bg="#0066cc") if self.save_btn['state'] == 'normal' else None)

        self._rect_id   = None
        self._start     = None
        self._end       = None

        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        self.bind("<KeyPress-s>", lambda e: self.confirm_save())
        self.bind("<KeyPress-S>", lambda e: self.confirm_save())
        self.bind("<KeyPress-r>", lambda e: self.reset())
        self.bind("<KeyPress-R>", lambda e: self.reset())
        self.bind("<Return>",     lambda e: self.confirm_save())

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.update_idletasks()
        self.geometry(f"+0+0")

    def on_close(self):
        self.destroy()

    def _on_press(self, event):
        self._start = (event.x, event.y)
        self._end   = (event.x, event.y)
        if self._rect_id:
            self.canvas.delete(self._rect_id)
            self._rect_id = None
        self.save_btn.config(state="disabled")

    def _on_drag(self, event):
        if self._start is None:
            return
        self._end = (event.x, event.y)
        if self._rect_id:
            self.canvas.delete(self._rect_id)
        self._rect_id = self.canvas.create_rectangle(
            *self._start, *self._end,
            outline="#00ccff", width=2, dash=(4, 2)
        )
        self._update_info(confirmed=False)

    def _on_release(self, event):
        if self._start is None:
            return
        self._end = (event.x, event.y)
        if self._rect_id:
            self.canvas.delete(self._rect_id)
        self._rect_id = self.canvas.create_rectangle(
            *self._start, *self._end,
            outline="#00ff88", width=2
        )
        self._update_info(confirmed=True)
        self.save_btn.config(state="normal")

    def _update_info(self, confirmed):
        if self._start and self._end:
            roi = self._compute_roi()
            status = "✔ Pronto para salvar" if confirmed else "Selecionando..."
            self.info_label.config(
                text=f"{status}  |  x={roi['x']} y={roi['y']}  w={roi['width']} h={roi['height']}",
                fg="#00ff88" if confirmed else "#00ccff"
            )

    def _compute_roi(self):
        x1 = int(min(self._start[0], self._end[0]) / self.scale)
        y1 = int(min(self._start[1], self._end[1]) / self.scale)
        x2 = int(max(self._start[0], self._end[0]) / self.scale)
        y2 = int(max(self._start[1], self._end[1]) / self.scale)
        return {
            "x":      x1,
            "y":      y1,
            "width":  max(1, x2 - x1),
            "height": max(1, y2 - y1),
        }

    def reset(self):
        if self._rect_id:
            self.canvas.delete(self._rect_id)
            self._rect_id = None
        self._start = None
        self._end   = None
        self.save_btn.config(state="disabled")
        self.info_label.config(text=f"Selecione a área para: {self.target_key}", fg="#dddddd")

    def confirm_save(self):
        if self._start is None or self._end is None:
            messagebox.showwarning("Atenção", "Nenhuma região selecionada ainda.")
            return
        if self._start == self._end:
            messagebox.showwarning("Atenção", "A seleção está vazia (ponto único).")
            return

        roi = self._compute_roi()
        save_config(self.target_key, roi, self.screenshot_pil)
        messagebox.showinfo("ROI Salva!", f"Região {self.target_key} salva com sucesso!")
        self.destroy()


class ModernButton(tk.Button):
    def __init__(self, parent, text, command, width=35):
        super().__init__(
            parent, text=text, command=command, width=width,
            font=("Segoe UI", 10, "bold"), bg="#222222", fg="#FFFFFF",
            activebackground="#333333", activeforeground="#FFFFFF",
            relief="flat", bd=0, pady=12, cursor="hand2"
        )
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self.config(bg="#333333")

    def on_leave(self, e):
        self.config(bg="#222222")


class MainMenu(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Star Fishing Setup")
        self.geometry("400x380")
        self.configure(bg="#0F0F0F")
        self.resizable(False, False)
        
        container = tk.Frame(self, bg="#0F0F0F")
        container.pack(expand=True, fill="both", padx=30, pady=30)

        lbl_title = tk.Label(
            container, text="CONFIGURAÇÃO DE VISÃO", 
            font=("Segoe UI", 14, "bold"), bg="#0F0F0F", fg="#FFFFFF"
        )
        lbl_title.pack(pady=(0, 5))

        lbl_sub = tk.Label(
            container, text="Mapeie os elementos na tela do jogo", 
            font=("Segoe UI", 9), bg="#0F0F0F", fg="#888888"
        )
        lbl_sub.pack(pady=(0, 30))

        ModernButton(
            container, text="BARRA DE PESCA", 
            command=lambda: self.start_capture("roi")
        ).pack(fill="x", pady=6)

        ModernButton(
            container, text="ALERTA 'INVENTORY FULL'", 
            command=lambda: self.start_capture("inventory_roi")
        ).pack(fill="x", pady=6)

        ModernButton(
            container, text="BOTÃO 'SELL ALL'", 
            command=lambda: self.start_capture("sell_button_roi")
        ).pack(fill="x", pady=6)
        
        lbl_hint = tk.Label(
            container, text="Você terá 2 segundos para focar no jogo\nantes da captura de tela.", 
            font=("Segoe UI", 8), bg="#0F0F0F", fg="#555555"
        )
        lbl_hint.pack(side="bottom", pady=(20, 0))

    def start_capture(self, target_key):
        self.withdraw()
        print(f"\n[Atenção] Focando no jogo em 2 segundos para capturar '{target_key}'...")
        time.sleep(2)
        print("Capturando tela...")
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            raw = sct.grab(monitor)
            screenshot = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
            
        selector = ROISelector(self, screenshot, target_key)
        self.wait_window(selector)
        self.deiconify()


if __name__ == "__main__":
    app = MainMenu()
    app.mainloop()

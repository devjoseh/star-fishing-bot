"""
roi_selector.py — Ferramenta visual para configurar a região da barra de pesca.

Uso:
    python roi_selector.py

Instruções:
    1. Uma captura da tela inteira será exibida em uma janela.
    2. Clique e arraste para selecionar a região onde a barra de pesca aparece.
    3. Clique em "Salvar ROI" (ou pressione S) para confirmar.
    4. Pressione R para resetar a seleção, ou feche a janela para cancelar.
"""

import tkinter as tk
from tkinter import messagebox
import json
import os
import sys

try:
    import mss
    import mss.tools
    from PIL import Image, ImageTk
except ImportError as e:
    print(f"Dependência faltando: {e}")
    print("Execute: pip install -r requirements.txt")
    sys.exit(1)

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

# Resolução máxima de exibição (escalonado para caber na tela)
MAX_DISPLAY_W = 1400
MAX_DISPLAY_H = 850


# ---------------------------------------------------------------------------
# Utilitários de config
# ---------------------------------------------------------------------------

def load_existing_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_roi(roi):
    config = load_existing_config()
    config["roi"] = roi
    config.setdefault("hold_time",       0.75)
    config.setdefault("start_key",       "F6")
    config.setdefault("stop_key",        "F7")
    config.setdefault("green_threshold", 10)
    config.setdefault("poll_interval",   0.05)

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

    print(f"\n✅  ROI salva em {CONFIG_FILE}:")
    print(f"    x={roi['x']}, y={roi['y']}, width={roi['width']}, height={roi['height']}")


# ---------------------------------------------------------------------------
# App Tkinter
# ---------------------------------------------------------------------------

class ROISelector(tk.Tk):
    def __init__(self, screenshot_pil):
        super().__init__()

        self.title("Star Fishing — Selecione a região da barra de pesca")
        self.resizable(False, False)

        # Calcula escala
        orig_w, orig_h = screenshot_pil.size
        scale = min(MAX_DISPLAY_W / orig_w, MAX_DISPLAY_H / orig_h, 1.0)
        self.scale = scale
        disp_w = int(orig_w * scale)
        disp_h = int(orig_h * scale)

        # Redimensiona imagem para exibição
        display_img = screenshot_pil.resize((disp_w, disp_h), Image.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(display_img)

        # Canvas
        self.canvas = tk.Canvas(self, width=disp_w, height=disp_h, cursor="crosshair")
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

        # Barra de rodapé
        footer = tk.Frame(self, bg="#1e1e1e")
        footer.pack(fill="x")

        self.info_label = tk.Label(
            footer, text="Clique e arraste para selecionar a região",
            bg="#1e1e1e", fg="#dddddd", font=("Consolas", 10), padx=10
        )
        self.info_label.pack(side="left", pady=6)

        btn_frame = tk.Frame(footer, bg="#1e1e1e")
        btn_frame.pack(side="right", padx=8, pady=4)

        tk.Button(
            btn_frame, text="↺ Resetar (R)", command=self.reset,
            bg="#555", fg="white", relief="flat", padx=8
        ).pack(side="left", padx=4)

        self.save_btn = tk.Button(
            btn_frame, text="💾 Salvar ROI (S)", command=self.confirm_save,
            bg="#1f6aa5", fg="white", relief="flat", padx=8,
            state="disabled"
        )
        self.save_btn.pack(side="left", padx=4)

        # Estado de seleção
        self._rect_id   = None
        self._start     = None
        self._end       = None
        self.roi_saved  = False

        # Eventos de mouse
        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        # Atalhos de teclado
        self.bind("<KeyPress-s>", lambda e: self.confirm_save())
        self.bind("<KeyPress-S>", lambda e: self.confirm_save())
        self.bind("<KeyPress-r>", lambda e: self.reset())
        self.bind("<KeyPress-R>", lambda e: self.reset())
        self.bind("<Return>",     lambda e: self.confirm_save())

        # Centraliza na tela
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        wx = (sw - self.winfo_width()) // 2
        wy = max(0, (sh - self.winfo_height()) // 2)
        self.geometry(f"+{wx}+{wy}")

    # ------------------------------------------------------------------
    # Eventos de mouse
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------

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
        self.info_label.config(text="Clique e arraste para selecionar a região", fg="#dddddd")

    def confirm_save(self):
        if self._start is None or self._end is None:
            messagebox.showwarning("Atenção", "Nenhuma região selecionada ainda.")
            return
        if self._start == self._end:
            messagebox.showwarning("Atenção", "A seleção está vazia (ponto único).")
            return

        roi = self._compute_roi()
        save_roi(roi)
        self.roi_saved = True
        messagebox.showinfo(
            "ROI Salva!",
            f"Região salva com sucesso!\n\n"
            f"x={roi['x']}, y={roi['y']}\n"
            f"w={roi['width']}, h={roi['height']}\n\n"
            f"Agora execute: python main.py"
        )
        self.destroy()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 55)
    print("  Star Fishing — Seletor de Região (ROI Selector)")
    print("=" * 55)
    print("Capturando tela...")

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        raw = sct.grab(monitor)
        screenshot = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

    print("Abrindo seletor visual...")
    app = ROISelector(screenshot)
    app.mainloop()

    if app.roi_saved:
        print("\nPronto! Execute agora:  python main.py")
    else:
        print("Cancelado. ROI não salva.")


if __name__ == "__main__":
    main()

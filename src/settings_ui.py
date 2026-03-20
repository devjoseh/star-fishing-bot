import tkinter as tk
from tkinter import messagebox
import json
import os

class ModernButton(tk.Button):
    def __init__(self, parent, text, command, width=35, bg="#222222"):
        super().__init__(
            parent, text=text, command=command, width=width,
            font=("Segoe UI", 10, "bold"), bg=bg, fg="#FFFFFF",
            activebackground="#333333", activeforeground="#FFFFFF",
            relief="flat", bd=0, pady=12, cursor="hand2"
        )
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        if self.cget("bg") == "#222222":
            self.config(bg="#333333")

    def on_leave(self, e):
        if self.cget("bg") == "#333333":
            self.config(bg="#222222")


class ModernEntry(tk.Frame):
    def __init__(self, parent, label_text, default_value, on_change=None):
        super().__init__(parent, bg="#1A1A1A")
        lbl = tk.Label(self, text=label_text, bg="#1A1A1A", fg="#AAAAAA", font=("Segoe UI", 9))
        lbl.pack(anchor="w", pady=(0, 2))
        
        self.entry = tk.Entry(
            self, bg="#222222", fg="#FFFFFF", insertbackground="#FFFFFF",
            relief="flat", font=("Segoe UI", 10), highlightthickness=1, 
            highlightbackground="#333333", highlightcolor="#0066CC"
        )
        self.entry.pack(fill="x", ipady=4, padx=1)
        self.entry.insert(0, str(default_value))
        
        if on_change:
            self.entry.bind("<KeyRelease>", lambda e: on_change())

    def get(self):
        return self.entry.get()

class ModernToggle(tk.Frame):
    def __init__(self, parent, label_text, default_state, on_change=None):
        super().__init__(parent, bg="#1A1A1A")
        self.state = default_state
        self.on_change = on_change
        
        lbl = tk.Label(self, text=label_text, bg="#1A1A1A", fg="#AAAAAA", font=("Segoe UI", 9))
        lbl.pack(side="left", padx=(0, 10))
        
        self.btn = tk.Button(
            self, text="ON" if self.state else "OFF",
            bg="#00FF88" if self.state else "#333333",
            fg="#000000" if self.state else "#FFFFFF",
            activebackground="#00CC66" if self.state else "#444444",
            activeforeground="#000000" if self.state else "#FFFFFF",
            relief="flat", bd=0, font=("Segoe UI", 9, "bold"), width=6, cursor="hand2",
            command=self.toggle
        )
        self.btn.pack(side="right")

    def toggle(self):
        self.state = not self.state
        if self.state:
            self.btn.config(text="ON", bg="#00FF88", fg="#000000", activebackground="#00CC66", activeforeground="#000000")
        else:
            self.btn.config(text="OFF", bg="#333333", fg="#FFFFFF", activebackground="#444444", activeforeground="#FFFFFF")
        
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
        
        # Center dialog relative to parent
        self.geometry("+{}+{}".format(
            parent.winfo_x() + 150,
            parent.winfo_y() + 200
        ))
        
        top_frame = tk.Frame(self, bg="#F0F0F0")
        top_frame.pack(pady=(20, 15))
        
        # Left action box (similar to "Click / Stop")
        lbl_action = tk.Label(
            top_frame, text=action_name, bg="#FFFFFF", fg="#0033CC", 
            font=("Arial", 10), width=12, relief="groove", bd=2
        )
        lbl_action.pack(side="left", padx=(0, 10), ipady=4)
        
        # Right hotkey box (similar to "F8")
        self.lbl_key = tk.Label(
            top_frame, text=str(self.result).upper(), bg="#FFFFFF", fg="#000000", 
            font=("Arial", 12), width=8, relief="solid", bd=1
        )
        self.lbl_key.pack(side="left", ipady=4)
        
        btn_frame = tk.Frame(self, bg="#F0F0F0")
        btn_frame.pack()
        
        btn_ok = tk.Button(btn_frame, text="Ok", width=8, bg="#FFFFFF", relief="solid", bd=1, command=self.confirm)
        btn_ok.pack(side="left", padx=10)
        
        btn_cancel = tk.Button(btn_frame, text="Cancel", width=8, bg="#FFFFFF", relief="solid", bd=1, command=self.cancel)
        btn_cancel.pack(side="left", padx=10)
        
        # Capture keystrokes
        self.bind("<Key>", self.on_key)
        
        self.transient(parent)
        self.grab_set()
        
        # Force focus so key events are caught immediately
        self.focus_force()
        self.wait_window(self)
        
    def on_key(self, event):
        sym = event.keysym
        
        # Ignore standalone modifiers if preferred, but F-keys and letters pass
        if sym in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Caps_Lock", "Tab"):
            return
            
        # Normalize common keys
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
        super().__init__(parent, bg="#1A1A1A")
        self.action_name = action_name
        self.on_change = on_change
        self.current_key = default_value
        
        lbl = tk.Label(self, text=label_text, bg="#1A1A1A", fg="#AAAAAA", font=("Segoe UI", 9))
        lbl.pack(anchor="w", pady=(0, 2))
        
        self.btn = tk.Button(
            self, text=str(self.current_key).upper(), bg="#222222", fg="#00FF88",
            activebackground="#333333", activeforeground="#00FF88",
            relief="flat", font=("Segoe UI", 10, "bold"), bd=0, cursor="hand2",
            command=self.open_dialog
        )
        self.btn.pack(fill="x", ipady=4, padx=1)
        self.btn.bind("<Enter>", lambda e: self.btn.config(bg="#333333"))
        self.btn.bind("<Leave>", lambda e: self.btn.config(bg="#222222"))
        
    def open_dialog(self):
        dialog = HotkeyDialog(self.winfo_toplevel(), self.action_name, self.current_key)
        if dialog.result and dialog.result != self.current_key:
            self.current_key = dialog.result
            self.btn.config(text=str(self.current_key).upper())
            if self.on_change:
                self.on_change()
                
    def get(self):
        return self.current_key


class SettingsApp(tk.Tk):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.title("Star Fishing — Control Panel")
        self.geometry("660x700")
        self.configure(bg="#0F0F0F")
        self.resizable(False, False)
        
        lbl_title = tk.Label(self, text="PAINEL DE CONTROLE", font=("Segoe UI", 14, "bold"), bg="#0F0F0F", fg="#FFFFFF")
        lbl_title.pack(pady=(25, 5))
        
        lbl_sub = tk.Label(self, text="O bot (F6/F7) roda normalmente enquanto esta janela estiver aberta.", font=("Segoe UI", 9), bg="#0F0F0F", fg="#888888")
        lbl_sub.pack(pady=(0, 15))
        
        main_frame = tk.Frame(self, bg="#0F0F0F")
        main_frame.pack(fill="both", expand=True, padx=20)
        
        left_col = tk.Frame(main_frame, bg="#0F0F0F")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 8))
        
        right_col = tk.Frame(main_frame, bg="#0F0F0F")
        right_col.pack(side="right", fill="both", expand=True, padx=(8, 0))
        
        c = self.bot.config
        
        def auto_save():
            self.save_settings(silent=True)
            
        # --- LEFT COLUMN ---
        card_keys = tk.Frame(left_col, bg="#1A1A1A", padx=15, pady=15)
        card_keys.pack(fill="x", pady=(0, 15))
        tk.Label(card_keys, text="TECLAS DE ATALHO", font=("Segoe UI", 10, "bold"), bg="#1A1A1A", fg="#FFFFFF").pack(anchor="w", pady=(0, 10))
        
        self.start_key = ModernHotkeyButton(card_keys, "Start / Stop", "Start Key", c.get("start_key", "F6"), auto_save)
        self.start_key.pack(fill="x", pady=4)
        self.stop_key = ModernHotkeyButton(card_keys, "Stop Forced", "Stop Key", c.get("stop_key", "F7"), auto_save)
        self.stop_key.pack(fill="x", pady=4)
        self.toggle_key = ModernHotkeyButton(card_keys, "Smart Pause", "Smart Pause Toggle", c.get("toggle_pause_key", "F8"), auto_save)
        self.toggle_key.pack(fill="x", pady=4)
        
        card_times = tk.Frame(left_col, bg="#1A1A1A", padx=15, pady=15)
        card_times.pack(fill="x")
        tk.Label(card_times, text="TEMPOS & DELAYS", font=("Segoe UI", 10, "bold"), bg="#1A1A1A", fg="#FFFFFF").pack(anchor="w", pady=(0, 10))
        
        self.hold_time = ModernEntry(card_times, "Hold Time (seg)", c.get("hold_time", 0.58), auto_save)
        self.hold_time.pack(fill="x", pady=4)
        self.post_cast = ModernEntry(card_times, "Atraso Pós-Arremesso", c.get("post_cast_delay", 0.1), auto_save)
        self.post_cast.pack(fill="x", pady=4)
        
        # --- RIGHT COLUMN ---
        card_pause = tk.Frame(right_col, bg="#1A1A1A", padx=15, pady=15)
        card_pause.pack(fill="x", pady=(0, 15))
        tk.Label(card_pause, text="SMART PAUSE (ANTI-AFK)", font=("Segoe UI", 10, "bold"), bg="#1A1A1A", fg="#FFFFFF").pack(anchor="w", pady=(0, 10))
        
        self.pause_enabled = ModernToggle(card_pause, "Ativar Smart Pause", c.get("inactive_pause_enabled", False), auto_save)
        self.pause_enabled.pack(fill="x", pady=4)
        
        self.pause_triggers = ModernEntry(card_pause, "Arremessos p/ Pausar", c.get("inactive_pause_triggers", 4), auto_save)
        self.pause_triggers.pack(fill="x", pady=4)
        self.pause_duration = ModernEntry(card_pause, "Duração Pausa (min)", c.get("inactive_pause_duration", 15.0), auto_save)
        self.pause_duration.pack(fill="x", pady=4)
        self.pause_thresh = ModernEntry(card_pause, "Tempo Spam (seg)", c.get("inactive_cast_time_threshold", 5.0), auto_save)
        self.pause_thresh.pack(fill="x", pady=4)
        
        card_adv = tk.Frame(right_col, bg="#1A1A1A", padx=15, pady=15)
        card_adv.pack(fill="x")
        tk.Label(card_adv, text="DETECÇÃO", font=("Segoe UI", 10, "bold"), bg="#1A1A1A", fg="#FFFFFF").pack(anchor="w", pady=(0, 10))
        
        self.green_thresh = ModernEntry(card_adv, "Min Pixels Verdes", c.get("green_threshold", 10), auto_save)
        self.green_thresh.pack(fill="x", pady=4)
        self.poll_interval = ModernEntry(card_adv, "Poll Interval (seg)", c.get("poll_interval", 0.1), auto_save)
        self.poll_interval.pack(fill="x", pady=4)
        
        # --- FOOTER ---
        footer = tk.Frame(self, bg="#0F0F0F")
        footer.pack(fill="x", side="bottom", pady=25)
        
        self.save_status = tk.Label(footer, text="Modifique qualquer campo e salvo automaticamente", font=("Segoe UI", 8), bg="#0F0F0F", fg="#444444")
        self.save_status.pack(pady=(0, 10))
        
        save_btn = ModernButton(footer, text="SALVAR / FECHAR JANELA", command=self.destroy, width=30, bg="#0066CC")
        save_btn.bind("<Enter>", lambda e: save_btn.config(bg="#0088FF"))
        save_btn.bind("<Leave>", lambda e: save_btn.config(bg="#0066CC"))
        save_btn.pack(ipadx=20)

    def save_settings(self, silent=False):
        try:
            c = self.bot.config
            
            new_start = str(self.start_key.get()).strip()
            new_stop = str(self.stop_key.get()).strip()
            new_toggle = str(self.toggle_key.get()).strip()
            
            if not new_start or not new_stop or not new_toggle:
                if not silent: messagebox.showwarning("Atenção", "As teclas de atalho não podem vazias.", parent=self)
                return
            
            c.config["start_key"] = new_start
            c.config["stop_key"] = new_stop
            c.config["toggle_pause_key"] = new_toggle
            
            c.config["hold_time"] = float(self.hold_time.get())
            c.config["post_cast_delay"] = float(self.post_cast.get())
            
            c.config["inactive_pause_enabled"] = bool(self.pause_enabled.get())
            c.config["inactive_pause_triggers"] = int(self.pause_triggers.get())
            c.config["inactive_pause_duration"] = float(self.pause_duration.get())
            c.config["inactive_cast_time_threshold"] = float(self.pause_thresh.get())
            
            c.config["green_threshold"] = int(self.green_thresh.get())
            c.config["poll_interval"] = float(self.poll_interval.get())
            
            # Save the JSON once
            c.save()
            
            # Recarrega hotkeys no bot ao vivo
            self.bot.inputs.set_keys(new_start, new_stop, new_toggle)
            
            self.save_status.config(text="✓ Salvo com sucesso!", fg="#00FF88")
            self.after(2000, lambda: self.save_status.config(text="", fg="#0F0F0F"))
                
            if not silent:
                messagebox.showinfo("Sucesso", "Configurações salvas. Janela pode ser fechada com segurança!", parent=self)
        except ValueError as e:
            if not silent:
                messagebox.showerror("Erro de Valor", f"Certifique-se de digitar números válidos.\nErro: {e}", parent=self)

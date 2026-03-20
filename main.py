"""
main.py — Entry point do Star Fishing Bot

Uso:
    python main.py

Controles padrão (editáveis em config.json):
    F6  →  Iniciar o loop de pesca
    F7  →  Parar o loop de pesca
    Ctrl+C  →  Encerrar o script
"""

import sys
import os
import time
import ctypes

# Evita problemas de escalonamento (DPI scaling) do Windows 
# fazendo o pydirectinput clicar na coordenada física correta
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Garante que src/ seja encontrado independente de onde o script é chamado
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from automator import FishingAutomator
from settings_ui import SettingsApp


BANNER = r"""
  _____ _              _____ _     _     _
 / ____| |            |  ___(_)   | |   (_)
| (___ | |_ __ _ _ __  | |_  _ ___| |__  _ _ __   __ _
 \___ \| __/ _` | '__| |  _|| / __| '_ \| | '_ \ / _` |
 ____) | || (_| | |    | |  | \__ \ | | | | | | | (_| |
|_____/ \__\__,_|_|    \_|  |_|___/_| |_|_|_| |_|\__, |
                                                   __/ |
                    Auto Fishing Bot              |___/
"""


def main():
    print(BANNER)
    print("=" * 55)

    bot = FishingAutomator()

    start_key = bot.config.get("start_key", "F6")
    stop_key  = bot.config.get("stop_key",  "F7")

    if not bot.config.has_roi():
        print("  ⚠️  ROI não configurada!")
        print("  Execute primeiro:  python roi_selector.py")
        print("=" * 55)
    else:
        roi = bot.config.get("roi")
        hold = bot.config.get("hold_time", 0.75)
        print(f"  ROI configurada   → x={roi['x']}, y={roi['y']}, "
              f"w={roi['width']}, h={roi['height']}")
        print(f"  Hold time         → {hold}s")

    print(f"\n  [ {start_key} ]  Iniciar pesca")
    print(f"  [ {stop_key} ]  Parar pesca")
    print(f"  [ {bot.config.get('toggle_pause_key', 'F8')} ]  Ligar/Desligar Smart Pause")
    print(f"  [ Ctrl+C ]  Sair via terminal")
    print("=" * 55)
    print()

    bot.start_hotkey_listener()
    print("[Main] Painel de Controle Iniciado. Pressione as hotkeys a qualquer momento.")
    print("[Main] Feche a aba do Painel de Controle para desligar o bot por completo.")

    try:
        app = SettingsApp(bot)
        app.mainloop()
    except KeyboardInterrupt:
        print("\n[Main] Encerrando...")
    finally:
        bot.stop()
        bot.stop_hotkey_listener()
        print("[Main] Até logo!")


if __name__ == "__main__":
    main()

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
from i18n import set_language, t


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
    set_language(bot.config.get("language", "pt"))

    start_key = bot.config.get("start_key", "F6")
    stop_key  = bot.config.get("stop_key",  "F7")

    if not bot.config.has_roi():
        print(t("main_no_roi"))
        print(t("main_run_roi"))
        print("=" * 55)
    else:
        roi = bot.config.get("roi")
        hold = bot.config.get("hold_time", 0.75)
        print(f"{t('main_roi_configured')}   → x={roi['x']}, y={roi['y']}, "
              f"w={roi['width']}, h={roi['height']}")
        print(f"{t('main_hold_time')}         → {hold}s")

    print(f"\n{t('main_start_fishing', start_key=start_key)}")
    print(t("main_stop_fishing", stop_key=stop_key))
    print(t("main_toggle_pause", toggle_pause_key=bot.config.get('toggle_pause_key', 'F8')))
    print(t("main_exit"))
    print("=" * 55)
    print()

    bot.start_hotkey_listener()
    print(t("main_panel_started"))
    print(t("main_panel_hint"))

    bot.wants_restart = False
    try:
        while True:
            app = SettingsApp(bot)
            app.mainloop()
            if not getattr(bot, "wants_restart", False):
                break
            bot.wants_restart = False
    except KeyboardInterrupt:
        print(t("main_shutting_down"))
    finally:
        bot.stop()
        bot.stop_hotkey_listener()
        print(t("main_goodbye"))


if __name__ == "__main__":
    main()

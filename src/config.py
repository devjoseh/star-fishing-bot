import json
import os
import sys


def _base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


CONFIG_FILE = os.path.join(_base_dir(), "config.json")

DEFAULT_CONFIG = {
    "roi": None,          # Definido pelo roi_selector.py
    "inventory_roi": None, # ROI para a mensagem de inventário cheio
    "sell_button_roi": None, # ROI para o botão Sell All
    "hold_time": 0.58,    # Tempo de pressionar o mouse (segundos)
    "start_key": "F6",    # Tecla para iniciar o loop
    "stop_key": "F7",     # Tecla para parar o loop
    "green_threshold": 10, # Mínimo de pixels verdes para detectar barra em repouso
    "poll_interval": 0.1,  # Intervalo de verificação em segundos
    "post_cast_delay": 0.1, # Atraso após o lançamento
    "inactive_pause_enabled": False,     # Ativar cooldown em áreas inativas
    "inactive_pause_triggers": 5,        # Arremessos rápidos consecutivos para ativar a pausa
    "inactive_pause_duration": 1,     # Duração da pausa em minutos
    "inactive_cast_time_threshold": 6.0, # Segundos máximos para ser considerado 'rápido/spammado'
    "auto_sell_enabled": True            # Vender automaticamente ao detectar inventário cheio
}


class ConfigManager:
    def __init__(self):
        self.config = dict(DEFAULT_CONFIG)
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    # Merge: mantém defaults para chaves não presentes
                    for key, value in data.items():
                        self.config[key] = value
                print(f"[Config] Configuração carregada de: {CONFIG_FILE}")
            except Exception as e:
                print(f"[Config] Erro ao carregar config: {e} — usando padrões.")
        else:
            print("[Config] config.json não encontrado. Execute roi_selector.py primeiro.")
            self.save()

    def save(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=4)
            print(f"[Config] Configuração salva em: {CONFIG_FILE}")
        except Exception as e:
            print(f"[Config] Erro ao salvar config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()

    def has_roi(self):
        return self.config.get("roi") is not None

import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

DEFAULT_CONFIG = {
    "roi": None,          # Definido pelo roi_selector.py
    "hold_time": 0.75,    # Tempo de pressionar o mouse (segundos)
    "start_key": "F6",    # Tecla para iniciar o loop
    "stop_key": "F7",     # Tecla para parar o loop
    "green_threshold": 10, # Mínimo de pixels verdes para detectar barra em repouso
    "poll_interval": 0.05  # Intervalo de verificação em segundos
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

import time
import pydirectinput
from pynput import keyboard


class InputHandler:
    """
    Gerencia:
    - Cast da isca (mouseDown + sleep + mouseUp)
    - Hotkeys de start/stop via pynput
    """

    def __init__(self):
        self._listener = None
        self._start_callback = None
        self._stop_callback = None
        self._start_key = None
        self._stop_key = None

    # ------------------------------------------------------------------
    # Cast
    # ------------------------------------------------------------------

    def cast_line(self, hold_time: float):
        """
        Executa o lançamento: pressiona o botão esquerdo, aguarda
        hold_time segundos e solta.
        """
        pydirectinput.mouseDown(button="left")
        time.sleep(hold_time)
        pydirectinput.mouseUp(button="left")

    # ------------------------------------------------------------------
    # Hotkeys
    # ------------------------------------------------------------------

    def set_callbacks(self, start_callback, stop_callback):
        self._start_callback = start_callback
        self._stop_callback = stop_callback

    def set_keys(self, start_key: str, stop_key: str):
        """Recebe strings como 'F6', 'F7', 'x', etc."""
        self._start_key = self._parse_key(start_key)
        self._stop_key  = self._parse_key(stop_key)

    @staticmethod
    def _parse_key(key_str: str):
        """Converte string para pynput Key ou char."""
        key_str = key_str.strip()
        # Tenta como Key especial (F1-F12, esc, space, etc.)
        if hasattr(keyboard.Key, key_str.lower()):
            return getattr(keyboard.Key, key_str.lower())
        # Teclas de função com capitalização (F6, F7...)
        lower = key_str.lower()
        for attr in dir(keyboard.Key):
            if attr.lower() == lower:
                return getattr(keyboard.Key, attr)
        # Caractere simples
        return keyboard.KeyCode.from_char(key_str)

    def start_listening(self):
        """Inicia o listener de teclado em background."""
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.daemon = True
        self._listener.start()

    def stop_listening(self):
        if self._listener:
            self._listener.stop()
            self._listener = None

    def _on_press(self, key):
        if self._start_key and key == self._start_key:
            if self._start_callback:
                self._start_callback()
        elif self._stop_key and key == self._stop_key:
            if self._stop_callback:
                self._stop_callback()

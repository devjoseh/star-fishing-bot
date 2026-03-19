import threading
import time
import random
import mss

from vision import VisionSystem
from inputs import InputHandler
from config import ConfigManager


class FishingAutomator:
    """
    Loop principal do bot de pesca.

    Fluxo correto:
        HOLDING_IDLE  →  (verde detectado)
             ↓
        [mouseUp]
             ↓
        CASTING  →  mouseDown por hold_time  →  mouseUp
             ↓
        HOLDING_IDLE  (mouseDown imediato, esperando próxima barrinha)
    """

    def __init__(self):
        self.config  = ConfigManager()
        self.vision  = VisionSystem(self.config)
        self.inputs  = InputHandler()

        self.running     = False
        self._stop_event = threading.Event()
        self._thread     = None

        # Hotkeys
        self.inputs.set_callbacks(self.start, self.stop)
        self.inputs.set_keys(
            self.config.get("start_key", "F6"),
            self.config.get("stop_key",  "F7"),
        )

    # ------------------------------------------------------------------
    # Controle externo
    # ------------------------------------------------------------------

    def start(self):
        if self.running:
            print("[Bot] Já está rodando.")
            return

        if not self.config.has_roi():
            print("[Bot] ❌  ROI não configurada! Execute roi_selector.py primeiro.")
            return

        print("[Bot] ▶  Iniciando loop de pesca...")
        self.running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        if not self.running:
            return
        print("[Bot] ⏹  Parando...")
        self._stop_event.set()
        # Garante que o mouse não fique preso segurado
        try:
            import pydirectinput
            pydirectinput.mouseUp(button="left")
        except Exception:
            pass
        self.running = False

    def start_hotkey_listener(self):
        self.inputs.start_listening()

    def stop_hotkey_listener(self):
        self.inputs.stop_listening()

    # ------------------------------------------------------------------
    # Loop principal
    # ------------------------------------------------------------------

    def _loop(self):
        import pydirectinput

        hold_time        = float(self.config.get("hold_time",        0.68))
        poll_interval    = float(self.config.get("poll_interval",    0.05))
        post_cast_delay  = float(self.config.get("post_cast_delay",  0.1))

        STATE_HOLDING_IDLE = "HOLDING_IDLE"   # mouse segurado, esperando a barra
        STATE_CASTING      = "CASTING"         # soltou + segurou pelo hold_time
        STATE_WAIT_GONE    = "WAIT_GONE"       # aguarda verde sumir antes de segurar de novo

        state = STATE_HOLDING_IDLE

        with mss.mss() as sct:

            # Inicia segurando o mouse imediatamente
            pydirectinput.mouseDown(button="left")
            ts = time.strftime("%H:%M:%S")
            print(f"[{ts}] 🖱  Mouse segurado — aguardando barra de pesca...")

            while not self._stop_event.is_set():

                # -----------------------------------------------------
                # HOLDING_IDLE: mouse pressionado, monitorando o verde
                # -----------------------------------------------------
                if state == STATE_HOLDING_IDLE:
                    frame = self.vision.capture_roi(sct)

                    if self.vision.is_bar_ready(frame):
                        # Verde detectado: solta o mouse
                        pydirectinput.mouseUp(button="left")
                        green_px = self.vision.count_green_pixels(frame)
                        ts = time.strftime("%H:%M:%S")
                        print(f"[{ts}] ✅  Barra detectada! ({green_px}px verdes) — Lançando...")
                        state = STATE_CASTING
                        continue  # age imediatamente, sem sleep

                # -----------------------------------------------------
                # CASTING: segura o mouse por hold_time e solta (lança)
                # -----------------------------------------------------
                elif state == STATE_CASTING:
                    pydirectinput.mouseDown(button="left")
                    # Aguarda hold_time respeitando stop_event
                    self._stop_event.wait(timeout=hold_time)

                    if self._stop_event.is_set():
                        pydirectinput.mouseUp(button="left")
                        break

                    pydirectinput.mouseUp(button="left")
                    ts = time.strftime("%H:%M:%S")
                    print(f"[{ts}] 🎣  Isca lançada! (hold={hold_time:.2f}s)")
                    state = STATE_WAIT_GONE

                # -----------------------------------------------------
                # WAIT_GONE: aguarda o verde desaparecer antes de
                #            segurar o mouse novamente
                # -----------------------------------------------------
                elif state == STATE_WAIT_GONE:
                    frame = self.vision.capture_roi(sct)
                    if not self.vision.is_bar_ready(frame):
                        # Verde sumiu — pequena pausa humana antes de segurar de novo
                        jitter = post_cast_delay * random.uniform(0.8, 1.2)
                        ts = time.strftime("%H:%M:%S")
                        print(f"[{ts}] ⏳  Aguardando {jitter:.2f}s antes de segurar...")
                        self._stop_event.wait(timeout=jitter)
                        if self._stop_event.is_set():
                            break
                        # Bota o mouse pra baixo e volta pro idle
                        pydirectinput.mouseDown(button="left")
                        ts = time.strftime("%H:%M:%S")
                        print(f"[{ts}] 🖱  Mouse segurado — aguardando próxima barra...")
                        state = STATE_HOLDING_IDLE

                time.sleep(poll_interval)

        # Garante soltura ao sair
        try:
            pydirectinput.mouseUp(button="left")
        except Exception:
            pass

        self.running = False
        print("[Bot] Loop encerrado.")

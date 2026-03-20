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
        self.inputs.set_callbacks(self.start, self.stop, self.toggle_smart_pause)
        self.inputs.set_keys(
            self.config.get("start_key", "F6"),
            self.config.get("stop_key",  "F7"),
            self.config.get("toggle_pause_key", "F8")
        )

    # ------------------------------------------------------------------
    # Controle externo
    # ------------------------------------------------------------------

    def toggle_smart_pause(self):
        current = self.config.get("inactive_pause_enabled", False)
        new_state = not current
        self.config.set("inactive_pause_enabled", new_state)
        state_str = "ATIVADO" if new_state else "DESATIVADO"
        print(f"\n[Bot] 🔄 Smart Pause foi {state_str} (Hotkey pressionada).")

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
        last_cast_time = 0.0
        consecutive_rapid_casts = 0

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
                    
                    frame = self.vision.capture_custom_roi(sct, "roi")

                    # O "sistema que já funciona": se houver uma quantia mínima de verde (>0)
                    # sabemos que a barrinha (que sempre tem um trecho verde fixo) 
                    # está de fato renderizada na tela, 
                    # significando que a isca não está na água!
                    is_bar_on_screen = self.vision.count_green_pixels(frame) > 0

                    # 1) Primeiro, verifica se o inventário está cheio E se a barra está visível (pesca não em andamento)
                    if self.vision.is_inventory_full(sct) and is_bar_on_screen:
                        ts = time.strftime("%H:%M:%S")
                        print(f"[{ts}] 🎒 Inventário Cheio detectado! Iniciando venda...")
                        
                        # Solta a vara antes de mexer no inventário
                        pydirectinput.mouseUp(button="left")
                        time.sleep(0.2)
                        
                        # Processo de venda
                        self.inputs.press_key('3')
                        time.sleep(1.2)  # Tempo pro menu abrir e renderizar
                        
                        sell_roi = self.config.get("sell_button_roi")
                        if sell_roi:
                            center_x = sell_roi["x"] + sell_roi["width"] // 2
                            # Leve ajuste para cima (ex: -10) ou para o centro exato. 
                            # Clicar numa estrela abaixo pode significar que o 'height' copiado incluiu a borda das estrelas
                            center_y = sell_roi["y"] + (sell_roi["height"] // 2) - 5
                            print(f"[{ts}] 💰 Movendo mouse e clicando em 'Sell All' (x={center_x}, y={center_y})")
                            self.inputs.click_at(center_x, center_y)
                        else:
                            print(f"[{ts}] ❌ ATENÇÃO: Botão Sell All não foi configurado.")
                            
                        time.sleep(0.5)
                        
                        # Volta pra vara
                        self.inputs.press_key('1')
                        time.sleep(1.5)  # Tempo pra o personagem puxar a vara de novo
                        
                        # Retorna a segurar a vara e ao estado idle
                        pydirectinput.mouseDown(button="left")
                        ts = time.strftime("%H:%M:%S")
                        print(f"[{ts}] 🖱  Mouse re-segurado — voltando a pescar...")
                        continue

                    # 2) Depois, verifica se a barra está pronta para fisgar/lançar (verde ultrapassou o threshold alto)
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
                    
                    # -------------------------------------------------
                    # Verificação de Smart Pause (Arremessos Rápidos)
                    # -------------------------------------------------
                    if self.config.get("inactive_pause_enabled", False):
                        current_time = time.time()
                        delta = current_time - last_cast_time
                        
                        threshold = self.config.get("inactive_cast_time_threshold", 5.0)
                        triggers  = self.config.get("inactive_pause_triggers", 4)
                        
                        if delta < threshold:
                            consecutive_rapid_casts += 1
                        else:
                            consecutive_rapid_casts = 0
                            
                        last_cast_time = current_time
                        
                        if consecutive_rapid_casts >= triggers:
                            ts = time.strftime("%H:%M:%S")
                            pause_mins = self.config.get("inactive_pause_duration", 15.0)
                            print(f"\n[{ts}] ⚠️  {triggers} arremessos muito rápidos ({delta:.1f}s) detectados!")
                            print(f"[{ts}] ⏸  Área de pesca parece estar *INATIVA*. Pausando robô por {pause_mins} minutos...\n")
                            
                            # O mouse já foi soltado acima, apenas garantimos a pausa do programa
                            pause_secs = pause_mins * 60
                            
                            while pause_secs > 0 and not self._stop_event.is_set():
                                wait_tick = min(60.0, pause_secs)
                                self._stop_event.wait(timeout=wait_tick)
                                pause_secs -= wait_tick
                                if pause_secs > 0 and not self._stop_event.is_set():
                                    print(f"   ⏳ Pausa inativa: restam {pause_secs/60:.1f} minutos para tentar novamente...")
                                    
                            if self._stop_event.is_set():
                                break
                            
                            ts = time.strftime("%H:%M:%S")
                            print(f"\n[{ts}] ▶  Pausa finalizada! Retomando pesca...")
                            consecutive_rapid_casts = 0
                            last_cast_time = time.time()
                            
                            pydirectinput.mouseDown(button="left")
                            state = STATE_HOLDING_IDLE
                            continue
                    
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

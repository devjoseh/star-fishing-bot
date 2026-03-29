import threading
import time
import random
import mss

from vision import VisionSystem
from inputs import InputHandler
from config import ConfigManager
from i18n import t


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

        # Hotkeys (Smart Pause é controlado via painel de configurações, não por hotkey)
        self.inputs.set_callbacks(self.start, self.stop)
        self.inputs.set_keys(
            self.config.get("start_key", "F6"),
            self.config.get("stop_key",  "F7"),
        )

    # ------------------------------------------------------------------
    # Controle externo
    # ------------------------------------------------------------------

    def toggle_smart_pause(self):
        current = self.config.get("inactive_pause_enabled", False)
        new_state = not current
        self.config.set("inactive_pause_enabled", new_state)
        state_str = t("bot_smart_pause_enabled") if new_state else t("bot_smart_pause_disabled")
        print(t("bot_pause_toggled", state=state_str))

    def start(self):
        if self.running:
            print(t("bot_already_running"))
            return

        if not self.config.has_roi():
            print(t("bot_no_roi"))
            return

        print(t("bot_start_loop"))
        self.running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        if not self.running:
            return
        print(t("bot_stopping"))
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
        cast_timestamps = []   # sliding window of recent cast times

        with mss.mss() as sct:

            # Inicia segurando o mouse imediatamente
            pydirectinput.mouseDown(button="left")
            ts = time.strftime("%H:%M:%S")
            print(f"[{ts}] {t('bot_mouse_held')}")

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
                    if self.config.get("auto_sell_enabled", True) and self.vision.is_inventory_full(sct) and is_bar_on_screen:
                        ts = time.strftime("%H:%M:%S")
                        print(f"[{ts}] {t('bot_inv_full')}")

                        # Solta a vara antes de mexer no inventário
                        pydirectinput.mouseUp(button="left")
                        time.sleep(0.2)

                        sell_roi = self.config.get("sell_button_roi")

                        # FIX 1: Move o mouse para a área do botão ANTES de pressionar '3'.
                        # Isso garante que a janela do Roblox mantém o foco e recebe a tecla.
                        if sell_roi:
                            focus_x = sell_roi["x"] + sell_roi["width"] // 2
                            focus_y = sell_roi["y"] + sell_roi["height"] // 2
                            pydirectinput.moveTo(focus_x, focus_y)
                            time.sleep(0.1)

                        # Abre o inventário (Backpack)
                        self.inputs.press_key('3')

                        # FIX 2: Delay maior para garantir que o inventário abre e renderiza completamente
                        time.sleep(1.5)

                        if sell_roi:
                            center_x = sell_roi["x"] + sell_roi["width"] // 2
                            # FIX 3: Clica no quarto superior do botão, bem longe das estrelas abaixo.
                            # height//4 garante que o clique nunca alcance as estrelas dos cards.
                            center_y = sell_roi["y"] + sell_roi["height"] // 4
                            print(f"[{ts}] {t('bot_clicking_sell', x=center_x, y=center_y)}")
                            self.inputs.click_at_precise(center_x, center_y)
                        else:
                            print(f"[{ts}] {t('bot_sell_not_config')}")

                        # FIX 4: Delay maior após o clique — aguarda a transação processar
                        # e o inventário fechar a animação antes de trocar de item
                        time.sleep(1.2)

                        # Volta pra vara
                        self.inputs.press_key('1')

                        # FIX 4 (cont.): Delay maior para a animação de equip completar.
                        # 1.5s era insuficiente — o mouseDown chegava antes da vara estar equipada.
                        time.sleep(2.0)

                        # Retorna a segurar a vara e ao estado idle
                        pydirectinput.mouseDown(button="left")
                        ts = time.strftime("%H:%M:%S")
                        print(f"[{ts}] {t('bot_mouse_reheld')}")
                        continue

                    # 2) Depois, verifica se a barra está pronta para fisgar/lançar (verde ultrapassou o threshold alto)
                    if self.vision.is_bar_ready(frame):
                        # Verde detectado: solta o mouse
                        pydirectinput.mouseUp(button="left")
                        green_px = self.vision.count_green_pixels(frame)
                        ts = time.strftime("%H:%M:%S")
                        print(f"[{ts}] {t('bot_bar_detected', green=green_px)}")
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
                    print(f"[{ts}] {t('bot_cast_done', hold=f'{hold_time:.2f}')}")
                    
                    # -------------------------------------------------
                    # Verificação de Smart Pause — janela deslizante
                    # Dispara SOMENTE se os últimos N arremessos
                    # ocorreram todos dentro da janela mínima configurada.
                    # Isso é impossível durante a pesca normal, mas 
                    # garantido quando não há peixes (spam).
                    # -------------------------------------------------
                    if self.config.get("inactive_pause_enabled", False):
                        current_time = time.time()
                        triggers  = self.config.get("inactive_pause_triggers", 4)
                        min_window = self.config.get("inactive_cast_time_threshold", 5.0)

                        # Adiciona timestamp atual e mantém só os últimos N
                        cast_timestamps.append(current_time)
                        if len(cast_timestamps) > triggers:
                            cast_timestamps.pop(0)

                        # Só avalia quando a janela está cheia
                        if len(cast_timestamps) == triggers:
                            window = cast_timestamps[-1] - cast_timestamps[0]

                            if window <= min_window:
                                ts = time.strftime("%H:%M:%S")
                                pause_mins = self.config.get("inactive_pause_duration", 15.0)
                                print(f"\n[{ts}] {t('bot_rapid_detect', triggers=triggers, delta=f'{window:.1f}')}")
                                print(f"[{ts}] {t('bot_inactive_area', mins=pause_mins)}\n")

                                # O mouse já foi soltado acima
                                pause_secs = pause_mins * 60

                                while pause_secs > 0 and not self._stop_event.is_set():
                                    wait_tick = min(60.0, pause_secs)
                                    self._stop_event.wait(timeout=wait_tick)
                                    pause_secs -= wait_tick
                                    if pause_secs > 0 and not self._stop_event.is_set():
                                        print(t("bot_pause_remaining", mins=f"{pause_secs/60:.1f}"))

                                if self._stop_event.is_set():
                                    break

                                ts = time.strftime("%H:%M:%S")
                                print(f"\n[{ts}] {t('bot_pause_finished')}")
                                cast_timestamps.clear()   # reseta a janela após a pausa

                                pydirectinput.mouseDown(button="left")
                                state = STATE_HOLDING_IDLE
                                continue
                    
                    wait_gone_start_time = time.time()
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
                        print(f"[{ts}] {t('bot_waiting_jitter', jitter=f'{jitter:.2f}')}")
                        self._stop_event.wait(timeout=jitter)
                        if self._stop_event.is_set():
                            break
                        # Bota o mouse pra baixo e volta pro idle
                        pydirectinput.mouseDown(button="left")
                        ts = time.strftime("%H:%M:%S")
                        print(f"[{ts}] {t('bot_mouse_held_next')}")
                        state = STATE_HOLDING_IDLE
                    elif time.time() - wait_gone_start_time > 5.0:
                        ts = time.strftime("%H:%M:%S")
                        print(f"[{ts}] {t('bot_wait_gone_timeout', time='5.0')}")
                        pydirectinput.mouseDown(button="left")
                        state = STATE_HOLDING_IDLE

                time.sleep(poll_interval)

        # Garante soltura ao sair
        try:
            pydirectinput.mouseUp(button="left")
        except Exception:
            pass

        self.running = False
        print(t("bot_loop_ended"))

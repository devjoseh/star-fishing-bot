import cv2
import numpy as np
import mss


class VisionSystem:
    """
    Captura a ROI configurada e detecta se a barra de pesca está
    em estado de 'repouso' (parte verde visível no topo da barra).
    """

    def __init__(self, config):
        self.config = config

        # Faixa de verde (HSV) — compatível com a cor verde da barra
        # H: 35–85 cobre desde verde-amarelado até verde puro
        self.green_lower = np.array([35, 60, 60])
        self.green_upper = np.array([85, 255, 255])

    def _get_mss_roi(self):
        """Converte a ROI do config para o formato do mss."""
        roi = self.config.get("roi")
        if not roi:
            return None
        return {
            "left":   roi["x"],
            "top":    roi["y"],
            "width":  roi["width"],
            "height": roi["height"],
        }

    def capture_roi(self, sct):
        """
        Captura a região de interesse da tela.
        Retorna um frame BGR ou None se a ROI não estiver configurada.
        """
        mss_roi = self._get_mss_roi()
        if mss_roi is None:
            return None
        img = np.array(sct.grab(mss_roi))
        return img[:, :, :3]  # Remove canal alpha (BGR)

    def is_bar_ready(self, frame):
        """
        Retorna True se a barra estiver em estado de 'repouso'
        (presença de pixels verdes suficientes na ROI).
        """
        if frame is None:
            return False

        threshold = self.config.get("green_threshold", 10)

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        green_mask = cv2.inRange(hsv, self.green_lower, self.green_upper)
        green_pixel_count = cv2.countNonZero(green_mask)

        return green_pixel_count >= threshold

    def count_green_pixels(self, frame):
        """Utilitário de debug: retorna a contagem de pixels verdes."""
        if frame is None:
            return 0
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        green_mask = cv2.inRange(hsv, self.green_lower, self.green_upper)
        return cv2.countNonZero(green_mask)

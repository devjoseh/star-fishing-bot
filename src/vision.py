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

        # Templates
        self.inv_template_edge = None
        self._load_templates()

    def _load_templates(self):
        import os
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        
        # Carrega Inventory Full
        inv_path = os.path.join(assets_dir, "inv_full_template.png")
        if os.path.exists(inv_path):
            img = cv2.imread(inv_path, cv2.IMREAD_COLOR)
            if img is not None:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                self.inv_template_edge = cv2.Canny(gray, 50, 200)

    def reload_config(self):
        """Pode ser chamado para recarregar o template, se necessário."""
        self._load_templates()

    def _get_mss_roi(self, key="roi"):
        """Converte a ROI do config para o formato do mss."""
        roi = self.config.get(key)

        if not roi:
            return None
        return {
            "left":   roi["x"],
            "top":    roi["y"],
            "width":  roi["width"],
            "height": roi["height"],
        }

    def capture_custom_roi(self, sct, key="roi"):
        """
        Captura uma região específica usando a chave de configuração.
        """
        mss_roi = self._get_mss_roi(key)
        if mss_roi is None:
            return None
        img = np.array(sct.grab(mss_roi))
        return img[:, :, :3]  # Remove canal alpha (BGR)

    def capture_roi(self, sct):
        """Mantido para compatibilidade, captura a ROI principal (barra)."""
        return self.capture_custom_roi(sct, "roi")

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

    def is_inventory_full(self, sct):
        """
        Verifica se a mensagem de inventário cheio está na tela
        usando Template Matching nas bordas da imagem para ignorar fundo dinâmico.
        """
        if self.inv_template_edge is None:
            return False

        frame = self.capture_custom_roi(sct, "inventory_roi")
        if frame is None:
            return False

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edge_frame = cv2.Canny(gray, 50, 200)

        # Template Matching nas bordas
        res = cv2.matchTemplate(edge_frame, self.inv_template_edge, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)

        # 0.4 de confiança nas bordas é bem alto, já que bordas são muito esparsas
        return max_val > 0.4

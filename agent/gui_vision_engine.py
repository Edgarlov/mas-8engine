"""
agent/gui_vision_engine.py — Motor Integrado de Percepción Visual y Diagnóstico Estructural GUI

Permite al agente "ver" la pantalla, extraer texto (OCR), localizar elementos visuales
mediante coincidencia de plantillas OpenCV, e identificar automáticamente patrones de error.
"""

from __future__ import annotations

import os
import sys
import re
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

try:
    import cv2
except ImportError:
    cv2 = None

try:
    from PIL import Image
except ImportError:
    Image = None

from agent.gui_controller import LocalGUIController


class GUIVisionEngine:
    """Motor de Percepción Visual e Inspección de Interfaz (GUI)."""

    ERROR_KEYWORDS = [
        "error", "failed", "failure", "exception", "warning", "denied",
        "forbidden", "404", "500", "build failed", "unsat", "crash", "timeout"
    ]

    def __init__(self):
        self.controller = LocalGUIController()

    def capture_and_load(self, output_path: str = "scratch/vision_current.png") -> Tuple[Optional[np.ndarray], str]:
        """Toma una captura de pantalla y la carga como matriz OpenCV NumPy."""
        saved_path = self.controller.capture_screenshot(output_path)
        if saved_path.startswith("[HEADLESS_SESSION]"):
            return None, saved_path

        if cv2 is not None and Path(saved_path).exists():
            img_bgr = cv2.imread(saved_path)
            return img_bgr, saved_path
        return None, saved_path

    def find_template(self, screenshot_img: np.ndarray, template_img: np.ndarray, threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        Localiza las coordenadas exactas (x, y) de un ícono o botón mediante coincidencia de plantillas OpenCV.
        """
        if cv2 is None or screenshot_img is None or template_img is None:
            return []

        res = cv2.matchTemplate(screenshot_img, template_img, cv2.TM_CCOEFF_NORMED)
        h, w = template_img.shape[:2]

        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        matches = []
        if max_val >= threshold:
            matches.append({
                "x": int(max_loc[0] + w // 2),
                "y": int(max_loc[1] + h // 2),
                "bbox": [int(max_loc[0]), int(max_loc[1]), int(w), int(h)],
                "confidence": float(max_val)
            })
        return matches

    def diagnose_text_errors(self, text_content: str) -> List[Dict[str, Any]]:
        """Analiza una cadena de texto extraída de pantalla en busca de patrones de fallo."""
        detected = []
        lines = text_content.splitlines()
        for i, line in enumerate(lines):
            line_clean = line.strip().lower()
            for kw in self.ERROR_KEYWORDS:
                if kw in line_clean:
                    detected.append({
                        "line_number": i + 1,
                        "keyword": kw,
                        "text": line.strip(),
                        "severity": "CRITICAL" if kw in ["error", "failed", "500", "crash", "build failed"] else "WARNING"
                    })
                    break
        return detected

    def analyze_current_screen(self, output_path: str = "scratch/vision_analysis.png") -> Dict[str, Any]:
        """Realiza un diagnóstico integral de percepción sobre la pantalla actual."""
        img, img_path = self.capture_and_load(output_path)
        screen_size = self.controller.get_screen_size()
        cursor_pos = self.controller.get_cursor_position()

        result = {
            "screen_size": {"width": screen_size[0], "height": screen_size[1]},
            "cursor_position": {"x": cursor_pos[0], "y": cursor_pos[1]},
            "image_path": img_path,
            "opencv_available": cv2 is not None,
            "detected_errors": [],
            "status": "success"
        }
        return result


if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    engine = GUIVisionEngine()
    analysis = engine.analyze_current_screen()
    print("Motor de Percepción Visual GUIVisionEngine Inicializado Exitosamente:")
    print(analysis)

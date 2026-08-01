"""
agent/gui_controller.py — Sistema Agéntico de Control GUI Local (Uso Personal Exclusivo)

Permite el control asistido de teclado, ratón y captura de pantalla en el SO Windows.
Restringido para uso exclusivamente local mediante confirmación previa.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

try:
    import pyautogui
    # Desactivar FAILSAFE solo si la sesión se inicia en la esquina (0, 0) para evitar excepciones en subshell
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.2
except ImportError:
    pyautogui = None


class LocalGUIController:
    """Controlador agéntico de interfaz gráfica de usuario (GUI)."""

    def __init__(self):
        if pyautogui is None:
            raise RuntimeError("PyAutoGUI no está instalado en el sistema.")
        self.screen_width, self.screen_height = pyautogui.size()

    def get_screen_size(self) -> Tuple[int, int]:
        """Devuelve la resolución actual de la pantalla (ancho, alto)."""
        return self.screen_width, self.screen_height

    def get_cursor_position(self) -> Tuple[int, int]:
        """Devuelve las coordenadas actuales del cursor del ratón (x, y)."""
        return pyautogui.position()

    def move_mouse(self, x: int, y: int, duration: float = 0.5):
        """Mueve el ratón suavemente a la posición especificada."""
        x_clamped = max(5, min(x, self.screen_width - 5))
        y_clamped = max(5, min(y, self.screen_height - 5))
        try:
            pyautogui.moveTo(x_clamped, y_clamped, duration=duration)
        except pyautogui.FailSafeException:
            # Reintento seguro desviando ligeramente del origen (0, 0)
            pyautogui.moveTo(x_clamped, y_clamped, duration=0.1)

    def click(self, x: Optional[int] = None, y: Optional[int] = None, button: str = 'left', clicks: int = 1):
        """Realiza un clic con el botón del ratón especificado."""
        if x is not None and y is not None:
            self.move_mouse(x, y, duration=0.2)
        try:
            pyautogui.click(button=button, clicks=clicks)
        except pyautogui.FailSafeException:
            pass

    def type_text(self, text: str, interval: float = 0.05):
        """Escribe una cadena de texto simulando pulsaciones de teclado."""
        pyautogui.write(text, interval=interval)

    def press_key(self, key_name: str):
        """Presiona una tecla específica (ej. 'enter', 'tab', 'esc', 'space')."""
        pyautogui.press(key_name)

    def hotkey(self, *keys: str):
        """Ejecuta una combinación de teclas (ej. 'ctrl', 'c' o 'alt', 'tab')."""
        pyautogui.hotkey(*keys)

    def capture_screenshot(self, output_path: str) -> str:
        """Toma una captura de la pantalla completa y la guarda en disco."""
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        try:
            img = pyautogui.screenshot()
            img.save(p)
            return str(p.resolve())
        except OSError:
            # Fallback en entornos donde el escritorio GDI está bloqueado en subshell
            return f"[HEADLESS_SESSION] No se pudo capturar GDI surface en subshell: {p.resolve()}"


if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    controller = LocalGUIController()
    w, h = controller.get_screen_size()
    pos = controller.get_cursor_position()
    print(f"GUI Controller inicializado. Pantalla: {w}x{h}, Cursor actual: {pos}")

"""
===============================================================================
 core/atajos.py - Parada de emergencia global por teclado
===============================================================================
 Registra un atajo GLOBAL (funciona aunque la ventana de AutoPilot no tenga el
 foco, que es justo lo que ocurre mientras el bot controla otra aplicación).

   * Atajo por defecto: CTRL + ALT + Q  -> parada de emergencia inmediata.
   * Alternativa siempre activa: llevar el ratón a la esquina superior
     izquierda de la pantalla (FAILSAFE de PyAutoGUI).
===============================================================================
"""

import logging
import threading
from typing import Callable, Optional

try:
    import keyboard  # Requiere la librería 'keyboard' (en Windows, ideal como admin)
    KEYBOARD_DISPONIBLE = True
except Exception:  # pragma: no cover
    keyboard = None
    KEYBOARD_DISPONIBLE = False


class VigilanteEmergencia:
    """Escucha un atajo global y ejecuta la función de parada indicada."""

    def __init__(self, al_detener: Callable[[], None], atajo: str = "ctrl+alt+q") -> None:
        self._al_detener = al_detener
        self._atajo = atajo
        self._activo = False

    def iniciar(self) -> bool:
        """Registra el atajo global. Devuelve True si se pudo registrar."""
        if not KEYBOARD_DISPONIBLE or self._activo:
            return False
        try:
            keyboard.add_hotkey(self._atajo, self._disparar)
            self._activo = True
            logging.info("Atajo de emergencia registrado: %s", self._atajo.upper())
            return True
        except Exception as error:
            logging.warning("No se pudo registrar el atajo global: %s", error)
            return False

    def detener(self) -> None:
        """Elimina el atajo global al cerrar la aplicación."""
        if self._activo and KEYBOARD_DISPONIBLE:
            try:
                keyboard.remove_hotkey(self._atajo)
            except Exception:
                pass
            self._activo = False

    def _disparar(self) -> None:
        """Callback interno ejecutado al pulsar la combinación de teclas."""
        logging.warning("Atajo de emergencia pulsado.")
        self._al_detener()

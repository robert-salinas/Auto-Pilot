"""
===============================================================================
 gui/hilo_trabajo.py - Ejecución de la automatización en segundo plano
===============================================================================
 La automatización NUNCA debe correr en el hilo de la interfaz: si lo hiciera,
 la ventana se congelaría y no se podría pulsar "Detener".
 Por eso usamos un QThread que emite señales hacia la GUI.
===============================================================================
"""

from typing import Any
from PySide6.QtCore import QThread, Signal

from core.motor import MotorAutomatizacion


class HiloAutomatizacion(QThread):
    """Ejecuta un flujo del motor en segundo plano y reporta su progreso."""

    # Señales: (mensaje, nivel) para el log y (exito) al terminar
    mensaje = Signal(str, str)
    finalizado = Signal(bool)

    def __init__(self, motor: MotorAutomatizacion, perfil_o_pasos: Any) -> None:
        super().__init__()
        self._motor = motor
        self._perfil_o_pasos = perfil_o_pasos

    def run(self) -> None:  # Método que Qt ejecuta en el nuevo hilo
        # Guardar callback previo y registrar emisor seguro mediante señal Qt
        emisor_previo = self._motor._emisor_log
        self._motor._emisor_log = lambda msg, nivel="info": self.mensaje.emit(msg, nivel)

        exito = False
        try:
            if isinstance(self._perfil_o_pasos, list):
                exito = self._motor.ejecutar_tarea_grabada(self._perfil_o_pasos)
            elif self._perfil_o_pasos == "__DEMO_VISUAL__":
                exito = self._motor.ejecutar_demostracion_visual()
            else:
                exito = self._motor.ejecutar_flujo_login(str(self._perfil_o_pasos))
        finally:
            self._motor._emisor_log = emisor_previo
            self.finalizado.emit(exito)

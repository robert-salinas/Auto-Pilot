"""
===============================================================================
 core/registro.py - Sistema de logging (consola + archivo + señal a la GUI)
===============================================================================
 Centraliza todos los mensajes del bot para que se vean:
   1. En el archivo recursos/registro.log (histórico permanente).
   2. En la consola en tiempo real de la interfaz gráfica.
===============================================================================
"""

import logging
import os
from datetime import datetime

# Carpeta donde guardamos el archivo de log
CARPETA_RECURSOS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "recursos"
)
RUTA_LOG = os.path.join(CARPETA_RECURSOS, "registro.log")


def configurar_logging() -> None:
    """Configura el logger raíz: escribe en archivo y en la consola del sistema."""
    os.makedirs(CARPETA_RECURSOS, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(RUTA_LOG, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def marca_tiempo() -> str:
    """Devuelve la hora actual formateada, útil para pintar en la consola de la GUI."""
    return datetime.now().strftime("%H:%M:%S")

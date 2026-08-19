"""
===============================================================================
 AutoPilot RPA - Punto de entrada de la aplicación
===============================================================================
 Descripción:
   Arranca la interfaz gráfica (PySide6) y conecta el motor de automatización.
   Este archivo NO contiene lógica de negocio: solo inicializa la aplicación.

 Autor: Desarrollo Senior RPA
 Requisitos: ver requirements.txt (instalar con instalar.bat)
===============================================================================
"""

import sys
import os

# Aseguramos que la carpeta del proyecto esté en el PATH de Python,
# así los imports de "core" y "gui" funcionan aunque se ejecute con doble clic.
RAIZ_PROYECTO = os.path.dirname(os.path.abspath(__file__))
if RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, RAIZ_PROYECTO)

from PySide6.QtWidgets import QApplication          # Núcleo de la aplicación Qt
from PySide6.QtGui import QIcon                     # Icono de la ventana

from gui.ventana_principal import VentanaPrincipal  # Nuestra ventana principal
from core.registro import configurar_logging        # Configuración del log en archivo


def main() -> int:
    """Inicializa Qt, crea la ventana principal y entra en el bucle de eventos."""

    # 1) Preparamos el sistema de registro (logs en /recursos/registro.log)
    configurar_logging()

    # 2) Creamos la aplicación Qt
    app = QApplication(sys.argv)
    app.setApplicationName("AutoPilot RPA")
    app.setOrganizationName("AutoPilot")

    # 3) Icono de la aplicación (si existe el archivo .ico)
    ruta_icono = os.path.join(RAIZ_PROYECTO, "assets", "icono.ico")
    if os.path.exists(ruta_icono):
        app.setWindowIcon(QIcon(ruta_icono))

    # 4) Mostramos la ventana principal
    ventana = VentanaPrincipal()
    ventana.show()

    # 5) Bucle de eventos: la app queda "viva" hasta que el usuario la cierre
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

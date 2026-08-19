"""
===============================================================================
 gui/overlay_grabacion.py - Overlay flotante de grabación
===============================================================================
 Ventana emergente siempre visible en la esquina superior derecha que
 notifica la grabación en curso y permite finalizarla con un clic.
===============================================================================
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor, QFont


class OverlayGrabacion(QWidget):
    """Overlay flotante transparente y sobrepuesto (Always-On-Top) durante la grabación."""

    solicitar_detener = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._pasos_cont = 0
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)

        # Contenedor visual minimalista
        self.panel = QWidget()
        self.panel.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 23, 42, 0.95);
                border: 1px solid #f43f5e;
                border-radius: 8px;
            }
        """)

        # Sombra
        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(12)
        sombra.setColor(QColor(0, 0, 0, 140))
        sombra.setOffset(0, 3)
        self.panel.setGraphicsEffect(sombra)

        panel_layout = QHBoxLayout(self.panel)
        panel_layout.setContentsMargins(10, 6, 10, 6)
        panel_layout.setSpacing(12)

        # Indicador de estado sin emojis
        self.lbl_indicador = QLabel("GRABANDO EN VIVO")
        self.lbl_indicador.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.lbl_indicador.setStyleSheet("color: #f43f5e; border: none; background: transparent; letter-spacing: 0.5px;")

        # Contador de Pasos
        self.lbl_pasos = QLabel("0 pasos")
        self.lbl_pasos.setStyleSheet("color: #94a3b8; font-size: 11px; border: none; background: transparent;")

        # Botón Detener
        self.btn_corta = QPushButton("Finalizar y Guardar")
        self.btn_corta.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_corta.setStyleSheet("""
            QPushButton {
                background-color: #f43f5e;
                color: #ffffff;
                font-weight: 600;
                font-size: 12px;
                border-radius: 5px;
                padding: 4px 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #e11d48;
            }
        """)
        self.btn_corta.clicked.connect(self.solicitar_detener.emit)

        panel_layout.addWidget(self.lbl_indicador)
        panel_layout.addWidget(self.lbl_pasos)
        panel_layout.addWidget(self.btn_corta)

        layout.addWidget(self.panel)
        self.resize(300, 46)

    def actualizar_pasos(self, cantidad: int) -> None:
        """Actualiza la cantidad de pasos registrados hasta el momento."""
        self._pasos_cont = cantidad
        self.lbl_pasos.setText(f"{cantidad} paso(s)")

    def posicionar_en_esquina(self) -> None:
        """Ubica el overlay en la esquina superior derecha de la pantalla principal."""
        from PySide6.QtWidgets import QApplication
        pantalla = QApplication.primaryScreen().availableGeometry()
        x = pantalla.x() + pantalla.width() - self.width() - 20
        y = pantalla.y() + 20
        self.move(x, y)

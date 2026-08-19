"""
===============================================================================
 gui/estilos.py - Tema Minimalista Premium (QSS)
===============================================================================
 Estilo visual limpio, moderno, minimalista y sin elementos innecesarios.
 Paleta de colores: Slate Dark & Electric Cyan / Crimson accents.
===============================================================================
"""

COLOR_FONDO = "#0f172a"
COLOR_PANEL = "#1e293b"
COLOR_BORDE = "#334155"
COLOR_TEXTO = "#f8fafc"
COLOR_SUAVE = "#94a3b8"
COLOR_ACENTO = "#06b6d4"
COLOR_PELIGRO = "#f43f5e"
COLOR_AVISO = "#f59e0b"

HOJA_ESTILOS = f"""
QWidget {{
    background-color: {COLOR_FONDO};
    color: {COLOR_TEXTO};
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 13px;
}}

/* ---------- Cabecera ---------- */
QLabel#titulo {{
    font-size: 20px;
    font-weight: 700;
    color: {COLOR_TEXTO};
    letter-spacing: 0.5px;
}}
QLabel#subtitulo {{
    font-size: 12px;
    color: {COLOR_SUAVE};
}}
QLabel#etiquetaEstado {{
    font-size: 12px;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 12px;
    background-color: {COLOR_PANEL};
    color: {COLOR_SUAVE};
    border: 1px solid {COLOR_BORDE};
}}

/* ---------- Pestañas Minimalistas ---------- */
QTabWidget::pane {{
    border: 1px solid {COLOR_BORDE};
    border-radius: 10px;
    background-color: {COLOR_PANEL};
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {COLOR_SUAVE};
    padding: 8px 18px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 600;
}}
QTabBar::tab:selected {{
    background: {COLOR_PANEL};
    color: {COLOR_ACENTO};
    border: 1px solid {COLOR_BORDE};
    border-bottom: none;
}}

/* ---------- Cajas y Contenedores ---------- */
QGroupBox {{
    border: 1px solid {COLOR_BORDE};
    border-radius: 10px;
    margin-top: 14px;
    padding: 12px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
    color: {COLOR_ACENTO};
}}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background-color: {COLOR_FONDO};
    border: 1px solid {COLOR_BORDE};
    border-radius: 6px;
    padding: 6px 10px;
    color: {COLOR_TEXTO};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {COLOR_ACENTO};
}}

/* ---------- Botones Botonera ---------- */
QPushButton {{
    background-color: {COLOR_PANEL};
    border: 1px solid {COLOR_BORDE};
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 600;
    color: {COLOR_TEXTO};
}}
QPushButton:hover {{
    border-color: {COLOR_ACENTO};
    background-color: #334155;
}}
QPushButton:pressed {{
    background-color: #1e293b;
}}
QPushButton:disabled {{
    color: #475569;
    border-color: #1e293b;
    background-color: #0f172a;
}}

/* Botones específicos centralizados (por objectName) */
#botonGrabar {{
    background-color: {COLOR_ACENTO};
    color: #0f172a;
    font-weight: 700;
    padding: 10px 16px;
    border: none;
}}
#botonGrabar:hover {{ background-color: #22d3ee; }}
#botonGrabar:pressed {{ background-color: #0891b2; }}

#botonDetener {{
    background-color: {COLOR_PELIGRO};
    color: #ffffff;
    font-weight: 700;
    padding: 10px 16px;
    border: none;
}}
#botonDetener:hover {{ background-color: #e11d48; }}
#botonDetener:pressed {{ background-color: #be123c; }}

#botonPausar {{
    background-color: {COLOR_AVISO};
    color: #0f172a;
    font-weight: 700;
    padding: 10px 16px;
    border: none;
}}
#botonPausar:hover {{ background-color: #fbbf24; }}
#botonPausar:pressed {{ background-color: #d97706; }}

#botonDemo {{
    background-color: #8b5cf6;
    color: #ffffff;
    font-weight: 700;
    padding: 10px 16px;
    border: none;
}}
#botonDemo:hover {{ background-color: #a78bfa; }}
#botonDemo:pressed {{ background-color: #7c3aed; }}

#botonGuardar {{
    background-color: #10b981;
    color: #ffffff;
    font-weight: 700;
    padding: 10px 16px;
    border: none;
}}
#botonGuardar:hover {{ background-color: #34d399; }}
#botonGuardar:pressed {{ background-color: #059669; }}

#botonReproducir {{
    background-color: #3b82f6;
    color: #ffffff;
    font-weight: 700;
    padding: 10px 16px;
    border: none;
}}
#botonReproducir:hover {{ background-color: #60a5fa; }}
#botonReproducir:pressed {{ background-color: #2563eb; }}

/* Estilos legacy para compatibilidad */
QPushButton#botonPrincipal {{
    background-color: {COLOR_ACENTO};
    color: #0f172a;
    font-size: 14px;
    padding: 10px 16px;
    border: none;
}}
QPushButton#botonPrincipal:hover {{ background-color: #22d3ee; }}

QPushButton#botonPausa {{
    background-color: transparent;
    color: {COLOR_AVISO};
    border: 1px solid {COLOR_AVISO};
    padding: 10px 16px;
}}
QPushButton#botonPausa:hover {{ background-color: rgba(245, 158, 11, 0.1); }}

QPushButton#botonParada {{
    background-color: {COLOR_PELIGRO};
    color: #ffffff;
    padding: 10px 16px;
    border: none;
}}
QPushButton#botonParada:hover {{ background-color: #e11d48; }}

/* ---------- Consola y Tablas ---------- */
QPlainTextEdit#consola {{
    background-color: #020617;
    border: 1px solid {COLOR_BORDE};
    border-radius: 8px;
    font-family: 'Consolas', 'Cascadia Code', monospace;
    font-size: 12px;
    padding: 8px;
}}

QListWidget, QTableWidget {{
    background-color: {COLOR_FONDO};
    border: 1px solid {COLOR_BORDE};
    border-radius: 8px;
    padding: 4px;
    gridline-color: {COLOR_BORDE};
}}

QListWidget::item {{ 
    padding: 6px; 
    border-radius: 4px; 
}}

QListWidget::item:selected, QTableWidget::item:selected {{
    background-color: {COLOR_ACENTO};
    color: #0f172a;
    font-weight: bold;
}}

QTableWidget::item {{
    padding: 4px;
    border: none;
}}

QTableWidget::item:hover {{
    background-color: #334155;
}}

QTableWidget::item:selected {{
    background-color: #475569;
    color: #f1f5f9;
}}

/* Cabeceras de tabla - mejorado */
QHeaderView::section {{
    background-color: #1e293b;
    color: #94a3b8;
    font-weight: 700;
    padding: 8px 6px;
    border: none;
    border-bottom: 2px solid {COLOR_ACENTO};
    border-right: 1px solid {COLOR_BORDE};
}}

QHeaderView::section:hover {{
    background-color: #334155;
}}

/* Barras de desplazamiento personalizadas - mejorado */
QScrollBar:vertical {{
    background: {COLOR_FONDO};
    width: 12px;
    margin: 0px;
    border-radius: 6px;
}}
QScrollBar::handle:vertical {{
    background: #475569;
    min-height: 20px;
    border-radius: 6px;
    margin: 2px;
}}
QScrollBar::handle:vertical:hover {{
    background: #64748b;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
    border: none;
}}

QScrollBar:horizontal {{
    background: {COLOR_FONDO};
    height: 12px;
    margin: 0px;
    border-radius: 6px;
}}
QScrollBar::handle:horizontal {{
    background: #475569;
    min-width: 20px;
    border-radius: 6px;
    margin: 2px;
}}
QScrollBar::handle:horizontal:hover {{
    background: #64748b;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
    border: none;
}}
"""

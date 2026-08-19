"""
===============================================================================
 gui/ventana_principal.py - Interfaz gráfica principal (PySide6)
===============================================================================
 Estructura de la ventana:

   Cabecera  : título, subtítulo y "píldora" con el estado actual del bot.
   Pestañas  :
       1. Panel        -> selección de perfil, botones grandes de control
                          y consola de log en tiempo real.
       2. Credenciales -> alta/edición/borrado de perfiles cifrados.
       3. Configuración-> tiempos de espera, precisión de imagen, tecleo.
   Pie       : recordatorio de las paradas de emergencia.

 IMPORTANTE: esta clase NO contiene lógica de automatización; delega todo en
 core.motor.MotorAutomatizacion.
===============================================================================
"""

import os
from datetime import datetime

from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtGui import QTextCursor, QShortcut, QKeySequence, QFont
from PySide6.QtWidgets import (
    QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTabWidget, QPlainTextEdit, QComboBox,
    QLineEdit, QGroupBox, QListWidget, QMessageBox, QDoubleSpinBox,
    QFileDialog, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QSpinBox,
)

from core.motor import MotorAutomatizacion, PYAUTOGUI_DISPONIBLE, PYWINAUTO_DISPONIBLE
from core.atajos import VigilanteEmergencia
from core.registro import marca_tiempo, RUTA_LOG
from core.grabador import GestorTareas, GrabadorEnVivo
from gui.estilos import HOJA_ESTILOS, COLOR_ACENTO, COLOR_PELIGRO, COLOR_AVISO, COLOR_SUAVE
from gui.hilo_trabajo import HiloAutomatizacion
from gui.overlay_grabacion import OverlayGrabacion


class VentanaPrincipal(QMainWindow):
    """Ventana principal de AutoPilot RPA."""

    paso_capturado_signal = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AutoPilot RPA - Automatización de escritorio")
        self.resize(1080, 760)
        self.setStyleSheet(HOJA_ESTILOS)

        # --- Motor y Gestores -----------------------------------------------
        self.motor = MotorAutomatizacion(emisor_log=self._log_desde_motor)
        self.gestor_tareas = GestorTareas()
        self.grabador_en_vivo = GrabadorEnVivo(al_capturar_paso=lambda p: self.paso_capturado_signal.emit(p))
        self.paso_capturado_signal.connect(self._al_capturar_paso_en_vivo)
        self.overlay_grabacion = OverlayGrabacion()
        self.overlay_grabacion.solicitar_detener.connect(self._detener_grabacion_overlay)
        self.pasos_grabados_actuales = []
        self.hilo = None  # Hilo de ejecución activo (si lo hay)

        # --- Atajo global de parada de emergencia (CTRL+ALT+Q) -------------
        self.vigilante = VigilanteEmergencia(al_detener=self.detener_automatizacion)
        atajo_ok = self.vigilante.iniciar()

        self._construir_interfaz()
        self._configurar_atajos_teclado()
        self._refrescar_perfiles()
        self._refrescar_tareas_grabadas()

        # Mensajes de bienvenida y diagnóstico del entorno
        self.escribir_log("AutoPilot RPA iniciado correctamente.", "ok")
        self.escribir_log(
            f"PyAutoGUI: {'disponible' if PYAUTOGUI_DISPONIBLE else 'NO disponible'} | "
            f"Pywinauto: {'disponible' if PYWINAUTO_DISPONIBLE else 'NO disponible (solo Windows)'}",
            "info" if PYAUTOGUI_DISPONIBLE else "warn",
        )
        self.escribir_log(
            "Parada de emergencia: CTRL+ALT+Q | Atajo de Grabación: Ctrl+Shift+R",
            "info" if atajo_ok else "warn",
        )

    # ================================================================== #
    # Construcción de la interfaz
    # ================================================================== #
    def _construir_interfaz(self) -> None:
        contenedor = QWidget()
        disposicion = QVBoxLayout(contenedor)
        disposicion.setContentsMargins(24, 20, 24, 18)
        disposicion.setSpacing(16)

        disposicion.addLayout(self._crear_cabecera())

        pestanas = QTabWidget()
        pestanas.addTab(self._crear_pestana_panel(), "  Panel  ")
        pestanas.addTab(self._crear_pestana_grabador(), " Grabador de Tareas  ")
        pestanas.addTab(self._crear_pestana_credenciales(), "  Credenciales  ")
        pestanas.addTab(self._crear_pestana_configuracion(), "  Configuración  ")
        disposicion.addWidget(pestanas, stretch=1)

        pie = QLabel(
            "Paradas de emergencia:  CTRL+ALT+Q  ·  botón rojo  ·  "
            "esquina superior izquierda (FAILSAFE)  |  Atajos: Ctrl+Shift+R (Grabar) · Ctrl+Shift+P (Reproducir)"
        )
        pie.setStyleSheet(f"color: {COLOR_SUAVE}; font-size: 12px;")
        pie.setAlignment(Qt.AlignCenter)
        disposicion.addWidget(pie)

        self.setCentralWidget(contenedor)

    def _crear_cabecera(self) -> QHBoxLayout:
        """Título de la app y etiqueta de estado (Inactivo / Ejecutando / ...)."""
        fila = QHBoxLayout()

        columna = QVBoxLayout()
        titulo = QLabel("AutoPilot RPA")
        titulo.setObjectName("titulo")
        subtitulo = QLabel("Automatización de inicios de sesión y tareas repetitivas")
        subtitulo.setObjectName("subtitulo")
        columna.addWidget(titulo)
        columna.addWidget(subtitulo)

        self.etiqueta_estado = QLabel("● Inactivo")
        self.etiqueta_estado.setObjectName("etiquetaEstado")

        fila.addLayout(columna)
        fila.addStretch()
        fila.addWidget(self.etiqueta_estado)
        return fila

    # ------------------------------------------------------------------ #
    # Pestaña 1: Panel de control
    # ------------------------------------------------------------------ #
    def _crear_pestana_panel(self) -> QWidget:
        pagina = QWidget()
        disposicion = QVBoxLayout(pagina)
        disposicion.setContentsMargins(18, 18, 18, 18)
        disposicion.setSpacing(14)

        # --- Selección del flujo a ejecutar --------------------------------
        caja_flujo = QGroupBox("Flujo a ejecutar")
        fila_flujo = QHBoxLayout(caja_flujo)
        fila_flujo.addWidget(QLabel("Perfil guardado:"))
        self.combo_perfiles = QComboBox()
        self.combo_perfiles.setMinimumWidth(280)
        fila_flujo.addWidget(self.combo_perfiles)
        fila_flujo.addStretch()
        boton_recargar = QPushButton("Recargar perfiles")
        boton_recargar.clicked.connect(self._refrescar_perfiles)
        fila_flujo.addWidget(boton_recargar)
        disposicion.addWidget(caja_flujo)

        # --- Botones grandes de control ------------------------------------
        fila_botones = QHBoxLayout()
        fila_botones.setSpacing(12)

        self.boton_iniciar = QPushButton("Iniciar Login")
        self.boton_iniciar.setObjectName("botonPrincipal")
        self.boton_iniciar.clicked.connect(self.iniciar_automatizacion)

        self.boton_demo = QPushButton("Probar Demostración Visual")
        self.boton_demo.setStyleSheet("background-color: #1e293b; border: 1px solid #334155; color: #f8fafc; font-weight: 600; font-size: 13px; padding: 10px 16px;")
        self.boton_demo.clicked.connect(self.iniciar_demostracion_visual)

        self.boton_pausa = QPushButton("Pausar")
        self.boton_pausa.setObjectName("botonPausa")
        self.boton_pausa.setEnabled(False)
        self.boton_pausa.clicked.connect(self.alternar_pausa)

        self.boton_parada = QPushButton("Detener")
        self.boton_parada.setObjectName("botonParada")
        self.boton_parada.setEnabled(False)
        self.boton_parada.clicked.connect(self.detener_automatizacion)

        for boton in (self.boton_iniciar, self.boton_demo, self.boton_pausa, self.boton_parada):
            fila_botones.addWidget(boton)
        disposicion.addLayout(fila_botones)

        # --- Consola de log en tiempo real ---------------------------------
        caja_consola = QGroupBox("Consola de Eventos")
        columna_consola = QVBoxLayout(caja_consola)

        self.consola = QPlainTextEdit()
        self.consola.setObjectName("consola")
        self.consola.setReadOnly(True)
        columna_consola.addWidget(self.consola)

        fila_acciones = QHBoxLayout()
        boton_limpiar = QPushButton("Limpiar Consola")
        boton_limpiar.clicked.connect(self.consola.clear)
        boton_archivo = QPushButton("Ver Archivo de Log")
        boton_archivo.clicked.connect(self._abrir_archivo_log)
        self.check_autoscroll = QCheckBox("Desplazamiento automático")
        self.check_autoscroll.setChecked(True)
        fila_acciones.addWidget(boton_limpiar)
        fila_acciones.addWidget(boton_archivo)
        fila_acciones.addStretch()
        fila_acciones.addWidget(self.check_autoscroll)
        columna_consola.addLayout(fila_acciones)

        disposicion.addWidget(caja_consola, stretch=1)
        return pagina

    # ------------------------------------------------------------------ #
    # Pestaña 2: Grabador & Visualizador de Tareas Personalizadas
    # ------------------------------------------------------------------ #
    def _crear_pestana_grabador(self) -> QWidget:
        pagina = QWidget()
        disposicion = QHBoxLayout(pagina)
        disposicion.setContentsMargins(18, 18, 18, 18)
        disposicion.setSpacing(16)

        # Columna Izquierda: Lista de Tareas Guardadas y Reproductor
        caja_tareas = QGroupBox("Tareas Guardadas")
        col_tareas = QVBoxLayout(caja_tareas)
        self.lista_tareas = QListWidget()
        self.lista_tareas.itemClicked.connect(self._cargar_tarea_seleccionada)
        col_tareas.addWidget(self.lista_tareas)

        fila_btns_tarea = QHBoxLayout()
        self.btn_reproducir_tarea = QPushButton("Reproducir Tarea (Ctrl+Shift+P)")
        self.btn_reproducir_tarea.setStyleSheet("background-color: #06b6d4; color: #0f172a; font-weight: 600; padding: 8px 12px; border: none; border-radius: 6px;")
        self.btn_reproducir_tarea.clicked.connect(self.reproducir_tarea_seleccionada)

        btn_eliminar_tarea = QPushButton("Eliminar Tarea")
        btn_eliminar_tarea.clicked.connect(self._eliminar_tarea)
        fila_btns_tarea.addWidget(self.btn_reproducir_tarea)
        fila_btns_tarea.addWidget(btn_eliminar_tarea)
        col_tareas.addLayout(fila_btns_tarea)
        disposicion.addWidget(caja_tareas, stretch=1)

        # Columna Derecha: Editor y Constructor de Tarea
        caja_editor = QGroupBox("Grabación en Vivo / Editor de Tarea")
        col_editor = QVBoxLayout(caja_editor)

        # Barra Superior de Controles
        fila_nombre = QHBoxLayout()
        fila_nombre.addWidget(QLabel("Nombre de la Tarea:"))
        self.txt_nombre_tarea = QLineEdit()
        self.txt_nombre_tarea.setPlaceholderText("Ej: Login_Intranet, Abrir_Excel...")
        fila_nombre.addWidget(self.txt_nombre_tarea)

        self.btn_overlay = QPushButton("Iniciar Grabación en Vivo (Ctrl+Shift+R)")
        self.btn_overlay.setStyleSheet("background-color: #f43f5e; color: #ffffff; font-weight: 600; padding: 8px 14px; border: none; border-radius: 6px;")
        self.btn_overlay.clicked.connect(self.iniciar_grabacion_overlay)
        fila_nombre.addWidget(self.btn_overlay)
        col_editor.addLayout(fila_nombre)

        # Formulario de adición de pasos manuales / por coordenadas
        caja_paso = QGroupBox("Agregar Paso Manual")
        grid_paso = QGridLayout(caja_paso)

        self.combo_tipo_paso = QComboBox()
        self.combo_tipo_paso.addItems(["clic", "mover", "teclear", "pulsar", "abrir_app", "espera"])
        
        self.txt_coord_x = QSpinBox()
        self.txt_coord_x.setRange(0, 5000)
        self.txt_coord_y = QSpinBox()
        self.txt_coord_y.setRange(0, 5000)

        btn_capturar_mouse = QPushButton("Capturar Posición Cursor")
        btn_capturar_mouse.clicked.connect(self._capturar_posicion_raton)

        self.txt_param_paso = QLineEdit()
        self.txt_param_paso.setPlaceholderText("Texto a teclear / Tecla / Comando de app...")

        btn_agregar_paso = QPushButton("Agregar Paso")
        btn_agregar_paso.setStyleSheet("background-color: #334155; color: #f8fafc; font-weight: 600;")
        btn_agregar_paso.clicked.connect(self._agregar_paso_a_lista)

        grid_paso.addWidget(QLabel("Tipo:"), 0, 0)
        grid_paso.addWidget(self.combo_tipo_paso, 0, 1)
        grid_paso.addWidget(QLabel("Coordenadas X/Y:"), 0, 2)
        
        sub_coords = QHBoxLayout()
        sub_coords.addWidget(self.txt_coord_x)
        sub_coords.addWidget(self.txt_coord_y)
        sub_coords.addWidget(btn_capturar_mouse)
        grid_paso.addLayout(sub_coords, 0, 3)

        grid_paso.addWidget(QLabel("Parámetro / Texto:"), 1, 0)
        grid_paso.addWidget(self.txt_param_paso, 1, 1, 1, 2)
        grid_paso.addWidget(btn_agregar_paso, 1, 3)

        col_editor.addWidget(caja_paso)

        # Tabla visual de pasos
        self.tabla_pasos = QTableWidget(0, 4)
        self.tabla_pasos.setHorizontalHeaderLabels(["#", "Acción", "Coordenadas X,Y", "Detalles / Parámetros"])
        self.tabla_pasos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        col_editor.addWidget(self.tabla_pasos, stretch=1)

        # Botones de Acción de Tabla
        fila_tabla_btns = QHBoxLayout()
        btn_borrar_paso = QPushButton("Eliminar Paso Seleccionado")
        btn_borrar_paso.clicked.connect(self._eliminar_paso_seleccionado)
        btn_limpiar_pasos = QPushButton("Limpiar Todo")
        btn_limpiar_pasos.clicked.connect(self._limpiar_tabla_pasos)

        btn_guardar_tarea = QPushButton("Guardar Tarea en Disco")
        btn_guardar_tarea.setStyleSheet("background-color: #10b981; color: #0f172a; font-weight: 600; padding: 8px 14px; border: none; border-radius: 6px;")
        btn_guardar_tarea.clicked.connect(self._guardar_tarea_actual)

        fila_tabla_btns.addWidget(btn_borrar_paso)
        fila_tabla_btns.addWidget(btn_limpiar_pasos)
        fila_tabla_btns.addStretch()
        fila_tabla_btns.addWidget(btn_guardar_tarea)
        col_editor.addLayout(fila_tabla_btns)

        disposicion.addWidget(caja_editor, stretch=2)
        return pagina

    # ------------------------------------------------------------------ #
    # Pestaña 2: Credenciales cifradas
    # ------------------------------------------------------------------ #
    def _crear_pestana_credenciales(self) -> QWidget:
        pagina = QWidget()
        disposicion = QHBoxLayout(pagina)
        disposicion.setContentsMargins(18, 18, 18, 18)
        disposicion.setSpacing(16)

        # Columna izquierda: lista de perfiles guardados
        caja_lista = QGroupBox("Perfiles guardados")
        columna_lista = QVBoxLayout(caja_lista)
        self.lista_perfiles = QListWidget()
        self.lista_perfiles.itemClicked.connect(self._cargar_perfil_seleccionado)
        columna_lista.addWidget(self.lista_perfiles)
        boton_eliminar = QPushButton("Eliminar perfil seleccionado")
        boton_eliminar.clicked.connect(self._eliminar_perfil)
        columna_lista.addWidget(boton_eliminar)
        disposicion.addWidget(caja_lista, stretch=1)

        # Columna derecha: formulario de alta/edición
        caja_form = QGroupBox("Nuevo perfil / editar existente")
        formulario = QGridLayout(caja_form)
        formulario.setVerticalSpacing(12)

        self.campo_perfil = QLineEdit()
        self.campo_perfil.setPlaceholderText("Ej.: INTRANET, SAP, CORREO")
        self.campo_usuario = QLineEdit()
        self.campo_usuario.setPlaceholderText("usuario@empresa.com")
        self.campo_contrasena = QLineEdit()
        self.campo_contrasena.setEchoMode(QLineEdit.Password)  # Oculta la escritura
        self.campo_contrasena.setPlaceholderText("••••••••••")
        self.campo_destino = QLineEdit()
        self.campo_destino.setPlaceholderText("Título de ventana o URL destino (opcional)")

        formulario.addWidget(QLabel("Nombre del perfil"), 0, 0)
        formulario.addWidget(self.campo_perfil, 0, 1)
        formulario.addWidget(QLabel("Usuario"), 1, 0)
        formulario.addWidget(self.campo_usuario, 1, 1)
        formulario.addWidget(QLabel("Contraseña"), 2, 0)
        formulario.addWidget(self.campo_contrasena, 2, 1)
        formulario.addWidget(QLabel("Ventana / URL"), 3, 0)
        formulario.addWidget(self.campo_destino, 3, 1)

        check_ver = QCheckBox("Mostrar contraseña")
        check_ver.toggled.connect(
            lambda visible: self.campo_contrasena.setEchoMode(
                QLineEdit.Normal if visible else QLineEdit.Password
            )
        )
        formulario.addWidget(check_ver, 4, 1)

        boton_guardar = QPushButton("Guardar de forma cifrada")
        boton_guardar.setObjectName("botonPrincipal")
        boton_guardar.clicked.connect(self._guardar_credenciales)
        formulario.addWidget(boton_guardar, 5, 0, 1, 2)

        aviso = QLabel(
            "Las contraseñas se cifran con AES (Fernet) y se guardan en el archivo .env.\n"
            "La clave maestra vive en recursos/clave.key: no la comparta ni la suba a Git."
        )
        aviso.setWordWrap(True)
        aviso.setStyleSheet(f"color: {COLOR_SUAVE}; font-size: 12px;")
        formulario.addWidget(aviso, 6, 0, 1, 2)
        formulario.setRowStretch(7, 1)

        disposicion.addWidget(caja_form, stretch=2)
        return pagina

    # ------------------------------------------------------------------ #
    # Pestaña 3: Configuración del motor
    # ------------------------------------------------------------------ #
    def _crear_pestana_configuracion(self) -> QWidget:
        pagina = QWidget()
        disposicion = QVBoxLayout(pagina)
        disposicion.setContentsMargins(18, 18, 18, 18)
        disposicion.setSpacing(16)

        caja = QGroupBox("Parámetros del motor de automatización")
        rejilla = QGridLayout(caja)
        rejilla.setVerticalSpacing(14)

        # Tiempo límite de las esperas inteligentes
        self.spin_timeout = QDoubleSpinBox()
        self.spin_timeout.setRange(1.0, 300.0)
        self.spin_timeout.setValue(self.motor.tiempo_limite)
        self.spin_timeout.setSuffix(" s")
        self.spin_timeout.valueChanged.connect(
            lambda valor: setattr(self.motor, "tiempo_limite", valor)
        )

        # Confianza al buscar imágenes en pantalla
        self.spin_confianza = QDoubleSpinBox()
        self.spin_confianza.setRange(0.50, 1.00)
        self.spin_confianza.setSingleStep(0.01)
        self.spin_confianza.setValue(self.motor.confianza_imagen)
        self.spin_confianza.valueChanged.connect(
            lambda valor: setattr(self.motor, "confianza_imagen", valor)
        )

        # Velocidad de tecleo simulado
        self.spin_tecleo = QDoubleSpinBox()
        self.spin_tecleo.setRange(0.00, 1.00)
        self.spin_tecleo.setSingleStep(0.01)
        self.spin_tecleo.setValue(self.motor.velocidad_tecleo)
        self.spin_tecleo.setSuffix(" s / tecla")
        self.spin_tecleo.valueChanged.connect(
            lambda valor: setattr(self.motor, "velocidad_tecleo", valor)
        )

        rejilla.addWidget(QLabel("Tiempo límite de espera inteligente"), 0, 0)
        rejilla.addWidget(self.spin_timeout, 0, 1)
        rejilla.addWidget(QLabel("Precisión al buscar imágenes"), 1, 0)
        rejilla.addWidget(self.spin_confianza, 1, 1)
        rejilla.addWidget(QLabel("Velocidad de tecleo"), 2, 0)
        rejilla.addWidget(self.spin_tecleo, 2, 1)
        rejilla.setColumnStretch(1, 1)

        disposicion.addWidget(caja)

        # Carpeta de capturas usadas por PyAutoGUI
        caja_rutas = QGroupBox("Carpeta de imágenes de referencia (PyAutoGUI)")
        fila = QHBoxLayout(caja_rutas)
        self.campo_carpeta = QLineEdit(os.path.join(os.getcwd(), "assets"))
        boton_examinar = QPushButton("Examinar…")
        boton_examinar.clicked.connect(self._elegir_carpeta)
        fila.addWidget(self.campo_carpeta)
        fila.addWidget(boton_examinar)
        disposicion.addWidget(caja_rutas)

        disposicion.addStretch()
        return pagina

    # ================================================================== #
    # Acciones de la interfaz
    # ================================================================== #
    @Slot()
    def iniciar_automatizacion(self) -> None:
        """Lanza el flujo del perfil seleccionado en un hilo secundario."""
        perfil = self.combo_perfiles.currentText().strip()
        if not perfil:
            QMessageBox.warning(
                self, "Sin perfil",
                "Primero cree un perfil en la pestaña 'Credenciales'."
            )
            return

        self._cambiar_estado("Ejecutando", COLOR_ACENTO)
        self.boton_iniciar.setEnabled(False)
        self.boton_demo.setEnabled(False)
        self.boton_pausa.setEnabled(True)
        self.boton_parada.setEnabled(True)

        self.hilo = HiloAutomatizacion(self.motor, perfil)
        self.hilo.mensaje.connect(self.escribir_log)
        self.hilo.finalizado.connect(self._al_finalizar)
        self.hilo.start()

    @Slot()
    def iniciar_demostracion_visual(self) -> None:
        """Lanza el flujo de demostración visual animada."""
        self._cambiar_estado("Demostración en vivo", COLOR_ACENTO)
        self.boton_iniciar.setEnabled(False)
        self.boton_demo.setEnabled(False)
        self.boton_pausa.setEnabled(True)
        self.boton_parada.setEnabled(True)

        self.hilo = HiloAutomatizacion(self.motor, "__DEMO_VISUAL__")
        self.hilo.mensaje.connect(self.escribir_log)
        self.hilo.finalizado.connect(self._al_finalizar)
        self.hilo.start()

    @Slot()
    def alternar_pausa(self) -> None:
        """Pausa o reanuda la ejecución en curso."""
        en_pausa = self.motor.alternar_pausa()
        self.boton_pausa.setText("▶   Reanudar" if en_pausa else "⏸   Pausar")
        self._cambiar_estado(
            "En pausa" if en_pausa else "Ejecutando",
            COLOR_AVISO if en_pausa else COLOR_ACENTO,
        )

    @Slot()
    def detener_automatizacion(self) -> None:
        """Parada de emergencia: aborta el flujo lo antes posible."""
        self.motor.solicitar_parada()
        self._cambiar_estado("Detenido", COLOR_PELIGRO)

    @Slot(bool)
    def _al_finalizar(self, exito: bool) -> None:
        """Restaura los botones cuando el hilo termina."""
        self.boton_iniciar.setEnabled(True)
        self.boton_demo.setEnabled(True)
        self.boton_pausa.setEnabled(False)
        self.boton_pausa.setText("⏸   Pausar")
        self.boton_parada.setEnabled(False)
        self._cambiar_estado(
            "Completado" if exito else "Finalizado con errores",
            COLOR_ACENTO if exito else COLOR_PELIGRO,
        )

    # ------------------------------------------------------------------ #
    # Gestión de perfiles
    # ------------------------------------------------------------------ #
    def _refrescar_perfiles(self) -> None:
        """Recarga la lista y el desplegable con los perfiles almacenados."""
        perfiles = self.motor.credenciales.listar_perfiles()
        self.combo_perfiles.clear()
        self.combo_perfiles.addItems(perfiles)
        self.lista_perfiles.clear()
        self.lista_perfiles.addItems(perfiles)

    def _guardar_credenciales(self) -> None:
        """Valida el formulario y guarda el perfil cifrado."""
        perfil = self.campo_perfil.text().strip()
        usuario = self.campo_usuario.text().strip()
        contrasena = self.campo_contrasena.text()

        if not perfil or not usuario or not contrasena:
            QMessageBox.warning(
                self, "Datos incompletos",
                "Debe completar perfil, usuario y contraseña."
            )
            return

        self.motor.credenciales.guardar(
            perfil, usuario, contrasena, self.campo_destino.text().strip()
        )
        self.escribir_log(f"Perfil '{perfil.upper()}' guardado de forma cifrada.", "ok")
        self.campo_contrasena.clear()
        self._refrescar_perfiles()

    def _cargar_perfil_seleccionado(self, item) -> None:
        """Rellena el formulario con los datos del perfil elegido."""
        datos = self.motor.credenciales.obtener(item.text())
        if not datos:
            return
        self.campo_perfil.setText(item.text())
        self.campo_usuario.setText(datos.get("usuario", ""))
        self.campo_destino.setText(datos.get("destino", ""))
        self.campo_contrasena.clear()  # Nunca precargamos la contraseña por seguridad

    def _eliminar_perfil(self) -> None:
        """Elimina el perfil seleccionado tras confirmación del usuario."""
        item = self.lista_perfiles.currentItem()
        if not item:
            return
        respuesta = QMessageBox.question(
            self, "Confirmar", f"¿Eliminar el perfil '{item.text()}'?"
        )
        if respuesta == QMessageBox.Yes:
            self.motor.credenciales.eliminar(item.text())
            self.escribir_log(f"Perfil '{item.text()}' eliminado.", "warn")
            self._refrescar_perfiles()

    # ------------------------------------------------------------------ #
    # Consola y utilidades
    # ------------------------------------------------------------------ #
    def _log_desde_motor(self, mensaje: str, nivel: str) -> None:
        """Puente entre el motor (hilo secundario) y la consola de la GUI."""
        self.escribir_log(mensaje, nivel)

    def escribir_log(self, mensaje: str, nivel: str = "info") -> None:
        """Añade una línea coloreada a la consola en tiempo real."""
        colores = {
            "ok": "#3ddc97",
            "warn": COLOR_AVISO,
            "error": COLOR_PELIGRO,
            "info": "#9fb0c5",
        }
        color = colores.get(nivel, colores["info"])
        etiqueta = {"ok": "ÉXITO", "warn": "AVISO", "error": "ERROR"}.get(nivel, "INFO")

        self.consola.appendHtml(
            f'<span style="color:#5b6675">[{marca_tiempo()}]</span> '
            f'<span style="color:{color};font-weight:600">{etiqueta:<6}</span> '
            f'<span style="color:#dbe3ee">{mensaje}</span>'
        )
        if self.check_autoscroll.isChecked():
            self.consola.moveCursor(QTextCursor.End)

    def _abrir_archivo_log(self) -> None:
        """Abre el archivo de log con la aplicación predeterminada del sistema."""
        if os.path.exists(RUTA_LOG):
            os.startfile(RUTA_LOG) if os.name == "nt" else os.system(f'xdg-open "{RUTA_LOG}"')

    def _elegir_carpeta(self) -> None:
        """Permite elegir la carpeta con las capturas de referencia."""
        carpeta = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de imágenes")
        if carpeta:
            self.campo_carpeta.setText(carpeta)

    def _configurar_atajos_teclado(self) -> None:
        """Configura los accesos rápidos por teclado (Shortcuts) dentro de la GUI."""
        # Ctrl+Shift+R -> Grabar con Overlay
        sc_grabar = QShortcut(QKeySequence("Ctrl+Shift+R"), self)
        sc_grabar.activated.connect(self.iniciar_grabacion_overlay)

        # Ctrl+Shift+P -> Reproducir Tarea Seleccionada
        sc_reproducir = QShortcut(QKeySequence("Ctrl+Shift+P"), self)
        sc_reproducir.activated.connect(self.reproducir_tarea_seleccionada)

    # ------------------------------------------------------------------ #
    # Lógica de la pestaña Grabador de Tareas
    # ------------------------------------------------------------------ #
    def _refrescar_tareas_grabadas(self) -> None:
        """Carga la lista de tareas JSON en el panel lateral."""
        tareas = self.gestor_tareas.listar_tareas()
        self.lista_tareas.clear()
        self.lista_tareas.addItems(tareas)

    def _cargar_tarea_seleccionada(self, item) -> None:
        """Muestra los pasos de la tarea seleccionada en la tabla visual."""
        nombre = item.text()
        datos = self.gestor_tareas.obtener_tarea(nombre)
        if not datos:
            return
        self.txt_nombre_tarea.setText(datos.get("nombre", nombre))
        self.pasos_grabados_actuales = datos.get("pasos", [])
        self._actualizar_tabla_pasos()
        self.escribir_log(f"Tarea '{nombre}' cargada ({len(self.pasos_grabados_actuales)} pasos).", "info")

    def _actualizar_tabla_pasos(self) -> None:
        """Rellena QTableWidget con los pasos grabados actuales."""
        self.tabla_pasos.setRowCount(0)
        for idx, paso in enumerate(self.pasos_grabados_actuales, 1):
            row = self.tabla_pasos.rowCount()
            self.tabla_pasos.insertRow(row)

            tipo = paso.get("tipo", "")
            x, y = paso.get("x", "-"), paso.get("y", "-")
            coords = f"({x}, {y})" if x != "-" else "-"
            
            param = ""
            if tipo == "teclear":
                param = paso.get("texto", "")
            elif tipo == "pulsar":
                param = ", ".join(paso.get("teclas", [])) if isinstance(paso.get("teclas"), list) else str(paso.get("teclas"))
            elif tipo == "abrir_app":
                param = paso.get("comando", "")
            elif tipo == "espera":
                param = f"{paso.get('segundos', 1)} segundos"

            self.tabla_pasos.setItem(row, 0, QTableWidgetItem(str(idx)))
            self.tabla_pasos.setItem(row, 1, QTableWidgetItem(tipo.upper()))
            self.tabla_pasos.setItem(row, 2, QTableWidgetItem(coords))
            self.tabla_pasos.setItem(row, 3, QTableWidgetItem(str(param)))

        if hasattr(self, "overlay_grabacion"):
            self.overlay_grabacion.actualizar_pasos(len(self.pasos_grabados_actuales))

    def _capturar_posicion_raton(self) -> None:
        """Captura las coordenadas X,Y del cursor actual."""
        try:
            import pyautogui
            pos = pyautogui.position()
            self.txt_coord_x.setValue(pos.x)
            self.txt_coord_y.setValue(pos.y)
            self.escribir_log(f"Coordenadas capturadas del cursor: ({pos.x}, {pos.y})", "ok")
        except Exception as err:
            self.escribir_log(f"No se pudo capturar posición: {err}", "warn")

    def _agregar_paso_a_lista(self) -> None:
        """Agrega el paso configurado en los campos a la tabla actual."""
        tipo = self.combo_tipo_paso.currentText()
        param = self.txt_param_paso.text().strip()
        x = self.txt_coord_x.value()
        y = self.txt_coord_y.value()

        nuevo_paso = {"tipo": tipo}
        if tipo in ("clic", "mover"):
            nuevo_paso["x"] = x
            nuevo_paso["y"] = y
            nuevo_paso["duracion"] = 0.7
        elif tipo == "teclear":
            nuevo_paso["texto"] = param
        elif tipo == "pulsar":
            nuevo_paso["teclas"] = [k.strip() for k in param.split("+") if k.strip()] or ["enter"]
        elif tipo == "abrir_app":
            nuevo_paso["comando"] = param
        elif tipo == "espera":
            try:
                nuevo_paso["segundos"] = float(param)
            except ValueError:
                nuevo_paso["segundos"] = 1.0

        self.pasos_grabados_actuales.append(nuevo_paso)
        self._actualizar_tabla_pasos()
        self.txt_param_paso.clear()

    def _eliminar_paso_seleccionado(self) -> None:
        row = self.tabla_pasos.currentRow()
        if 0 <= row < len(self.pasos_grabados_actuales):
            self.pasos_grabados_actuales.pop(row)
            self._actualizar_tabla_pasos()

    def _limpiar_tabla_pasos(self) -> None:
        self.pasos_grabados_actuales.clear()
        self._actualizar_tabla_pasos()

    def _guardar_tarea_actual(self) -> None:
        nombre = self.txt_nombre_tarea.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Nombre Requerido", "Ingrese un nombre para guardar la tarea.")
            return
        if not self.pasos_grabados_actuales:
            QMessageBox.warning(self, "Sin Pasos", "Agregue al menos un paso antes de guardar la tarea.")
            return
        self.gestor_tareas.guardar_tarea(nombre, self.pasos_grabados_actuales)
        self.escribir_log(f"Tarea '{nombre}' guardada exitosamente con {len(self.pasos_grabados_actuales)} pasos.", "ok")
        self._refrescar_tareas_grabadas()

    def _eliminar_tarea(self) -> None:
        item = self.lista_tareas.currentItem()
        if not item:
            return
        if QMessageBox.question(self, "Eliminar", f"¿Eliminar la tarea '{item.text()}'?") == QMessageBox.Yes:
            self.gestor_tareas.eliminar_tarea(item.text())
            self._refrescar_tareas_grabadas()
            self._limpiar_tabla_pasos()

    @Slot()
    def reproducir_tarea_seleccionada(self) -> None:
        if not self.pasos_grabados_actuales:
            item = self.lista_tareas.currentItem()
            if item:
                self._cargar_tarea_seleccionada(item)

        if not self.pasos_grabados_actuales:
            QMessageBox.warning(self, "Sin Tarea", "Seleccione o cree una tarea con pasos para reproducir.")
            return

        self._cambiar_estado("Reproduciendo Tarea", COLOR_ACENTO)
        self.boton_iniciar.setEnabled(False)
        self.boton_pausa.setEnabled(True)
        self.boton_parada.setEnabled(True)

        self.hilo = HiloAutomatizacion(self.motor, self.pasos_grabados_actuales)
        self.hilo.mensaje.connect(self.escribir_log)
        self.hilo.finalizado.connect(self._al_finalizar)
        self.hilo.start()

    # ------------------------------------------------------------------ #
    # Lógica de Grabación Simultánea en Vivo con Listener
    # ------------------------------------------------------------------ #
    @Slot()
    def iniciar_grabacion_overlay(self) -> None:
        """Inicia los listeners en segundo plano para captura simultánea en vivo."""
        self._limpiar_tabla_pasos()
        self.overlay_grabacion.posicionar_en_esquina()
        self.overlay_grabacion.actualizar_pasos(0)
        self.overlay_grabacion.show()
        self.escribir_log("Grabación en vivo iniciada (capturando clics y teclado en tiempo real).", "warn")
        self.grabador_en_vivo.iniciar()

    def _al_capturar_paso_en_vivo(self, paso: dict) -> None:
        """Callback ejecutado en segundo plano cuando el usuario hace clic o escribe."""
        self.pasos_grabados_actuales.append(paso)
        self._actualizar_tabla_pasos()

    def _detener_grabacion_overlay(self) -> None:
        """Detiene la captura en vivo y oculta el overlay."""
        pasos = self.grabador_en_vivo.detener()
        self.overlay_grabacion.hide()
        
        # Eliminar el último clic si corresponde al botón de finalizar del overlay
        if self.pasos_grabados_actuales:
            ultimo = self.pasos_grabados_actuales[-1]
            if ultimo.get("tipo") == "clic":
                # Si el clic ocurrió cerca de la esquina superior derecha donde está el overlay
                from PySide6.QtWidgets import QApplication
                geo = self.overlay_grabacion.geometry()
                x_clic, y_clic = ultimo.get("x", 0), ultimo.get("y", 0)
                if geo.x() <= x_clic <= geo.x() + geo.width() and geo.y() <= y_clic <= geo.y() + geo.height():
                    self.pasos_grabados_actuales.pop()
                    self._actualizar_tabla_pasos()

        self.escribir_log(f"Grabación finalizada con {len(self.pasos_grabados_actuales)} pasos capturados.", "ok")

    # ------------------------------------------------------------------ #
    def _cambiar_estado(self, texto: str, color: str) -> None:
        """Actualiza la píldora de estado de la cabecera."""
        self.etiqueta_estado.setText(f"● {texto}")
        self.etiqueta_estado.setStyleSheet(
            f"color:{color}; border:1px solid {color}; background-color: rgba(0,0,0,0.2);"
            "font-size:13px; font-weight:600; padding:6px 14px; border-radius:14px;"
        )

    def closeEvent(self, evento) -> None:  # noqa: N802 (nombre exigido por Qt)
        """Al cerrar: liberamos el atajo global y detenemos el bot."""
        if hasattr(self, "overlay_grabacion"):
            self.overlay_grabacion.close()
        self.motor.solicitar_parada()
        self.vigilante.detener()
        super().closeEvent(evento)

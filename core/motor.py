"""
===============================================================================
 core/motor.py - Motor de automatización (PyAutoGUI + Pywinauto)
===============================================================================
 Contiene TODA la lógica de automatización, separada por completo de la GUI.
 La interfaz solo llama a estos métodos y escucha las señales de log.

 Tecnologías combinadas:
   * PyAutoGUI  -> control visual: mover el ratón, escribir, buscar imágenes
                   en pantalla (útil cuando la app no expone controles).
   * Pywinauto  -> control nativo de ventanas de Windows: enfocar ventanas,
                   escribir en campos reales, pulsar botones por su nombre.

 Seguridad operativa:
   * PyAutoGUI FAILSAFE activado: llevar el ratón a la esquina superior
     izquierda aborta cualquier acción (esquina caliente de emergencia).
   * Bandera de parada revisada antes de cada paso.
===============================================================================
"""

import logging
import platform
import threading
import time
from typing import Callable, Optional

from core.utilidades import esperar_hasta, reintentar, TiempoAgotadoError
from core.credenciales import GestorCredenciales

# ---------------------------------------------------------------------------
# Importaciones "tolerantes": permiten abrir la app aunque falte una librería
# (por ejemplo pywinauto en un equipo que no sea Windows).
# ---------------------------------------------------------------------------
try:
    import pyautogui
    pyautogui.FAILSAFE = True   # Esquina superior izquierda = parada de emergencia
    pyautogui.PAUSE = 0.15      # Micro-pausa entre acciones para dar estabilidad
    PYAUTOGUI_DISPONIBLE = True
except Exception:               # pragma: no cover
    pyautogui = None
    PYAUTOGUI_DISPONIBLE = False

try:
    from pywinauto import Application, Desktop
    PYWINAUTO_DISPONIBLE = platform.system() == "Windows"
except Exception:               # pragma: no cover
    Application = None
    Desktop = None
    PYWINAUTO_DISPONIBLE = False


class MotorAutomatizacion:
    """Orquesta los pasos de una automatización de inicio de sesión.

    Uso típico:
        motor = MotorAutomatizacion(emisor_log=mi_funcion_log)
        motor.ejecutar_flujo_login("INTRANET")
    """

    def __init__(self, emisor_log: Optional[Callable[[str, str], None]] = None) -> None:
        # Función que la GUI nos pasa para pintar mensajes en su consola.
        self._emisor_log = emisor_log or (lambda mensaje, nivel="info": None)

        # Eventos de control de ejecución (seguros entre hilos).
        self._evento_parada = threading.Event()   # True = detener
        self._evento_pausa = threading.Event()
        self._evento_pausa.set()                  # set() = NO pausado

        self.credenciales = GestorCredenciales()

        # Parámetros configurables desde la pestaña "Configuración"
        self.tiempo_limite = 20.0     # segundos de espera máxima por elemento
        self.confianza_imagen = 0.85  # precisión al buscar imágenes (requiere OpenCV)
        self.velocidad_tecleo = 0.05  # segundos entre pulsaciones de tecla

    # ================================================================== #
    # Control de ejecución
    # ================================================================== #
    def solicitar_parada(self) -> None:
        """Marca la bandera de parada: el flujo se aborta en el siguiente paso."""
        self._evento_parada.set()
        self._evento_pausa.set()  # Desbloqueamos por si estaba en pausa
        self.log("PARADA DE EMERGENCIA activada por el usuario.", "error")

    def alternar_pausa(self) -> bool:
        """Pausa o reanuda la ejecución. Devuelve True si queda en pausa."""
        if self._evento_pausa.is_set():
            self._evento_pausa.clear()
            self.log("Ejecución EN PAUSA.", "warn")
            return True
        self._evento_pausa.set()
        self.log("Ejecución REANUDADA.", "ok")
        return False

    def reiniciar_estado(self) -> None:
        """Limpia las banderas antes de empezar una nueva ejecución."""
        self._evento_parada.clear()
        self._evento_pausa.set()

    @property
    def detenido(self) -> bool:
        return self._evento_parada.is_set()

    def _punto_de_control(self) -> None:
        """Se llama antes de cada paso: respeta la pausa y aborta si hay parada."""
        self._evento_pausa.wait()           # Bloquea mientras esté en pausa
        if self._evento_parada.is_set():
            raise InterruptedError("Automatización detenida por el usuario.")

    # ================================================================== #
    # Registro
    # ================================================================== #
    def log(self, mensaje: str, nivel: str = "info") -> None:
        """Envía el mensaje al archivo de log y a la consola de la interfaz."""
        {"error": logging.error, "warn": logging.warning}.get(nivel, logging.info)(mensaje)
        self._emisor_log(mensaje, nivel)

    # ================================================================== #
    # Acciones con PYWINAUTO (control nativo de Windows)
    # ================================================================== #
    def abrir_aplicacion(self, ruta_ejecutable: str):
        """Lanza una aplicación de escritorio y devuelve su objeto Application."""
        self._punto_de_control()
        if not PYWINAUTO_DISPONIBLE:
            raise RuntimeError("Pywinauto solo está disponible en Windows.")

        self.log(f"Abriendo aplicación: {ruta_ejecutable}")
        # backend 'uia' funciona con apps modernas (WPF, UWP, Electron, .NET)
        aplicacion = Application(backend="uia").start(ruta_ejecutable)
        self.log("Aplicación lanzada correctamente.", "ok")
        return aplicacion

    def enfocar_ventana(self, titulo_parcial: str):
        """Busca una ventana por parte de su título y la trae al frente.

        Usa espera inteligente: reintenta hasta que la ventana exista.
        """
        self._punto_de_control()
        if not PYWINAUTO_DISPONIBLE:
            raise RuntimeError("Pywinauto solo está disponible en Windows.")

        def buscar():
            ventana = Desktop(backend="uia").window(title_re=f".*{titulo_parcial}.*")
            return ventana if ventana.exists() else None

        ventana = esperar_hasta(
            buscar,
            tiempo_limite=self.tiempo_limite,
            descripcion=f"ventana '{titulo_parcial}'",
            cancelado=lambda: self.detenido,
        )
        reintentar(ventana.set_focus, descripcion="enfocar ventana")
        self.log(f"Ventana '{titulo_parcial}' enfocada.", "ok")
        return ventana

    def escribir_en_campo(self, ventana, nombre_control: str, texto: str,
                          es_secreto: bool = False) -> None:
        """Escribe texto en un control nativo identificado por su nombre."""
        self._punto_de_control()

        def obtener_control():
            control = ventana.child_window(auto_id=nombre_control) \
                if nombre_control.isidentifier() else ventana.child_window(title=nombre_control)
            return control if control.exists() else None

        control = esperar_hasta(
            obtener_control,
            tiempo_limite=self.tiempo_limite,
            descripcion=f"campo '{nombre_control}'",
            cancelado=lambda: self.detenido,
        )
        control.set_focus()
        control.type_keys(texto, with_spaces=True)
        self.log(
            f"Texto escrito en '{nombre_control}': "
            f"{'********' if es_secreto else texto}", "ok"
        )

    # ================================================================== #
    # Acciones con PYAUTOGUI (control visual por imagen y coordenadas)
    # ================================================================== #
    def localizar_imagen(self, ruta_imagen: str):
        """Espera hasta encontrar una imagen en pantalla y devuelve su centro."""
        self._punto_de_control()
        if not PYAUTOGUI_DISPONIBLE:
            raise RuntimeError("PyAutoGUI no está disponible en este equipo.")

        def buscar():
            try:
                return pyautogui.locateCenterOnScreen(
                    ruta_imagen, confidence=self.confianza_imagen
                )
            except Exception:
                # Sin OpenCV instalado, 'confidence' no está soportado
                return pyautogui.locateCenterOnScreen(ruta_imagen)

        return esperar_hasta(
            buscar,
            tiempo_limite=self.tiempo_limite,
            descripcion=f"imagen '{ruta_imagen}'",
            cancelado=lambda: self.detenido,
        )

    def clic_en_imagen(self, ruta_imagen: str) -> None:
        """Busca una imagen en pantalla y hace clic en su centro."""
        posicion = self.localizar_imagen(ruta_imagen)
        pyautogui.moveTo(posicion, duration=0.3)  # Movimiento suave y natural
        pyautogui.click()
        self.log(f"Clic realizado sobre la imagen '{ruta_imagen}'.", "ok")

    def teclear(self, texto: str, es_secreto: bool = False) -> None:
        """Escribe texto con el teclado virtual (funciona en cualquier ventana)."""
        self._punto_de_control()
        pyautogui.write(texto, interval=self.velocidad_tecleo)
        self.log(f"Tecleado: {'********' if es_secreto else texto}", "ok")

    def pulsar(self, *teclas: str) -> None:
        """Pulsa una tecla suelta ('enter') o una combinación ('ctrl', 'c')."""
        self._punto_de_control()
        if len(teclas) == 1:
            pyautogui.press(teclas[0])
        else:
            pyautogui.hotkey(*teclas)
        self.log(f"Tecla(s) pulsada(s): {' + '.join(teclas)}", "ok")

    # ================================================================== #
    # Acciones VISUALES y ANIMADAS con PyAutoGUI (Ratón, teclado y apps)
    # ================================================================== #
    def mover_raton_animado(self, x: int, y: int, duracion: float = 1.0) -> None:
        """Mueve el puntero del ratón suavemente hacia las coordenadas (x, y)."""
        self._punto_de_control()
        if PYAUTOGUI_DISPONIBLE:
            self.log(f"Moviendo ratón a coordenadas ({x}, {y}) con animación ({duracion}s)...", "info")
            pyautogui.moveTo(x, y, duration=duracion, tween=pyautogui.easeOutQuad)
            self.log(f"Ratón posicionado en ({x}, {y}).", "ok")

    def clic_en_coordenadas(self, x: int, y: int, duracion_movimiento: float = 0.8) -> None:
        """Mueve el ratón con animación hasta (x, y) y realiza un clic izquierdo."""
        self._punto_de_control()
        if PYAUTOGUI_DISPONIBLE:
            self.mover_raton_animado(x, y, duracion=duracion_movimiento)
            time.sleep(0.2)
            pyautogui.click()
            self.log(f"Clic realizado en ({x}, {y}).", "ok")

    def abrir_aplicacion_sistema(self, nombre_o_comando: str) -> None:
        """Abre una aplicación de Windows (ej: calc, notepad, edge) o URL."""
        self._punto_de_control()
        self.log(f"Abriendo aplicación / comando: '{nombre_o_comando}'...", "info")
        import subprocess
        subprocess.Popen(nombre_o_comando, shell=True)
        self.log(f"Aplicación '{nombre_o_comando}' lanzada.", "ok")
        time.sleep(1.5)

    def ejecutar_demostracion_visual(self) -> bool:
        """Ejecuta un flujo 100% VISUAL que muestra el movimiento suave del ratón,
        apertura de Bloc de notas, tecleado dinámico y movimientos por la pantalla."""
        self.reiniciar_estado()
        inicio = time.time()
        self.log("=== INICIANDO DEMOSTRACIÓN VISUAL DE AUTOMATIZACIÓN ===", "ok")

        try:
            ancho, alto = pyautogui.size() if PYAUTOGUI_DISPONIBLE else (1920, 1080)
            self.log(f"Resolución de pantalla detectada: {ancho}x{alto}", "info")

            # 1. Movimiento animado a las 4 esquinas/centros de la pantalla
            self.log("Paso 1: Demostración de movimiento suave del cursor del ratón...", "info")
            puntos = [
                (int(ancho * 0.5), int(alto * 0.3)),
                (int(ancho * 0.7), int(alto * 0.5)),
                (int(ancho * 0.3), int(alto * 0.5)),
                (int(ancho * 0.5), int(alto * 0.5))
            ]
            for px, py in puntos:
                self.mover_raton_animado(px, py, duracion=0.7)

            # 2. Abrir Bloc de Notas automáticamente
            self.log("Paso 2: Abriendo el Bloc de Notas (Notepad)...", "info")
            self.abrir_aplicacion_sistema("notepad.exe")
            time.sleep(1.0)

            # 3. Escribir texto en el Bloc de Notas
            self.log("Paso 3: Escribiendo texto de demostración en vivo...", "info")
            self.teclear("Hola! Esto es AutoPilot RPA controlando la computadora.\n", es_secreto=False)
            time.sleep(0.5)
            self.teclear("Viendo el movimiento del raton, teclado y apertura de aplicaciones automaticas.\n", es_secreto=False)
            time.sleep(0.5)
            self.teclear("Todo listo para automatizar tus tareas diarias!", es_secreto=False)

            # 4. Movimiento final en círculo/cuadrado con el ratón
            self.log("Paso 4: Realizando clics y trayectorias en pantalla...", "info")
            cx, cy = int(ancho * 0.5), int(alto * 0.5)
            for dx, dy in [(50, 50), (-50, 50), (-50, -50), (50, -50), (0, 0)]:
                self.mover_raton_animado(cx + dx, cy + dy, duracion=0.3)

            duracion = round(time.time() - inicio, 2)
            self.log(f"=== Demostración visual completada con éxito en {duracion}s ===", "ok")
            return True

        except InterruptedError as parada:
            self.log(str(parada), "error")
            return False
        except Exception as error:
            self.log(f"ERROR en demostración: {error}", "error")
            return False

    def ejecutar_flujo_login(self, perfil: str) -> bool:
        """Realiza un inicio de sesión usando las credenciales guardadas.

        Estrategia:
          1. Recupera las credenciales cifradas del perfil.
          2. Intenta la vía NATIVA (Pywinauto) enfocando la ventana destino.
          3. Si no existe la ventana, usa la vía VISUAL (PyAutoGUI):
             usuario -> TAB -> contraseña -> ENTER.
          4. Verifica el resultado esperando a que desaparezca el login.

        Devuelve True si terminó sin errores.
        """
        self.reiniciar_estado()
        inicio = time.time()

        datos = self.credenciales.obtener(perfil)
        if not datos:
            self.log(f"No existen credenciales guardadas para el perfil '{perfil}'.", "error")
            return False

        self.log(f"=== Iniciando flujo de login para '{perfil}' ===")

        try:
            destino = (datos.get("destino") or "").strip()

            # --- Paso 1: preparar la ventana destino -----------------------
            if destino and PYWINAUTO_DISPONIBLE:
                try:
                    self.enfocar_ventana(destino)
                except (TiempoAgotadoError, RuntimeError):
                    self.log(
                        "No se encontró la ventana nativa; se continúa en modo visual.",
                        "warn",
                    )

            # --- Paso 2: escribir usuario ----------------------------------
            self.log("Escribiendo el nombre de usuario...")
            self.teclear(datos["usuario"])

            # --- Paso 3: pasar al campo de contraseña ----------------------
            self.pulsar("tab")

            # --- Paso 4: escribir contraseña (nunca se muestra en el log) --
            self.log("Escribiendo la contraseña (oculta)...")
            self.teclear(datos["contrasena"], es_secreto=True)

            # --- Paso 5: confirmar -----------------------------------------
            self.pulsar("enter")

            # --- Paso 6: espera inteligente de confirmación ----------------
            self.log("Esperando la carga posterior al inicio de sesión...")
            try:
                esperar_hasta(
                    lambda: True,  # Sustituir por una comprobación real del sistema destino
                    tiempo_limite=3,
                    descripcion="confirmación de sesión",
                    cancelado=lambda: self.detenido,
                )
            except TiempoAgotadoError:
                self.log("No se confirmó la sesión dentro del tiempo límite.", "warn")

            duracion = round(time.time() - inicio, 2)
            self.log(f"=== Flujo completado con éxito en {duracion}s ===", "ok")
            return True

        except InterruptedError as parada:
            self.log(str(parada), "error")
            return False
        except TiempoAgotadoError as agotado:
            self.log(f"FALLO por tiempo: {agotado}", "error")
            return False
        except Exception as error:  # Cualquier otro fallo inesperado
            self.log(f"ERROR inesperado: {error}", "error")
            return False

    def ejecutar_tarea_grabada(self, pasos: list) -> bool:
        """Ejecuta una secuencia personalizada de pasos grabados por el usuario.

        Tipos de pasos soportados:
          - "mover": {"x": int, "y": int, "duracion": float}
          - "clic": {"x": int, "y": int, "tipo_clic": str}
          - "teclear": {"texto": str}
          - "pulsar": {"teclas": list}
          - "abrir_app": {"comando": str}
          - "espera": {"segundos": float}
        """
        self.reiniciar_estado()
        inicio = time.time()
        self.log(f"=== INICIANDO TAREA GRABADA ({len(pasos)} pasos) ===", "ok")

        try:
            for idx, paso in enumerate(pasos, 1):
                self._punto_de_control()
                tipo = paso.get("tipo")
                self.log(f"Paso {idx}/{len(pasos)}: {tipo.upper()}", "info")

                if tipo == "mover":
                    self.mover_raton_animado(paso.get("x", 0), paso.get("y", 0), duracion=paso.get("duracion", 0.7))

                elif tipo == "clic":
                    self.clic_en_coordenadas(paso.get("x", 0), paso.get("y", 0))

                elif tipo == "teclear":
                    self.teclear(paso.get("texto", ""), es_secreto=paso.get("secreto", False))

                elif tipo == "pulsar":
                    teclas = paso.get("teclas", ["enter"])
                    if isinstance(teclas, str):
                        teclas = [teclas]
                    self.pulsar(*teclas)

                elif tipo == "abrir_app":
                    self.abrir_aplicacion_sistema(paso.get("comando", ""))

                elif tipo == "espera":
                    seg = paso.get("segundos", 1.0)
                    self.log(f"Esperando {seg}s...", "info")
                    time.sleep(seg)

                # Pausa breve entre pasos para mayor estabilidad visual
                time.sleep(0.3)

            duracion = round(time.time() - inicio, 2)
            self.log(f"=== Tarea completada con éxito en {duracion}s ===", "ok")
            return True

        except InterruptedError as parada:
            self.log(str(parada), "error")
            return False
        except Exception as error:
            self.log(f"ERROR ejecutando tarea: {error}", "error")
            return False

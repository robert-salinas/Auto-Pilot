"""
===============================================================================
 core/grabador.py - Grabación Simultánea en Vivo de Clics y Combinaciones de Teclas
===============================================================================
 Escucha eventos globales del sistema operativo (clics, trayectorias del ratón,
 escritura normal y combinaciones de teclas como Ctrl+C, Ctrl+V, Alt+Tab, etc.)
 en tiempo real usando pynput.
===============================================================================
"""

import json
import os
import logging
from typing import List, Dict, Any, Optional, Callable

from pynput import mouse, keyboard

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_TAREAS = os.path.join(RAIZ, "recursos", "tareas")


class GestorTareas:
    """Administra la lectura y escritura de tareas personalizadas en formato JSON."""

    def __init__(self) -> None:
        os.makedirs(CARPETA_TAREAS, exist_ok=True)

    def _ruta_tarea(self, nombre: str) -> str:
        nombre_limpio = "".join(c for c in nombre if c.isalnum() or c in ("_", "-")).strip()
        return os.path.join(CARPETA_TAREAS, f"{nombre_limpio}.json")

    def guardar_tarea(self, nombre: str, pasos: List[Dict[str, Any]], descripcion: str = "") -> str:
        """Guarda una lista de pasos en un archivo JSON."""
        ruta = self._ruta_tarea(nombre)
        contenido = {
            "nombre": nombre,
            "descripcion": descripcion,
            "pasos": pasos
        }
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(contenido, f, indent=2, ensure_ascii=False)
        logging.info("Tarea '%s' guardada con %d pasos en %s", nombre, len(pasos), ruta)
        return ruta

    def obtener_tarea(self, nombre: str) -> Optional[Dict[str, Any]]:
        """Carga los datos de una tarea desde su archivo JSON."""
        ruta = self._ruta_tarea(nombre)
        if not os.path.exists(ruta):
            return None
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as err:
            logging.error("Error leyendo tarea '%s': %s", nombre, err)
            return None

    def listar_tareas(self) -> List[str]:
        """Devuelve los nombres de todas las tareas guardadas."""
        if not os.path.exists(CARPETA_TAREAS):
            return []
        archivos = os.listdir(CARPETA_TAREAS)
        nombres = []
        for arch in archivos:
            if arch.endswith(".json"):
                nombres.append(arch[:-5])
        return sorted(nombres)

    def eliminar_tarea(self, nombre: str) -> bool:
        """Elimina el archivo de una tarea."""
        ruta = self._ruta_tarea(nombre)
        if os.path.exists(ruta):
            os.remove(ruta)
            logging.info("Tarea '%s' eliminada.", nombre)
            return True
        return False


class GrabadorEnVivo:
    """Escucha clics del ratón, coordenadas y combinaciones de teclado simultáneamente en vivo."""

    def __init__(self, al_capturar_paso: Optional[Callable[[Dict[str, Any]], None]] = None) -> None:
        self.al_capturar_paso = al_capturar_paso
        self.pasos_grabados: List[Dict[str, Any]] = []
        self._grabando = False
        self._listener_mouse = None
        self._listener_teclado = None
        self._buffer_texto = ""
        self._teclas_modificadoras = set()

    def iniciar(self) -> None:
        """Inicia los listeners en segundo plano para captura en tiempo real."""
        if self._grabando:
            return
        self._grabando = True
        self.pasos_grabados.clear()
        self._buffer_texto = ""
        self._teclas_modificadoras.clear()

        self._listener_mouse = mouse.Listener(on_click=self._al_hacer_clic)
        self._listener_teclado = keyboard.Listener(
            on_press=self._al_presionar_tecla,
            on_release=self._al_soltar_tecla
        )

        self._listener_mouse.start()
        self._listener_teclado.start()
        logging.info("Grabación en vivo con soporte de combinaciones iniciada.")

    def detener(self) -> List[Dict[str, Any]]:
        """Detiene la captura en vivo y consolida la lista de pasos."""
        if not self._grabando:
            return self.pasos_grabados
        self._grabando = False

        self._vaciar_buffer_texto()

        if self._listener_mouse:
            self._listener_mouse.stop()
        if self._listener_teclado:
            self._listener_teclado.stop()

        logging.info("Grabación en vivo finalizada con %d pasos.", len(self.pasos_grabados))
        return list(self.pasos_grabados)

    def _registrar_paso(self, paso: Dict[str, Any]) -> None:
        self.pasos_grabados.append(paso)
        if self.al_capturar_paso:
            self.al_capturar_paso(paso)

    def _vaciar_buffer_texto(self) -> None:
        if self._buffer_texto:
            paso = {"tipo": "teclear", "texto": self._buffer_texto}
            self._buffer_texto = ""
            self._registrar_paso(paso)

    def _al_hacer_clic(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if not self._grabando or not pressed:
            return

        self._vaciar_buffer_texto()
        paso = {
            "tipo": "clic",
            "x": int(x),
            "y": int(y),
            "boton": "left" if button == mouse.Button.left else "right"
        }
        self._registrar_paso(paso)

    def _al_presionar_tecla(self, key) -> None:
        if not self._grabando:
            return

        nombre_tecla = None
        try:
            if hasattr(key, 'char') and key.char:
                nombre_tecla = key.char.lower()
        except AttributeError:
            pass

        if not nombre_tecla:
            nombre_tecla = str(key).replace("Key.", "").lower()

        # Si presiona una tecla modificadora (ctrl, alt, shift)
        if nombre_tecla in ("ctrl", "ctrl_l", "ctrl_r", "alt", "alt_l", "alt_r", "shift", "shift_l", "shift_r", "cmd", "cmd_l", "cmd_r"):
            mod = "ctrl" if "ctrl" in nombre_tecla else ("alt" if "alt" in nombre_tecla else ("shift" if "shift" in nombre_tecla else "win"))
            self._teclas_modificadoras.add(mod)
            return

        # Si hay modificadores activos (ej: Ctrl+C, Ctrl+V, Alt+Tab, Ctrl+A)
        if self._teclas_modificadoras:
            self._vaciar_buffer_texto()
            combo = sorted(list(self._teclas_modificadoras)) + [nombre_tecla]
            paso = {"tipo": "pulsar", "teclas": combo}
            self._registrar_paso(paso)
            return

        # Teclas especiales sueltas (Enter, Tab, Backspace, etc.)
        if nombre_tecla in ("enter", "tab", "backspace", "esc", "space", "delete", "up", "down", "left", "right"):
            self._vaciar_buffer_texto()
            if nombre_tecla == "space":
                self._buffer_texto += " "
            else:
                paso = {"tipo": "pulsar", "teclas": [nombre_tecla]}
                self._registrar_paso(paso)
            return

        # Carácter normal escrito
        if hasattr(key, 'char') and key.char:
            self._buffer_texto += key.char

    def _al_soltar_tecla(self, key) -> None:
        if not self._grabando:
            return

        nombre_tecla = str(key).replace("Key.", "").lower()
        if "ctrl" in nombre_tecla:
            self._teclas_modificadoras.discard("ctrl")
        elif "alt" in nombre_tecla:
            self._teclas_modificadoras.discard("alt")
        elif "shift" in nombre_tecla:
            self._teclas_modificadoras.discard("shift")
        elif "cmd" in nombre_tecla:
            self._teclas_modificadoras.discard("win")

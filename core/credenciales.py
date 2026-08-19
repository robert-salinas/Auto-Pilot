"""
===============================================================================
 core/credenciales.py - Gestión SEGURA de usuarios y contraseñas
===============================================================================
 Estrategia de seguridad (nunca se "queman" credenciales en el código):

   1. Se genera automáticamente una clave maestra (Fernet / AES-128 + HMAC)
      guardada en recursos/clave.key con permisos del usuario actual.
   2. Las credenciales se guardan CIFRADAS en el archivo .env, en la forma:
         PERFIL_<NOMBRE>=<cadena_cifrada_base64>
   3. Al leerlas, se descifran solo en memoria; jamás se escriben en claro.

 Si el archivo clave.key se pierde, las credenciales antiguas dejan de poder
 descifrarse (comportamiento esperado y deseable en seguridad).
===============================================================================
"""

import json
import os
import logging
from typing import Dict, Optional

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv, set_key, unset_key, dotenv_values

# ---------------------------------------------------------------------------
# Rutas de los archivos usados por el gestor
# ---------------------------------------------------------------------------
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_RECURSOS = os.path.join(RAIZ, "recursos")
RUTA_CLAVE = os.path.join(CARPETA_RECURSOS, "clave.key")
RUTA_ENV = os.path.join(RAIZ, ".env")

PREFIJO = "PERFIL_"  # Prefijo con el que identificamos cada perfil en el .env


class GestorCredenciales:
    """Guarda, lee y elimina credenciales cifradas asociadas a un 'perfil'.

    Un perfil representa un sitio o aplicación (por ejemplo: 'INTRANET',
    'SAP', 'CORREO'), y contiene usuario, contraseña y una URL/ruta opcional.
    """

    def __init__(self) -> None:
        os.makedirs(CARPETA_RECURSOS, exist_ok=True)
        self._fernet = Fernet(self._obtener_o_crear_clave())
        # Creamos el .env si aún no existe para evitar errores de escritura
        if not os.path.exists(RUTA_ENV):
            with open(RUTA_ENV, "w", encoding="utf-8") as archivo:
                archivo.write("# Credenciales cifradas de AutoPilot RPA\n")
        load_dotenv(RUTA_ENV, override=True)

    # ------------------------------------------------------------------ #
    # Clave maestra
    # ------------------------------------------------------------------ #
    @staticmethod
    def _obtener_o_crear_clave() -> bytes:
        """Devuelve la clave maestra; la crea la primera vez que se ejecuta."""
        if os.path.exists(RUTA_CLAVE):
            with open(RUTA_CLAVE, "rb") as archivo:
                return archivo.read().strip()

        clave = Fernet.generate_key()
        with open(RUTA_CLAVE, "wb") as archivo:
            archivo.write(clave)
        logging.info("Se generó una nueva clave maestra de cifrado.")
        return clave

    # ------------------------------------------------------------------ #
    # Operaciones públicas
    # ------------------------------------------------------------------ #
    def guardar(self, perfil: str, usuario: str, contrasena: str,
                destino: str = "") -> None:
        """Cifra y almacena las credenciales de un perfil en el archivo .env."""
        perfil = self._normalizar(perfil)
        datos = {"usuario": usuario, "contrasena": contrasena, "destino": destino}
        cifrado = self._fernet.encrypt(json.dumps(datos).encode("utf-8")).decode()
        set_key(RUTA_ENV, f"{PREFIJO}{perfil}", cifrado)
        logging.info("Credenciales del perfil '%s' guardadas de forma cifrada.", perfil)

    def obtener(self, perfil: str) -> Optional[Dict[str, str]]:
        """Devuelve un diccionario con usuario/contrasena/destino, o None."""
        perfil = self._normalizar(perfil)
        valores = dotenv_values(RUTA_ENV)
        cifrado = valores.get(f"{PREFIJO}{perfil}")
        if not cifrado:
            return None
        try:
            return json.loads(self._fernet.decrypt(cifrado.encode()).decode("utf-8"))
        except (InvalidToken, ValueError):
            logging.error("No se pudo descifrar el perfil '%s' (clave incorrecta).", perfil)
            return None

    def eliminar(self, perfil: str) -> None:
        """Elimina por completo un perfil del archivo .env."""
        perfil = self._normalizar(perfil)
        unset_key(RUTA_ENV, f"{PREFIJO}{perfil}")
        logging.info("Perfil '%s' eliminado.", perfil)

    def listar_perfiles(self) -> list:
        """Devuelve la lista de nombres de perfiles almacenados."""
        valores = dotenv_values(RUTA_ENV)
        return sorted(
            clave[len(PREFIJO):] for clave in valores if clave.startswith(PREFIJO)
        )

    # ------------------------------------------------------------------ #
    # Utilidades internas
    # ------------------------------------------------------------------ #
    @staticmethod
    def _normalizar(perfil: str) -> str:
        """Convierte el nombre a MAYÚSCULAS y sin espacios (formato de variable)."""
        return perfil.strip().upper().replace(" ", "_")

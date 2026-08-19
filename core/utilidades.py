"""
===============================================================================
 core/utilidades.py - Esperas inteligentes y helpers de automatización
===============================================================================
 Aquí vive la pieza clave de robustez del bot: NUNCA usamos time.sleep fijo
 para esperar a que algo aparezca. En su lugar usamos bucles de reintento con
 tiempo límite (polling), de modo que:

   - Si el equipo va rápido, el bot continúa de inmediato.
   - Si el equipo/página va lento, el bot espera hasta el límite configurado.
===============================================================================
"""

import time
import logging
from typing import Callable, Any, Optional


class TiempoAgotadoError(Exception):
    """Se lanza cuando una espera inteligente supera su tiempo límite."""


def esperar_hasta(
    condicion: Callable[[], Any],
    tiempo_limite: float = 15.0,
    intervalo: float = 0.4,
    descripcion: str = "condición",
    cancelado: Optional[Callable[[], bool]] = None,
) -> Any:
    """Ejecuta `condicion()` repetidamente hasta que devuelva un valor "verdadero".

    Parámetros
    ----------
    condicion    : función sin argumentos; se considera cumplida si su
                   resultado no es None/False/"" (valor "truthy").
    tiempo_limite: segundos máximos de espera antes de fallar.
    intervalo    : pausa entre reintentos (evita saturar la CPU).
    descripcion  : texto para los mensajes de log/errores.
    cancelado    : función opcional que devuelve True si el usuario pulsó
                   "Detener"; permite abortar la espera al instante.

    Devuelve
    --------
    El valor devuelto por `condicion()` en cuanto se cumple.

    Lanza
    -----
    TiempoAgotadoError si se supera `tiempo_limite`.
    InterruptedError   si `cancelado()` devuelve True.
    """
    inicio = time.time()
    intentos = 0

    while time.time() - inicio < tiempo_limite:
        if cancelado is not None and cancelado():
            raise InterruptedError("Automatización detenida por el usuario.")

        intentos += 1
        try:
            resultado = condicion()
            if resultado:
                transcurrido = round(time.time() - inicio, 2)
                logging.info(
                    "OK -> %s encontrada en %ss (%d intentos).",
                    descripcion, transcurrido, intentos,
                )
                return resultado
        except Exception as error:  # La condición puede fallar mientras carga
            logging.debug("Reintento de '%s': %s", descripcion, error)

        time.sleep(intervalo)

    raise TiempoAgotadoError(
        f"Tiempo agotado ({tiempo_limite}s) esperando: {descripcion}"
    )


def reintentar(
    accion: Callable[[], Any],
    intentos: int = 3,
    espera_entre: float = 1.0,
    descripcion: str = "acción",
) -> Any:
    """Ejecuta una acción y la reintenta si lanza una excepción.

    Útil para clics o escrituras que pueden fallar puntualmente
    (ventana que aún no tiene el foco, por ejemplo).
    """
    ultimo_error: Optional[Exception] = None

    for numero in range(1, intentos + 1):
        try:
            return accion()
        except Exception as error:
            ultimo_error = error
            logging.warning(
                "Fallo en '%s' (intento %d/%d): %s", descripcion, numero, intentos, error
            )
            time.sleep(espera_entre)

    raise RuntimeError(f"La acción '{descripcion}' falló tras {intentos} intentos: {ultimo_error}")

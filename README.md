# AutoPilot RPA

**AutoPilot RPA** es una potente aplicación de escritorio desarrollada en Python para la automatización de tareas repetitivas e inicios de sesión seguros mediante técnicas híbridas (control nativo de Windows, reconocimiento visual, y grabación en vivo de tareas).

---

## Características Principales

- **Grabación en Vivo de Tareas (Live Task Recorder)**: Captura y graba interacciones del usuario (clics del ratón, entrada de teclado) en tiempo real para crear tareas reutilizables automáticamente.
- **Gestión Segura de Credenciales**: Cifrado fuerte AES-128 (Fernet) para contraseñas. Nunca almacena claves en texto plano.
- **Automatización Híbrida**:
  - **Vía Nativa (Pywinauto)**: Identificación y control directo de elementos UI en Windows.
  - **Vía Visual (PyAutoGUI + OpenCV)**: Control por coordenadas e imágenes cuando las aplicaciones no exponen controles nativos.
- **Interfaz Moderna**: GUI desarrollada con **PySide6 (Qt 6)** con tema oscuro profesional y consola de logs en tiempo real.
- **Seguridad Operativa**:
  - Parada de emergencia global vía teclado (`CTRL + ALT + Q`).
  - Esquina de seguridad de PyAutoGUI (`FAILSAFE`).
  - Ejecución en segundo plano mediante hilos independientes (`QThread`) para evitar congelamientos.

---

## Estructura del Proyecto

```text
Automatizacion de Escritorio/
├── core/                   # Lógica de automatización, seguridad y backend
│   ├── __init__.py
│   ├── atajos.py          # Listener para la parada de emergencia global
│   ├── credenciales.py    # Gestor de cifrado y archivo .env
│   ├── grabador.py        # Grabador en vivo de tareas (pynput)
│   ├── motor.py           # Motor principal de PyAutoGUI / Pywinauto
│   ├── registro.py        # Configuración del sistema de logs
│   └── utilidades.py      # Esperas inteligentes y reintentos
├── gui/                    # Interfaz de usuario (PySide6)
│   ├── __init__.py
│   ├── estilos.py         # Hojas de estilo QSS
│   ├── hilo_trabajo.py    # Hilo QThread para no congelar la GUI
│   ├── overlay_grabacion.py # Overlay flotante para grabación en vivo
│   └── ventana_principal.py # Ventana y componentes visuales
├── assets/                 # Imágenes de referencia e iconos
├── recursos/               # Clave maestra y registros de ejecución (.log)
├── main.py                 # Punto de entrada de la aplicación
├── instalar.bat            # Script de instalación y arranque rápido
└── requirements.txt        # Librerías necesarias
```

---

## Instalación y Uso

### Opción 1: Inicio Rápido (Windows)
Simplemente haz doble clic en `instalar.bat`. El script creará un entorno virtual (`venv`), instalará las dependencias necesarias y lanzará la aplicación automáticamente.

### Opción 2: Instalación Manual

1. Clonar o descargar el proyecto.
2. Crear e iniciar un entorno virtual de Python:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Ejecutar la aplicación:
   ```bash
   python main.py
   ```

---

## Dependencias

- **pynput** (5.0+) - Captura global de eventos de teclado y ratón para la grabación en vivo de tareas. Permite monitorear interacciones del usuario en tiempo real sin importar qué aplicación tenga el foco.
- **PyAutoGUI** - Control del ratón y teclado, ejecución de clics y escritura de texto.
- **Pywinauto** - Acceso a controles nativos de Windows (opcional, para aplicaciones con UI expuesta).
- **OpenCV** - Procesamiento visual de imágenes para reconocimiento basado en visión.
- **PySide6** - Framework Qt 6 para la interfaz gráfica moderna.
- **cryptography** - Cifrado AES-128 de credenciales.

---

## Grabación en Vivo de Tareas (Live Task Recording)

### ¿Cómo usar la grabación en vivo?

La característica de "Grabador de Tareas en Vivo" te permite grabar tus interacciones (clics del ratón, entrada de teclado) para convertirlas automáticamente en tareas reutilizables.

#### Iniciando una Sesión de Grabación

1. Abre la aplicación **AutoPilot RPA**
2. Haz clic en el botón **"Iniciar Grabación en Vivo"** (botón cian en la interfaz principal)
3. Un overlay flotante aparecerá en la **esquina superior derecha** de la pantalla con:
   - Un **contador de pasos** que muestra cuántas interacciones se han capturado
   - Un botón **"Finalizar y Guardar"** para detener la grabación

#### Grabando Interacciones

Mientras el grabador está activo:
- **Clics del ratón**: Se capturan automáticamente con sus coordenadas (x, y)
- **Entrada de teclado**: Se registran todas las pulsaciones de teclas:
  - Caracteres alfanuméricos (a-z, A-Z, 0-9)
  - Teclas especiales (Enter, Tab, Backspace, Delete, Escape, etc.)
  - Combinaciones de teclas (Shift+Letra, Ctrl+V, Alt+Tab, etc.)
- **Contador en vivo**: El overlay actualiza el contador de pasos en tiempo real

#### Deteniendo la Grabación

1. Haz clic en **"Finalizar y Guardar"** en el overlay
2. La grabación se detiene inmediatamente
3. El overlay se cierra
4. Todos los pasos capturados aparecen en la tabla **"Pasos Grabados"** en la pestaña de grabación

#### Guardando la Tarea Grabada

1. En la tabla de pasos, revisa los pasos capturados
2. Haz clic en **"Guardar Tarea"**
3. Selecciona o crea un **perfil** (nombre de la tarea)
4. La tarea se guarda en `recursos/tareas/` como un archivo JSON

#### Replicando una Tarea Grabada

1. Ve a la pestaña **"Reproducir"**
2. Selecciona la tarea que grabaste
3. Haz clic en **"Probar Demostración Visual"** para una previsualización
4. Haz clic en **"Iniciar Login"** para ejecutar la tarea completa
5. Usa los botones de **"Pausar"** y **"Detener"** para controlar la ejecución

### Eventos de Teclado Capturados

Los siguientes eventos se graban como pasos individuales:
- **Pulsación de tecla**: Cada carácter (a, b, c, 1, 2, @, etc.)
- **Combinaciones**: Shift, Ctrl, Alt + letra/número
- **Teclas funcionales**: Tab, Enter, Backspace, Delete, Escape, Inicio, Fin, Re Pág, Av Pág
- **Teclas de dirección**: Arriba, Abajo, Izquierda, Derecha
- **Teclas del sistema**: Pausa, Bloqueo Mayús, Impresión de pantalla

### Limitaciones de la Grabación

- **Movimiento del ratón sin clics**: No se captura. Solo se registran clics con coordenadas.
- **Gestos multitoque**: No soportados (pantallas táctiles).
- **Aplicaciones con restricciones**: Algunas aplicaciones de seguridad pueden bloquear la captura de entrada.
- **Retraso de reproducción**: La velocidad de reproducción es la que grabaste. Para acelerar, usa el control de velocidad en la GUI.

---

## Paradas de Emergencia

El bot incluye 3 mecanismos independientes para abortar una automatización en cualquier momento:

1. **Atajo Global de Teclado**: Presiona `CTRL + ALT + Q` (funciona aunque la ventana no tenga el foco).
2. **Esquina de Seguridad (PyAutoGUI FAILSAFE)**: Mueve rápidamente el puntero del ratón hacia la **esquina superior izquierda** de la pantalla.
3. **Botonera GUI**: Presiona el botón rojo **Detener (Emergencia)** en el panel de la aplicación.

---

## Seguridad y Privacidad

- Las credenciales introducidas en la pestaña **Credenciales** se cifran individualmente y se guardan en el archivo `.env`.
- La clave de cifrado se genera automáticamente en `recursos/clave.key`. **Nunca compartas ni subas este archivo a repositorios públicos.**
- Las tareas grabadas se guardan como archivos JSON en `recursos/tareas/`. Revisa su contenido si necesitas verificar qué se grabó.

---

## Solución de Problemas

### La grabación no captura nada

- Asegúrate de que la ventana de la aplicación o la ventana de destino tenga el foco cuando hagas clics
- Algunos antivirus pueden bloquear `pynput`. Añade la carpeta del proyecto a la lista blanca del antivirus

### Los clics grabados no se reproducen en el sitio correcto

- El grabador registra coordenadas de pantalla absolutas. Si cambias la resolución o el tamaño de la ventana entre grabación y reproducción, los clics pueden no coincidir
- Verifica que la aplicación tenga la misma posición en pantalla durante la reproducción

### La aplicación se congela durante la reproducción

- Usa el botón **"Pausar"** para detener temporalmente y luego **"Reanudar"**
- Si se congela completamente, usa `CTRL + ALT + Q` para parada de emergencia



@echo off
chcp 65001 > nul
title Instalador y Configurador de AutoPilot RPA

set "RAIZ=%~dp0"
cd /d "%RAIZ%"

echo ===============================================================================
echo                   AutoPilot RPA - Instalacion y Configuracion
echo ===============================================================================
echo.

IF NOT EXIST "venv" (
    echo [1/4] Creando entorno virtual de Python (venv)...
    python -m venv venv
    IF ERRORLEVEL 1 (
        echo [ERROR] No se pudo crear el entorno virtual. Asegurese de tener Python instalado.
        pause
        exit /b 1
    )
) ELSE (
    echo [1/4] Entorno virtual existente detectado.
)

echo [2/4] Instalando / Actualizando dependencias requeridas...
call venv\Scripts\activate.bat
pip install --upgrade pip > nul
pip install -r requirements.txt

IF ERRORLEVEL 1 (
    echo [ERROR] Hubo un problema instalando los paquetes de requirements.txt.
    pause
    exit /b 1
)

echo [3/4] Creando acceso directo en el Escritorio...
cscript //nologo crear_acceso_directo.vbs

echo [4/4] Iniciando AutoPilot RPA (GUI)...
echo.
start "" "venv\Scripts\pythonw.exe" main.py

exit /b 0

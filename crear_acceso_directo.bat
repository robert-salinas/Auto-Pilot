@echo off
chcp 65001 > nul
title Crear Acceso Directo en el Escritorio

set "RAIZ=%~dp0"
set "TARGET=%RAIZ%iniciar_gui.bat"

echo Creando acceso directo en el Escritorio de Windows...

powershell -Command "$desktop = [System.Environment]::GetFolderPath('Desktop'); $lnk = [System.IO.Path]::Combine($desktop, 'AutoPilot RPA.lnk'); $ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut($lnk); $s.TargetPath = '%TARGET%'; $s.WorkingDirectory = '%RAIZ%'; $s.Save(); write-host '[OK] Acceso directo AutoPilot RPA creado en:' $lnk"

pause

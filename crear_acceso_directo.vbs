Set WshShell = CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")

' Get the directory where this VBS script is located (the project root)
strScriptPath = WScript.ScriptFullName
strProjectDir = WshShell.CurrentDirectory

' Create shortcut
Set objLink = WshShell.CreateShortcut(strDesktop & "\AutoPilot RPA.lnk")
objLink.TargetPath = strProjectDir & "\iniciar_gui.bat"
objLink.WorkingDirectory = strProjectDir
objLink.Description = "AutoPilot RPA - Automatizacion de Escritorio"
objLink.IconLocation = strProjectDir & "\assets\icon.ico"
objLink.Save

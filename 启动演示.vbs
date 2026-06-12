Set WshShell = CreateObject("WScript.Shell")
pythonPath = "C:\Program Files\Python312\python.exe"
scriptPath = WshShell.CurrentDirectory & "\demo.py"

WshShell.Run "cmd /c chcp 65001 >nul && """ & pythonPath & """ """ & scriptPath & """ && pause", 1, False
Set WshShell = Nothing

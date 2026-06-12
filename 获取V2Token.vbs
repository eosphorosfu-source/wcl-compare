Set WshShell = CreateObject("WScript.Shell")
pythonPath = "C:\Program Files\Python312\python.exe"
scriptPath = WshShell.CurrentDirectory & "\setup_v2_token.py"
WshShell.Run "cmd /k chcp 65001 >nul && """ & pythonPath & """ """ & scriptPath & """", 1, False
Set WshShell = Nothing

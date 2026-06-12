Set WshShell = CreateObject("WScript.Shell")
pythonPath = "C:\Program Files\Python312\python.exe"
scriptPath = WshShell.CurrentDirectory & "\web_app.py"
url = "http://127.0.0.1:5000"

' Start Flask server, keep cmd window open
WshShell.Run "cmd /k chcp 65001 >nul && """ & pythonPath & """ """ & scriptPath & """", 1, False

' Wait for server startup
WScript.Sleep 2500

' Open browser
WshShell.Run url, 1, False

Set WshShell = Nothing

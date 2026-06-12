Set WshShell = CreateObject("WScript.Shell")
pythonPath = "C:\Program Files\Python312\python.exe"
scriptPath = WshShell.CurrentDirectory & "\interactive_run.py"

' 用 /k 保持窗口打开，chcp 65001 设置 UTF-8
WshShell.Run "cmd /k chcp 65001 >nul && """ & pythonPath & """ """ & scriptPath & """", 1, False

Set WshShell = Nothing

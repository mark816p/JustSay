Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "venv\Scripts\python.exe" & chr(34) & " main.py", 0
Set WshShell = Nothing

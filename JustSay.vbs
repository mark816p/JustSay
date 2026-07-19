Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currentDir
WshShell.Run chr(34) & currentDir & "\venv\Scripts\pythonw.exe" & chr(34) & " main.py", 0
Set WshShell = Nothing

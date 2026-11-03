Set WshShell = CreateObject("WScript.Shell")
strPath = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
strScript = strPath & "joint_life_desktop.py"
WshShell.Run "python " & Chr(34) & strScript & Chr(34), 0, False

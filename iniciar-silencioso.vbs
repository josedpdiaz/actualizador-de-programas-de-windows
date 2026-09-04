Set WshShell = CreateObject("WScript.Shell")

' 1. Si la ventana ya esta abierta, enfocarla inmediatamente y salir
If WshShell.AppActivate("Actualizador de Programas") Then
    WScript.Quit 0
End If

' 2. Si el servidor ya esta corriendo, abrir la ventana una sola vez
On Error Resume Next
Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
http.open "GET", "http://127.0.0.1:5055/api/status", False
http.setTimeouts 400, 400, 400, 400
http.send

If Err.Number = 0 And http.status = 200 Then
    WshShell.Run "msedge.exe --app=http://127.0.0.1:5055 --window-size=1320,860", 1, False
    WScript.Quit 0
End If
On Error Goto 0

' 3. Si no estaba corriendo, iniciar el servidor normalmente
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run "python app.py", 0, False

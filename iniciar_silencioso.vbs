' iniciar_silencioso.vbs
' Inicia el backend y frontend del Dashboard SEACE sin mostrar ventanas.
' Se puede ejecutar directamente o via Tarea Programada de Windows.

Dim sh, ruta

Set sh = CreateObject("WScript.Shell")
ruta = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))

' --- Verificar si el backend ya corre ---
Dim puerto8000
On Error Resume Next
Set puerto8000 = CreateObject("Scripting.FileSystemObject")
Dim objShell2
Set objShell2 = CreateObject("WScript.Shell")
Dim resultado
resultado = objShell2.Run("cmd /c netstat -ano | find "":8000"" | find ""LISTENING""", 0, True)
On Error GoTo 0

If resultado = 0 Then
    ' Ya esta corriendo - abrir navegador y salir
    sh.Run "http://localhost:3000", 1, False
    WScript.Quit
End If

' --- Iniciar Backend (Python/FastAPI) sin ventana ---
' Usamos pythonw para no mostrar consola
Dim cmdBackend
cmdBackend = "cmd /c cd /d """ & ruta & "backend"" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > """ & ruta & "logs\backend.log"" 2>&1"
sh.Run cmdBackend, 0, False

' Esperar que el backend arranque (6 segundos)
WScript.Sleep 6000

' --- Iniciar Frontend (Next.js) sin ventana ---
Dim cmdFrontend
cmdFrontend = "cmd /c cd /d """ & ruta & "frontend"" && npm run dev > """ & ruta & "logs\frontend.log"" 2>&1"
sh.Run cmdFrontend, 0, False

' Esperar que el frontend compile (20 segundos)
WScript.Sleep 20000

' --- Abrir el navegador ---
sh.Run "http://localhost:3000", 1, False

Set sh = Nothing

# Inicio opcional: Windows solicita elevación una vez para esta sesión.
# No modifica UAC, tareas programadas ni permisos persistentes.
$ErrorActionPreference = 'Stop'
try {
    $running = Invoke-RestMethod 'http://127.0.0.1:5055/api/status' -TimeoutSec 2
} catch { $running = $null }
if ($null -ne $running) {
    Write-Host 'El actualizador ya está abierto. Esta sesión sigue con sus permisos actuales.'
    Write-Host 'Cierra primero el servidor del actualizador antes de iniciar el modo administrador.'
    Read-Host 'Pulsa Intro para cerrar' | Out-Null
    exit 1
}
$pythonPath = (Get-Command python.exe -ErrorAction Stop).Source
$appPath = Join-Path $PSScriptRoot 'app.py'
Start-Process -FilePath $pythonPath -ArgumentList ('"' + $appPath + '"') -WorkingDirectory $PSScriptRoot -Verb RunAs -WindowStyle Hidden

# Script para instalar el Actualizador en la carpeta oculta de Programas de Windows
# y actualizar el acceso directo del Escritorio

$sourceDir = $PSScriptRoot
$targetDir = Join-Path $env:LOCALAPPDATA "Programs\ActualizadorProgramasWindows"
$desktopPath = [System.Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktopPath "Actualizador de Programas.lnk"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Instalador del Actualizador Automatico de Programas" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Origen (Copia de seguridad): $sourceDir"
Write-Host "Destino en Programas (Disco): $targetDir"

# 1. Crear directorio destino si no existe
if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
}

# 2. Copiar archivos del proyecto
$excludeList = @('__pycache__', '*.lock', '*.tmp')
Get-ChildItem -Path $sourceDir -Exclude $excludeList -Force | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $targetDir -Recurse -Force
}

# 2.1 Migrar el bundle de historial Git y el script de backup si existen en la carpeta padre
$parentDir = Split-Path -Parent $sourceDir
$bundlePath = Join-Path $parentDir "03-IA-ACTUALIZADOR-PROGRAMAS-WINDOWS-GIT-HISTORY.bundle"
$backupScriptPath = Join-Path $parentDir "backup-03-git-history.ps1"

if (Test-Path $bundlePath) {
    Copy-Item -Path $bundlePath -Destination $targetDir -Force
    Write-Host "[OK] Bundle de historial Git migrado a la carpeta de Programas." -ForegroundColor Green
}
if (Test-Path $backupScriptPath) {
    Copy-Item -Path $backupScriptPath -Destination $targetDir -Force
    Write-Host "[OK] Script de backup Git migrado a la carpeta de Programas." -ForegroundColor Green
}

# 3. Verificar que los archivos clave se copiaron correctamente
$requiredFiles = @("app.py", "iniciar.bat", "iniciar-silencioso.vbs", "web")
$allPresent = $true
foreach ($file in $requiredFiles) {
    $destFile = Join-Path $targetDir $file
    if (-not (Test-Path $destFile)) {
        Write-Host "Falta archivo: $destFile" -ForegroundColor Red
        $allPresent = $false
    }
}

if (-not $allPresent) {
    Write-Host "Error: No se copiaron todos los archivos necesarios." -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Archivos copiados correctamente a la carpeta de Programas." -ForegroundColor Green

# 4. Actualizar el Acceso Directo en el Escritorio
$wshShell = New-Object -ComObject WScript.Shell
$shortcut = $wshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "wscript.exe"
$shortcut.Arguments = "`"$targetDir\iniciar-silencioso.vbs`""
$shortcut.WorkingDirectory = $targetDir
$shortcut.Description = "Actualizador Automatico de Programas de Windows (winget)"
$shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,238"
$shortcut.Save()

Write-Host "[OK] Acceso directo del Escritorio actualizado:" -ForegroundColor Green
Write-Host "     Destino: $targetDir\iniciar-silencioso.vbs" -ForegroundColor Yellow

# 5. Tambien creamos un acceso directo opcional 'Actualizador (Consola)' por si desea ver la terminal de iniciar.bat
$shortcutBatPath = Join-Path $desktopPath "Actualizador de Programas (Consola).lnk"
$shortcutBat = $wshShell.CreateShortcut($shortcutBatPath)
$shortcutBat.TargetPath = Join-Path $targetDir "iniciar.bat"
$shortcutBat.WorkingDirectory = $targetDir
$shortcutBat.Description = "Actualizador Automatico de Programas (Modo Consola)"
$shortcutBat.IconLocation = "$env:SystemRoot\System32\shell32.dll,238"
$shortcutBat.Save()

Write-Host "[OK] Acceso directo con consola creado en: $shortcutBatPath" -ForegroundColor Green
Write-Host "Instalacion completada con exito." -ForegroundColor Cyan

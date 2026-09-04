$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$wshShell = New-Object -ComObject WScript.Shell
$desktopPath = [System.Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktopPath "Actualizador de Programas.lnk"

$shortcut = $wshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "wscript.exe"
$shortcut.Arguments = "`"$scriptDir\iniciar-silencioso.vbs`""
$shortcut.WorkingDirectory = $scriptDir
$shortcut.Description = "Actualizador Automatico de Programas de Windows (winget)"
$shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,238"
$shortcut.Save()

Write-Host "Acceso directo creado exitosamente en el Escritorio: $shortcutPath" -ForegroundColor Green

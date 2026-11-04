# Tiny Turbo Racers 3D — one-command Godot editor setup on Windows 10/11.
# Opens the actual project, NOT the previous WebView Android Studio folder.
$ErrorActionPreference = 'Stop'
$Version = '4.7.2'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallDir = Join-Path $env:LOCALAPPDATA 'RibhLab\Godot-4.7.2'
$Download = "https://github.com/godotengine/godot/releases/download/4.7.2-stable/Godot_v4.7.2-stable_win64.exe.zip"
$Executable = Join-Path $InstallDir 'Godot_v4.7.2-stable_win64.exe'

Write-Host 'Tiny Turbo Racers: setting up original Godot 3D game...' -ForegroundColor Cyan
if (-not (Test-Path $Executable)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    $Zip = Join-Path $env:TEMP 'Godot_v4.7.2-stable_win64.exe.zip'
    Write-Host 'Downloading official Godot 4.7.2...'
    Invoke-WebRequest -Uri $Download -OutFile $Zip -UseBasicParsing
    Expand-Archive -Path $Zip -DestinationPath $InstallDir -Force
    Remove-Item $Zip -Force
}
if (-not (Test-Path $Executable)) {
    throw "Godot is missing after extraction: $Executable"
}
if (-not (Test-Path (Join-Path $Root 'project.godot'))) {
    throw "project.godot not found in $Root"
}
Write-Host "Opening Godot 3D project from $Root" -ForegroundColor Green
& $Executable --editor --path $Root

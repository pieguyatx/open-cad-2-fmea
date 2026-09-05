<#
.SYNOPSIS
    Windows Headless Execution Wrapper for CAD Auto-DFMEA Generator.
    Used for terminal execution instead of the graphical interface.
#>

param (
    [Parameter(Mandatory=$true)]
    [string]$InputFile,
    [string]$OutputFile = "Windows_DFMEA.csv",
    [string]$ConfigPath = "config/rules.json",
    [switch]$UseAI
)

$FreeCADPaths = @(
    "C:\Program Files\FreeCAD 0.21\bin\freecadcmd.exe",
    "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe",
    "C:\Program Files\FreeCAD\bin\freecadcmd.exe",
    "$env:LOCALAPPDATA\Programs\FreeCAD\bin\freecadcmd.exe"
)

$FreeCADCmd = $null
foreach ($path in $FreeCADPaths) {
    if (Test-Path $path) {
        $FreeCADCmd = $path
        break
    }
}

if (-not $FreeCADCmd) {
    Write-Error "[Error] FreeCAD binary not found."
    exit 1
}

$ScriptArgs = @("main.py", "-i", "`"$InputFile`"", "-o", "`"$OutputFile`"", "--config", "`"$ConfigPath`"")

if ($UseAI) {
    $ScriptArgs += "--ai"
}

# '&' executes the string path as a command in PowerShell
& $FreeCADCmd $ScriptArgs
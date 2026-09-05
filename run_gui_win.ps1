<#
.SYNOPSIS
    Launches the Open-Source FMEA Generator GUI on Windows.
#>

$FreeCADPaths = @(
    "C:\Program Files\FreeCAD 0.21",
    "C:\Program Files\FreeCAD 1.0",
    "C:\Program Files\FreeCAD",
    "$env:LOCALAPPDATA\Programs\FreeCAD"
)

$FreeCADBase = $null
foreach ($path in $FreeCADPaths) {
    if (Test-Path "$path\bin\freecad.exe") {
        $FreeCADBase = $path
        break
    }
}

if (-not $FreeCADBase) {
    Write-Error "[Error] FreeCAD installation not detected. Please install FreeCAD via 'winget install FreeCAD.FreeCAD'."
    exit 1
}

$env:PATH = "$FreeCADBase\bin;$FreeCADBase\lib;" + $env:PATH
$env:PYTHONPATH = "$FreeCADBase\bin;$FreeCADBase\lib"

Write-Host "[*] Launching FMEA GUI Environment..." -ForegroundColor Green
python gui.py
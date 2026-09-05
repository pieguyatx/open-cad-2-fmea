<#
.SYNOPSIS
    Launches the Open-Source FMEA Generator GUI on Windows.
    
    ARCHITECTURE NOTE:
    This wrapper script ensures Windows can find the FreeCAD background files.
    Running `python gui.py` directly usually fails because Python doesn't know 
    where FreeCAD's C++ DLLs are located. This script temporarily adds them 
    to the system environment variables before launching.
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

# Attach paths so the script can resolve underlying FreeCAD dependencies 
$env:PATH = "$FreeCADBase\bin;$FreeCADBase\lib;" + $env:PATH
$env:PYTHONPATH = "$FreeCADBase\bin;$FreeCADBase\lib"

Write-Host "[*] Launching FMEA GUI Environment..." -ForegroundColor Green
python gui.py
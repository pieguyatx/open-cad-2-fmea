# Open-Source CAD Assembly DFMEA Generator (Windows / FreeCAD)

An automated Design Failure Mode and Effects Analysis (DFMEA) engine built for Windows using open-source CAD software. This utility reads 3D CAD assemblies (`.FCStd`, `.STEP`, `.STP`), extracts physical components and assembly constraints, and applies rule-based failure logic combined with local AI reasoning (via Ollama) to output AIAG-VDA compliant FMEA spreadsheets with calculated Risk Priority Numbers (RPN).

## Features

- **Free & Open-Source Stack:** Designed for hardware engineers and the 3D printing community without access to proprietary CAD suites.
- **Native Windows Desktop UI:** Includes a Tkinter-based graphical interface for easy file selection, analysis, and CSV exporting.
- **3D Print Geometry Checks:** Automatically flags non-manifold or thin-wall FDM slicer risks directly from CAD boundary boxes.
- **Local AI Functional Reasoning:** Uses local LLMs (Llama 3 running via Ollama) to infer physics-of-failure modes without exposing CAD data to public cloud APIs.

## Installation (Windows 10/11)

Open **PowerShell as Administrator** and install the core dependencies via Winget:

```powershell
winget install Python.Python.3.11
winget install FreeCAD.FreeCAD
winget install Ollama.Ollama
```
*Note: Restart PowerShell after installation so your system updates environment paths.*

To use the optional AI functional reasoning, start the Ollama service and download the model:

```powershell
ollama serve
# In a separate PowerShell window:
ollama pull llama3
```

## Usage

### 1. Graphical User Interface (Recommended)

Launch the desktop application to browse files, toggle AI analysis, and view RPN scores interactively:

```powershell
.\run_gui_win.ps1
```

### 2. Command-Line Interface (Headless)

Run batch processing or integrate into automated toolchains without a GUI:

```powershell
.\run_win.ps1 -InputFile "C:\Path\To\Assembly.STEP" -OutputFile "Report.csv" -UseAI
```


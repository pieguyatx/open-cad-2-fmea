# Open-Source CAD Assembly DFMEA Generator (Windows / FreeCAD)

An automated Design Failure Mode and Effects Analysis (DFMEA) engine built for Windows using open-source CAD software. This utility reads 3D CAD assemblies (`.FCStd`, `.STEP`, `.STP`), extracts physical components and assembly constraints, and applies rule-based failure logic combined with local AI reasoning (via Ollama) to output AIAG-VDA compliant FMEA spreadsheets with calculated Risk Priority Numbers (RPN).

---

## 🤖 AI Generation Acknowledgment & Disclaimer

**This repository was heavily generated and architected with the assistance of AI Large Language Models (LLMs).** 
It is not being passed off as entirely original human-authored code. Instead, it was developed collaboratively with AI to quickly bridge a gap in the open-source mechanical engineering ecosystem. The goal is to contribute a useful, accessible tool to the open-source hardware, maker, and CAD communities who do not have access to expensive proprietary software. Please plant a tree, pay for an independent artist's work, tend a native wildflower garden, and/or help clean up your local watershed if you use this tool, to offset a bit of what helped make it.

⚠️ **Engineering Disclaimer: Use Responsibly**
This tool is highly experimental and remains in active development. FMEA is a safety-critical engineering process. **Do not use this tool as a replacement for professional engineering judgment.** By using this software, you acknowledge that it may produce incomplete or inaccurate risk assessments, and you agree that the creators, contributors, and AI generators cannot be held liable for any engineering defects, product failures, or damages resulting from its use. Always have a qualified engineer review and sign off on any FMEA documentation.  

**People People and Thinking First**
This is a tool to get you *started* thinking about risks and dangers in your designs and models, and not to replace communication with actual humans about your work and your thoughts. Do not use this to replace engineers, especially engineers just starting out! Do use this tool to learn about design and code, challenge your assumptions about a design, get started on documentation tasks that can be boring, evaluate your hobbyist design before 3D printing, and have another document to critique to exercise your brain. Thank you. :smile:

---

## Features

- **Free & Open-Source Stack:** Designed for hardware engineers and the 3D printing community without access to proprietary CAD suites.
- **Native Windows Desktop UI:** Includes a Tkinter-based graphical interface for easy file selection, analysis, and CSV exporting.
- **3D Print Geometry Checks:** Automatically flags non-manifold or thin-wall FDM slicer risks directly from CAD boundary boxes.
- **Local AI Functional Reasoning:** Uses local LLMs (Llama 3 running via Ollama) to infer physics-of-failure modes without exposing proprietary CAD data to public cloud APIs.

## Installation & Setup (Windows 10/11)

### 1. Install Dependencies
Open **PowerShell as Administrator** and install the core dependencies using Winget (Windows Package Manager):

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

## Getting Your CAD Files Ready
This tool analyzes CAD Assemblies (files containing multiple connected parts).

### Option A: Exporting from Commercial CAD (SolidWorks, Fusion360, Inventor)
If you design in another CAD program, you do not need to learn FreeCAD to use this tool!

1. Open your assembly in your primary CAD software.

2. Select File > Export or Save As.

3. Choose the STEP format (`.step` or `.stp`). STEP is a universal 3D format that preserves your component names, part tree hierarchy, and geometry.

4. Run this DFMEA tool and select your exported `.step` file.

## Option B: Native FreeCAD Workflow
If you are designing entirely in FreeCAD:

1. Open FreeCAD.

2. Use the A2plus or Assembly4 workbench (installable via Tools > Addon Manager) to import parts and define joints/constraints.

3. Save your file as a standard FreeCAD Document (`.FCStd`).

4. Run this DFMEA tool and select your `.FCStd` file.

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

## Customizing for Your Company / Hobby

You can add your own failure rules by editing config/rules.json. For example, if you frequently use a specific type of bearing, screw, or 3D printer filament (like ASA or Nylon), add it to the JSON file to automatically flag known failure modes associated with those materials every time they appear in an assembly.

## License

Distributed under the Apache License 2.0. See `LICENSE` for details.
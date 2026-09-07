import os
import sys
import json
import csv
import argparse

from src.cad_extractor import FreeCADAssemblyExtractorWin, LocalLLMReasonerWin
from src.geometry_analyzer import GeometryPhysicsAnalyzer

# --- CLI SCRIPT EXPLAINED ---
# This is the "headless" equivalent of gui.py. It runs identical logic 
# but takes inputs from your terminal command prompt rather than a desktop window. 
# This is useful if you want to automate report generation in scripts or batch folders.

def run_pipeline(input_file, output_csv, config_path, use_ai=False):
    if not os.path.exists(config_path):
        print(f"[Error] Missing config file at {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        rules = json.load(f)

    extractor = FreeCADAssemblyExtractorWin()
    print(f"[*] Extracting CAD context from: {input_file}")
    
    try:
        cad_context = extractor.extract_context(input_file)
    except Exception as e:
        print(f"[Error] Failed to parse CAD file: {e}")
        sys.exit(1)

    fmea_records = []

    # 1. 3D Print Warnings
    print("\n[*] Stage 1: Running 3D Print manufacturability checks...")
    for warn in cad_context.get("print_warnings", []):
        sev, occ, det = 7, 8, 3
        fmea_records.append({
            "Component": warn["component"], "Function": "3D Print Manufacturability",
            "Failure Mode": warn["type"], "Effect": warn["detail"],
            "Severity": sev, "Occurrence": occ, "Detection": det, "RPN": sev*occ*det,
            "Action": "Increase feature wall thickness in CAD model"
        })

    # 2. Physics & Geometry Rules
    print("\n[*] Stage 2: Running Physics and Geometry checks...")
    geo_analyzer = GeometryPhysicsAnalyzer(cad_context)
    for p_warn in geo_analyzer.analyze_assembly_physics():
        fmea_records.append({
            "Component": p_warn.get("component", "Unknown"),
            "Function": p_warn.get("function", "Unknown"),
            "Failure Mode": p_warn.get("failure_mode", "Unknown"),
            "Effect": p_warn.get("effect", "Unknown"),
            "Severity": p_warn.get("severity", 5),
            "Occurrence": p_warn.get("occurrence", 5),
            "Detection": p_warn.get("detection", 5),
            "RPN": p_warn.get("rpn", 125),
            "Action": p_warn.get("action", "None")
        })

    # 3. Material & Component Rules
    print("\n[*] Stage 3: Running Material and Component rules...")
    for comp in cad_context["components"]:
        c_name = comp["name"]
        c_mat = comp["material"].lower()
        
        for section in ["components", "materials"]:
            for rule in rules.get(section, []):
                if any(k in c_name.lower() or k in c_mat for k in rule["match_keywords"]):
                    sev = int(rule.get("severity", 5))
                    occ = int(rule.get("occurrence", 5))
                    det = int(rule.get("detection", 5))
                    fmea_records.append({
                        "Component": c_name, "Function": rule.get("function", "Load Transmission"),
                        "Failure Mode": rule["failure_mode"], "Effect": rule["effect"],
                        "Severity": sev, "Occurrence": occ, "Detection": det, "RPN": sev*occ*det,
                        "Action": rule["action"]
                    })

    # 4. Optional AI Pass
    if use_ai:
        print("[*] Stage 4: Running Optional Local LLM Functional Reasoning (Ollama)...")
        reasoner = LocalLLMReasonerWin()
        ai_data = reasoner.infer_failure_modes(cad_context)
        for item in ai_data:
            try:
                sev = int(item.get("severity", 5))
                occ = int(item.get("occurrence", 5))
                det = int(item.get("detection", 5))
                fmea_records.append({
                    "Component": str(item.get("component", "System")), "Function": str(item.get("function", "N/A")),
                    "Failure Mode": str(item.get("failure_mode", "N/A")), "Effect": str(item.get("effect", "N/A")),
                    "Severity": sev, "Occurrence": occ, "Detection": det, "RPN": sev*occ*det,
                    "Action": str(item.get("action", "N/A"))
                })
            except (ValueError, TypeError):
                continue

    # Sort highest risk to the top
    fmea_records.sort(key=lambda x: x["RPN"], reverse=True)

    fieldnames = ["Component", "Function", "Failure Mode", "Effect", "Severity", "Occurrence", "Detection", "RPN", "Action"]
    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(fmea_records)

    print(f"[+] Success! Exported {len(fmea_records)} FMEA rows to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Windows CAD Auto-dFMEA CLI Generator")
    parser.add_argument("-i", "--input", required=True, help="Path to CAD file (.FCStd / .STEP)")
    parser.add_argument("-o", "--output", default="dFMEA_Output.csv", help="Output path")
    parser.add_argument("--config", default="config/rules.json", help="Rules file path")
    parser.add_argument("--ai", action="store_true", help="Enable local LLM pass")

    args = parser.parse_args()
    run_pipeline(args.input, args.output, args.config, use_ai=args.ai)
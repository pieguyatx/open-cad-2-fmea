"""CAD Extractor Module

This module interfaces with FreeCAD libraries to parse geometric data from CAD
files (STEP, IGES, FCStd, etc.). It extracts shape properties including face and 
edge counts, total volume, bounding boxes, and dimensional features like minimum 
wall thickness and hole diameters for downstream dFMEA evaluation.
"""

import sys
import os
import re
import json
import urllib.request
import urllib.error

# --- ENVIRONMENT SETUP EXPLAINED ---
# FreeCAD comes with its own private Python environment and C++ libraries. 
# Because this script runs using your standard Windows Python installation, 
# we must manually locate FreeCAD's folder on your hard drive and add its 
# 'bin' and 'lib' folders to Python's search path so it knows how to read CAD files.
# Customize the paths to check here for your installation of FreeCAD
WIN_FREECAD_BASE_PATHS = [
    r"C:\Program Files\FreeCAD 0.21",
    r"C:\Program Files\FreeCAD 1.0",
    r"C:\Program Files\FreeCAD",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\FreeCAD"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\FreeCAD 1.1")
]

for base_path in WIN_FREECAD_BASE_PATHS:
    bin_path = os.path.join(base_path, "bin")
    lib_path = os.path.join(base_path, "lib")
    if os.path.exists(bin_path) and bin_path not in sys.path:
        sys.path.append(bin_path)
    if os.path.exists(lib_path) and lib_path not in sys.path:
        sys.path.append(lib_path)

try:
    import FreeCAD
    import Part
    FREECAD_AVAILABLE = True
except ImportError as e:
    print(f"[Warning] FreeCAD binaries could not be loaded: {e}")
    print("[Warning] CAD extraction features will be disabled.")
    # Fallback flag if running in a standalone environment without FreeCAD binaries
    FREECAD_AVAILABLE = False


class FreeCADAssemblyExtractorWin:
    def __init__(self):
        pass

    def extract_context(self, file_path):
        """Opens a CAD assembly file (.FCStd or .STEP) and reads its parts and joints."""
        file_path = os.path.abspath(file_path)
        if not FREECAD_AVAILABLE:
            raise RuntimeError(
                "FreeCAD modules are not available. Please configure your PYTHONPATH to include FreeCAD/bin."
            )
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CAD File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        context = {
            "assembly_name": os.path.basename(file_path),
            "components": [],
            "joints": [],
            "print_warnings": []
        }

        doc = None
        try:
            # STEP files are universal text formats. FreeCAD reads them by 
            # creating a temporary blank project and inserting the geometry into it.
            if ext in [".step", ".stp"]:
                doc = FreeCAD.newDocument("STEP_Import")
                try:
                    Part.insert(file_path, doc.Name)
                except Exception as e:
                    print(f"[Warning] Failed to parse STEP geometry for {file_path}: {e}")
                    return context
            else:
                doc = FreeCAD.openDocument(file_path)

            total_objs = len(doc.Objects) # info for progress notification

            for index, obj in enumerate(doc.Objects):
                
                # Terminal progress indicator
                print(f"[*] Extracting CAD Object {index + 1}/{total_objs}: {obj.Label}          ", end="\r")
                sys.stdout.flush()

                if obj.isDerivedFrom("App::Part") or obj.isDerivedFrom("Part::Feature"):
                    mat_name = ""
                    if hasattr(obj, "Material") and obj.Material:
                        mat_name = obj.Material.get("CardName", "")
                    elif "mat:" in obj.Label.lower():
                        mat_name = obj.Label

                    mass = 0.0
                    dimensions = {"x": 1.0, "y": 1.0, "z": 1.0}
                    shape_obj = None

                    # Read 3D shape data to compute bounding sizes, weight estimates, and clash checks
                    if hasattr(obj, "Shape") and obj.Shape and not obj.Shape.isNull():
                        shape = obj.Shape
                        shape_obj = shape  # <-- Stored so geometry_analyzer.py can check for spatial clashes
                        
                        bbox = shape.BoundBox
                        dimensions = {
                            "x": max(bbox.XLength, 0.1),
                            "y": max(bbox.YLength, 0.1),
                            "z": max(bbox.ZLength, 0.1)
                        }
                        
                        try:
                            volume_mm3 = shape.Volume
                            density_g_mm3 = 0.00785  # Generic baseline steel/aluminum density (~7.85 g/cm3)
                            mass = (volume_mm3 * density_g_mm3) / 1000.0  # Converted to kg
                        except Exception:
                            # Stop corrupted CAD from going through
                            raise RuntimeError(f"Corrupt geometry detected in {obj.Name}: {e}") 

                        # 3D Printing check: look for microscopic faces smaller than 1mm^2 
                        # that often cause FDM 3D printer slicers to fail or leave gaps.
                        for face in shape.Faces:
                            if 0.0 < face.Area < 1.0: 
                                context["print_warnings"].append({
                                    "component": obj.Label,
                                    "type": "Thin Feature / Micro-Face (<1.0mm²)",
                                    "detail": f"Contains micro-face area of {face.Area:.3f}mm². Risk of slicing gap."
                                })
                                break

                    context["components"].append({
                        "name": obj.Label,
                        "type": obj.TypeId,
                        "material": mat_name,
                        "mass": mass,
                        "dimensions": dimensions,
                        "shape_object": shape_obj  # <-- Passed to geometry analyzer
                    })

                # Grab assembly joint constraint definitions
                if any(k in obj.TypeId for k in ["Joint", "Constraint", "Element"]):
                    context["joints"].append({
                        "name": obj.Label,
                        "type": str(getattr(obj, "JointType", "Assembly Constraint")),
                        "linked_objects": [e for e in getattr(obj, "Elements", [])]
                    })
        finally:
        #     # Clean up memory by closing the document when finished
        #     if doc is not None:
        #         try:
        #             FreeCAD.closeDocument(doc.Name)
        #         except Exception:
        #             pass
            print("") # Print a clean newline after the loop finishes
            pass # leave document open

        return context


class LocalLLMReasonerWin:
    def __init__(self, model="llama3", endpoint="http://localhost:11434/api/generate"):
        self.model = model
        self.endpoint = endpoint

    def _clean_json_response(self, raw_text):
        raw_text = raw_text.strip()
        match = re.search(r"\[\s*\{.*\}\s*\]", raw_text, re.DOTALL)
        if match:
            return match.group(0)
        return raw_text

    def infer_failure_modes(self, cad_context):
        # Strip C++ FreeCAD objects before passing to the JSON serializer
        safe_context = {
            "assembly_name": cad_context.get("assembly_name", ""),
            "components": [{k: v for k, v in c.items() if k != "shape_object"} for c in cad_context.get("components", [])],
            "joints": cad_context.get("joints", []),
            "print_warnings": cad_context.get("print_warnings", [])
        }
        prompt = f"""
You are an expert Reliability, 3D Printing, and dFMEA Engineer.
Analyze the following CAD assembly context (Components, Materials, Joints, Print Warnings) and deduce functional failure modes.

CAD CONTEXT:
{json.dumps(safe_context, indent=2)}

OUTPUT REQUIREMENT:
Return ONLY a valid JSON array of objects. Do not use markdown blocks.
JSON structure per object:
{{
  "component": "Name",
  "function": "Function",
  "failure_mode": "Failure Mode",
  "effect": "Failure Effect",
  "cause": "Cause",
  "action": "Action",
  "severity": integer (1-10),
  "occurrence": integer (1-10),
  "detection": integer (1-10)
}}
"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }

        try:
            req = urllib.request.Request(
                self.endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=45) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                raw_response = res_data.get("response", "[]")
                cleaned_json = self._clean_json_response(raw_response)
                return json.loads(cleaned_json)
        except Exception as e:
            print(f"[Warning] LLM reasoning skipped or returned invalid JSON: {e}")
            return []
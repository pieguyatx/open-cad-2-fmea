import sys
import os
import re
import json
import urllib.request
import urllib.error

WIN_FREECAD_BASE_PATHS = [
    r"C:\Program Files\FreeCAD 0.21",
    r"C:\Program Files\FreeCAD 1.0",
    r"C:\Program Files\FreeCAD",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\FreeCAD")
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
except ImportError:
    pass


class FreeCADAssemblyExtractorWin:
    def __init__(self):
        pass

    def extract_context(self, file_path):
        file_path = os.path.abspath(file_path)
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
            if ext in [".step", ".stp"]:
                doc = FreeCAD.newDocument("STEP_Import")
                try:
                    Part.insert(file_path, doc.Name)
                except Exception as e:
                    print(f"[Warning] Failed to parse STEP geometry for {file_path}: {e}")
                    return context
            else:
                doc = FreeCAD.openDocument(file_path)

            for obj in doc.Objects:
                if obj.isDerivedFrom("App::Part") or obj.isDerivedFrom("Part::Feature"):
                    mat_name = ""
                    if hasattr(obj, "Material") and obj.Material:
                        mat_name = obj.Material.get("CardName", "")
                    elif "mat:" in obj.Label.lower():
                        mat_name = obj.Label

                    if hasattr(obj, "Shape") and obj.Shape and not obj.Shape.isNull():
                        shape = obj.Shape
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
                        "material": mat_name
                    })

                if any(k in obj.TypeId for k in ["Joint", "Constraint", "Element"]):
                    context["joints"].append({
                        "name": obj.Label,
                        "type": str(getattr(obj, "JointType", "Assembly Constraint")),
                        "linked_objects": [e for e in getattr(obj, "Elements", [])]
                    })
        finally:
            if doc is not None:
                try:
                    FreeCAD.closeDocument(doc.Name)
                except Exception:
                    pass

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
        prompt = f"""
You are an expert Reliability, 3D Printing, and DFMEA Engineer.
Analyze the following CAD assembly context (Components, Materials, Joints, Print Warnings) and deduce functional failure modes.

CAD CONTEXT:
{json.dumps(cad_context, indent=2)}

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
import math

class GeometryPhysicsAnalyzer:
    """
    GEOMETRY & PHYSICS ANALYZER EXPLAINED:
    Instead of asking an AI to guess if a part might break, this module uses pure 
    mathematical rules based on standard mechanical engineering principles. 
    It looks at the physical dimensions, weight, and assembly joints extracted 
    from your CAD file to catch common physical design oversights automatically.
    """
    def __init__(self, cad_context):
        self.components = cad_context.get("components", [])
        self.joints = cad_context.get("joints", [])
        self.physics_warnings = []

    def analyze_assembly_physics(self):
        """Runs all deterministic physical checks and returns a list of FMEA warnings."""
        self._check_cantilever_and_mass()
        self._check_metal_on_metal_rotation()
        self._check_thermal_expansion_mismatches()
        return self.physics_warnings

    def _check_cantilever_and_mass(self):
        """
        RULE 1: Heavy Cantilever Stress
        If a part is heavy (> 500 grams) and its length is much greater than its 
        thickness (a long overhang or 'cantilever'), it creates a massive bending 
        moment on its mounting screws. This rule catches parts likely to snap 
        their fasteners under vibration or weight.
        """
        for comp in self.components:
            mass = comp.get("mass", 0.0)
            dims = comp.get("dimensions", {"x": 1.0, "y": 1.0, "z": 1.0})
            
            # Check if part weighs over 500g
            if mass > 0.5:
                max_dim = max(dims["x"], dims["y"], dims["z"])
                min_dim = min(dims["x"], dims["y"], dims["z"])
                
                # Check if length is 5x greater than thickness (slender overhang)
                if max_dim / (min_dim + 1e-6) > 5.0:
                    self.physics_warnings.append({
                        "component": comp["name"],
                        "function": "Cantilever Structural Support",
                        "failure_mode": "Fastener Shear / Cantilever Bending Fatigue",
                        "effect": "Fasteners snap under combined bending moment and shear loading, causing structural detachment.",
                        "cause": f"Heavy mass ({mass:.2f} kg) acting over a slender cantilever moment arm (~{max_dim:.1f} mm).",
                        "severity": 8, "occurrence": 5, "detection": 3,
                        "rpn": 8 * 5 * 3,
                        "action": "Add structural dowel pins, increase fastener thread diameter, or incorporate a support gusset."
                    })

    def _check_metal_on_metal_rotation(self):
        """
        RULE 2: Unlubricated Metal-on-Metal Rotation
        If the assembly has a rotating or concentric joint between two metal parts 
        (like a steel shaft inside a steel housing) and no bearing, bushing, or 
        plastic liner is mentioned in the component names, it flags an unlubricated 
        metal-on-metal friction risk that will instantly seize or gall.
        """
        for joint in self.joints:
            j_type = joint.get("type", "").lower()
            if "rotation" in j_type or "concentric" in j_type or "revolute" in j_type:
                linked = joint.get("linked_objects", [])
                
                has_bearing = False
                metal_count = 0
                
                for obj_name in linked:
                    name_lower = obj_name.lower()
                    # Check if a bearing or soft bushing is present to prevent galling
                    if any(b in name_lower for b in ["bearing", "bush", "bushing", "ptfe", "brass", "nylon"]):
                        has_bearing = True
                    if any(m in name_lower for m in ["steel", "aluminum", "iron", "metal", "titanium"]):
                        metal_count += 1

                if metal_count >= 2 and not has_bearing:
                    self.physics_warnings.append({
                        "component": f"Joint: {joint['name']}",
                        "function": "Rotational Axis Guidance",
                        "failure_mode": "Metal-on-Metal Galling and Seizure",
                        "effect": "High friction causes immediate surface micro-welding, destroying the rotating assembly.",
                        "cause": "Direct sliding or rotating contact between unlubricated metal surfaces under load.",
                        "severity": 8, "occurrence": 6, "detection": 4,
                        "rpn": 8 * 6 * 4,
                        "action": "Insert a bronze bushing, sealed ball bearing, or specify an anodized surface with grease lubrication."
                    })

    def _check_thermal_expansion_mismatches(self):
        """
        RULE 3: Thermal Expansion Mismatch in Rigid Joints
        Different materials expand at different rates when temperatures change. 
        If an Aluminum part is rigidly bolted directly to a Steel part, thermal 
        cycles will cause the parts to fight each other, shearing bolts or warping 
        the frame.
        """
        for joint in self.joints:
            j_type = joint.get("type", "").lower()
            if "fixed" in j_type or "rigid" in j_type:
                linked = joint.get("linked_objects", [])
                materials_found = []
                
                for obj_name in linked:
                    name_lower = obj_name.lower()
                    if "aluminum" in name_lower or "al_" in name_lower:
                        materials_found.append("Aluminum")
                    elif "steel" in name_lower or "iron" in name_lower or "stainless" in name_lower:
                        materials_found.append("Steel")

                if "Aluminum" in materials_found and "Steel" in materials_found:
                    self.physics_warnings.append({
                        "component": f"Rigid Joint: {joint['name']}",
                        "function": "Multi-Material Structural Rigidity",
                        "failure_mode": "Thermal Stress Warping / Fastener Shear",
                        "effect": "Fasteners shear or components buckle during ambient thermal cycling.",
                        "cause": "Coefficient of Thermal Expansion (CTE) mismatch between Aluminum (~23 µm/m°C) and Steel (~12 µm/m°C).",
                        "severity": 7, "occurrence": 4, "detection": 5,
                        "rpn": 7 * 4 * 5,
                        "action": "Slot the mounting holes to allow thermal sliding clearance, or match the material profiles."
                    })
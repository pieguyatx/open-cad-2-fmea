import os
import sys
import json
import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src.cad_extractor import FreeCADAssemblyExtractorWin, LocalLLMReasonerWin


class FmeaGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Open-Source CAD Assembly DFMEA Generator")
        self.root.geometry("1150x680")

        self.selected_file = ""
        self.fmea_records = []

        # --- ARCHITECTURE NOTE: UI LAYOUT ---
        # We use Tkinter because it is built into Python natively. No extra installations.
        # The layout is split into a Control Frame (top), Table Frame (middle), Export Frame (bottom).
        control_frame = ttk.Frame(root, padding=10)
        control_frame.pack(fill=tk.X)

        ttk.Button(control_frame, text="Select CAD File (.STEP / .STP / .FCStd)", command=self.browse_file).pack(side=tk.LEFT, padx=5)
        self.lbl_file = ttk.Label(control_frame, text="No file selected", font=("Segoe UI", 9, "italic"))
        self.lbl_file.pack(side=tk.LEFT, padx=5)

        self.var_ai = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="Enable Local AI (Ollama)", variable=self.var_ai).pack(side=tk.LEFT, padx=15)

        ttk.Button(control_frame, text="Run DFMEA Analysis", command=self.run_analysis).pack(side=tk.RIGHT, padx=5)

        table_frame = ttk.Frame(root, padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("Component", "Function", "Failure Mode", "Effect", "Severity", "Occurrence", "Detection", "RPN", "Action")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)
            width = 65 if col in ["Severity", "Occurrence", "Detection", "RPN"] else 135
            self.tree.column(col, width=width, anchor=tk.CENTER if col in ["Severity", "Occurrence", "Detection", "RPN"] else tk.W)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        bottom_frame = ttk.Frame(root, padding=10)
        bottom_frame.pack(fill=tk.X)
        ttk.Button(bottom_frame, text="Export DFMEA Report to CSV", command=self.export_csv).pack(side=tk.RIGHT)

    def browse_file(self):
        filetypes = [("CAD Assemblies", "*.FCStd *.step *.stp"), ("All Files", "*.*")]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            self.selected_file = path
            self.lbl_file.config(text=os.path.basename(path), font=("Segoe UI", 9, "bold"))

    def run_analysis(self):
        if not self.selected_file:
            messagebox.showwarning("Warning", "Please select a CAD file first.")
            return

        # Clear existing table data before running a new analysis
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.fmea_records.clear()

        config_path = "config/rules.json"
        if not os.path.exists(config_path):
            messagebox.showerror("Error", f"Missing config file at {config_path}")
            return

        with open(config_path, "r", encoding="utf-8") as f:
            rules = json.load(f)

        try:
            extractor = FreeCADAssemblyExtractorWin()
            cad_context = extractor.extract_context(self.selected_file)
        except Exception as e:
            messagebox.showerror("CAD Processing Error", f"Failed to parse CAD file:\n{e}")
            return

        # 1. Process Geometry Warnings (e.g., thin features for 3D printing)
        for warn in cad_context.get("print_warnings", []):
            sev, occ, det = 7, 8, 3
            self.fmea_records.append({
                "Component": warn["component"], "Function": "3D Print Manufacturability",
                "Failure Mode": warn["type"], "Effect": warn["detail"],
                "Severity": sev, "Occurrence": occ, "Detection": det, "RPN": sev*occ*det,
                "Action": "Increase feature wall thickness in CAD model"
            })

        # 2. Process predefined component and material rules from rules.json
        for comp in cad_context["components"]:
            c_name = comp["name"]
            c_mat = comp["material"].lower()
            
            for section in ["components", "materials"]:
                for rule in rules.get(section, []):
                    if any(k in c_name.lower() or k in c_mat for k in rule["match_keywords"]):
                        sev = int(rule.get("severity", 5))
                        occ = int(rule.get("occurrence", 5))
                        det = int(rule.get("detection", 5))
                        self.fmea_records.append({
                            "Component": c_name, "Function": rule.get("function", "Load Transmission"),
                            "Failure Mode": rule["failure_mode"], "Effect": rule["effect"],
                            "Severity": sev, "Occurrence": occ, "Detection": det, "RPN": sev*occ*det,
                            "Action": rule["action"]
                        })

        # 3. Request LLM generated insights if the user checked the box
        if self.var_ai.get():
            reasoner = LocalLLMReasonerWin()
            ai_data = reasoner.infer_failure_modes(cad_context)
            for item in ai_data:
                try:
                    sev = int(item.get("severity", 5))
                    occ = int(item.get("occurrence", 5))
                    det = int(item.get("detection", 5))
                    self.fmea_records.append({
                        "Component": str(item.get("component", "System")), "Function": str(item.get("function", "N/A")),
                        "Failure Mode": str(item.get("failure_mode", "N/A")), "Effect": str(item.get("effect", "N/A")),
                        "Severity": sev, "Occurrence": occ, "Detection": det, "RPN": sev*occ*det,
                        "Action": str(item.get("action", "N/A"))
                    })
                except (ValueError, TypeError):
                    continue

        # Sort Records by Risk Priority Number (RPN) Descending to highlight high-risk items at the top
        self.fmea_records.sort(key=lambda x: x["RPN"], reverse=True)

        # Populate the GUI table
        for rec in self.fmea_records:
            self.tree.insert("", tk.END, values=(
                rec["Component"], rec["Function"], rec["Failure Mode"], rec["Effect"],
                rec["Severity"], rec["Occurrence"], rec["Detection"], rec["RPN"], rec["Action"]
            ))

        messagebox.showinfo("Success", f"Analysis complete! Found {len(self.fmea_records)} FMEA entries.")

    def export_csv(self):
        """Allows user to save the FMEA table into a CSV format compatible with Excel and QMS systems."""
        if not self.fmea_records:
            messagebox.showwarning("Warning", "No FMEA data to export.")
            return

        out_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if out_path:
            fieldnames = ["Component", "Function", "Failure Mode", "Effect", "Severity", "Occurrence", "Detection", "RPN", "Action"]
            with open(out_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.fmea_records)
            messagebox.showinfo("Export Complete", f"FMEA report saved to:\n{out_path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = FmeaGuiApp(root)
    root.mainloop()
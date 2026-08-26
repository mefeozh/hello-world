---
name: fusion360-inspection
description: Programmatic inspection and validation for Fusion 360 models. Replaces screenshot-based validation with B-Rep queries, timeline health checks, and parameter inspection.
---

# Fusion 360 Programmatic Inspection & Validation

This skill provides a suite of programmatic tools to inspect, analyze, and validate Fusion 360 models using the `fusion_mcp_execute` tool. Programmatic inspection is essential for verifying geometric correctness, checking model health, and ensuring design intent without relying on manual checks or screenshot analysis.

## 1. B-Rep Tree Traversal

To understand the full structure of a component, you need to traverse its Boundary Representation (B-Rep) hierarchy. The following script walks through all occurrences, bodies, faces, edges, and vertices, printing a hierarchical summary.

```python
import adsk.core
import adsk.fusion
import traceback

def traverse_brep():
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        design = app.activeProduct
        if not design:
            return "No active design."

        rootComp = design.rootComponent
        output = []

        def process_component(comp, indent=""):
            output.append(f"{indent}Component: {comp.name}")
            
            for i in range(comp.bRepBodies.count):
                body = comp.bRepBodies.item(i)
                output.append(f"{indent}  Body {i}: {body.name}")
                output.append(f"{indent}    Faces: {body.faces.count}")
                output.append(f"{indent}    Edges: {body.edges.count}")
                output.append(f"{indent}    Vertices: {body.vertices.count}")

        # Process Root
        process_component(rootComp)
        
        # Process Occurrences (Recursive)
        def process_occurrences(occs, indent=""):
            for j in range(occs.count):
                occ = occs.item(j)
                output.append(f"{indent}Occurrence: {occ.name}")
                process_component(occ.component, indent + "  ")
                if occ.childOccurrences and occ.childOccurrences.count > 0:
                    process_occurrences(occ.childOccurrences, indent + "  ")
        
        process_occurrences(rootComp.occurrences, "  ")

        return "\n".join(output)

    except:
        return f"Failed:\n{traceback.format_exc()}"

traverse_brep()
```

## 2. Geometry Analysis

Extracting physical and geometric properties is crucial for validation. This script calculates volume, surface area, bounding box, center of mass, and inertia for a given body.

```python
import adsk.core
import adsk.fusion
import traceback

def analyze_geometry():
    app = adsk.core.Application.get()
    try:
        design = app.activeProduct
        if not design:
            return "No active design."
        
        rootComp = design.rootComponent
        if rootComp.bRepBodies.count == 0:
            return "No bodies found in the root component."
            
        body = rootComp.bRepBodies.item(0)
        physProps = body.physicalProperties
        
        # Bounding Box
        bbox = body.boundingBox
        width = bbox.maxPoint.x - bbox.minPoint.x
        height = bbox.maxPoint.y - bbox.minPoint.y
        depth = bbox.maxPoint.z - bbox.minPoint.z
        
        # Internal units are cm, cm^2, cm^3, kg
        report = [
            f"Analysis for Body: {body.name}",
            f"Volume (cm^3): {physProps.volume:.4f}",
            f"Surface Area (cm^2): {physProps.area:.4f}",
            f"Mass (kg): {physProps.mass:.4f}",
            f"Density (kg/cm^3): {physProps.density:.6f}",
            f"Center of Mass (x,y,z cm): ({physProps.centerOfMass.x:.4f}, {physProps.centerOfMass.y:.4f}, {physProps.centerOfMass.z:.4f})",
            f"Bounding Box (WxHxD cm): {width:.4f} x {height:.4f} x {depth:.4f}"
        ]
        
        return "\n".join(report)

    except:
        return f"Failed:\n{traceback.format_exc()}"

analyze_geometry()
```

## 3. Face Type Classification

Different manufacturing processes require specific face types. This script classifies every face of a body into its underlying mathematical surface representation.

```python
import adsk.core
import adsk.fusion
import traceback

def classify_faces():
    app = adsk.core.Application.get()
    try:
        design = app.activeProduct
        if not design:
            return "No active design."
            
        rootComp = design.rootComponent
        if rootComp.bRepBodies.count == 0:
            return "No bodies to classify."
            
        body = rootComp.bRepBodies.item(0)
        
        face_types = {
            adsk.core.Plane.classType(): "Planar",
            adsk.core.Cylinder.classType(): "Cylindrical",
            adsk.core.Cone.classType(): "Conical",
            adsk.core.Sphere.classType(): "Spherical",
            adsk.core.Torus.classType(): "Toroidal",
            adsk.core.NurbsSurface.classType(): "NURBS"
        }
        
        counts = {name: 0 for name in face_types.values()}
        counts["Other"] = 0
        
        for i in range(body.faces.count):
            face = body.faces.item(i)
            geom = face.geometry
            geom_type = geom.classType()
            
            if geom_type in face_types:
                counts[face_types[geom_type]] += 1
            else:
                counts["Other"] += 1
                
        report = [f"Face Classification for Body '{body.name}':"]
        for t, count in counts.items():
            if count > 0:
                report.append(f"  {t}: {count}")
                
        return "\n".join(report)

    except:
        return f"Failed:\n{traceback.format_exc()}"

classify_faces()
```

## 4. Timeline Health Audit

A robust parametric model must have a healthy timeline without errors or warnings. This script iterates through the timeline and checks the health state of each feature.

```python
import adsk.core
import adsk.fusion
import traceback

def audit_timeline():
    app = adsk.core.Application.get()
    try:
        design = app.activeProduct
        if not design:
            return "No active design."
            
        timeline = design.timeline
        
        health_map = {
            adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState: "Healthy",
            adsk.fusion.FeatureHealthStates.WarningFeatureHealthState: "Warning",
            adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState: "Error",
            adsk.fusion.FeatureHealthStates.SuppressedFeatureHealthState: "Suppressed",
            adsk.fusion.FeatureHealthStates.UnknownFeatureHealthState: "Unknown"
        }
        
        report = ["Timeline Health Audit:"]
        errors_found = False
        
        for i in range(timeline.count):
            obj = timeline.item(i)
            ent = obj.entity
            if not ent:
                continue
                
            health_code = obj.healthState
            health_str = health_map.get(health_code, "Unknown")
            
            name = getattr(ent, "name", "Unnamed Feature")
            report.append(f"[{i}] {name} ({ent.classType()}): {health_str}")
            
            if health_code in [adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState, 
                               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState]:
                errors_found = True
                
        if not errors_found:
            report.append("\nTimeline is clean! No errors or warnings.")
            
        return "\n".join(report)

    except:
        return f"Failed:\n{traceback.format_exc()}"

audit_timeline()
```

## 5. Parameter Inspection & Modification

Parameters drive the parametric behavior of the model. Here we inspect, modify, and add parameters.

```python
import adsk.core
import adsk.fusion
import traceback

def inspect_parameters():
    app = adsk.core.Application.get()
    try:
        design = app.activeProduct
        if not design:
            return "No active design."
            
        params = design.allParameters
        user_params = design.userParameters
        model_params = design.modelParameters
        
        report = ["=== User Parameters ==="]
        for i in range(user_params.count):
            p = user_params.item(i)
            report.append(f"{p.name} = {p.expression} (Evaluates to: {p.value} {p.unit})")
            
        report.append("\n=== Model Parameters ===")
        for i in range(model_params.count):
            p = model_params.item(i)
            report.append(f"{p.name} = {p.expression} (Evaluates to: {p.value} {p.unit})")
            
        # Example: Modify a parameter
        # p = user_params.itemByName("MyParam")
        # if p: p.expression = "50 mm"
        
        # Example: Add a new user parameter
        # if not user_params.itemByName("NewParam"):
        #     user_params.add("NewParam", adsk.core.ValueInput.createByString("10 mm"), "mm", "A new test param")
        
        return "\n".join(report)

    except:
        return f"Failed:\n{traceback.format_exc()}"

inspect_parameters()
```

## 6. Sketch Analysis

Unclosed or under-constrained sketches are common sources of instability. This script analyzes sketch profiles and constraints.

```python
import adsk.core
import adsk.fusion
import traceback

def analyze_sketches():
    app = adsk.core.Application.get()
    try:
        design = app.activeProduct
        if not design:
            return "No active design."
            
        rootComp = design.rootComponent
        report = []
        
        for i in range(rootComp.sketches.count):
            sketch = rootComp.sketches.item(i)
            report.append(f"Sketch: {sketch.name}")
            
            curves_count = sketch.sketchCurves.count
            points_count = sketch.sketchPoints.count
            profiles_count = sketch.profiles.count
            
            report.append(f"  Curves: {curves_count}")
            report.append(f"  Points: {points_count}")
            report.append(f"  Profiles (closed areas): {profiles_count}")
            
            if profiles_count == 0 and curves_count > 0:
                report.append("  WARNING: Sketch contains curves but no closed profiles!")
                
            report.append(f"  Geometric Constraints: {sketch.geometricConstraints.count}")
            report.append(f"  Dimensions: {sketch.sketchDimensions.count}")
            
        if rootComp.sketches.count == 0:
            report.append("No sketches found.")
            
        return "\n".join(report)

    except:
        return f"Failed:\n{traceback.format_exc()}"

analyze_sketches()
```

## 7. Validation Assertions

Reusable assertion functions for writing programmatic unit tests for your CAD models. You can incorporate these into validation scripts.

```python
import adsk.core
import adsk.fusion

def assert_body_count(comp, expected):
    actual = comp.bRepBodies.count
    if actual != expected:
        raise ValueError(f"Assertion failed: Expected {expected} bodies, found {actual}")
    return True

def assert_face_count_range(body, min_faces, max_faces):
    actual = body.faces.count
    if not (min_faces <= actual <= max_faces):
        raise ValueError(f"Assertion failed: Expected face count between {min_faces} and {max_faces}, found {actual}")
    return True

def assert_volume_range(body, min_vol_cm3, max_vol_cm3):
    actual = body.physicalProperties.volume
    if not (min_vol_cm3 <= actual <= max_vol_cm3):
        raise ValueError(f"Assertion failed: Expected volume between {min_vol_cm3} and {max_vol_cm3} cm^3, found {actual:.4f}")
    return True

def assert_bounding_box(body, expected_dims_cm, tolerance=0.01):
    bbox = body.boundingBox
    w = bbox.maxPoint.x - bbox.minPoint.x
    h = bbox.maxPoint.y - bbox.minPoint.y
    d = bbox.maxPoint.z - bbox.minPoint.z
    
    ex_w, ex_h, ex_d = expected_dims_cm
    
    if abs(w - ex_w) > tolerance or abs(h - ex_h) > tolerance or abs(d - ex_d) > tolerance:
        raise ValueError(f"Assertion failed: Expected bbox ({ex_w}, {ex_h}, {ex_d}), found ({w:.4f}, {h:.4f}, {d:.4f})")
    return True

def assert_timeline_healthy(design):
    timeline = design.timeline
    for i in range(timeline.count):
        obj = timeline.item(i)
        if obj.healthState in [adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState, 
                               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState]:
            ent = obj.entity
            name = getattr(ent, "name", "Unnamed")
            raise ValueError(f"Assertion failed: Timeline feature '{name}' is in error/warning state.")
    return True
```

## 8. Full Inspection Script

A master script that runs all validations and produces a comprehensive report.

```python
import adsk.core
import adsk.fusion
import traceback

def full_inspection():
    app = adsk.core.Application.get()
    try:
        design = app.activeProduct
        if not design:
            return "No active design."
            
        rootComp = design.rootComponent
        report = ["=== FUSION 360 FULL INSPECTION REPORT ==="]
        
        # 1. Component & Body Summary
        report.append("\n--- B-REP SUMMARY ---")
        report.append(f"Root Component: {rootComp.name}")
        report.append(f"Total Bodies: {rootComp.bRepBodies.count}")
        report.append(f"Total Sketches: {rootComp.sketches.count}")
        
        # 2. Timeline Health
        report.append("\n--- TIMELINE HEALTH ---")
        timeline = design.timeline
        errors = 0
        for i in range(timeline.count):
            obj = timeline.item(i)
            if obj.healthState in [adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState, 
                                   adsk.fusion.FeatureHealthStates.WarningFeatureHealthState]:
                errors += 1
        report.append(f"Timeline Length: {timeline.count}")
        report.append(f"Features with Errors/Warnings: {errors}")
        if errors > 0:
            report.append("FAIL: Timeline is not healthy.")
        else:
            report.append("PASS: Timeline is clean.")
            
        # 3. Parameter Check
        report.append("\n--- PARAMETERS ---")
        report.append(f"User Parameters: {design.userParameters.count}")
        report.append(f"Model Parameters: {design.modelParameters.count}")
        
        # 4. Detailed Body Analysis
        report.append("\n--- BODY ANALYSIS ---")
        for i in range(rootComp.bRepBodies.count):
            body = rootComp.bRepBodies.item(i)
            phys = body.physicalProperties
            bbox = body.boundingBox
            w = bbox.maxPoint.x - bbox.minPoint.x
            h = bbox.maxPoint.y - bbox.minPoint.y
            d = bbox.maxPoint.z - bbox.minPoint.z
            
            report.append(f"Body {i+1}: {body.name}")
            report.append(f"  Faces: {body.faces.count}")
            report.append(f"  Volume: {phys.volume:.4f} cm^3")
            report.append(f"  Mass: {phys.mass:.4f} kg")
            report.append(f"  BBox: {w:.2f} x {h:.2f} x {d:.2f} cm")
            
        report.append("\n=== END OF REPORT ===")
        return "\n".join(report)

    except:
        return f"Inspection Failed:\n{traceback.format_exc()}"

full_inspection()
```

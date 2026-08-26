---
name: fusion360-features
description: 3D feature operations for Fusion 360 via MCP. Covers extrude, revolve, sweep, loft, cut, fillet, chamfer, shell, mirror, pattern, combine, draft, rib, and feature tree management. Enforces feature-graph thinking and incremental editing.
---

# Fusion 360 Features Skill Guide

This guide provides comprehensive instructions and patterns for creating and modifying 3D features in Fusion 360 via the MCP interface.

## 1. Feature Tree Philosophy
Feature order matters. Plan the tree before executing.
- **Base Features:** Create the main body first (Extrude, Revolve, Sweep, Loft).
- **Additive Features:** Add material (Bosses, Ribs).
- **Subtractive Features:** Remove material (Cuts, Holes).
- **Modifiers:** Shell before fillets. Fillets and chamfers should be applied LAST in the feature tree to avoid breaking downstream references.

## 2. Extrude

### New Body / Join / Cut
```python
import adsk.core, adsk.fusion, traceback, math

def create_extrude():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        
        # Assume sketch exists and has a profile
        sketch = root.sketches.itemByName('BaseSketch')
        if not sketch:
            return "Error: Sketch not found."
            
        profile = sketch.profiles.item(0)
        
        extrudes = root.features.extrudeFeatures
        extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        
        # Distance (user specifies mm, internal is cm)
        distance = adsk.core.ValueInput.createByReal(5.0) # 50mm
        extrudeInput.setDistanceExtent(False, distance)
        
        # Taper angle
        taper_angle = adsk.core.ValueInput.createByReal(0)
        extrudeInput.taperAngle = taper_angle
        
        extrude = extrudes.add(extrudeInput)
        extrude.name = "MainBody_Extrude"
        
        print(f"Extrude created: {extrude.name}")
        
    except:
        print(f"Failed:\n{traceback.format_exc()}")

create_extrude()
```

### Two-Side Symmetric
```python
import adsk.core, adsk.fusion, traceback

def create_symmetric_extrude():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        
        sketch = root.sketches.itemByName('BaseSketch')
        profile = sketch.profiles.item(0)
        
        extrudes = root.features.extrudeFeatures
        extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        
        distance = adsk.core.ValueInput.createByReal(2.5) # 25mm each way
        extrudeInput.setSymmetricExtent(distance, True) # True for total length, False for half length
        
        extrude = extrudes.add(extrudeInput)
        extrude.name = "SymmBody_Extrude"
        print(f"Symmetric Extrude created: {extrude.name}")
    except:
        print(traceback.format_exc())

create_symmetric_extrude()
```

## 3. Revolve

```python
import adsk.core, adsk.fusion, traceback, math

def create_revolve():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        
        sketch = root.sketches.itemByName('ProfileSketch')
        profile = sketch.profiles.item(0)
        axis = root.xConstructionAxis
        
        revolves = root.features.revolveFeatures
        revolveInput = revolves.createInput(profile, axis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        
        # Full revolution
        angle = adsk.core.ValueInput.createByReal(math.pi * 2)
        revolveInput.setAngleExtent(False, angle)
        
        revolve = revolves.add(revolveInput)
        revolve.name = "Revolved_Body"
        print("Revolve created.")
    except:
        print(traceback.format_exc())

create_revolve()
```

## 4. Sweep

```python
import adsk.core, adsk.fusion, traceback

def create_sweep():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        
        profile_sketch = root.sketches.itemByName('SweepProfile')
        path_sketch = root.sketches.itemByName('SweepPath')
        
        profile = profile_sketch.profiles.item(0)
        path = root.features.createPath(path_sketch.sketchCurves.item(0))
        
        sweeps = root.features.sweepFeatures
        sweepInput = sweeps.createInput(profile, path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        
        sweepInput.orientation = adsk.fusion.SweepOrientationTypes.PerpendicularOrientationType
        
        sweep = sweeps.add(sweepInput)
        sweep.name = "Swept_Body"
        print("Sweep created.")
    except:
        print(traceback.format_exc())

create_sweep()
```

## 5. Loft

```python
import adsk.core, adsk.fusion, traceback

def create_loft():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        
        sketch1 = root.sketches.itemByName('LoftProfile1')
        sketch2 = root.sketches.itemByName('LoftProfile2')
        
        lofts = root.features.loftFeatures
        loftInput = lofts.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        
        loftInput.loftSections.add(sketch1.profiles.item(0))
        loftInput.loftSections.add(sketch2.profiles.item(0))
        
        loftInput.isSolid = True
        
        loft = lofts.add(loftInput)
        loft.name = "Lofted_Body"
        print("Loft created.")
    except:
        print(traceback.format_exc())

create_loft()
```

## 6. Cut Operations

```python
import adsk.core, adsk.fusion, traceback

def create_cut():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        
        sketch = root.sketches.itemByName('HoleSketch')
        profile = sketch.profiles.item(0)
        
        extrudes = root.features.extrudeFeatures
        extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.CutFeatureOperation)
        
        distance = adsk.core.ValueInput.createByReal(-2.0)
        extrudeInput.setDistanceExtent(False, distance)
        
        extrude = extrudes.add(extrudeInput)
        extrude.name = "Hole_Cut"
        print("Cut created.")
    except:
        print(traceback.format_exc())

create_cut()
```

## 7. Fillet

```python
import adsk.core, adsk.fusion, traceback

def create_fillet():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        
        body = root.bRepBodies.itemByName('MainBody_Extrude')
        if not body:
            return "Body not found."
            
        # Strategy: find edges by geometry type (e.g. straight vertical edges)
        edgesToFillet = adsk.core.ObjectCollection.create()
        for edge in body.edges:
            if type(edge.geometry) == adsk.core.Line3D:
                edgesToFillet.add(edge)
                
        fillets = root.features.filletFeatures
        filletInput = fillets.createInput()
        
        radius = adsk.core.ValueInput.createByReal(0.2) # 2mm
        filletInput.addConstantRadiusEdgeSet(edgesToFillet, radius, True)
        
        fillet = fillets.add(filletInput)
        fillet.name = "Main_Fillet"
        print("Fillet created.")
    except:
        print(traceback.format_exc())

create_fillet()
```

## 8. Chamfer

```python
import adsk.core, adsk.fusion, traceback

def create_chamfer():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        
        body = root.bRepBodies.itemByName('MainBody_Extrude')
        edgesToChamfer = adsk.core.ObjectCollection.create()
        edgesToChamfer.add(body.edges.item(0)) # Select specific edge
        
        chamfers = root.features.chamferFeatures
        chamferInput = chamfers.createInput(edgesToChamfer, True)
        
        distance = adsk.core.ValueInput.createByReal(0.1)
        chamferInput.setToEqualDistance(distance)
        
        chamfer = chamfers.add(chamferInput)
        chamfer.name = "Edge_Chamfer"
        print("Chamfer created.")
    except:
        print(traceback.format_exc())

create_chamfer()
```

## 9. Shell

```python
import adsk.core, adsk.fusion, traceback

def create_shell():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        
        body = root.bRepBodies.itemByName('MainBody_Extrude')
        faces = adsk.core.ObjectCollection.create()
        faces.add(body.faces.item(0)) # Face to remove
        
        shells = root.features.shellFeatures
        shellInput = shells.createInput(faces)
        
        thickness = adsk.core.ValueInput.createByReal(0.1) # 1mm thick
        shellInput.insideThickness = thickness
        
        shell = shells.add(shellInput)
        shell.name = "Body_Shell"
        print("Shell created.")
    except:
        print(traceback.format_exc())

create_shell()
```

## 10. Mirror

```python
import adsk.core, adsk.fusion, traceback

def create_mirror():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        
        body = root.bRepBodies.itemByName('MainBody_Extrude')
        plane = root.xyConstructionPlane
        
        entities = adsk.core.ObjectCollection.create()
        entities.add(body)
        
        mirrors = root.features.mirrorFeatures
        mirrorInput = mirrors.createInput(entities, plane)
        
        mirror = mirrors.add(mirrorInput)
        mirror.name = "Body_Mirror"
        print("Mirror created.")
    except:
        print(traceback.format_exc())

create_mirror()
```

## 11. Pattern

```python
import adsk.core, adsk.fusion, traceback

def create_circular_pattern():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        
        feature = root.features.itemByName('Hole_Cut')
        axis = root.zConstructionAxis
        
        entities = adsk.core.ObjectCollection.create()
        entities.add(feature)
        
        patterns = root.features.circularPatternFeatures
        patternInput = patterns.createInput(entities, axis)
        patternInput.quantity = adsk.core.ValueInput.createByReal(4)
        patternInput.totalAngle = adsk.core.ValueInput.createByString('360 deg')
        
        pattern = patterns.add(patternInput)
        pattern.name = "Hole_Pattern"
        print("Circular pattern created.")
    except:
        print(traceback.format_exc())

create_circular_pattern()
```

## 12. Combine

```python
import adsk.core, adsk.fusion, traceback

def create_combine():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        
        targetBody = root.bRepBodies.item(0)
        toolBody = root.bRepBodies.item(1)
        
        toolBodies = adsk.core.ObjectCollection.create()
        toolBodies.add(toolBody)
        
        combines = root.features.combineFeatures
        combineInput = combines.createInput(targetBody, toolBodies)
        combineInput.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        
        combine = combines.add(combineInput)
        combine.name = "Bodies_Combine"
        print("Combine created.")
    except:
        print(traceback.format_exc())

create_combine()
```

## 13. Draft

```python
import adsk.core, adsk.fusion, traceback, math

def create_draft():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        
        body = root.bRepBodies.item(0)
        faces = adsk.core.ObjectCollection.create()
        faces.add(body.faces.item(1)) # Face to draft
        
        plane = root.xyConstructionPlane
        
        drafts = root.features.draftFeatures
        draftInput = drafts.createInput(faces, plane, True)
        
        angle = adsk.core.ValueInput.createByReal(math.radians(5))
        draftInput.setSingleAngle(True, angle)
        
        draft = drafts.add(draftInput)
        draft.name = "Face_Draft"
        print("Draft created.")
    except:
        print(traceback.format_exc())

create_draft()
```

## 14. Incremental Editing

```python
import adsk.core, adsk.fusion, traceback

def edit_extrude():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        
        extrude = root.features.itemByName('MainBody_Extrude')
        if extrude:
            # Modify parameter
            dist_param = extrude.distanceOne
            dist_param.value = 10.0 # Change to 100mm (in cm)
            print("Extrude updated.")
        else:
            print("Feature not found.")
    except:
        print(traceback.format_exc())

edit_extrude()
```

## 15. Feature Naming
Always rename features upon creation. This enables incremental editing and makes the timeline readable.
```python
feature.name = "Descriptive_Name_Type" # e.g. BasePlate_Extrude
```

## 16. Quality Gate
After running operations, check timeline health:
```python
def check_health():
    app = adsk.core.Application.get()
    design = app.activeProduct
    
    # Check for feature errors
    for feature in design.rootComponent.features:
        if feature.healthState == adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState:
            print(f"Feature '{feature.name}' has errors: {feature.errorOrWarningMessage}")
```

## 17. Common Failures Table

| Failure Mode | Cause | Resolution |
| :--- | :--- | :--- |
| Profile not found | Sketch name incorrect or no closed profiles | Check sketch geometry, ensure lines are connected |
| Boolean failed | Cut operation has no intersecting bodies | Ensure distance is correct and extends into body |
| Feature suppressed | Upstream error | Resolve upstream errors, roll back timeline to debug |
| Wrong operation type | Using `Join` when `NewBody` was intended | Set `FeatureOperations.NewBodyFeatureOperation` |
| Index out of bounds | Geometry changed, invalidating index | Use geometry heuristics (e.g. coordinates) instead of indices |

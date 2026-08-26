---
name: fusion360-sketch
description: 2D sketching discipline for Fusion 360 via MCP. Covers sketch creation, all curve types, geometric and dimensional constraints, construction geometry, profile management, parametric curve generation, and sketch validation. Enforces constraint-first design intent.
---

# Fusion 360 Sketching Discipline

This document is the definitive guide for creating and managing 2D sketches in Fusion 360 via the MCP interface. 2D sketching is the foundational element of parametric modeling.

## Important Note on Units
Internal Fusion 360 units for length are **centimeters (cm)** and for angles are **radians**. Scripts MUST convert from standard engineering units (mm, degrees) to cm and radians. 

## 1. Sketch Creation

Sketches can be created on standard origin planes (XY, XZ, YZ), planar faces of existing bodies, or custom construction planes.

```python
import adsk.core, adsk.fusion, traceback, math

def create_base_sketches():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        
        # 1. Sketch on standard XY plane
        xy_plane = root.xYConstructionPlane
        sketch_xy = root.sketches.add(xy_plane)
        sketch_xy.name = "Base_XY_Sketch"
        
        # 2. Sketch on a custom offset plane
        planes = root.constructionPlanes
        plane_input = planes.createInput()
        # Offset 50 mm (5.0 cm) from XY
        offset_val = adsk.core.ValueInput.createByReal(5.0)
        plane_input.setByOffset(xy_plane, offset_val)
        offset_plane = planes.add(plane_input)
        offset_plane.name = "Offset_Plane_50mm"
        
        sketch_offset = root.sketches.add(offset_plane)
        sketch_offset.name = "Offset_Sketch"
        
        print(f"Created sketches: {sketch_xy.name}, {sketch_offset.name}")
        
    except:
        print("Failed to create sketches:\\n{}".format(traceback.format_exc()))

create_base_sketches()
```

## 2. Curve Types

Fusion 360 supports a wide range of sketch curves. 

```python
import adsk.core, adsk.fusion, traceback, math

def draw_curve_types():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        sketch = root.sketches.add(root.xYConstructionPlane)
        sketch.name = "Curve_Types_Sketch"
        
        # Unit conversion factor mm -> cm
        mm = 0.1
        
        # 1. Lines
        lines = sketch.sketchCurves.sketchLines
        line1 = lines.addByTwoPoints(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(100*mm, 0, 0))
        
        # 2. Circles (Center, Radius)
        circles = sketch.sketchCurves.sketchCircles
        circle = circles.addByCenterRadius(adsk.core.Point3D.create(50*mm, 50*mm, 0), 20*mm)
        
        # 3. Arcs (3-Point, Center-Start-End)
        arcs = sketch.sketchCurves.sketchArcs
        arc3pt = arcs.addByThreePoints(
            adsk.core.Point3D.create(0, 100*mm, 0),
            adsk.core.Point3D.create(25*mm, 125*mm, 0),
            adsk.core.Point3D.create(50*mm, 100*mm, 0)
        )
        
        # 4. Rectangles (Center rectangle)
        center_pt = adsk.core.Point3D.create(150*mm, 50*mm, 0)
        corner_pt = adsk.core.Point3D.create(175*mm, 75*mm, 0)
        # addCenterPointRectangle returns an ObjectCollection of lines
        rect_lines = lines.addCenterPointRectangle(center_pt, corner_pt)
        
        # 5. Ellipses
        ellipses = sketch.sketchCurves.sketchEllipses
        ellipse = ellipses.add(
            adsk.core.Point3D.create(150*mm, 150*mm, 0),
            adsk.core.Point3D.create(200*mm, 150*mm, 0),
            adsk.core.Point3D.create(150*mm, 170*mm, 0)
        )
        
        # 6. Splines (Fitted points)
        splines = sketch.sketchCurves.sketchFittedSplines
        points = adsk.core.ObjectCollection.create()
        points.add(adsk.core.Point3D.create(200*mm, 0, 0))
        points.add(adsk.core.Point3D.create(225*mm, 50*mm, 0))
        points.add(adsk.core.Point3D.create(250*mm, 20*mm, 0))
        points.add(adsk.core.Point3D.create(300*mm, 80*mm, 0))
        spline = splines.add(points)
        
        print("Successfully created all base curve types.")
        
    except:
        print("Curve creation failed:\\n{}".format(traceback.format_exc()))

draw_curve_types()
```

## 3. Construction Geometry

Construction lines do not contribute to sketch profiles but are essential for axis lines, symmetry references, and layout geometry.

```python
import adsk.core, adsk.fusion, traceback, math

def create_construction_geometry():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        sketch = root.sketches.add(root.xYConstructionPlane)
        sketch.name = "Construction_Sketch"
        
        mm = 0.1
        lines = sketch.sketchCurves.sketchLines
        
        # Create a centerline for mirroring/revolving
        centerline = lines.addByTwoPoints(
            adsk.core.Point3D.create(0, -100*mm, 0),
            adsk.core.Point3D.create(0, 100*mm, 0)
        )
        centerline.isConstruction = True
        
        print(f"Created construction line. isConstruction: {centerline.isConstruction}")
        
    except:
        print("Construction geometry failed:\\n{}".format(traceback.format_exc()))

create_construction_geometry()
```

## 4. Geometric Constraints

Proper parametric modeling relies on geometric constraints to capture design intent before applying dimensions.

```python
import adsk.core, adsk.fusion, traceback, math

def apply_geometric_constraints():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        sketch = root.sketches.add(root.xYConstructionPlane)
        
        mm = 0.1
        lines = sketch.sketchCurves.sketchLines
        circles = sketch.sketchCurves.sketchCircles
        constraints = sketch.geometricConstraints
        
        line1 = lines.addByTwoPoints(adsk.core.Point3D.create(0,0,0), adsk.core.Point3D.create(100*mm, 10*mm, 0))
        line2 = lines.addByTwoPoints(adsk.core.Point3D.create(0,0,0), adsk.core.Point3D.create(10*mm, 100*mm, 0))
        circle1 = circles.addByCenterRadius(adsk.core.Point3D.create(50*mm, 50*mm, 0), 20*mm)
        
        # 1. Horizontal/Vertical
        constraints.addHorizontal(line1)
        constraints.addVertical(line2)
        
        # 2. Coincident (Origin to line start)
        origin_pt = sketch.originPoint
        constraints.addCoincident(line1.startSketchPoint, origin_pt)
        constraints.addCoincident(line2.startSketchPoint, origin_pt)
        
        # 3. Perpendicular
        # Already handled by Horiz/Vert, but let's add a 3rd line
        line3 = lines.addByTwoPoints(line1.endSketchPoint, adsk.core.Point3D.create(100*mm, 50*mm, 0))
        constraints.addPerpendicular(line1, line3)
        
        # 4. Tangent
        constraints.addTangent(line3, circle1)
        
        # 5. Equal
        line4 = lines.addByTwoPoints(adsk.core.Point3D.create(-50*mm, 0, 0), adsk.core.Point3D.create(-50*mm, 50*mm, 0))
        constraints.addEqual(line2, line4)
        
        print("Successfully applied geometric constraints.")
        
    except:
        print("Constraints failed:\\n{}".format(traceback.format_exc()))

apply_geometric_constraints()
```

## 5. Dimensional Constraints

After geometric constraints, specify dimensions to fully define the sketch.

```python
import adsk.core, adsk.fusion, traceback, math

def apply_dimensional_constraints():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        sketch = root.sketches.add(root.xYConstructionPlane)
        
        mm = 0.1
        lines = sketch.sketchCurves.sketchLines
        circles = sketch.sketchCurves.sketchCircles
        dims = sketch.sketchDimensions
        
        line1 = lines.addByTwoPoints(adsk.core.Point3D.create(0,0,0), adsk.core.Point3D.create(100*mm, 0, 0))
        circle1 = circles.addByCenterRadius(adsk.core.Point3D.create(50*mm, 50*mm, 0), 20*mm)
        
        # Text placement point
        text_pt_linear = adsk.core.Point3D.create(50*mm, -20*mm, 0)
        text_pt_radial = adsk.core.Point3D.create(70*mm, 70*mm, 0)
        
        # Linear Dimension (Length of line1)
        dim_linear = dims.addDistanceDimension(
            line1.startSketchPoint, 
            line1.endSketchPoint,
            adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
            text_pt_linear
        )
        dim_linear.parameter.value = 120 * mm # Modifying the value param
        
        # Radial/Diameter Dimension
        dim_dia = dims.addDiameterDimension(circle1, text_pt_radial)
        dim_dia.parameter.value = 50 * mm
        
        print(f"Dimensions applied. Line length: {dim_linear.parameter.value/mm}mm, Circle Dia: {dim_dia.parameter.value/mm}mm")
        
    except:
        print("Dimensions failed:\\n{}".format(traceback.format_exc()))

apply_dimensional_constraints()
```

## 6. Sketch Profiles

A closed loop in a sketch creates a profile, which is required for solid feature operations (Extrude, Revolve, etc.).

```python
import adsk.core, adsk.fusion, traceback, math

def check_sketch_profiles():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        sketch = root.sketches.add(root.xYConstructionPlane)
        
        mm = 0.1
        lines = sketch.sketchCurves.sketchLines
        # Create a closed square
        pts = [
            adsk.core.Point3D.create(0,0,0),
            adsk.core.Point3D.create(100*mm,0,0),
            adsk.core.Point3D.create(100*mm,100*mm,0),
            adsk.core.Point3D.create(0,100*mm,0)
        ]
        
        for i in range(4):
            lines.addByTwoPoints(pts[i], pts[(i+1)%4])
            
        # The profiles property dynamically calculates closed regions
        profile_count = sketch.profiles.count
        print(f"Found {profile_count} profile(s).")
        
        if profile_count > 0:
            profile0 = sketch.profiles.item(0)
            print(f"Profile 0 area: {profile0.areaProperties().area} cm^2")
        
    except:
        print("Profile check failed:\\n{}".format(traceback.format_exc()))

check_sketch_profiles()
```

## 7. Projected Geometry

To relate a sketch to existing features, you must project geometry into the sketch.

```python
import adsk.core, adsk.fusion, traceback, math

def project_geometry():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        
        # Assume there's a body in the root component. We grab its first face.
        if root.bRepBodies.count == 0:
            print("No bodies found to project.")
            return
            
        body = root.bRepBodies.item(0)
        face = body.faces.item(0)
        
        # Create a sketch offset from XY
        planes = root.constructionPlanes
        plane_input = planes.createInput()
        plane_input.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(10.0))
        offset_plane = planes.add(plane_input)
        sketch = root.sketches.add(offset_plane)
        
        # Project the edges of the face into the sketch
        for edge in face.edges:
            sketch.project(edge)
            
        print("Successfully projected geometry.")
        
    except:
        print("Project geometry failed:\\n{}".format(traceback.format_exc()))

# Only run if a body exists
# project_geometry() 
```

## 8. Parametric Curve Generation

For complex shapes (involute gears, airfoils), compute coordinates via math functions and generate a fitted spline.

```python
import adsk.core, adsk.fusion, traceback, math

def parametric_curve_points(t_start, t_end, num_points, func_x, func_y):
    """
    Generates an ObjectCollection of Point3D from parametric equations.
    func_x and func_y should accept 't' and return cm.
    """
    pts = adsk.core.ObjectCollection.create()
    t_step = (t_end - t_start) / (num_points - 1)
    
    for i in range(num_points):
        t = t_start + i * t_step
        x = func_x(t)
        y = func_y(t)
        pts.add(adsk.core.Point3D.create(x, y, 0))
    return pts

def generate_sine_wave():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        sketch = root.sketches.add(root.xYConstructionPlane)
        sketch.name = "Sine_Wave"
        
        # Params: amplitude 50mm, wavelength 200mm
        amp = 5.0 # cm
        wavelength = 20.0 # cm
        
        # t from 0 to 2*pi
        func_x = lambda t: (t / (2*math.pi)) * wavelength
        func_y = lambda t: math.sin(t) * amp
        
        pts = parametric_curve_points(0, 2*math.pi, 50, func_x, func_y)
        
        spline = sketch.sketchCurves.sketchFittedSplines.add(pts)
        print("Sine wave generated.")
        
    except:
        print("Parametric generation failed:\\n{}".format(traceback.format_exc()))

generate_sine_wave()
```

## 9. Sketch Editing

To modify existing sketches, locate the sketch by name and edit its dimension parameters.

```python
import adsk.core, adsk.fusion, traceback, math

def edit_existing_sketch(sketch_name, new_dim_value_mm):
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root = design.rootComponent
        
        sketch = root.sketches.itemByName(sketch_name)
        if not sketch:
            print(f"Sketch '{sketch_name}' not found.")
            return
            
        mm = 0.1
        
        # Modify the first dimension found
        if sketch.sketchDimensions.count > 0:
            dim = sketch.sketchDimensions.item(0)
            dim.parameter.value = new_dim_value_mm * mm
            print(f"Updated dimension to {new_dim_value_mm} mm.")
        else:
            print("No dimensions found to edit.")
            
    except:
        print("Sketch editing failed:\\n{}".format(traceback.format_exc()))

# edit_existing_sketch("Base_XY_Sketch", 150)
```

## 10. Sketch Validation & Quality Gates

**Quality Gate Checklist:**
1. **Fully Constrained:** Ensure geometry has geometric or dimensional constraints preventing arbitrary dragging.
2. **Profiles Exist:** `sketch.profiles.count > 0` if solid modeling is intended.
3. **No Self-Intersections:** Ensure profiles do not loop back over themselves unless intentionally separated into multiple profiles.
4. **Constraint Count:** Over-constraining leads to failure; verify dimensions don't conflict with geometric constraints.

```python
def validate_sketch(sketch):
    try:
        profile_count = sketch.profiles.count
        dim_count = sketch.sketchDimensions.count
        geom_const_count = sketch.geometricConstraints.count
        
        print(f"Validation for '{sketch.name}':")
        print(f" - Profiles: {profile_count}")
        print(f" - Dimensions: {dim_count}")
        print(f" - Geometric Constraints: {geom_const_count}")
        
        if profile_count == 0:
            print("WARNING: No profiles found. Sketch cannot be extruded.")
    except:
        pass
```

## 11. Common Failures Table

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **Open Profiles** | Missing coincident constraints at curve endpoints. | Use `addCoincident()` between `curve1.endSketchPoint` and `curve2.startSketchPoint`. |
| **Over-constrained** | Adding a dimension that contradicts existing geometric constraints (e.g., adding an angle to perpendicular lines). | Design intent check. Use reference dimensions if needed, or remove conflicting geometric constraints. |
| **Wrong Plane** | Applying a sketch to a face or plane that was deleted/modified earlier in the timeline. | Use stable references (Origin planes) or robust custom construction planes. |
| **Self-intersecting** | Sketch geometry crosses itself, causing ambiguity in profile generation. | Split curves or use construction lines to isolate intersecting areas. |
| **Units Error** | Entering dimensions as `50` assuming mm, but Fusion interprets it as cm. | ALWAYS multiply raw float numbers by `0.1` (mm to cm factor). |

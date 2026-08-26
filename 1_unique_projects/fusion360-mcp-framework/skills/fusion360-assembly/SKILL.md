---
name: fusion360-assembly
description: Assembly and mating operations for Fusion 360 via MCP. Covers component creation, joint types (rigid, revolute, slider, cylindrical, pin-slot, planar, ball), as-built joints, joint limits, motion links, contact sets, interference detection, BOM generation, and exploded views.
---

# Fusion 360 MCP Skill: Assembly & Mating

This skill guide provides advanced, engineering-grade patterns for creating assemblies, joints, motion links, and analyzing interference within Fusion 360 using the MCP framework.

## 1. Assembly Concepts

In Fusion 360, the assembly structure is determined by **Components** and **Occurrences**. 
- **Top-Down Assembly**: Designing parts within the context of an assembly. You create components inside the main design file.
- **Bottom-Up Assembly**: Designing parts individually and inserting them as external components.
- **Ground Component**: In any assembly, at least one component (usually the base or chassis) must be grounded to serve as the fixed reference frame.
- **Component vs. Occurrence**: A `Component` contains the geometry (bodies, sketches). An `Occurrence` is an instance of a component in an assembly. When you mate components, you are actually mating *Occurrences*. 

## 2. Component Creation

### Create New Component & Move Bodies
This pattern demonstrates how to create a new component within the root component and optionally move existing bodies into it.

```python
import adsk.core, adsk.fusion, traceback

def create_component_pattern():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root_comp = design.rootComponent
        
        # 1. Create a new empty component
        transform = adsk.core.Matrix3D.create()
        new_occ = root_comp.occurrences.addNewComponent(transform)
        new_comp = new_occ.component
        new_comp.name = "Chassis_Base"
        
        # 2. (Optional) Ground the component
        new_occ.isGrounded = True
        
        # 3. Create component from existing body (simulation)
        # Assuming we have a body named 'Floating_Body' in the root
        bodies = root_comp.bRepBodies
        target_body = None
        for b in bodies:
            if b.name == "Floating_Body":
                target_body = b
                break
                
        if target_body:
            # Note: Moving a body into a component technically creates a new feature
            # Often it's better to create a new occurrence and copy the body, or use Cut/Paste features.
            # In API, creating base features in the new component and copying the body is standard.
            base_feature = new_comp.features.baseFeatures.add()
            base_feature.startEdit()
            new_comp.bRepBodies.add(target_body, base_feature)
            base_feature.finishEdit()
            target_body.deleteMe() # Remove original
            
        return {"status": "success", "component_name": new_comp.name, "is_grounded": new_occ.isGrounded}
    except:
        return {"status": "error", "message": traceback.format_exc()}

print(create_component_pattern())
```

## 3. Positioning

Positioning occurs by applying a `Matrix3D` transform to an Occurrence. 

```python
import adsk.core, adsk.fusion, traceback, math

def position_occurrence_pattern(occurrence_name, tx_cm, ty_cm, tz_cm, rx_rad, ry_rad, rz_rad):
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root_comp = design.rootComponent
        
        # Find occurrence
        target_occ = None
        for occ in root_comp.occurrences:
            if occ.name == occurrence_name:
                target_occ = occ
                break
                
        if not target_occ:
            return {"status": "error", "message": f"Occurrence {occurrence_name} not found."}
            
        # Create transform matrix
        mat = adsk.core.Matrix3D.create()
        
        # Rotation (apply X, Y, Z sequentially)
        mat.setToRotation(rx_rad, adsk.core.Vector3D.create(1, 0, 0), adsk.core.Point3D.create(0, 0, 0))
        
        mat_y = adsk.core.Matrix3D.create()
        mat_y.setToRotation(ry_rad, adsk.core.Vector3D.create(0, 1, 0), adsk.core.Point3D.create(0, 0, 0))
        mat.transformBy(mat_y)
        
        mat_z = adsk.core.Matrix3D.create()
        mat_z.setToRotation(rz_rad, adsk.core.Vector3D.create(0, 0, 1), adsk.core.Point3D.create(0, 0, 0))
        mat.transformBy(mat_z)
        
        # Translation
        mat.translation = adsk.core.Vector3D.create(tx_cm, ty_cm, tz_cm)
        
        # Apply transform
        target_occ.transform2 = mat
        
        # Capture position
        design.snapshots.add()
        
        return {"status": "success", "message": f"Positioned {occurrence_name}"}
    except:
        return {"status": "error", "message": traceback.format_exc()}

print(position_occurrence_pattern("Component1:1", 5.0, 0, 0, 0, math.pi/2, 0))
```

## 4. Joint Types & 6. Joint Origins

Fusion 360 supports several joint types. Selecting the correct geometry (JointGeometry) is critical.

```python
import adsk.core, adsk.fusion, traceback

def create_joints_pattern():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root_comp = design.rootComponent
        joints = root_comp.joints
        
        # Assume we have occ1 and occ2
        occ1 = root_comp.occurrences.itemByName("PartA:1")
        occ2 = root_comp.occurrences.itemByName("PartB:1")
        
        if not occ1 or not occ2:
            return {"status": "error", "message": "Missing required occurrences"}
            
        # Rigid Joint / Revolute Joint Example with Assembly Context Proxies
        # 1. Find edge in body context
        edge1 = None
        for edge in body1.edges:
            if edge.geometry.objectType == adsk.core.Circle3D.classType():
                edge1 = edge
                break
                
        edge2 = None
        for edge in body2.edges:
            if edge.geometry.objectType == adsk.core.Circle3D.classType():
                edge2 = edge
                break

        # 2. Create proxies for assembly occurrences (CRITICAL)
        edge1_proxy = edge1.createForAssemblyContext(occ1)
        edge2_proxy = edge2.createForAssemblyContext(occ2)

        # 3. Create Joint Geometry from proxies
        geo1 = adsk.fusion.JointGeometry.createByCurve(edge1_proxy, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
        geo2 = adsk.fusion.JointGeometry.createByCurve(edge2_proxy, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)

        # 4. Create Joint Input
        jointInput = root.joints.createInput(geo1, geo2)
        jointInput.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
        joint = root.joints.add(jointInput)
        joint.name = "Part_Revolute_Joint"
        
        # === SET JOINT TYPE ===
        
        # 1. Rigid (0 DOF)
        joint_input.setAsRigidJointMotion()
        
        # 2. Revolute (1 DOF rotation)
        # joint_input.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
        
        # 3. Slider (1 DOF translation)
        # joint_input.setAsSliderJointMotion(adsk.fusion.JointDirections.XAxisJointDirection)
        
        # 4. Cylindrical (2 DOF)
        # joint_input.setAsCylindricalJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
        
        # 5. Pin-Slot (2 DOF)
        # joint_input.setAsPinSlotJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection, adsk.fusion.JointDirections.XAxisJointDirection)
        
        # 6. Planar (3 DOF)
        # joint_input.setAsPlanarJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
        
        # 7. Ball (3 DOF rotation)
        # joint_input.setAsBallJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection, adsk.fusion.JointDirections.XAxisJointDirection)
        
        # Create the joint
        joint = joints.add(joint_input)
        joint.name = "My_Rigid_Joint"
        
        return {"status": "success", "joint_name": joint.name, "type": joint.jointMotion.jointType}
    except:
        return {"status": "error", "message": traceback.format_exc()}

print(create_joints_pattern())
```

## 5. As-Built Joints

As-Built joints define relationships between components that are already in their correct relative positions.

```python
import adsk.core, adsk.fusion, traceback

def create_as_built_joint():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root_comp = design.rootComponent
        
        occ1 = root_comp.occurrences.itemByName("Chassis:1")
        occ2 = root_comp.occurrences.itemByName("Cover:1")
        
        as_built_joints = root_comp.asBuiltJoints
        joint_input = as_built_joints.createInput(occ1, occ2, None)
        
        # Set to Rigid
        joint_input.setAsRigidJointMotion()
        
        joint = as_built_joints.add(joint_input)
        
        return {"status": "success", "joint_name": joint.name}
    except:
        return {"status": "error", "message": traceback.format_exc()}

print(create_as_built_joint())
```

## 7. Joint Limits & 8. Motion Links

```python
import adsk.core, adsk.fusion, traceback, math

def limit_and_link_pattern():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root_comp = design.rootComponent
        
        # 1. Setting Joint Limits on a Revolute Joint
        joint1 = root_comp.joints.itemByName("Revolute1")
        if joint1 and joint1.jointMotion.jointType == adsk.fusion.JointTypes.RevoluteJointType:
            rev_motion = joint1.jointMotion
            rev_motion.rotationLimits.isMinimumValueEnabled = True
            rev_motion.rotationLimits.minimumValue = -math.pi / 4  # -45 degrees
            rev_motion.rotationLimits.isMaximumValueEnabled = True
            rev_motion.rotationLimits.maximumValue = math.pi / 4   # 45 degrees
            
        # 2. Motion Link (Linking two revolute joints)
        joint2 = root_comp.joints.itemByName("Revolute2")
        if joint1 and joint2:
            motion_links = root_comp.motionLinks
            link_input = motion_links.createInput(joint1, joint2)
            # Gear ratio: for every 360 deg on joint1, joint2 moves 180 deg (2:1 ratio)
            link_input.angleEquivalent = math.pi
            link = motion_links.add(link_input)
            
        return {"status": "success", "message": "Limits and links applied"}
    except:
        return {"status": "error", "message": traceback.format_exc()}

print(limit_and_link_pattern())
```

## 9. Contact Sets & 10. Interference Detection

```python
import adsk.core, adsk.fusion, traceback

def analyze_assembly_pattern():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        
        # Enable Contact Sets
        design.isContactSetsEnabled = True
        
        # Interference Detection
        root_comp = design.rootComponent
        occurrences = root_comp.occurrences
        
        # Collect all bodies
        body_col = adsk.core.ObjectCollection.create()
        for occ in occurrences:
            for body in occ.bRepBodies:
                body_col.add(body)
                
        if body_col.count < 2:
            return {"status": "info", "message": "Not enough bodies for interference."}
            
        # Create interference input
        interference_input = design.createInterferenceInput(body_col)
        interference_input.areCoincidentFacesIncluded = False
        
        results = design.analyzeInterference(interference_input)
        
        interference_details = []
        for result in results:
            vol = result.interferenceBody.volume if result.interferenceBody else 0
            interference_details.append({
                "body1": result.entityOne.name,
                "body2": result.entityTwo.name,
                "volume_cm3": vol
            })
            
        return {"status": "success", "interferences": interference_details}
    except:
        return {"status": "error", "message": traceback.format_exc()}

print(analyze_assembly_pattern())
```

## 11. BOM Generation

```python
import adsk.core, adsk.fusion, traceback

def generate_bom():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root_comp = design.rootComponent
        
        bom = {}
        
        def traverse(occurrences):
            for occ in occurrences:
                comp = occ.component
                part_number = comp.partNumber
                if part_number in bom:
                    bom[part_number]['quantity'] += 1
                else:
                    bom[part_number] = {
                        'name': comp.name,
                        'quantity': 1,
                        'material': comp.bRepBodies.item(0).physicalMaterial.name if comp.bRepBodies.count > 0 else "N/A"
                    }
                if occ.childOccurrences:
                    traverse(occ.childOccurrences)
                    
        traverse(root_comp.occurrences)
        
        return {"status": "success", "bom": bom}
    except:
        return {"status": "error", "message": traceback.format_exc()}

print(generate_bom())
```

## 12. Exploded View (Programmatic Concept)

Fusion 360 API lacks a direct "Exploded View" feature creation tool. Instead, programmatic exploded views are achieved by translating occurrences outward from the assembly center and capturing a snapshot.

```python
import adsk.core, adsk.fusion, traceback

def explode_assembly(distance_cm=10.0):
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root_comp = design.rootComponent
        
        for occ in root_comp.occurrences:
            if not occ.isGrounded:
                # Get vector from origin to component center
                bbox = occ.boundingBox
                center_x = (bbox.maxPoint.x + bbox.minPoint.x) / 2
                center_y = (bbox.maxPoint.y + bbox.minPoint.y) / 2
                center_z = (bbox.maxPoint.z + bbox.minPoint.z) / 2
                
                vec = adsk.core.Vector3D.create(center_x, center_y, center_z)
                vec.normalize()
                vec.scaleBy(distance_cm)
                
                mat = occ.transform2
                mat.translation = adsk.core.Vector3D.create(
                    mat.translation.x + vec.x,
                    mat.translation.y + vec.y,
                    mat.translation.z + vec.z
                )
                occ.transform2 = mat
                
        design.snapshots.add()
        return {"status": "success", "message": "Assembly exploded"}
    except:
        return {"status": "error", "message": traceback.format_exc()}
```

## 13. Quality Gate

Before finishing an assembly task, always run this checklist script.

```python
import adsk.core, adsk.fusion, traceback

def quality_gate():
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        root_comp = design.rootComponent
        
        checks = {
            "grounded_component_exists": False,
            "all_components_named": True,
            "unnamed_components": [],
            "failed_joints": []
        }
        
        # Check grounding and names
        for occ in root_comp.occurrences:
            if occ.isGrounded:
                checks["grounded_component_exists"] = True
            if occ.component.name.startswith("Component"):
                checks["all_components_named"] = False
                checks["unnamed_components"].append(occ.component.name)
                
        # Check joints
        for joint in root_comp.joints:
            if joint.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:
                checks["failed_joints"].append(joint.name)
                
        passed = checks["grounded_component_exists"] and checks["all_components_named"] and len(checks["failed_joints"]) == 0
        
        return {"status": "success", "passed": passed, "checks": checks}
    except:
        return {"status": "error", "message": traceback.format_exc()}
```

## 14. Common Failures

| Failure | Cause | Solution |
|---------|-------|----------|
| `RuntimeError: 2 : InternalValidationError` on Joints | Invalid JointGeometry or proxy context error. | Ensure you are referencing faces/edges in the context of the root component (use `createForAssemblyContext`). |
| Missing Movement | Component is grounded, or conflicting rigid joints exist. | Check `isGrounded` property and review joint tree. |
| Component flies into space | Matrix translation values passed in incorrect units (mm instead of cm). | ALWAYS divide mm inputs by 10. |
| Circular Reference | Trying to mate an occurrence to its own child. | Check parent-child hierarchy before applying joints. |

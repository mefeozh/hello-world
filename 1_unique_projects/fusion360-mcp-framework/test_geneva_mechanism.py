import adsk.core, adsk.fusion, traceback, math, json

def run(context):
    app = adsk.core.Application.get()
    ui  = app.userInterface
    result = {"status": "success", "steps": [], "errors": []}
    
    try:
        # Setup Document
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = app.activeProduct
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        result["steps"].append("Created new parametric Fusion document")

        # Dimensions in CM (internal API units)
        center_distance_cm = 8.0     # 80 mm
        post_radius_cm = 0.6         # 12 mm dia post
        post_height_cm = 2.5         # 25 mm height
        base_w_cm = 16.0             # 160 mm width
        base_h_cm = 10.0             # 100 mm height
        base_thick_cm = 1.0          # 10 mm thickness
        
        driver_radius_cm = 4.0       # 40 mm radius
        pin_radius_cm = 0.39         # 7.8 mm dia pin
        pin_height_cm = 1.2          # 12 mm pin height
        pin_offset_cm = 4.0          # 40 mm pin offset
        
        geneva_slots = 4
        geneva_outer_r_cm = center_distance_cm * math.cos(math.pi / geneva_slots) # ~5.657 cm
        slot_width_cm = 0.82         # 8.2 mm slot width
        slot_depth_cm = 3.2          # 32 mm slot depth

        # -------------------------------------------------------------
        # STEP 1: Base Frame Component
        # -------------------------------------------------------------
        occ_base = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp_base = occ_base.component
        comp_base.name = "Base_Frame"
        occ_base.isGrounded = True   # Ground the base
        
        sk_base = comp_base.sketches.add(comp_base.xYConstructionPlane)
        sk_base.sketchCurves.sketchLines.addCenterPointRectangle(
            adsk.core.Point3D.create(center_distance_cm / 2.0, 0, 0),
            adsk.core.Point3D.create(center_distance_cm / 2.0 + base_w_cm / 2.0, base_h_cm / 2.0, 0)
        )
        sk_base.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), post_radius_cm)
        sk_base.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(center_distance_cm, 0, 0), post_radius_cm)
        
        prof_base_plate = max(sk_base.profiles, key=lambda p: p.areaProperties().area)
        ext_base_input = comp_base.features.extrudeFeatures.createInput(
            prof_base_plate, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        ext_base_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(base_thick_cm))
        ext_base = comp_base.features.extrudeFeatures.add(ext_base_input)
        body_base = ext_base.bodies.item(0)
        body_base.name = "Base_Plate_Body"

        # Shaft Posts
        sk_posts = comp_base.sketches.add(comp_base.xYConstructionPlane)
        sk_posts.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), post_radius_cm)
        sk_posts.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(center_distance_cm, 0, 0), post_radius_cm)
        profs_posts = adsk.core.ObjectCollection.create()
        for p in sk_posts.profiles: profs_posts.add(p)
            
        ext_post_input = comp_base.features.extrudeFeatures.createInput(
            profs_posts, adsk.fusion.FeatureOperations.JoinFeatureOperation
        )
        ext_post_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(base_thick_cm + post_height_cm))
        comp_base.features.extrudeFeatures.add(ext_post_input)
        result["steps"].append("Created Grounded Base Frame with Shaft Posts")

        # -------------------------------------------------------------
        # STEP 2: Driver Wheel Component
        # -------------------------------------------------------------
        occ_driver = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp_driver = occ_driver.component
        comp_driver.name = "Driver_Wheel"
        
        sk_driver = comp_driver.sketches.add(comp_driver.xYConstructionPlane)
        sk_driver.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), driver_radius_cm)
        sk_driver.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), post_radius_cm)
        
        prof_disk = max(sk_driver.profiles, key=lambda p: p.areaProperties().area)
        ext_driver_disk = comp_driver.features.extrudeFeatures.createInput(
            prof_disk, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        ext_driver_disk.setDistanceExtent(False, adsk.core.ValueInput.createByReal(0.8))
        ext_driver = comp_driver.features.extrudeFeatures.add(ext_driver_disk)
        body_driver = ext_driver.bodies.item(0)
        body_driver.name = "Driver_Wheel_Body"
        
        # Drive Pin
        sk_pin = comp_driver.sketches.add(comp_driver.xYConstructionPlane)
        sk_pin.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(pin_offset_cm, 0, 0), pin_radius_cm
        )
        prof_pin = sk_pin.profiles.item(0)
        ext_pin_input = comp_driver.features.extrudeFeatures.createInput(
            prof_pin, adsk.fusion.FeatureOperations.JoinFeatureOperation
        )
        ext_pin_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(0.8 + pin_height_cm))
        comp_driver.features.extrudeFeatures.add(ext_pin_input)
        result["steps"].append("Created Driver Wheel Component")

        # -------------------------------------------------------------
        # STEP 3: Geneva Wheel Component
        # -------------------------------------------------------------
        mat_geneva = adsk.core.Matrix3D.create()
        mat_geneva.translation = adsk.core.Vector3D.create(center_distance_cm, 0, 0)
        occ_geneva = root.occurrences.addNewComponent(mat_geneva)
        comp_geneva = occ_geneva.component
        comp_geneva.name = "Geneva_Wheel"
        
        sk_geneva = comp_geneva.sketches.add(comp_geneva.xYConstructionPlane)
        sk_geneva.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), geneva_outer_r_cm)
        sk_geneva.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), post_radius_cm)
        
        half_w = slot_width_cm / 2.0
        for i in range(4):
            angle = i * (math.pi / 2.0)
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            
            p1 = adsk.core.Point3D.create((center_distance_cm - slot_depth_cm) * cos_a - half_w * sin_a, (center_distance_cm - slot_depth_cm) * sin_a + half_w * cos_a, 0)
            p2 = adsk.core.Point3D.create((geneva_outer_r_cm + 0.5) * cos_a - half_w * sin_a, (geneva_outer_r_cm + 0.5) * sin_a + half_w * cos_a, 0)
            p3 = adsk.core.Point3D.create((geneva_outer_r_cm + 0.5) * cos_a + half_w * sin_a, (geneva_outer_r_cm + 0.5) * sin_a - half_w * cos_a, 0)
            p4 = adsk.core.Point3D.create((center_distance_cm - slot_depth_cm) * cos_a + half_w * sin_a, (center_distance_cm - slot_depth_cm) * sin_a - half_w * cos_a, 0)
            
            lines = sk_geneva.sketchCurves.sketchLines
            lines.addByTwoPoints(p1, p2)
            lines.addByTwoPoints(p2, p3)
            lines.addByTwoPoints(p3, p4)
            lines.addByTwoPoints(p4, p1)

        prof_geneva_wheel = max(sk_geneva.profiles, key=lambda p: p.areaProperties().area)
        ext_geneva_input = comp_geneva.features.extrudeFeatures.createInput(
            prof_geneva_wheel, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        ext_geneva_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(0.8))
        ext_geneva_feat = comp_geneva.features.extrudeFeatures.add(ext_geneva_input)
        body_geneva = ext_geneva_feat.bodies.item(0)
        body_geneva.name = "Geneva_Star_Wheel_Body"
        result["steps"].append("Created Geneva Star Wheel Component")

        # -------------------------------------------------------------
        # STEP 4: Kinematic Joints using Proxy B-Rep Edge Geometry
        # -------------------------------------------------------------
        edge_driver_bore = None
        for edge in body_driver.edges:
            if edge.geometry.objectType == adsk.core.Circle3D.classType():
                edge_driver_bore = edge
                break
                
        edge_geneva_bore = None
        for edge in body_geneva.edges:
            if edge.geometry.objectType == adsk.core.Circle3D.classType():
                edge_geneva_bore = edge
                break
                
        edge_post1 = None
        edge_post2 = None
        for edge in body_base.edges:
            if edge.geometry.objectType == adsk.core.Circle3D.classType():
                center = edge.geometry.center
                if abs(center.x) < 0.1 and not edge_post1:
                    edge_post1 = edge
                elif abs(center.x - center_distance_cm) < 0.1 and not edge_post2:
                    edge_post2 = edge

        # Create proxies for assembly occurrences
        edge_driver_proxy = edge_driver_bore.createForAssemblyContext(occ_driver)
        edge_post1_proxy = edge_post1.createForAssemblyContext(occ_base)
        
        edge_geneva_proxy = edge_geneva_bore.createForAssemblyContext(occ_geneva)
        edge_post2_proxy = edge_post2.createForAssemblyContext(occ_base)

        # Create Joint Geometry from proxies
        geo_driver = adsk.fusion.JointGeometry.createByCurve(edge_driver_proxy, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
        geo_post1 = adsk.fusion.JointGeometry.createByCurve(edge_post1_proxy, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
        
        geo_geneva = adsk.fusion.JointGeometry.createByCurve(edge_geneva_proxy, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
        geo_post2 = adsk.fusion.JointGeometry.createByCurve(edge_post2_proxy, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)

        # Create Revolute Joints
        joint_input_driver = root.joints.createInput(geo_driver, geo_post1)
        joint_input_driver.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
        joint_driver = root.joints.add(joint_input_driver)
        joint_driver.name = "Driver_Revolute_Joint"
        result["steps"].append("Created Driver Revolute Joint by Proxy Circle3D Edge")

        joint_input_geneva = root.joints.createInput(geo_geneva, geo_post2)
        joint_input_geneva.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
        joint_geneva = root.joints.add(joint_input_geneva)
        joint_geneva.name = "Geneva_Revolute_Joint"
        result["steps"].append("Created Geneva Revolute Joint by Proxy Circle3D Edge")

        # -------------------------------------------------------------
        # STEP 5: Quality Gate Audit
        # -------------------------------------------------------------
        timeline = design.timeline
        unhealthy = 0
        for i in range(timeline.count):
            item = timeline.item(i)
            if item.healthState in [adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState,
                                    adsk.fusion.FeatureHealthStates.WarningFeatureHealthState]:
                unhealthy += 1
                result["errors"].append(f"Timeline item {i} ({item.entity.name}) warning/error")
                
        result["timeline_health"] = "PASS" if unhealthy == 0 else "FAIL"
        result["data"] = {
            "total_occurrences": root.occurrences.count,
            "joints_count": root.joints.count,
            "is_base_grounded": occ_base.isGrounded,
            "driver_joint": joint_driver.name,
            "geneva_joint": joint_geneva.name
        }
        
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(str(e))
        result["traceback"] = traceback.format_exc()
        
    print(json.dumps(result, indent=2))

run(None)

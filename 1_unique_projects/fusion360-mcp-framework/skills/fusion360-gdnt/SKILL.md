---
name: fusion360-gdnt
description: Geometric Dimensioning and Tolerancing per ASME Y14.5-2018 for Fusion 360 via MCP. Covers datum features, feature control frames, form/orientation/location/profile/runout tolerances, material condition modifiers, bonus tolerances, composite tolerances, and application in Fusion 360 drawings.
---

# Geometric Dimensioning and Tolerancing (GD&T) for Fusion 360

## 1. Why GD&T

Without Geometric Dimensioning & Tolerancing (GD&T), a part cannot be reliably inspected, quality-controlled, or guaranteed to assemble. Basic coordinate tolerancing (± tolerances) inherently fails to control form, orientation, or location of features relative to one another in a mathematically rigorous way. 

In traditional coordinate tolerancing, a hole might be called out as 10 ± 0.1 mm from an edge. However, this creates a square tolerance zone, meaning the diagonal distance allows more deviation than the horizontal/vertical distances. Furthermore, it assumes the edge is perfectly straight and square, which it never is. 

GD&T is the explicit engineering language between design, manufacturing, and metrology. It shifts the paradigm from "how to make it" to "how it functions." It guarantees functional requirements (like assembly mating) while simultaneously opening up manufacturing tolerances (through concepts like bonus tolerance and cylindrical tolerance zones). For a senior mechanical engineer, mastering ASME Y14.5-2018 (or ISO 1101) is non-negotiable.

## 2. Datum Features

Datum features are the physical, tangible features on a part (like a face or a bore) that are used to establish a conceptual Datum Reference Frame (DRF) — a set of three mutually perpendicular planes. The DRF is the theoretical coordinate system against which all geometric tolerances are measured.

### Selection Rules and the 3-2-1 Principle
Datums must be selected based on the part's functional assembly and mating surfaces.
*   **Primary Datum (A)**: Establishes the orientation of the part. Usually a large, primary contact surface. It restricts 3 degrees of freedom (DOF) — typically 1 translation and 2 rotations. (The "3" in 3-2-1, meaning 3 minimum points of contact).
*   **Secondary Datum (B)**: Establishes location. Usually a secondary mating face or a centering feature (like a bore). It restricts 2 DOF — typically 1 translation and 1 rotation. (The "2" in 3-2-1).
*   **Tertiary Datum (C)**: Prevents final rotation. Usually a slot, a pin hole, or a final edge. Restricts the final 1 DOF. (The "1" in 3-2-1).

### Defining Datums in Fusion 360 API
While Fusion 360's API has limited support for applying GD&T directly to 3D model features (Model-Based Definition - MBD) or 2D Drawings, standardizing nomenclature via attributes is the recommended workaround for agent-based automation.

```python
import adsk.core, adsk.fusion, traceback

def tag_datum_feature(component, face, datum_letter):
    """
    Tags a B-Rep face as a Datum Feature using Fusion 360 attributes.
    This establishes a persistent reference for downstream drawing generation.
    """
    try:
        # Validate inputs
        if not isinstance(face, adsk.fusion.BRepFace):
            return {"status": "error", "message": "Input is not a B-Rep face"}
        
        # Apply the attribute
        face.attributes.add('GDnT', 'DatumLetter', datum_letter)
        face.attributes.add('GDnT', 'FeatureType', 'Datum')
        
        return {"status": "success", "message": f"Tagged face as Datum {datum_letter}"}
    except:
        return {"status": "error", "message": traceback.format_exc()}
```

## 3. Feature Control Frame (FCF)

The Feature Control Frame is the sentence structure of GD&T. It reads from left to right.

### Syntax
`[ Geometric Symbol ] | [ Tolerance Zone Size/Shape ] [ Material Modifier ] | [ Primary Datum ] [ Mod ] | [ Secondary Datum ] [ Mod ] | [ Tertiary Datum ] [ Mod ]`

**Example:**
`[ ⌖ ] | [ ⌀ 0.1 Ⓜ ] | [ A ] | [ B Ⓜ ] | [ C ]`

**Translation:**
"The Position (⌖) of this feature's axis must lie within a Cylindrical (⌀) tolerance zone of 0.1mm at Maximum Material Condition (Ⓜ), relative to Primary Datum A, Secondary Datum B at MMC (Ⓜ), and Tertiary Datum C."

## 4. Tolerance Types (ASME Y14.5-2018)

### Form Tolerances (No Datums Allowed)
Form tolerances control the shape of a feature independent of its location or orientation. They never reference datums.

*   **Flatness (▱)**: Controls how flat a surface is. 
    *   *Tolerance Zone*: Two parallel planes.
    *   *Usage*: Primary mating surfaces, sealing faces. 
    *   *Example*: Mating face of a valve body.
*   **Straightness (—)**: Controls how straight a line element or a feature's axis is.
    *   *Tolerance Zone*: Two parallel lines (surface) or a cylinder (axis).
    *   *Usage*: Shafts, guide rails.
    *   *Example*: A linear bearing shaft to prevent binding.
*   **Circularity / Roundness (○)**: Controls how circular a 2D cross-section is.
    *   *Tolerance Zone*: Two concentric circles.
    *   *Usage*: Bearing journals, seals.
    *   *Example*: An O-ring groove diameter.
*   **Cylindricity (⌭)**: Controls how cylindrical a 3D surface is (combines circularity, straightness, and taper).
    *   *Tolerance Zone*: Two concentric cylinders.
    *   *Usage*: Hydraulic bores, precision pins.
    *   *Example*: The bore of a hydraulic piston cylinder.

### Orientation Tolerances (Requires Datums)
Controls the tilt of a feature relative to a datum.

*   **Perpendicularity (⟂)**: Controls how perfectly 90° a feature is to a datum.
    *   *Tolerance Zone*: Two parallel planes or a cylinder.
    *   *Usage*: Mounting bosses, dowel pins.
    *   *Example*: A tapped hole must be perpendicular to the mating face so the bolt head seats flush.
*   **Parallelism (∥)**: Controls how perfectly parallel a feature is to a datum.
    *   *Tolerance Zone*: Two parallel planes or a cylinder.
    *   *Usage*: Guide rails, spacer blocks.
    *   *Example*: Top surface of a precision spacer block relative to its bottom.
*   **Angularity (∠)**: Controls how close a feature is to a basic angle (other than 90° or 0°) relative to a datum.
    *   *Tolerance Zone*: Two parallel planes or a cylinder.
    *   *Usage*: Tapered bores, angled mounting pads.
    *   *Example*: A 45° dovetail slide.

### Location Tolerances (Requires Datums)
Controls where a feature is located.

*   **Position (⌖)**: The most common and powerful GD&T symbol. Controls the location of a feature of size (hole, pin, slot).
    *   *Tolerance Zone*: Typically a cylinder (if ⌀ is specified) or two parallel planes.
    *   *Usage*: Hole patterns, dowel locations.
    *   *Example*: A 4-hole bolt circle.
*   **Concentricity (◎)**: Controls the median points of a part relative to a datum axis. *Note: Removed in ASME Y14.5-2018; replaced by Position or Runout in modern design due to inspection difficulty.*
    *   *Tolerance Zone*: Cylinder.
    *   *Usage*: Coaxial features.
*   **Symmetry (⌯)**: Controls median points relative to a center plane. *Note: Also removed in Y14.5-2018; replace with Position or Profile.*

### Profile Tolerances (May or May Not Use Datums)
Controls the entire surface geometry. The most comprehensive GD&T control.

*   **Profile of a Line (⌒)**: Controls a 2D cross-section.
    *   *Tolerance Zone*: Two uniform 2D boundaries around the true profile.
    *   *Usage*: Extrusion profiles, sheet metal bends.
*   **Profile of a Surface (⌓)**: Controls a 3D surface. Can control form, orientation, and location simultaneously.
    *   *Tolerance Zone*: Two uniform 3D boundaries around the true profile.
    *   *Usage*: Castings, forgings, complex aerodynamic surfaces.
    *   *Example*: The contour of a turbine blade.

### Runout Tolerances (Requires Datums)
Controls the composite variation of form and location of a rotating part.

*   **Circular Runout (↗)**: Controls 2D circular elements independently as the part rotates.
    *   *Tolerance Zone*: Two concentric circles.
    *   *Usage*: Shafts, O-ring grooves.
    *   *Example*: Checking a spinning shaft with a dial indicator at a specific cross-section.
*   **Total Runout (⌰)**: Controls the entire 3D surface simultaneously as the part rotates. Tighter than circular runout.
    *   *Tolerance Zone*: Two concentric cylinders.
    *   *Usage*: High-speed spindles, pump shafts.
    *   *Example*: The mounting journal for a high-speed spindle bearing.

## 5. Material Condition Modifiers

Material Condition Modifiers are a core concept that allows manufacturing flexibility while guaranteeing functional assembly. They apply to Features of Size (FOS) like holes and pins.

### The Modifiers
*   **MMC - Maximum Material Condition (Ⓜ)**: The condition where the feature contains the *maximum* amount of material within its size limits. 
    *   *Pin*: Largest allowable diameter.
    *   *Hole*: Smallest allowable diameter.
    *   *Usage*: Clearance fits. Guarantees that parts will assemble under worst-case conditions.
*   **LMC - Least Material Condition (Ⓛ)**: The condition where the feature contains the *least* amount of material.
    *   *Pin*: Smallest allowable diameter.
    *   *Hole*: Largest allowable diameter.
    *   *Usage*: Wall thickness preservation, preventing breakout.
*   **RFS - Regardless of Feature Size (No Symbol)**: The default condition in ASME Y14.5. The geometric tolerance is strictly held regardless of the feature's produced size.
    *   *Usage*: Press fits, balancing, alignment, when the feature must be perfectly centered regardless of size.

### Bonus Tolerance (The Power of MMC)
When MMC (Ⓜ) is applied to a position tolerance, the tolerance zone is allowed to increase (bonus tolerance) as the feature departs from MMC towards LMC. This is because a smaller pin (or larger hole) has more clearance to shift off-center while still assembling.

**Worked Example: Bonus Tolerance Calculation**
*   **Design Callout**: 
    *   Hole Diameter: Ø 10.0 ± 0.1 (Limits: 9.9 to 10.1)
    *   Position Tolerance: [ ⌖ ] | [ ⌀ 0.2 Ⓜ ] | [ A ] | [ B ] | [ C ]
*   **MMC of Hole**: 9.9 (Smallest hole = most material)
*   **Virtual Condition (VC)**: MMC - Pos. Tol. = 9.9 - 0.2 = Ø 9.7 (The worst-case theoretical boundary the mating pin must clear).

| Produced Hole Size | Departure from MMC | Stated Tolerance | Bonus Tolerance | Total Positional Tolerance Allowed |
| :--- | :--- | :--- | :--- | :--- |
| Ø 9.9 (MMC) | 0.0 | Ø 0.2 | 0.0 | **Ø 0.2** |
| Ø 10.0 | 0.1 | Ø 0.2 | +0.1 | **Ø 0.3** |
| Ø 10.1 (LMC) | 0.2 | Ø 0.2 | +0.2 | **Ø 0.4** |

*Conclusion*: If the machinist drills the hole larger (e.g., 10.1), they are rewarded with twice the positional tolerance (0.4 instead of 0.2), reducing scrap while still guaranteeing assembly.

## 6. Composite Position Tolerance

Used for patterns of features (like a bolt circle) where the location of the pattern to the datums can be loose, but the location of the features relative to each other must be tight. It uses a single position symbol with two (or more) rows.

### The Two Segments
1.  **Upper Segment (PLTZF - Pattern Locating Tolerance Zone Framework)**: Controls the location and orientation of the *entire pattern* relative to the datum reference frame.
2.  **Lower Segment (FRTZF - Feature Relating Tolerance Zone Framework)**: Controls the location and orientation of the features *relative to each other*. The lower segment tolerance must be smaller than the upper. Datums in the lower segment only control orientation, not location.

**Worked Example: Bolt Circle**
`[ ⌖ ] | [ ⌀ 1.0 Ⓜ ] | [ A ] | [ B ] | [ C ]` (Upper: Locates pattern to part edges)
`        | [ ⌀ 0.2 Ⓜ ] | [ A ]`             (Lower: Holes must be tight to each other and perpendicular to A)

This means the entire bolt circle can shift up to 1.0mm off-center relative to the part edges, but the bolts themselves will always align perfectly with the mating part because their hole-to-hole variation is held to 0.2mm.

## 7. Application in Fusion 360

Currently, Fusion 360's API support for Model-Based Definition (MBD) and programmatic drawing creation with GD&T is extremely limited. 

### API Limitations
*   You cannot programmatically place a fully formatted FCF directly onto a 2D drawing via the API.
*   3D annotations (MBD) are not fully exposed for creation via the Python API.

### Manual / Agent Workflow Strategy
1.  **Agent Role**: The AI agent should calculate the necessary tolerances based on fit constraints (e.g., calculating MMC virtual conditions for a clearance fit).
2.  **Tagging**: The agent tags the B-Rep faces with attributes defining their GD&T requirements (Datums, FCF strings).
3.  **Documentation**: The agent generates a separate markdown report or JSON file mapping specific feature IDs/names to their required GD&T callouts.
4.  **User Action**: The human engineer takes this report and uses the native Fusion 360 Drawing workspace UI to apply the FCFs and datum identifiers manually.

## 8. Common Applications (Recipes)

*   **Shaft/Hole Clearance Fits**: Use Position with MMC (Ⓜ). 
    *   *Hole*: `[ ⌖ ] | [ ⌀ X.X Ⓜ ] | [ A ] | [ B ] | [ C ]`
    *   *Shaft*: `[ ⌖ ] | [ ⌀ X.X Ⓜ ] | [ A ] | [ B ] | [ C ]`
*   **Primary Mating Surfaces**: Use Flatness to ensure a good seal or stable base.
    *   `[ ▱ ] | [ 0.05 ]` (No datums)
*   **Precision Mounting Bores**: Use Perpendicularity to ensure pins or bolts don't bind.
    *   `[ ⟂ ] | [ ⌀ 0.02 ] | [ A ]` (Where A is the mounting face)
*   **Complex Castings/Forgings**: Use Profile of a Surface to lock down the entire raw geometry relative to datums.
    *   `[ ⌓ ] | [ 1.5 ] | [ A ] | [ B ] | [ C ]`
*   **High-Speed Rotating Shafts**: Use Total Runout on bearing journals relative to the axis established by the bearing centers.
    *   `[ ⌰ ] | [ 0.01 ] | [ A-B ]` (Where A and B are the bearing journals)

## 9. GD&T Quick Reference Table

| Symbol | Name | Type | Datums Allowed? | Tolerance Zone Shape | Typical Use |
| :---: | :--- | :--- | :---: | :--- | :--- |
| ▱ | Flatness | Form | No | 2 Parallel Planes | Mating surfaces |
| — | Straightness | Form | No | 2 Parallel Lines/Cylinder | Shafts, rails |
| ○ | Circularity | Form | No | 2 Concentric Circles | Journals, bores |
| ⌭ | Cylindricity | Form | No | 2 Concentric Cylinders | Hydraulic cylinders |
| ⟂ | Perpendicularity| Orientation| Yes | 2 Planes/Cylinder | Mounting holes |
| ∥ | Parallelism | Orientation| Yes | 2 Planes/Cylinder | Guide blocks |
| ∠ | Angularity | Orientation| Yes | 2 Planes/Cylinder | Tapered features |
| ⌖ | Position | Location | Yes | Cylinder/2 Planes | Hole patterns |
| ◎ | Concentricity | Location | Yes | Cylinder | Coaxiality (deprecated) |
| ⌯ | Symmetry | Location | Yes | 2 Parallel Planes | Center planes (deprecated)|
| ⌒ | Profile of a Line| Profile | Optional| 2 Uniform Boundaries (2D)| Extrusions |
| ⌓ | Profile of Surface| Profile | Optional| 2 Uniform Boundaries (3D)| Castings, molds |
| ↗ | Circular Runout | Runout | Yes | 2 Concentric Circles | Spinning shafts |
| ⌰ | Total Runout | Runout | Yes | 2 Concentric Cylinders | High speed spindles |

## 10. Common Mistakes

1.  **Wrong Datum Order**: Datums denote functional assembly order, NOT alphabetical order. `| A | B | C |` is entirely different from `| B | C | A |`. The primary datum restricts the most degrees of freedom.
2.  **Missing Material Condition Modifiers**: Failing to specify MMC on clearance holes leaves bonus tolerance on the table, driving up manufacturing costs unnecessarily because machinists are held strictly to RFS.
3.  **Position Without Datums**: Position locates a feature. It *must* be located relative to something. A position FCF without datums is invalid.
4.  **Using Concentricity Instead of Position/Runout**: Concentricity is notoriously difficult to inspect (it requires deriving median points). In 99% of cases, Position or Runout is what you actually want. ASME Y14.5-2018 completely removed Concentricity for this reason.
5.  **Over-Tolerancing (Tolerance Stacking)**: Applying tight profile tolerances to non-critical surfaces, or defining redundant dimensional tolerances alongside comprehensive GD&T. If a surface is controlled by a profile, you don't need basic ± dimensions controlling the same feature.
6.  **Square Tolerance Zones for Holes**: Using coordinate dimensions (e.g., X=10±0.1, Y=10±0.1) for holes instead of positional GD&T (`[ ⌖ ] | [ ⌀ 0.28 ]`). The square zone allows a diagonal error of ~0.14, rejecting perfectly functional holes that fall in the corners of the equivalent cylindrical zone.

---
name: fusion360-drafting
description: Engineering drawing creation for Fusion 360 via MCP. Covers drawing creation, view types (base, projected, section, detail, auxiliary, isometric), dimensioning, annotations, surface finish symbols, title blocks, BOM tables, and balloon annotations. Follows ASME Y14.100 and ISO 128 standards.
---

# Fusion 360 MCP Skill: Engineering Drawings / Drafting (fusion360-drafting)

This skill provides patterns for generating and managing engineering drawings in Fusion 360 via the MCP interface.

> [!WARNING]
> **CRITICAL API LIMITATION:** The Fusion 360 API for the Drawing workspace (`adsk.drawing`) is **heavily restricted** compared to the Design workspace. Currently, the API primarily supports creating a drawing from a design, creating base/projected views, and adding basic annotations. Many advanced features (section views, detail views, dimensions, BOMs, balloons) **cannot be fully automated via Python API** in the current Fusion 360 release and require manual intervention or UI workarounds. This guide covers what is automatable and provides best-practice manual workflows for the rest.

## 1. Drawing Creation

Creates a new drawing document from the active 3D design, specifying the standard, paper size, and drawing template if applicable.

```python
import adsk.core, adsk.fusion, adsk.drawing, traceback

def create_drawing(app, design):
    try:
        # Get active document
        doc = app.activeDocument
        if doc.dataFile is None:
            return "ERROR: Design must be saved before creating a drawing."
        
        # Access the export manager or drawing creation API
        drawingManager = design.drawingManager # Note: drawing API differs
        
        # Note: True automated drawing creation is often done via creating a new document
        # from a template or using Drawing document type.
        
        # The correct way to create a drawing via API from an existing design:
        drawingDoc = app.documents.add(adsk.core.DocumentTypes.DrawingDocumentType)
        drawing = drawingDoc.drawing
        
        # Alternatively, creating a drawing from a component:
        # As of recent API updates, adsk.drawing provides some access.
        
        print("Drawing document created successfully.")
        return drawingDoc
        
    except:
        return f"ERROR:\n{traceback.format_exc()}"
```
*Note: Due to API limits, creating a fully linked drawing from a specific component with a specific template via pure Python is notoriously difficult. Often, the best approach is to prompt the user to use the UI (`File -> New Drawing -> From Design`).*

## 2. View Types

The API allows placing Base Views and Projected Views. Other view types (Section, Detail, Auxiliary, Break) generally require manual creation.

### Base and Projected Views (Automatable)

```python
import adsk.core, adsk.fusion, adsk.drawing, traceback

def place_base_and_projected_views(app):
    try:
        doc = app.activeDocument
        if doc.documentType != adsk.core.DocumentTypes.DrawingDocumentType:
            return "ERROR: Active document is not a drawing."
            
        drawing = doc.drawing
        sheet = drawing.sheets.item(0)
        
        # Note: Placing views programmatically requires specific API versions and is limited.
        # This is a conceptual pattern for supported APIs.
        
        # In reality, the Fusion Drawing API currently does NOT allow programmatic 
        # creation of drawing views from scratch via Python. 
        # (It allows reading existing views, but not creating them).
        
        return "Drawing View creation is currently NOT SUPPORTED via Python API. Must be done manually."
        
    except:
        return f"ERROR:\n{traceback.format_exc()}"
```

### Manual Workflow Guidance for Views
Since view generation is heavily restricted in the API:
- **Base View**: Select the primary face that shows the most characteristic contour. Choose First Angle (ISO) or Third Angle (ASME) projection in Document Settings.
- **Projected Views**: Generate Top and Right (or Left) views from the base view.
- **Section View**: Use for internal features (Full, Half, Offset, Aligned).
- **Detail View**: Use for tight areas where dimensions would be cluttered.
- **Auxiliary View**: Use for features on inclined planes to show true shape and size.
- **Isometric View**: Place in the top right corner for reference, usually shaded.

## 3. Dimensioning

**API Status:** Reading dimensions is sometimes possible; creating dimensions via API is generally **not supported**.

### Manual Dimensioning Best Practices
- **Linear/Angular**: Place off the view where possible. Avoid crossing dimension lines.
- **Diameter/Radial**: Use diameter for full circles (holes), radial for arcs (fillets/rounds).
- **Ordinate Dimensioning**: Use for parts with many features from a single datum (e.g., CNC machined plates).
- **Hole Callouts**: Use the Hole and Thread Note tool. It automatically links to the hole feature data (e.g., `M6x1.0 - 6H \n ↧ 12`).
- **Completeness**: Ensure every feature is located (X, Y) and sized (W, H, D). Do not over-dimension (duplicate dimensions).

## 4. Annotations

**API Status:** Minimal support.

### Manual Workflow for Annotations
- **Center Marks**: Apply to all holes and circular features.
- **Centerlines**: Apply to all cylindrical features in side views.
- **Surface Finish**: Apply standard roughness values (e.g., Ra 3.2, Ra 0.8) to mating surfaces.
- **Weld Symbols**: Use standard AWS/ISO symbols pointing to the joint line.
- **General Notes**: Place in the bottom left or above the title block. (e.g., "1. ALL DIMENSIONS IN MM. 2. REMOVE ALL BURRS AND SHARP EDGES.")

## 5. Title Block

**API Status:** The API allows reading and sometimes updating title block attributes if they are defined as promptable attributes in the template.

```python
import adsk.core, adsk.fusion, adsk.drawing, traceback

def update_title_block_attributes(app, new_values_dict):
    try:
        doc = app.activeDocument
        if doc.documentType != adsk.core.DocumentTypes.DrawingDocumentType:
            return "ERROR: Active document is not a drawing."
            
        drawing = doc.drawing
        sheet = drawing.sheets.item(0)
        title_block = sheet.titleBlocks.item(0)
        
        # Iterate through attributes and update matching keys
        updated_count = 0
        if title_block and title_block.attributes:
            for attr in title_block.attributes:
                if attr.name in new_values_dict:
                    attr.value = new_values_dict[attr.name]
                    updated_count += 1
                    
        return f"SUCCESS: Updated {updated_count} title block attributes."
        
    except:
        return f"ERROR:\n{traceback.format_exc()}"
```

### Standard Fields
- Part Name / Description
- Part Number
- Material
- Mass
- Revision
- Scale
- General Tolerances (e.g., X.X ±0.1, X.XX ±0.05)
- Drawn By / Date

## 6. BOM & Balloons

**API Status:** Reading parts lists is sometimes supported; creating them is manual.

### Manual Workflow
- **Parts List (BOM)**: Place on the first sheet, usually anchored to the title block or top right corner. Ensure columns match company standards (Item, Qty, Part Number, Description, Material).
- **Balloons**: Auto-balloon the assembly view. Re-arrange balloons for neatness (align to magnetic lines). Ensure every item in the BOM is ballooned at least once.

## 7. Sheet Management

**API Status:** You can read sheets, but adding sheets with specific templates via API is limited.

```python
import adsk.core, adsk.fusion, adsk.drawing, traceback

def list_drawing_sheets(app):
    try:
        doc = app.activeDocument
        if doc.documentType != adsk.core.DocumentTypes.DrawingDocumentType:
            return "ERROR: Active document is not a drawing."
            
        drawing = doc.drawing
        output = []
        for i in range(drawing.sheets.count):
            sheet = drawing.sheets.item(i)
            output.append(f"Sheet {i+1}: {sheet.name}")
            
        return "\n".join(output)
    except:
        return f"ERROR:\n{traceback.format_exc()}"
```

## 8. Standards Compliance

- **ASME Y14.100**: Standard for US engineering drawing practices. Typically uses Third-Angle Projection. Dimensions usually in Inches (or explicitly noted mm).
- **ISO 128**: International standard. Typically uses First-Angle Projection. Dimensions usually in millimeters.
- **Projection Symbol**: The title block MUST contain the projection angle cone symbol to avoid manufacturing errors.

## 9. API Limitations Summary

- **What CAN be done via API**: Read active drawing, read sheets, read/write predefined title block attributes.
- **What CANNOT be done via API**: Create views (base, projected, section, detail), create dimensions, create BOMs, create balloons, generate PDF exports programmatically (without UI dialogs in some versions).
- **Agent Strategy**: The AI Agent should construct the 3D model perfectly with all metadata (Part Numbers, Materials) so that when the user manually generates the drawing, the BOM and Title Block auto-populate correctly. The Agent can also update title block attributes via API if the drawing is open.

## 10. Quality Gate Checklist

Before considering a drawing complete (manual or automated checks):
1. **Views**: Are all necessary views present to fully define the part?
2. **Dimensions**: Is the part fully dimensioned? (No missing dimensions, no over-dimensioning).
3. **Tolerances**: Are critical fits toleranced? Are general tolerances specified?
4. **Annotations**: Are all holes called out? Center marks present?
5. **Title Block**: Is the title block completely filled out (Material, Mass, Rev, Name)?
6. **BOM**: For assemblies, is the BOM present and every item ballooned?
7. **Scale**: Is the scale appropriate and accurately stated in the title block?

## 11. Common Failures

| Failure Mode | Cause | Resolution |
| :--- | :--- | :--- |
| **API Error on View Creation** | Fusion 360 API does not support view creation | Use manual UI workflow. |
| **Missing Dimensions** | Feature not located or sized | Methodically check X, Y, and Size for every feature from daums. |
| **Over-dimensioning** | Duplicate dimensions or closed loops | Remove redundant dimensions. Use reference dimensions `(XX)` if needed. |
| **Wrong Projection Angle** | Default settings mismatch standard | Check Document Settings -> standard (ISO/ASME) and projection angle. |
| **Broken View References** | 3D model updated, drawing not updated | Open drawing and click "Update" chain icon in the toolbar. |
| **Empty BOM Fields** | Model components lack properties | Fill out properties (Part Number, Description, Material) in the 3D Design workspace before making drawing. |

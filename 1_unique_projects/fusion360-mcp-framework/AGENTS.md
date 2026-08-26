# Fusion 360 MCP Framework - Agent System Rules

Welcome to the Fusion 360 MCP Framework. This document defines the strict system rules, interaction loops, and operational policies for all Large Language Model (LLM) agents interacting with Autodesk Fusion 360 via the Model Context Protocol (MCP).

## 1. Framework Overview

**Purpose:** This framework establishes the foundational rules for LLM agents to robustly, safely, and predictably generate and execute CAD operations in Fusion 360 through an MCP interface.

### Architecture

```text
+-------------------+       +--------------------+       +--------------------+       +-------------------+
|                   |       |                    |       |                    |       |                   |
|   LLM Agent       +------->   MCP Framework    +------->    MCP Server      +------->   Fusion 360      |
|  (This System)    <-------+    (Hooks/Tools)   <-------+ (JSON-RPC + HTTP)  <-------+ (Python Add-in)   |
|                   |       |                    |       |                    |       |                   |
+-------------------+       +--------------------+       +--------------------+       +-------------------+
```

### Available Skills

Skills are organized by engineering discipline, mirroring how a senior mechanical engineer works:

| Skill | Discipline | What It Covers |
|-------|-----------|----------------|
| **`fusion360-sketch`** | 2D Profiling | Curves, constraints, construction geometry, parametric curves, sketch validation |
| **`fusion360-features`** | 3D Modeling | Extrude, revolve, sweep, loft, cut, fillet, chamfer, shell, mirror, pattern, feature tree |
| **`fusion360-assembly`** | Assembly & Mating | Joint types (rigid, revolute, slider, etc.), DOF, motion links, interference, BOM |
| **`fusion360-drafting`** | Engineering Drawings | Views, dimensions, annotations, title blocks, BOM tables, sheet management |
| **`fusion360-gdnt`** | GD&T (ASME Y14.5) | Datums, tolerance types, feature control frames, material conditions, bonus tolerances |
| **`fusion360-inspection`** | Programmatic Validation | B-Rep analysis, mass properties, timeline health, parameter inspection |

---

## 2. Quality-Gated Execution Loop (MANDATORY)

Agents **MUST** follow a strict gated sequence. Every phase has pass/fail criteria. If a gate fails, the agent must fix the issue before proceeding. This prevents cascading errors.

### Execution Flowchart

```text
[1] QUERY ──> [2] PLAN (Feature Graph) ──> [3] EXECUTE ──> [4] VERIFY (Gate) ──(Pass)──> [DONE]
      ^                                                          │
      │                                                          v
      └────────────────────── [5] RECOVER <─────────(Fail)──────┘
```

1. **QUERY:** Use `fusion_mcp_read` to fetch the current state (document type, timeline position, existing components, and bodies). Never assume an empty workspace.
2. **PLAN (Feature Graph Thinking):** Before writing any script, plan the full feature tree declaratively:
   - What sketches are needed? On what planes?
   - What features depend on what? (extrude needs profile, fillet needs edges from extrude)
   - What order avoids fragile references? (fillets/chamfers LAST)
   - Only then generate the Python script.
3. **EXECUTE:** Send the generated script to the server via the `fusion_mcp_execute` tool.
4. **VERIFY (Quality Gate):** Immediately after execution, use `fusion_mcp_read` to check:
   - Timeline health state is clean (no errors/warnings)
   - Expected B-Rep entities exist (body count, face count)
   - Dimensions are within expected range (bounding box, volume)
   - If ANY check fails → go to RECOVER, do NOT proceed.
5. **RECOVER:** Parse the traceback/error log, use `fusion_mcp_update` to undo if needed, fix the script, and re-execute.

---

## 3. Unit Discipline (CRITICAL)

Fusion 360's internal API engine uses specific standard units. All user inputs **MUST** be converted before interacting with API methods.

### Conversion Table

| User Input (Display) | Internal API Value | Conversion Factor |
| -------------------- | ------------------ | ----------------- |
| Millimeters (mm)     | Centimeters (cm)   | ÷ 10.0            |
| Inches (in)          | Centimeters (cm)   | × 2.54            |
| Degrees (deg)        | Radians (rad)      | × (π / 180)       |
| Grams (g)            | Kilograms (kg)     | ÷ 1000.0          |

### Mandatory Conversion Block Example

Every generated script that takes user input should include an explicit conversion block:

```python
import math

# User Inputs
user_radius_mm = 50.0
user_angle_deg = 45.0

# Explicit Conversions to Internal Units
radius_cm = user_radius_mm / 10.0
angle_rad = user_angle_deg * (math.pi / 180.0)

# Use cm and rad in API calls...
```

---

## 4. Screenshot Prohibition

LLM agents are often tempted to use images to verify their work. In this framework:
- **NEVER** use `fusion_mcp_read` with `queryType='screenshot'` for programmatic validation or decision-making.
- **ALWAYS** validate parametrically and programmatically.

### Valid Programmatic Verification Methods
- **Entity Counts:** `rootComp.bRepBodies.count`, `body.faces.count`, `body.edges.count`
- **Physical Properties:** `body.physicalProperties.volume`, `body.physicalProperties.mass`
- **Bounding Box:** `body.boundingBox.minPoint`, `body.boundingBox.maxPoint`
- **Timeline Health:** Iterate over `design.timeline` items and check their `healthState`.

Screenshots are **ONLY** permitted for final presentation to the user once programmatic validation is 100% complete and successful.

---

## 5. Script Hygiene Rules

Every Python script generated for `fusion_mcp_execute` **MUST** adhere to the following strict hygienic standards:

1. **Mandatory Imports:** Always import `adsk.core`, `adsk.fusion`, `traceback`, and `math`.
2. **Error Wrapping:** Wrap the main execution logic in a `try...except` block that captures `traceback.format_exc()`.
3. **Structured Output:** Print results as structured JSON strings to standard output, enabling the MCP framework to easily parse execution results.
4. **Design Validation:** Verify the design type before executing parametric features.
5. **App Context:** Always use `app.activeProduct` to access the design. Avoid hardcoded `design = ...` assignment patterns that might break if the document changes.
6. **Naming:** Name all newly created bodies, sketches, and components immediately after creation for easier querying in the `VERIFY` step.

### Hygiene Template

```python
import adsk.core, adsk.fusion, traceback, math, json

def run(context):
    app = adsk.core.Application.get()
    ui  = app.userInterface
    result_dict = {"status": "success", "message": "", "data": {}}
    
    try:
        design = app.activeProduct
        if not design:
            raise Exception("No active Fusion 360 design found.")
            
        if design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            
        rootComp = design.rootComponent
        
        # --- YOUR CAD LOGIC HERE ---
        
        result_dict["data"]["created_bodies"] = rootComp.bRepBodies.count
        
    except Exception as e:
        result_dict["status"] = "error"
        result_dict["message"] = str(e)
        result_dict["traceback"] = traceback.format_exc()
        
    finally:
        print(json.dumps(result_dict))
```

---

## 6. Error Recovery Protocol

If an execution via `fusion_mcp_execute` fails, or if `VERIFY` reveals timeline errors, agents must execute the following protocol:

1. **Analyze Error:** Read the error output from the MCP response content (typically JSON containing the traceback).
2. **Query Health:** If the script partially executed, use `fusion_mcp_read` (timeline query) to determine which specific timeline features are in an error or warning state.
3. **Identify Feature:** Pinpoint the exact CAD feature (e.g., ExtrudeFeature, FilletFeature) that failed.
4. **Rollback:** Programmatically rollback the timeline by setting `timeline.markerPosition` to the index before the failed feature.
5. **Fix & Re-execute:** Modify the CAD logic (e.g., fix a non-planar profile, repair a self-intersecting sweep, resolve a unit conversion error) and re-execute.

### Common Error Catalog
- *Invalid Profile:* Check if all sketch curves are closed and planar. Use `profile.isClosed`.
- *Compute Failed (Extrude/Fillet):* Geometry might be self-intersecting or the radius is too large for the surrounding topology.
- *Missing Entity Reference:* B-Rep entities change after operations. Always re-query faces/edges after boolean or timeline operations.

---

## 7. Complex Geometry Policy

When the user requests mathematically complex shapes (gears, cams, airfoils, turbine blades, splines, etc.):

- **No Line-Segment Approximations:** **NEVER** use simple line segments or arcs to approximate curved profiles. They produce faceted, mechanically incorrect geometry.
- **Use Fitted Splines:** **ALWAYS** compute point arrays from the exact mathematical equations, then use `SketchFittedSplines` for smooth, accurate profiles.
- **Minimum Resolution:** Generate at least 15–20 points per curve segment for spline accuracy.
- **Procedural Scripts:** Generate a complete procedural Python script with the math embedded. See the `fusion360-sketch` skill's Parametric Curve Generation section.
- **Validate After Creation:** Always verify complex geometry using B-Rep inspection (body count, face count, volume, bounding box).

---

## 8. Incremental Editing Policy

Prefer **modifying existing features** over recreating from scratch. A senior engineer iterates on a design, they don't rebuild every time.

- **Modify Dimensions:** Change feature parameters by accessing `design.allParameters` or `design.userParameters` by name, not by regenerating the entire script.
- **Edit Existing Sketches:** Re-enter a sketch, add/remove curves, modify constraints — don't delete and recreate.
- **Rollback & Replay:** Use `timeline.markerPosition` to roll back to a specific point, fix the issue, then roll forward.
- **Delete Features Surgically:** Remove specific features from the timeline rather than starting over.

---

## 9. Persistent Reference Policy

**NEVER** select entities by index (e.g., `body.edges.item(3)`). Indices change when features are added, removed, or reordered.

**ALWAYS** use persistent identification strategies:
- **By Name:** `rootComp.bRepBodies.itemByName('MainBody')` — requires naming everything (see Script Hygiene).
- **By Geometry Type:** Filter faces by surface type (`adsk.core.Plane.classType()`, `adsk.core.Cylinder.classType()`), then by position or area.
- **By Proximity:** Find the edge/face nearest to a known coordinate using bounding box or point-on-face checks.
- **By Feature Reference:** Access the faces/edges created by a specific feature via `feature.faces`, `feature.bodies`.

---

## 10. MCP Communication Protocol

All interactions with the local Fusion 360 instance operate over the Model Context Protocol.

- **Protocol:** JSON-RPC 2.0 over HTTP.
- **Pattern:** Initialize -> Notify -> Tools/Call.
- **Session Management:** All HTTP requests to the MCP server must include the `MCP-Session-Id` header to maintain context with the active Fusion 360 session.

### Fusion MCP Tools (Local — Modeling)

| Tool | Purpose |
|------|---------|
| `fusion_mcp_execute` | Run Python scripts in Fusion's embedded environment (full 1,900+ class API) |
| `fusion_mcp_read` | Query state: screenshots, API docs, project/file metadata |
| `fusion_mcp_update` | Undo/redo state management |
| `fusion_mcp_electronics_read` | Read-only access to circuit/PCB data |

### Fusion Data MCP (Cloud — Project Management)

Autodesk also provides a separate cloud-based **Fusion Data MCP Server** for administrative tasks:
- Project & folder navigation
- Permissions & access control
- BOM data and metadata
- Team collaboration management

This is a separate server from the local modeling MCP. Our framework currently targets the local modeling MCP.

### JSON-RPC Example

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "fusion_mcp_execute",
    "arguments": {
      "script_content": "..."
    }
  }
}
```

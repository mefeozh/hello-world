# 🏆 Category 3: Flagship Mechanical Engineering Design Projects

This directory contains comprehensive machine element systems, aerospace transmission gearboxes, fatigue analysis engines, hydrodynamic lubrication solvers, and industrial hydraulic network optimizers.

---

## 📂 Projects

### 1. [`helicopter-gearbox-design/`](./helicopter-gearbox-design)
- **System:** 620 kW Twin-Engine Helicopter Reduction Gearbox ($6400 \rightarrow 1280\text{ RPM}$, exact ratio 5.0).
- **Standards & Equations:**
  - Helical Stage: AGMA 2101-D04 bending stress ($\sigma_F$) & pitting resistance ($\sigma_H$) with dynamic factors ($K_v$) and geometry factors ($I, J$).
  - Spiral Bevel Stage: AGMA 2003-B97 cone geometry, mean pitch diameter, and crowning factors ($K_{mb}$).
  - Shaft & Bearings: DE-Goodman fatigue under rotating bending + mean torsion; ISO 281 & Weibull bearing rating life ($L_{10h}$).

### 2. [`jaw-crusher-machine-design/`](./jaw-crusher-machine-design)
- **System:** 10 kN Single-Toggle Jaw Crusher Mechanism.
- **Standards & Equations:**
  - Kinematics: 2D multi-link planar mechanism kinematics and toggle force equilibrium.
  - Belt Drive: Euler-Eytelwein friction model ($F_1/F_2 = e^{f\alpha}$) and wrap-angle geometry.
  - Shaft Sizing: Soderberg fatigue criterion with Marin surface/size/reliability modifiers and notch sensitivity ($K_f, K_{fs}$).
  - Pins & Welds: MSST pin sizing (`fsolve`), ISO 286 $H7/f7$ tolerance selection, and Modified Goodman bracket fillet weld sizing.

### 3. [`hydrodynamic-journal-bearing/`](./hydrodynamic-journal-bearing)
- **System:** Centrally Grooved Hydrodynamic Journal Bearing.
- **Standards & Equations:**
  - Hydrodynamics: Short Bearing (Ocvirk) Approximation for Sommerfeld Number ($S$) and eccentricity ratio ($\epsilon$).
  - Thermal Equilibrium: Iterative heat balance with temperature-dependent viscosity (SAE 30 exponential model) and pressurized axial leakage ($Q$).
  - Optimization: Constrained by Trumpler's design criteria ($h_0 \ge h_{0,\min}$, $T_{\max} \le 120^\circ\text{C}$, $P_{st} \le 2068\text{ kPa}$) mapped to ISO 286 basic hole fits ($H7/f7, H8/e8$), and loss-of-lubrication failure mode.

### 4. [`marine-pipeline-hydraulics/`](./marine-pipeline-hydraulics)
- **System:** Industrial Marine Intake and Outfall Pipeline Network ($50,000\text{ m}^3/\text{h}$).
- **Standards & Equations:**
  - Survey Ingestion: Civil 3D LandXML terrain parsing with Ramer-Douglas-Peucker (RDP) polyline simplification.
  - Friction Solver: Darcy-Weisbach friction factor solved via Colebrook-White equation (Brent's method).
  - Biofouling Evaluation: Brand New ($k = 1.5\ \mu\text{m}$) vs. 10-Year Biofouling ($k = 1.5\text{ mm}$).
  - Grade Lines: Energy Grade Line (EGL), Hydraulic Grade Line (HGL), pump head, and cavitation / NPSH verification.

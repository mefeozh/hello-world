# ⚙️ Category 2: General Mechanical Engineering Projects

This directory contains foundational computational mechanics, numerical algorithms, kinematic mechanisms, vibration damping models, and manufacturing plasticity solvers.

---

## 📂 Projects

### 1. [`me310-numerical-methods/`](./me310-numerical-methods)
- **01. Interpolation & Splines:** Lagrange, Newton divided differences (Horner's rule), Quadratic/Natural Cubic splines ($C^1/C^2$ continuity), Bernstein-Bézier curves.
- **02. Hybrid Root Finders:** Illinois Regula-Falsi / Bisection hybrid solver and 2D zero-contour tracker.
- **03. Linear Solvers & FLOP Benchmarks:** Tridiagonal Matrix Algorithm (TDMA / Thomas), Jacobi, Gauss-Seidel with SOR, and exact software FLOP counter benchmarks.
- **04. Lunar Rover Sensor Fusion:** Complementary filtering, zero-phase forward-backward smoothing, and bounded least-squares Coulomb/viscous friction identification ($F = a \operatorname{sgn}(v) + b v$).
- **05. Transient Heat PDE Solvers:** 1D heat diffusion equation with central differences and explicit time steppers (RK2, RK3, RK4, Adams-Bashforth).

### 2. [`me301-mechanism-dynamics/`](./me301-mechanism-dynamics)
- **Kinematics & Dynamics:** 4-bar linkage and slider-crank vector loop closures, Freudenstein analytical solution, and D'Alembert inverse dynamics ($0^\circ-360^\circ$ joint reaction and driving torque curves).

### 3. [`me302-vibrations-viv/`](./me302-vibrations-viv)
- **Vibration Modeling:** Cantilever wind turbine mast SDOF model, vortex-induced vibration (VIV) harmonic forcing, frequency response spectrum, and resonant peak minimization.

### 4. [`me303-sheet-metal-plasticity/`](./me303-sheet-metal-plasticity)
- **Forming Mechanics:** Sheet metal V-die bending, plastic deformation radius, springback ratio ($R_b/R_f = 1 - 3k + 4k^3$), and punch tonnage sizing.

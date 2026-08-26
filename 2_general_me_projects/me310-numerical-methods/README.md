# 🔢 ME 310: Numerical Methods in Mechanical Engineering Suite

**Author:** Mehmet Efe Özhan (METU Mechanical Engineering)

---

## 📂 Sub-Modules

1. **`01_interpolation_splines_bezier/`**: Lagrange polynomials, Newton's divided difference evaluation (Horner's rule), Quadratic/Natural Cubic splines with tridiagonal second derivative solvers ($M_i$), and Cubic Bézier curves via de Casteljau algorithm.
2. **`02_hybrid_root_finders/`**: Robust hybrid root finder combining Illinois Regula-Falsi with Bisection and 2D zero-contour solvers.
3. **`03_linear_solvers_tdma_flops/`**: Direct TDMA (Thomas algorithm, $O(n)$) vs. Iterative Jacobi and Gauss-Seidel with Successive Over-Relaxation (SOR) with exact software FLOP counter instrumentation.
4. **`04_lunar_rover_sensor_fusion/`**: Complementary filter state estimator, zero-phase forward-backward smoothing (`scipy.signal.filtfilt`), and bounded least-squares Coulomb/viscous friction parameter identification.
5. **`05_transient_pde_rk_integrators/`**: 1D transient heat diffusion PDE finite difference solver coupled with explicit multi-stage Runge-Kutta (RK2/3/4) and Adams-Bashforth integrators.

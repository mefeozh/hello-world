# 📳 ME 302: Structural Vibrations & Vortex-Induced Resonance

**Author:** Mehmet Efe Özhan (METU Mechanical Engineering)

---

## 📌 Technical Summary

Models steady-state harmonic response and fluid-structure interaction for wind turbine masts:
- SDOF cantilever mast model ($k_{\text{eq}} = 3EI/L^3$).
- Vortex-Induced Vibration (VIV) quadratic velocity forcing ($F_0 \propto \rho D^3 L \omega^2$).
- Resonant peak damping optimization via bounded scalar search (`scipy.optimize.minimize_scalar`).

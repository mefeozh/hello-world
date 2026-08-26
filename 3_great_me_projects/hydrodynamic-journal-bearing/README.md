# 🛢️ Hydrodynamic Journal Bearing Thermal-Fluid Optimizer

**Author:** Mehmet Efe Özhan (METU Mechanical Engineering)  
**Methodology:** Ocvirk Short Bearing Approximation, Trumpler Design Criteria, ISO 286 Fits

---

## 📌 Technical Summary

This project models and optimizes a **centrally grooved hydrodynamic journal bearing** running SAE 30 lubricant under steady-state operating conditions. It solves the non-linear coupling between fluid-film eccentricity, frictional heat generation, viscosity decay, and forced axial coolant leakage flow.

---

## 📐 Mathematical Formulation

### 1. Hydrodynamic Lubrication (Ocvirk Short Bearing Theory)
- **Sommerfeld Number ($S$):**
  $$S = \left(\frac{R}{c}\right)^2 \frac{\mu N}{P_{\text{unit}}}$$
- **Eccentricity Ratio ($\epsilon$):**
  $$S = \frac{(1 - \epsilon^2)^2}{\pi (L/D)^2 \sqrt{16 \epsilon^2 + \pi^2 (1 - \epsilon^2)}}$$

### 2. Thermal Equilibrium Loop
- **Temperature-Dependent Viscosity (SAE 30):**
  $$\mu(T) = \mu_0 e^{-b (T - T_0)}$$
- **Frictional Heat Generation:**
  $$H_{\text{total}} = 2 \left( f W_{\text{half}} R \omega \right), \quad f = \frac{2 \pi^2 S}{\sqrt{1 - \epsilon^2}} \left(\frac{c}{R}\right)$$
- **Pressurized Lubricant Flow Rate ($Q$):**
  $$Q = \frac{\pi P_s R c^3 (1 + 1.5 \epsilon^2)}{3 \mu L}$$
- **Temperature Rise:**
  $$\Delta T = \frac{H_{\text{total}}}{\rho c_p Q}, \quad T_{\text{ave}} = T_{\text{in}} + \frac{\Delta T}{2}$$

### 3. Trumpler's Design Criteria
- Minimum film thickness: $h_0 = c(1 - \epsilon) \ge 5.08\,\mu\text{m} + 0.04 D$
- Maximum temperature: $T_{\max} = T_{\text{in}} + \Delta T \le 120^\circ\text{C}$
- Starting unit load: $P_{st} \le 2068\text{ kPa}$

---

## 💻 Usage

```bash
python journal_bearing_solver.py
```
Output includes converged thermal operating parameters, ISO 286 tolerance class mapping ($H7/f7$, $H8/e8$), and loss-of-lube failure mode checks.

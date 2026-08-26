# 🚁 Aerospace Helicopter Reduction Gearbox Design & AGMA Stress Analysis System

**Author:** Mehmet Efe Özhan (METU Mechanical Engineering)  
**Primary References:** AGMA 2101-D04, AGMA 2003-B97, ISO 281, Shigley's Mechanical Engineering Design

---

## 📌 System Specifications

This system models and optimizes a **620 kW twin-engine helicopter main reduction gearbox** transmitting power from two high-speed turbine input shafts to a vertical rotor drive.

- **Total Input Power ($P_{\text{input}}$):** $620\text{ kW}$ ($2 \times 310\text{ kW}$ dual turbine inputs)
- **Input Shaft Speed ($N_1$):** $6400\text{ RPM}$ (Helical pinion)
- **Target Output Shaft Speed ($N_3$):** $1280\text{ RPM}$ (Bevel gear)
- **Total Speed Reduction Ratio ($u_{\text{total}}$):** $5.0$ (Exact)
- **Helical Stage Ratio ($u_h$):** $1.90 - 2.10$
- **Bevel Stage Ratio ($u_b$):** $2.40 - 2.60$
- **Design Load Life ($N_{\text{cycles}}$):** $3 \times 10^8\text{ cycles}$ at $96\%$ reliability
- **Bending Safety Factor ($S_F$):** $\ge 1.40$
- **Contact/Pitting Safety Factor ($S_H$):** $\ge \sqrt{1.40} \approx 1.183$
- **AGMA Quality Number ($Q_v$):** $9$ (Precision ground aerospace gearing)

---

## 📐 Mathematical Formulation

### 1. Helical Gear Stage (AGMA 2101-D04)
- **Bending Stress ($\sigma_F$):**
  $$\sigma_F = \frac{F_t}{b \cdot m_n} \cdot K_o \cdot K_v \cdot K_s \cdot K_H \cdot K_B \cdot \frac{1}{Y_J} \le \frac{S_t \cdot Y_N}{S_F \cdot Y_\theta \cdot Y_Z}$$
- **Contact Stress / Pitting Resistance ($\sigma_H$):**
  $$\sigma_H = Z_E \sqrt{\frac{F_t}{b \cdot d_1} \cdot K_o \cdot K_v \cdot K_s \cdot K_H \cdot K_B \cdot \frac{1}{Z_I}} \le \frac{S_c \cdot Z_N \cdot Z_W}{S_H \cdot Y_\theta \cdot Y_Z}$$
- **Dynamic Factor ($K_v$):**
  $$A = 50 + 56(1 - B), \quad B = 0.25(12 - Q_v)^{2/3}, \quad K_v = \left(\frac{A + \sqrt{200 v_t}}{A}\right)^B$$

### 2. Spiral Bevel Gear Stage (AGMA 2003-B97)
- **Mean Pitch Diameter ($d_{mv}$):**
  $$d_{mv} = d_{bv} - b \sin\delta_p$$
- **Bevel Bending Stress:**
  $$\sigma_{Fb} = \frac{2 T_b}{d_{mv} \cdot b \cdot m_b} \cdot K_o \cdot K_v \cdot K_{mb} \cdot \frac{1}{Y_{Jb}}$$

### 3. Shaft Fatigue & Bearing Life
- **DE-Goodman Shaft Failure Criterion:**
  $$\frac{1}{n} = \frac{16}{\pi d^3} \left[ \frac{\sqrt{4(K_f M_a)^2 + 3(K_{fs} T_a)^2}}{S_e} + \frac{\sqrt{4(K_f M_m)^2 + 3(K_{fs} T_m)^2}}{S_{ut}} \right]$$
- **Rolling Element Bearing Life (ISO 281):**
  $$L_{10h} = \frac{10^6}{60 N} \left( \frac{C}{P_{\text{eq}}} \right)^p \ge 3500\text{ hours}$$

---

## 💻 Usage

Run the optimization and AGMA stress report:
```bash
python Gear_Design.py
```
Parameters and stress factors can be overridden dynamically using the `MANUAL_OVERRIDES` dictionary in `Gear_Design.py`.

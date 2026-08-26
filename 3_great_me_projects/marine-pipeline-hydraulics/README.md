# 🌊 Marine Pipeline Hydraulic Analysis & GIS Bathymetric Optimization

**Author:** Mehmet Efe Özhan (METU Mechanical Engineering)  
**Primary Standards:** Darcy-Weisbach, Colebrook-White, LandXML GIS Terrain Profiles

---

## 📌 System Overview

This system evaluates and optimizes heavy-duty **marine intake and outfall cooling pipeline networks ($50,000\text{ m}^3/\text{h}$)** using 3D bathymetric terrain profiles extracted from Civil 3D LandXML files.

---

## 📐 Mathematical Formulation

### 1. GIS Bathymetric Polyline Simplification
- Uses the **Ramer-Douglas-Peucker (RDP)** algorithm and Savitzky-Golay filtering to clean raw GPS/bathymetry survey points into continuous hydraulic pipeline profiles.

### 2. Darcy-Weisbach & Colebrook-White Friction
- **Head Loss:**
  $$h_f = f \frac{L}{D} \frac{V^2}{2g}$$
- **Implicit Colebrook-White Friction Factor ($f$):**
  $$\frac{1}{\sqrt{f}} = -2 \log_{10}\left( \frac{k}{3.7 D} + \frac{2.51}{\text{Re} \sqrt{f}} \right)$$
- Solved numerically using Brent's method (`scipy.optimize.brentq`).

### 3. Operational Comparison
- **Brand New HDPE Pipeline:** Surface roughness $k = 1.5\ \mu\text{m}$
- **10-Year Marine Biofouling:** Surface roughness $k = 1.5\text{ mm}$ ($1000\times$ friction increase)

---

## 💻 Usage

```bash
python Pipeflow.py
```
Generates automated Hydraulic Grade Line (HGL), Energy Grade Line (EGL), and pump head requirement curves across intake and outfall diffusers.

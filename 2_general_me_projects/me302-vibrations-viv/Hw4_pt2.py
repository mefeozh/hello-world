import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

# --- Given System Parameters ---
F0 = 6000.0           # Excitation force amplitude (N)
omega_rpm = [800, 1100] # Operating range (rpm)
m_orig = 400.0        # Original mass (kg)
k_orig = 1000e3       # Original stiffness (N/m)
zeta_orig = 0.12      # Original damping ratio
g = 9.81              # Gravity (m/s^2)

# Convert rpm to rad/s
omega_op = [w * 2 * np.pi / 60 for w in omega_rpm]
w_min, w_max = omega_op[0], omega_op[1]

# --- Helper Functions ---
def calc_dynamics(w, m, k, zeta):
    """Calculates Transmissibility (T) and Amplitude (X) for given parameters."""
    wn = np.sqrt(k / m)
    r = w / wn
    
    # Magnification factor denominator
    den = np.sqrt((1 - r**2)**2 + (2 * zeta * r)**2)
    
    # Amplitude X
    X = (F0 / k) / den
    
    # Transmissibility T
    T = np.sqrt(1 + (2 * zeta * r)**2) / den
    
    # Transmitted Force FT
    FT = T * F0
    return T, X, FT

# Frequency array for plotting
w_vals = np.linspace(0, 250, 1000)

# ==========================================
# Part (a) & (b): Current System Analysis
# ==========================================
wn_orig = np.sqrt(k_orig / m_orig)
T_orig, X_orig, FT_orig = calc_dynamics(w_vals, m_orig, k_orig, zeta_orig)

# Check regulations at the lowest operating speed (worst-case for isolation)
T_curr, X_curr, FT_curr = calc_dynamics(w_min, m_orig, k_orig, zeta_orig)

print("--- (b) Current System Evaluation ---")
print(f"Max Amplitude at operating speed: {X_curr*1000:.2f} mm (Limit: 2.5 mm)")
print(f"Max Transmitted Force at operating speed: {FT_curr:.2f} N (Limit: 2000 N)")
print("Result: CURRENT SETUP FAILS.\n")

# ==========================================
# Part (c): Adding Concrete Mass
# ==========================================
# We need X <= 0.0025 m and FT <= 2000 N at w = 83.77 rad/s.
# We will find the mass that satisfies both and take the maximum required.

def force_diff(m):
    _, _, FT = calc_dynamics(w_min, m, k_orig, zeta_orig)
    return FT - 2000.0

def amp_diff(m):
    _, X, _ = calc_dynamics(w_min, m, k_orig, zeta_orig)
    return X - 0.0025

# Solve for mass requirements
m_req_force = fsolve(force_diff, 500)[0]
m_req_amp = fsolve(amp_diff, 500)[0]

m_new1 = max(m_req_force, m_req_amp)
mc = m_new1 - m_orig

T_new1, _, _ = calc_dynamics(w_vals, m_new1, k_orig, zeta_orig)

print("--- (c) Adding Concrete Mass Solution ---")
print(f"Required total mass: {m_new1:.2f} kg")
print(f"Smallest additional concrete mass (mc): {mc:.2f} kg")
print(f"Condition governing the mass: {'Force Transmissibility' if m_req_force > m_req_amp else 'Vibration Amplitude'}\n")

# ==========================================
# Part (d): Softer Elastomeric Mounts
# ==========================================
k_new = 150e3   # N/m
zeta_new = 0.05

# Check regulations at lowest operating speed
T_new2_op, X_new2_op, FT_new2_op = calc_dynamics(w_min, m_orig, k_new, zeta_new)
T_new2, _, _ = calc_dynamics(w_vals, m_orig, k_new, zeta_new)

print("--- (d) Softer Elastomeric Mounts Solution ---")
print(f"Max Amplitude: {X_new2_op*1000:.2f} mm (Limit: 2.5 mm)")
print(f"Max Transmitted Force: {FT_new2_op:.2f} N (Limit: 2000 N)")
print("Result: NEW MOUNTS PASS.\n")

# ==========================================
# Part (e): Trade-offs (Static Deflection & Resonance)
# ==========================================
delta_st1 = (m_new1 * g) / k_orig
delta_st2 = (m_orig * g) / k_new

# Resonance amplitudes (approximately when w = wn)
wn_new1 = np.sqrt(k_orig / m_new1)
wn_new2 = np.sqrt(k_new / m_orig)

_, X_res1, _ = calc_dynamics(wn_new1, m_new1, k_orig, zeta_orig)
_, X_res2, _ = calc_dynamics(wn_new2, m_orig, k_new, zeta_new)

print("--- (e) Trade-off Analysis ---")
print("Solution 1 (Added Mass):")
print(f"  Static Deflection: {delta_st1*1000:.2f} mm")
print(f"  Resonance Amplitude (Startup): {X_res1*1000:.2f} mm")
print("Solution 2 (Softer Mounts):")
print(f"  Static Deflection: {delta_st2*1000:.2f} mm")
print(f"  Resonance Amplitude (Startup): {X_res2*1000:.2f} mm")

# ==========================================
# Plotting Force Transmissibility
# ==========================================
plt.figure(figsize=(10, 6))

# Plot the three transmissibility curves
plt.plot(w_vals, T_orig, 'r-', linewidth=2, label='Original System')
plt.plot(w_vals, T_new1, 'b--', linewidth=2, label=f'Added Mass (mc = {mc:.1f} kg)')
plt.plot(w_vals, T_new2, 'g-.', linewidth=2, label='Softer Mounts')

# Shade the operating frequency range
plt.axvspan(w_min, w_max, color='yellow', alpha=0.3, label='Operating Range (800-1100 rpm)')

# Formatting the plot
plt.title('Force Transmissibility vs. Excitation Frequency', fontsize=14)
plt.xlabel('Frequency (rad/s)', fontsize=12)
plt.ylabel('Force Transmissibility $T$', fontsize=12)
plt.axhline(1, color='k', linestyle=':', label='T = 1 (Isolation Boundary)')
plt.ylim(0, 3)
plt.xlim(0, 250)
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
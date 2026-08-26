import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize_scalar

# Given Problem Parameters
m = 60.0          # Mass (kg)
E = 210e9         # Young's modulus (N/m^2)
D = 0.2           # Diameter (m)
L = 3.0           # Length (m)
rho = 1.204       # Air density (kg/m^3)

# Calculate natural frequency (omega_n)
# Assuming a cantilever beam model for the wind turbine
I = (np.pi * D**4) / 64  # Area moment of inertia for a solid cylinder
# Note: For a real turbine, it might be a hollow cylinder, but based on given info we assume solid for E and I calculation, or given mass is an equivalent mass.
# Let's use the equivalent mass stiffness relation: omega_n = sqrt(k_eq / m)
# For a cantilever beam with an end mass, k_eq = 3EI/L^3. 
# However, the problem gives E but doesn't specify if it's hollow. 
# Let's calculate equivalent stiffness k.
k = (3 * E * I) / (L**3)
omega_n = np.sqrt(k / m)

# Function to calculate forcing amplitude F0
def calc_F0(omega, D_val=D):
    return 0.317 * rho * (D_val**3) * L * (omega**2)

# Function to calculate steady-state amplitude X0
def calc_X0(omega, zeta, D_val=D):
    """
    Calculates the steady-state amplitude of vibration.
    Formula: X0 = (F0 / k) / sqrt((1 - (omega/omega_n)^2)^2 + (2 * zeta * (omega/omega_n))^2)
    Since k = m * omega_n^2, we can rewrite: X0 = (F0 / m) / sqrt((omega_n^2 - omega^2)^2 + (2 * zeta * omega * omega_n)^2)
    """
    F0 = calc_F0(omega, D_val)
    # Using the standard form with mass
    denominator = m * np.sqrt((omega_n**2 - omega**2)**2 + (2 * zeta * omega * omega_n)**2)
    return F0 / denominator

# --- Part (a) ---
print("--- Part (a) ---")
print(f"Calculated Natural Frequency (omega_n): {omega_n:.2f} rad/s")

# Frequency range for plotting (around natural frequency)
omega_range = np.linspace(0, 2 * omega_n, 500)
zeta_values = [0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]

plt.figure(figsize=(10, 6))

for zeta in zeta_values:
    X0_vals = [calc_X0(w, zeta) for w in omega_range]
    # Convert to mm for better visualization
    X0_vals_mm = [x * 1000 for x in X0_vals]
    plt.plot(omega_range, X0_vals_mm, label=f'$\zeta$ = {zeta}')

plt.title('Steady-State Amplitude vs. Forcing Frequency')
plt.xlabel('Forcing Frequency, $\omega$ (rad/s)')
plt.ylabel('Steady-State Amplitude, $X_0$ (mm)')
plt.axvline(x=omega_n, color='k', linestyle='--', label='Natural Frequency ($\omega_n$)')
plt.legend()
plt.grid(True)
plt.xlim(0, 2 * omega_n)
# Save the plot (optional, but good for self-contained scripts)
plt.savefig('amplitude_vs_frequency.png')
print("Plot generated and saved as 'amplitude_vs_frequency.png'.")
print("Comment on zeta: A lower damping ratio leads to higher amplitude near resonance. For a wind turbine generating energy from vibrations, a very high damping ratio would kill the vibrations, but too low might cause structural failure. An intermediate value balances energy capture and structural integrity.")

# --- Part (b) ---
print("\n--- Part (b) ---")
design_zeta = 0.2

# To find maximum amplitude, we need to find the frequency omega that maximizes X0.
# We can minimize the negative of the X0 function.
def neg_X0_for_opt(omega):
    return -calc_X0(omega, design_zeta)

# The maximum amplitude usually occurs near omega_n.
res = minimize_scalar(neg_X0_for_opt, bounds=(0, 2*omega_n), method='bounded')
omega_max_amp = res.x

print(f"Frequency for max amplitude (omega_max): {omega_max_amp:.2f} rad/s")

# Given relation: omega = 0.4 * pi * V_wind / D
# Therefore: V_wind = (omega * D) / (0.4 * pi)
V_wind_max_amp = (omega_max_amp * D) / (0.4 * np.pi)
print(f"Wind speed for maximum amplitude (V_wind): {V_wind_max_amp:.2f} m/s")

# --- Part (c) ---
print("\n--- Part (c) ---")
max_X0 = calc_X0(omega_max_amp, design_zeta)
max_X0_mm = max_X0 * 1000
print(f"Corresponding maximum amplitude: {max_X0_mm:.4f} mm")

# --- Part (d) ---
print("\n--- Part (d) ---")
target_max_amp_m = 0.10 / 1000  # 0.10 mm in meters

def max_amp_for_D(D_new):
    # Recalculate k and omega_n for the new diameter
    I_new = (np.pi * D_new**4) / 64
    k_new = (3 * E * I_new) / (L**3)
    omega_n_new = np.sqrt(k_new / m)
    
    # We need to find the new maximum amplitude.
    # We define a function for X0 that uses the *new* D and *new* omega_n
    def local_neg_X0(omega):
        # We need to write out the X0 formula here to use the updated omega_n_new
        F0 = calc_F0(omega, D_new)
        denominator = m * np.sqrt((omega_n_new**2 - omega**2)**2 + (2 * design_zeta * omega * omega_n_new)**2)
        return -(F0 / denominator)
    
    # Find the peak frequency for this specific D_new
    # Search around the new natural frequency
    res = minimize_scalar(local_neg_X0, bounds=(0.1*omega_n_new, 2*omega_n_new), method='bounded')
    # Return the positive maximum amplitude
    return -res.fun

# We want to find a diameter D_new such that max_amp_for_D(D_new) <= target_max_amp_m.
# Let's find the D_new that makes it exactly equal to the target.
def objective_func_D(D_new):
    return (max_amp_for_D(D_new) - target_max_amp_m)**2

# We start our search near the original diameter. We expect we might need to increase it to make it stiffer.
res_D = minimize_scalar(objective_func_D, bounds=(0.05, 1.0), method='bounded')
new_D = res_D.x

print(f"Redesigned Diameter (D) to limit amplitude to 0.1 mm: {new_D:.4f} m")

# Verification
final_max_amp = max_amp_for_D(new_D)
print(f"Verification: Max amplitude with new D = {final_max_amp * 1000:.4f} mm")

# Calculate the new natural frequency and wind speed for max amplitude with new design
I_final = (np.pi * new_D**4) / 64
k_final = (3 * E * I_final) / (L**3)
omega_n_final = np.sqrt(k_final / m)

# Find new peak frequency
def local_neg_X0_final(omega):
    F0 = calc_F0(omega, new_D)
    denominator = m * np.sqrt((omega_n_final**2 - omega**2)**2 + (2 * design_zeta * omega * omega_n_final)**2)
    return -(F0 / denominator)

res_final = minimize_scalar(local_neg_X0_final, bounds=(0.1*omega_n_final, 2*omega_n_final), method='bounded')
omega_max_amp_final = res_final.x
V_wind_max_amp_final = (omega_max_amp_final * new_D) / (0.4 * np.pi)

print(f"New Natural Frequency: {omega_n_final:.2f} rad/s")
print(f"Wind speed for max amplitude with new design: {V_wind_max_amp_final:.2f} m/s")
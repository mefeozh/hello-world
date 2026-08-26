import numpy as np
import matplotlib.pyplot as plt

# ==============================================================================
# 1. Define Operating Parameters
# ==============================================================================
# Geometry
D = 0.050        # Diameter in m (50 mm)
R = D / 2.0      # Radius in m
L_total = 0.055  # Total length in m (55 mm)
w_g = 0.005      # Central annular groove width in m (5 mm)

# A central annular groove effectively splits the bearing into two shorter lands (bearings)
L = (L_total - w_g) / 2.0  # Effective length of each bearing half (25 mm)

# Speeds and Loads
N_rpm = 2400.0
N_revs = N_rpm / 60.0      # Speed in rev/s
omega = N_revs * 2 * np.pi # Speed in rad/s
U = omega * R              # Linear surface speed in m/s

# Environmental and Fluid Properties
T_in = 40.0      # Inlet oil temperature in Celsius
P_s = 500000.0   # Supply pressure in Pa (500 kPa)
rho = 860.0      # Density of SAE 30 oil (kg/m^3)
CH = 1760.0      # Specific heat of oil (J/kg.C)

# Clearances to evaluate for part (a) (20 to 100 microns, 10 micron increments)
clearances = np.arange(20, 101, 10) * 1e-6

# --- Trumpler's Design Criteria ---
h0_min_microns = 0.00508 + 0.00004 * D

Tmax_limit = 120.0 # Celsius

# ==============================================================================
# 2. Standard ISO Fits for 50 mm Nominal Diameter (IS0 286, 30-50mm range)
# ==============================================================================
# Defines limit deviations for hole and shaft in micrometers (μm)
standard_fits = {
    'H7/g6': {'hole': (0, 25), 'shaft': (-25, -9)},
    'H7/f7': {'hole': (0, 25), 'shaft': (-50, -25)}, 
    'H7/e7': {'hole': (0, 25), 'shaft': (-75, -50)}, 
    'H8/f5': {'hole': (0, 39), 'shaft': (-36, -25)},  # Added per user request
    'H8/f7': {'hole': (0, 39), 'shaft': (-50, -25)},
    'H8/f8': {'hole': (0, 39), 'shaft': (-64, -25)},
    'H8/e8': {'hole': (0, 39), 'shaft': (-89, -50)},
    'H8/d8': {'hole': (0, 39), 'shaft': (-119, -80)},
    'H8/d9': {'hole': (0, 39), 'shaft': (-142, -80)},
    'H8/c8': {'hole': (0, 39), 'shaft': (-159, -120)}
}

def get_fit_limits_radial(fit_name):
    """ Returns the min and max RADIAL clearance for a given basic hole fit in meters. """
    hole = standard_fits[fit_name]['hole']
    shaft = standard_fits[fit_name]['shaft']
    cd_min = hole[0] - shaft[1]  # Diametral clearance min (um)
    cd_max = hole[1] - shaft[0]  # Diametral clearance max (um)
    return (cd_min / 2.0) * 1e-6, (cd_max / 2.0) * 1e-6

# ==============================================================================
# 3. Iterative Analytical Methods
# ==============================================================================
def calc_viscosity(T_C):
    """ SAE 30 viscosity curve fit (returns Pa.s) """
    # Equation derived from the SAE Viscosity charts
    mu_mPas = 0.097149 * np.exp(1360.0 / (1.8 * T_C + 127.0))
    return mu_mPas / 1000.0

def short_bearing_S(eps, L_D):
    """ Analytical Sommerfeld number using Short Bearing (Ocvirk) Approximation """
    term1 = (1 - eps**2)**2
    term2 = np.pi * eps * np.sqrt(16 * eps**2 + np.pi**2 * (1 - eps**2))
    return (term1 / term2) * (1 / L_D)**2

def find_epsilon(S_target, L_D):
    """ 
    Find eccentricity ratio analytically for a given Sommerfeld number.
    Uses robust Bisection Method to strictly avoid external numerical systems (like scipy).
    """
    left = 0.0001
    right = 0.9999
    
    for _ in range(100):
        mid = (left + right) / 2.0
        S_mid = short_bearing_S(mid, L_D)
        
        # S monotonically decreases as eps approaches 1
        if S_mid > S_target:
            left = mid
        else:
            right = mid
            
    return (left + right) / 2.0

def solve_bearing(W_total, c, pressure=P_s):
    """
    Analyzes bearing thermal equilibrium and operating parameters.
    Uses analytical equations and relaxation iteration.
    Returns: h0, eps, T_max, T_ave, S
    """
    W_half = W_total / 2.0 # Load supported by one land
    P_unit = W_half / (2 * R * L) # Unit load on one land
    L_D = L / D
    
    T_ave = T_in + 15.0 # Initial thermal guess
    
    # Iterative heat balance solver
    for _ in range(250):
        mu = calc_viscosity(T_ave)
        S = ((R / c)**2) * (mu * N_revs / P_unit)
        eps = find_epsilon(S, L_D)
        
        # 1. Heat generation (Friction of one land)
        f_rc = 2 * np.pi**2 * S / max(1e-6, np.sqrt(1 - eps**2))
        f = f_rc * (c / R)
        H_half = f * W_half * R * omega
        H_total = 2 * H_half # Total heat generated out of the whole bearing
        
        # 2. Coolant Flow carrying heat away
        if pressure > 1.0:
            # Pressurized centrally grooved (Shigley flow equation)
            # Total forced axial flow leaving both bearing halves
            Q_total = (np.pi * pressure * R * c**3 * (1 + 1.5 * eps**2)) / (3 * mu * L)
        else:
            # Lubrication System Failure (Atmospheric supply)
            # Flow is solely the net hydrodynamic outward axial flow (side leakage).
            # Treating the central groove as an atmospheric bath. Both lands leak from both inner and outer ends.
            # Q_side_one_land = U * L * c * eps (for both ends).
            Q_total = 2 * (U * L * c * eps)
            
        # 3. Temperature Rise
        dT = H_total / (rho * CH * Q_total) if Q_total > 1e-12 else 500.0
        
        T_ave_new = T_in + dT / 2.0
        
        # Check convergence
        if abs(T_ave_new - T_ave) < 0.05:
            T_ave = T_ave_new
            break
            
        # Relaxation factor for stability when P_s is 0
        T_ave = 0.1 * T_ave_new + 0.9 * T_ave
        
    T_max = T_in + dT
    h0 = c * (1 - eps)
    return h0, eps, T_max, T_ave, S

# ==============================================================================
# PART A: Determine Optimum Clearance Range & Basic Hole Fit
# ==============================================================================
print("=" * 60)
print("PART A: OPTIMUM CLEARANCE AND BASIC HOLE FIT")
print("-" * 60)
h0_list = []
Tmax_list = []

# Trumpler Starting Load Condition
P_st_kPa = (5000.0 / (2 * L * D)) / 1000.0
P_st_safe = P_st_kPa <= 2068.0
print(f"=> Trumpler Starting Load P_st: {P_st_kPa:.0f} kPa <= 2068 kPa [{'SAFE' if P_st_safe else 'UNSAFE'}]")

for c in clearances:
    h0, eps, T_max, _, _ = solve_bearing(W_total=5000.0, c=c, pressure=P_s)
    h0_list.append(h0 * 1e6)
    Tmax_list.append(T_max)
    
    # Check if Trumpler's criteria are satisfied
    is_safe = (h0*1e6 >= h0_min_microns) and (T_max <= Tmax_limit) and P_st_safe
    status = "SAFE" if is_safe else "UNSAFE"
    print(f"c = {c*1e6:3.0f} um -> h0 = {h0*1e6:5.2f} um, T_max = {T_max:6.2f} C [{status}]")

# From an engineering perspective, the optimum clearance is the smallest clearance 
# that safely satisfies Trumpler's minimum film thickness AND temperature criteria.
# We will analytically interpolate the exact clearance c_opt where BOTH limits are met.

c_safe_h0 = clearances[0] * 1e6 # default
c_safe_Tmax = clearances[-1] * 1e6 # default safe assumption

# 1. Find where h0 crosses h0_min_microns (h0 is increasing with c)
if h0_list[0] < h0_min_microns:
    for i in range(len(clearances)-1):
        h1, h2 = h0_list[i], h0_list[i+1]
        if h1 <= h0_min_microns <= h2:
            c1, c2 = clearances[i]*1e6, clearances[i+1]*1e6
            slope = (h2 - h1) / (c2 - c1)
            c_safe_h0 = c1 + (h0_min_microns - h1) / slope
            break

# 2. Find where T_max crosses Tmax_limit (T_max is decreasing with c)
if Tmax_list[0] > Tmax_limit:
    for i in range(len(clearances)-1):
        T1, T2 = Tmax_list[i], Tmax_list[i+1]
        if T1 >= Tmax_limit >= T2:
            c1, c2 = clearances[i]*1e6, clearances[i+1]*1e6
            slope = (T2 - T1) / (c2 - c1)
            c_safe_Tmax = c1 + (Tmax_limit - T1) / slope
            break
else:
    c_safe_Tmax = clearances[0] * 1e6 # already safe

c_opt_microns = max(c_safe_h0, c_safe_Tmax)
if np.isnan(c_opt_microns): # robust fallback
    c_opt_microns = clearances[-1] * 1e6

c_opt = c_opt_microns * 1e-6
print(f"\n=> Determined Optimum Radial Clearance (Minimum safe via Trumpler constraints): {c_opt_microns:.1f} um")

# Find the closest ISO basic hole system fit
best_fit = None
min_err = float('inf')

for fit_name in standard_fits.keys():
    c_min, c_max = get_fit_limits_radial(fit_name)
    c_avg = (c_min + c_max) / 2.0
    err = abs(c_avg - c_opt)
    if err < min_err:
        min_err = err
        best_fit = fit_name

c_min_opt, c_max_opt = get_fit_limits_radial(best_fit)
print(f"=> Selected Best Basic Hole Fit: {best_fit}")
print(f"   Radial Clearance Limits for fit: {c_min_opt*1e6:.1f} um to {c_max_opt*1e6:.1f} um")
print(f"   (Average Clearance: {(c_min_opt+c_max_opt)/2*1e6:.1f} um)")

# ==============================================================================
# PART B: Overload Condition (1.5x Steady Load) -> W = 7.5 kN
# ==============================================================================
print("\n" + "=" * 60)
print("PART B: OVERLOAD CONDITION (LOAD = 7.5 kN, P_s = 500 kPa)")
print("-" * 60)
W_overload = 5000.0 * 1.5

# Lower limit of chosen fit (tighter clearance)
h0_min_b, eps_min_b, T_max_min_b, _, _ = solve_bearing(W_overload, c_min_opt, P_s)
print(f"At Lower Limit (c_min = {c_min_opt*1e6:.1f} um):")
print(f"  Film Thickness (h0)  = {h0_min_b*1e6:.2f} um")
print(f"  Eccentricity Ratio   = {eps_min_b:.4f}")

# Upper limit of chosen fit (looser clearance)
h0_max_b, eps_max_b, T_max_max_b, _, _ = solve_bearing(W_overload, c_max_opt, P_s)
print(f"At Upper Limit (c_max = {c_max_opt*1e6:.1f} um):")
print(f"  Film Thickness (h0)  = {h0_max_b*1e6:.2f} um")
print(f"  Eccentricity Ratio   = {eps_max_b:.4f}")

# Average clearance
c_avg_opt = (c_min_opt + c_max_opt) / 2.0
h0_avg_b, eps_avg_b, T_max_avg_b, _, _ = solve_bearing(W_overload, c_avg_opt, P_s)
print(f"At Average Clearance (c_avg = {c_avg_opt*1e6:.1f} um):")
print(f"  Film Thickness (h0)  = {h0_avg_b*1e6:.2f} um")
print(f"  Eccentricity Ratio   = {eps_avg_b:.4f}")

# ==============================================================================
# PART C: Lubrication System Failure (Atmospheric Pressure Supply)
# ==============================================================================
print("\n" + "=" * 60)
print("PART C: LUBE SYSTEM FAILURE (LOAD = 5.0 kN, P_s = ATMOSPHERIC)")
print("-" * 60)
W_normal = 5000.0
P_atm = 0.0 # Gauge pressure is zero

# Lower limit of chosen fit
h0_min_c, eps_min_c, T_max_min_c, _, _ = solve_bearing(W_normal, c_min_opt, P_atm)
print(f"At Lower Limit (c_min = {c_min_opt*1e6:.1f} um):")
print(f"  Film Thickness (h0)  = {h0_min_c*1e6:.2f} um")
print(f"  Eccentricity Ratio   = {eps_min_c:.4f}")
print(f"  Max Temperature      = {T_max_min_c:.2f} C")

# Upper limit of chosen fit
h0_max_c, eps_max_c, T_max_max_c, _, _ = solve_bearing(W_normal, c_max_opt, P_atm)
print(f"At Upper Limit (c_max = {c_max_opt*1e6:.1f} um):")
print(f"  Film Thickness (h0)  = {h0_max_c*1e6:.2f} um")
print(f"  Eccentricity Ratio   = {eps_max_c:.4f}")
print(f"  Max Temperature      = {T_max_max_c:.2f} C")

# Average clearance
h0_avg_c, eps_avg_c, T_max_avg_c, _, _ = solve_bearing(W_normal, c_avg_opt, P_atm)
print(f"At Average Clearance (c_avg = {c_avg_opt*1e6:.1f} um):")
print(f"  Film Thickness (h0)  = {h0_avg_c*1e6:.2f} um")
print(f"  Eccentricity Ratio   = {eps_avg_c:.4f}")
print(f"  Max Temperature      = {T_max_avg_c:.2f} C")

# ==============================================================================
# 4. PLOTTING (Part A Plot updated to include Trumpler limits perfectly)
# ==============================================================================
plt.figure(figsize=(12, 5))
plt.style.use('ggplot')

# Plot 1: Minimum Film Thickness
plt.subplot(1, 2, 1)
plt.plot(clearances * 1e6, h0_list, 'b-o', mfc='white', linewidth=2, label='Analytical h0')
plt.axhline(h0_min_microns, color='red', linestyle=':', linewidth=2, label=f"Trumpler Limit ({h0_min_microns:.2f} $\mu$m)")
plt.axvline(c_opt * 1e6, color='green', linestyle='--', label=f'Opt c = {c_opt*1e6:.1f} $\mu$m')
plt.xlabel('Radial Clearance, c ($\mu$m)', fontweight='bold')
plt.ylabel('Minimum Film Thickness, $h_0$ ($\mu$m)', fontweight='bold')
plt.title('Minimum Film Thickness vs. Radial Clearance', fontweight='bold')
plt.legend()

# Plot 2: Maximum Temperature
plt.subplot(1, 2, 2)
plt.plot(clearances * 1e6, Tmax_list, 'r-s', mfc='white', linewidth=2, label='Analytical Tmax')
plt.axhline(Tmax_limit, color='red', linestyle=':', linewidth=2, label=f"Trumpler Limit ({Tmax_limit} $^\circ$C)")
plt.axvline(c_opt * 1e6, color='green', linestyle='--', label=f'Opt c = {c_opt*1e6:.1f} $\mu$m')
plt.xlabel('Radial Clearance, c ($\mu$m)', fontweight='bold')
plt.ylabel('Maximum Temperature, $T_{max}$ ($^\circ$C)', fontweight='bold')
plt.title('Maximum Temperature vs. Radial Clearance', fontweight='bold')
plt.legend()

plt.tight_layout()
plt.savefig('journal_bearing_optimization.png')
print("\nPlots generated and saved to 'journal_bearing_optimization.png'. Execution Complete.")

import matplotlib
matplotlib.use('TkAgg')
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from scipy.optimize import fsolve

#!!!THE CODE AND THE COMMENTS ARE MADE FROM MEHMET EFE ÖZHAN 2446672!!!

# system constrains
 # 1. GEOMETRIC CONSTRAINTS (Lengths in mm) 
dims = {
    "a6": 39.2,          # Crank (A0-A)
    "a7": 225.4,         # Pitman (AC)
    "b7": 29.4,          # Pitman offset (BC)
    "a8": 235.2,         # Rear Toggle (C0-C)
    "a9": 411.6,         # Front Toggle (BD)
    "a10": 475.3,        # Moving Jaw (D0-D)
    "C_dist": 372.4,     # Distance from D0 to F_crush
    "A0C0_x": 245.0,     # Ground pivot x-dist
    "A0C0_y": 245.0,     # Ground pivot y-dist
    "A0D0_x": 196.0,     # Ground pivot x-dist
    "A0D0_y": 98.0,      # Ground pivot y-dist
    "a11": 390.0,        # Center distance (motor to flywheel)
    "h11": 120.0,        # Height difference (motor to flywheel)
}

# 2. OPERATIONAL & DESIGN PARAMETERS 
specs = {
    "F_crush": 10000,           # 10 kN in Newtons [cite: 112]
    "motor_speed_rpm": 1200,    # Motor RPM
    "speed_ratio": 16,          # Motor to Flywheel ratio
    "reliability": 0.9,         # 90%
    "temp_C": 20,               # Operating temp
    "friction_coeff_f": 0.26,   # Belt friction
    "flywheel_D": 380,          # Flywheel diameter (mm)
    "d2_d1_ratio": 1.15,        # Shaft diameter ratio
    "fos": 2.1,                 # Factor of Safety
    "side_ratio_link9": 1.25,   # Hollow square ratio (outer/inner)
}

# 3. CRITICAL POSITION ANGLES (Degrees)
angles_crit = {
    "theta6": np.deg2rad(333.85),
    "theta7": np.deg2rad(268.76),
    "theta8": np.deg2rad(13.79),
    "theta9": np.deg2rad(354.33),
    "theta10": np.deg2rad(260.54),
    "angle_BA_CA":  0.12970253715591196
}

# 4. SHAFT & PIN DESIGN DIMENSIONS (mm) 
design_dims = {
    "L1": 85.0,
    "L2": 240.0,
    "L3": 500.0,
    "r_d_fillet": 0.125,        # Fillet radius ratio (r/d)
    "LB1": 35.0,
    "LB2": 88.0,
    "LB3": 24.0
}

# 5. MATERIAL PROPERTIES (Dataset 2: Steel HR) 
# Values From the Shigley's Table A-20 (S_ut / S_y in MPa)
materials = {
    "links":    {"name": "1050", "S_ut": 620, "S_y": 340, "E": 190e3},
    "pins":     {"name": "1095", "S_ut": 830, "S_y": 460, "E": 200e3},
    "shaft":    {"name": "1030", "S_ut": 470, "S_y": 260}, 
    "brackets": {"name": "1030", "S_ut": 470, "S_y": 260}
}
found_forces_and_torques = {
    "F9": 0,
    "F8": 0,
    "F_A0x": 0,
    "F_A0y": 0,
    "T_shaft": 0,
    "F_A_total": 0
}


def get_shear_moment(x_array, loads):
    """
    Calculates Shear (V) and Moment (M) arrays for a given set of point loads.
    loads: list of tuples (position, force)
    x_array: numpy array of x positions
    """
    V = np.zeros_like(x_array)
    M = np.zeros_like(x_array)
    
    # Sort loads by position just in case
    loads.sort(key=lambda x: x[0])
    
    for i, x in enumerate(x_array):
        v_val = 0
        m_val = 0
        
        for pos, force in loads:
            if x >= pos: 
                v_val += force
                m_val += force * (x - pos)
                
        V[i] = v_val
        M[i] = m_val
        
    return V, M

def plot_diagrams(x, V, M, title_suffix="", filename=None):
    """
    Plots Shear and Moment diagrams.
    """
    # Create a new figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    
    # Shear
    ax1.plot(x * 1000, V, 'b-', label='Shear (V)')
    ax1.fill_between(x * 1000, V, alpha=0.3, color='b')
    ax1.set_ylabel('Shear Force (N)')
    ax1.set_title(f'Shear Diagram {title_suffix}')
    ax1.grid(True)
    ax1.legend()
    
    # Moment
    ax2.plot(x * 1000, M, 'r-', label='Moment (M)')
    ax2.fill_between(x * 1000, M, alpha=0.3, color='r')
    ax2.set_xlabel('Position (mm)')
    ax2.set_ylabel('Bending Moment (Nm)')
    ax2.set_title(f'Moment Diagram {title_suffix}')
    ax2.grid(True)
    ax2.legend()
    
    plt.tight_layout()
    if filename:
        plt.savefig(filename)
        print(f"Saved plot to {filename}")
    plt.close(fig)

def solve_forces(dims, specs, angles):
    """
    Calculates the reaction forces and input torque for the jaw crusher mechanism.
    """
    # --- GEOMETRY SETUP ---
    # Link 7 (Pitman) Geometry
    # a7 = AC, b7 = BC (perp offset).
    C7 = np.sqrt(dims["a7"]**2 + dims["b7"]**2)
    print("C7: ", C7)
    lambda_7 = np.arctan(dims["b7"] / dims["a7"]) 
    
    angle_CA = angles["theta7"] + lambda_7
    print("angle_CA: ", np.rad2deg(angle_CA))
    # Position Vectors relative to A
    # r_BA: Vector from A to B. User uses theta7 for this.
    r_BA = np.array([C7 * np.cos(angles["theta7"]), 
                     C7 * np.sin(angles["theta7"]), 0])
    print("r_BA: ", r_BA)
    
    # r_CA: Vector from A to C. User uses theta7 + lambda_7.
    r_CA = np.array([dims["a7"] * np.cos(angle_CA),
                     dims["a7"] * np.sin(angle_CA), 0])
    print("r_CA: ", r_CA)

    # --- STEP 1: LINK 10 (THE JAW) ---
    # Find F9 (Force from Link 9 on Jaw).
    # Moment Balance about D0:
    # M_crush + M_F9 = 0
    
    # Force F9 acts at D.
    # Lever arm vector from D0 to D:
    r_D_D0 = np.array([dims["a10"] * np.cos(angles["theta10"]),
                       dims["a10"] * np.sin(angles["theta10"]), 0])
                       
    # Force Direction for F9: Along Link 9 (theta9).

    dir_F9 = np.array([np.cos(angles["theta9"]), np.sin(angles["theta9"]), 0])
    
    # Moment of F9 about D0 = (r_D_D0 x F9_vec)_z
    # = Mag * (r_D_D0 x dir_F9)_z
    m_unit_F9 = np.cross(r_D_D0, dir_F9)[2]
    

    moment_crush = specs["F_crush"] * dims["C_dist"]
    # moment = F_9 * lever + M_crush = 0
    #F_9 = -cos(theta9)*F_9 i - sin(theta9)*F_9 j

    lever_val = dims["a10"] * np.sin(angles['theta9'] - angles['theta10'])
    f9_mag = -moment_crush / lever_val
    # Force Vector F9 (on Jaw)
    F9_vec = f9_mag * dir_F9
    
    # --- STEP 2: LINK 7 ---
    F_B = -F9_vec
    print("F_B: ", F_B)
    # 2. Force at C from Link 8.
    dir_F8 = -np.array([np.cos(angles["theta8"]), np.sin(angles["theta8"]), 0])
    
    # Sum Moments about A = 0
    # (r_BA x F_B) + (r_CA x F_C) = 0
    # (r_BA x F_B) + (r_CA x (F8_mag * dir_F8)) = 0
    # M_B + F8_mag * M_unit_C = 0
    
    M_B = np.cross(r_BA, F_B)[2]
    M_unit_C = np.cross(r_CA, dir_F8)[2]

    f8_mag = -M_B / M_unit_C

    F_C = f8_mag * dir_F8
    print("F_C: ", F_C)
    # Sum Forces for Reaction at A
    # F_A + F_B + F_C = 0
    F_A = -(F_B + F_C)
    print("F_A: ", F_A)
    
    # --- STEP 3: LINK 6 (THE CRANK) ---
    F_on_Crank = -F_A
    print("F_on_Crank: ", F_on_Crank)
    r_A = np.array([dims["a6"] * np.cos(angles["theta6"]),
                    dims["a6"] * np.sin(angles["theta6"]), 0])
    F_A_mag = np.sqrt(F_A[0]**2 + F_A[1]**2)
    print("F_A_mag: ", F_A_mag)
    # Sum Moments about A0 = 0
    # T6 + (r_A x F_on_Crank) = 0
    T6_vec = np.cross(r_A, F_on_Crank)
    T_shaft = -T6_vec[2] # Reaction torque required
    
    # Calculate Raw Results for Shaft Analysis
    raw_results = {
        "F_A0x": F_A[0],
        "F_A0y": F_A[1],
        "T_shaft": abs(T_shaft), 
        "F_crush": specs["F_crush"],
        "F9": abs(f9_mag),
        "F8": f8_mag
    }

    #adding datas to the dictionary
    found_forces_and_torques = {
        "F9": f9_mag,
        "F8": f8_mag,
        "F_A0x": F_A[0],
        "F_A0y": F_A[1],
        "T_shaft": T_shaft,
        "F_A_total": np.sqrt(F_A[0]**2 + F_A[1]**2)
    }

    formatted_results = {
        "F_Link9 (N)": round(abs(f9_mag), 5),
        "F_Link8 (N)": round(abs(f8_mag), 5),
        "F_CrankPin_x (N)": round(F_A[0], 5),
        "F_CrankPin_y (N)": round(F_A[1], 5),
        "Torque_Crank (Nm)": round(T_shaft / 1000, 5)
    }
    
    return formatted_results, raw_results

def analyze_shaft_soderberg(dims, specs, materials, forces, design_dims):
    """
    Performs shaft design analysis using Soderberg Criterion (Repeated Load).
    Layout: x=0 (Crank), x=L1 (Bearing1), x=L2 (Flywheel), x=L3 (Bearing2)
    """
    print("\n" + "="*40)
    print("      SHAFT DESIGN & FATIGUE ANALYSIS")
    print("="*40)

    # --- 1. BELT FORCE CALCULATION ---
    # Retrieve parameters
    D = specs["flywheel_D"] / 1000.0  # mm to m
    d = D / specs["speed_ratio"]
    C = dims["a11"] / 1000.0          # mm to m
    
    # Recalculate C based on user formula C = sqrt(a11^2 + h11^2)
    # Note: user might have used C from dims directly as linear dist if a11 was x and h11 was y
    C_actual = np.sqrt((dims["a11"]/1000)**2 + (dims["h11"]/1000)**2)
    
    # Wrap Angle (alpha)
    # alpha = 180 + 2 * asin((D - d) / (2 * C))
    term = (D - d) / (2 * C_actual)
    alpha_rad = np.pi + 2 * np.arcsin(term)
    alpha_deg = np.rad2deg(alpha_rad)
    
    print(f"Wrap Angle: {alpha_deg:.2f} deg ({alpha_rad:.2f} rad)")

    # Solve for F1, F2
    f = specs["friction_coeff_f"]
    ratio = np.exp(f * alpha_rad)
    #experimental torque data for now

    T_Shaft = forces["T_shaft"]
    # Torque on Shaft
    T_shaft = T_Shaft / 1000.0 # Nm

    term_tan = np.arctan(dims["h11"] / dims["a11"])      # tan^-1(h11/a11)
    term_sin = np.arcsin(term)      # sin^-1(...)
    
    angle_f1 = -(term_tan - term_sin)       # Angle for F1
    print("angle_f1: ", np.rad2deg(angle_f1))
    angle_f2 = -(term_tan + term_sin)       # Angle for F2
    print("angle_f2: ", np.rad2deg(angle_f2))
    
    # (F1 - F2) * (D / 2) = T_shaft
    F2 = (2 * T_shaft / D) / (ratio - 1)
    F1 = F2 * ratio
    F1_x,F1_y = F1 * np.cos(angle_f1), F1 * np.sin(angle_f1)
    F2_x,F2_y = F2 * np.cos(angle_f2), F2 * np.sin(angle_f2)
    print("F1_x: ", F1_x)
    print("F1_y: ", F1_y)
    print("F2_x: ", F2_x)
    print("F2_y: ", F2_y)
    F_belt_mag = np.sqrt((F1_x + F2_x)**2 + (F1_y + F2_y)**2)
    
    print(f"Torque on Shaft: {-T_shaft:.2f} Nm")
    print(f"Belt Forces: F1={F1:.1f} N, F2={F2:.1f} N")
    print(f"Total Belt Load: {F_belt_mag:.1f} N")

    # Belt Force Direction (User: +z horiz, -y down)
    F_belt_x = -(F1_x + F2_x)
    F_belt_y = -(F1_y + F2_y)
    print("belt forces: ", F_belt_x, F_belt_y)
    # --- 2. STATIC ANALYSIS (REACTIONS) ---
    # Load at Crank (x_beam = 0):
    P_crank_y = -forces["F_A0y"] 
    P_crank_x = -forces["F_A0x"] 
    
    L1, L2, L3 = design_dims["L1"]/1000, design_dims["L2"]/1000, design_dims["L3"]/1000

    # Moments about Bearing 1 (L1) to find Bearing 2 (L3)
    # Sum M_L1 = -P_crank * L1 + F_belt * (L2 - L1) + R_B2 * (L3 - L1) = 0
    R_B2y = (P_crank_y * L1 - F_belt_y * (L2 - L1)) / (L3 - L1)
    R_B2x = (P_crank_x * L1 - F_belt_x * (L2 - L1)) / (L3 - L1)
    print("reaction at bearing 2: ", R_B2y, R_B2x)
    # Sum Forces
    R_B1y = -(P_crank_y + F_belt_y + R_B2y)
    R_B1x = -(P_crank_x + F_belt_x + R_B2x)
    print("reaction at bearing 1: ", R_B1y, R_B1x)

    # Max Moment (Usually at Bearing 1 since it's the pivot between loads)
    M_B1 = np.sqrt((P_crank_y * L1)**2 + (P_crank_x * L1)**2)
    M_Fly = np.sqrt((R_B2y * (L3 - L2))**2 + (R_B2x * (L3 - L2))**2)
    M_max = max(M_B1, M_Fly)
    print("max moment: ", M_max)
    
    print(f"Moment at Bearing 1: {M_B1:.1f} Nm")
    print(f"Moment at Flywheel: {M_Fly:.1f} Nm")

    # --- PLOTTING SHAFT DIGRAMS ---
    x_len = design_dims["L3"] / 1000.0
    x_vals = np.linspace(0, x_len, 500)
    
    # Vertical Plane (Y) Loads: (Pos, Force).
    loads_y = [
        (0.0, P_crank_y),
        (L1, R_B1y),
        (L2, F_belt_y),
        (L3, R_B2y)
    ]
    
    # Horizontal Plane (X) Loads
    loads_z = [
        (0.0, P_crank_x),
        (L1, R_B1x),
        (L2, F_belt_x),
        (L3, R_B2x)
    ]
    
    # Calculate V and M
    Vy, My = get_shear_moment(x_vals, loads_y)
    Vz, Mz = get_shear_moment(x_vals, loads_z)
    
    # Total Moment
    M_total = np.sqrt(My**2 + Mz**2)
    
    # Plotting
    plot_diagrams(x_vals, Vy, My, "(Vertical - Z-Y Plane)", "shaft_vertical_shear_moment.png")
    plot_diagrams(x_vals, Vz, Mz, "(Horizontal - Z-X Plane)", "shaft_horizontal_shear_moment.png")
    
    # Plot Total Moment
    plt.figure(figsize=(8, 4))
    plt.plot(x_vals * 1000, M_total, 'g-', label='Total Moment (M_tot)')
    plt.fill_between(x_vals * 1000, M_total, alpha=0.3, color='g')
    plt.xlabel('Position (mm)')
    plt.ylabel('Resultant Moment (Nm)')
    plt.title('Resultant Bending Moment along Shaft')
    plt.grid(True)
    plt.legend()
    plt.savefig("shaft_total_moment.png")
    print("Saved plot to shaft_total_moment.png")
    plt.close()
    
    # Verify Max Moment matches
    M_max_plot = np.max(M_total)
    print(f"Max Moment from Plot: {M_max_plot:.2f} Nm")
    
    M_design = M_max_plot # Use the plot max as it's more comprehensive
    d1 = 0.030 # initial guess

    # --- 4. DIAMETER DESIGN Iterative(SODERBERG) ---
    S_ut = materials["shaft"]["S_ut"] * 1e6 # Pa
    S_y = materials["shaft"]["S_y"] * 1e6  # Pa
    S_e_prime = 0.5 * S_ut
        

    # Marin Factors
    k_a = 4.51 * (materials["shaft"]["S_ut"])**(-0.265) # Machined (using MPa)
    k_c = 1.0 # Bending
    k_d = 1.0 # Temp (20C)
    k_e = 0.897 # Reliability 90%

    # Stress Concentration
    K_t = 1.5
    K_ts = 1.2
    q = 0.8 
    K_f = 1 + q * (K_t - 1)
    q_s = 0.85
    K_fs = 1 + q_s * (K_ts - 1)
    print("K_f: ", K_f)
    print("K_fs: ", K_fs)

    for i in range(1, 7):

        # Material Props
        
        d_mm = d1 * 1000
        if 2.79 <= d_mm <= 51:
            k_b = 1.24 * (d_mm)**-0.107
        else:
            k_b = 1.51 * (d_mm)**-0.157


        
        S_e = k_a * k_b * k_c * k_d * k_e * S_e_prime
        
        #new solderberg equation for using theta mean and theta alternating as same and Pmax/2
        n = specs["fos"]
        
        # For 0 to Max loading:
        Ma = Mm = M_max / 2
        Ta = Tm = T_shaft / 2
        
        # First term (Alternating)
        term_a = (1/S_e) * np.sqrt((K_f * Ma)**2 + 0.75 * (K_fs * Ta)**2)
        
        # Second term (Mean)
        term_m = (1/S_y) * np.sqrt((K_f * Mm)**2 + 0.75 * (K_fs * Tm)**2)
        
        # Full formula for d^3
        d_cubed = (32 * n / np.pi) * (term_a + term_m)
        
        d_req = d_cubed**(1/3)
    
        
        d1 = d_req
        print(f"Required Diameter: {d_req*1000:.3f} mm")
    
    d2 = d1 * specs["d2_d1_ratio"]

    return {
        "d1_required_mm": round(d1 * 1000, 2),
        "d2_required_mm": round(d2 * 1000, 2),
        "M_max_Nm": round(M_design, 2),
        "F_belt_total_N": round(F_belt_mag, 2),
        "Safety_Factor": specs["fos"],
        "notch_radius": design_dims["r_d_fillet"]*d1*1000
    }



formatted_res, raw_res = solve_forces(dims, specs, angles_crit)
print("\n" + "="*40)
print("      KINEMATIC FORCE ANALYSIS RESULTS")
print("="*40)
for k, v in formatted_res.items():
    print(f"{k:<20}: {v:>10}")
print("="*40 + "\n")

# Run Shaft Analysis
# Update materials (User specified)

shaft_res = analyze_shaft_soderberg(dims, specs, materials, raw_res, design_dims)

print("\n" + "="*40)
print("      SHAFT DESIGN & FATIGUE ANALYSIS")
print("="*40)
for k, v in shaft_res.items():
    print(f"{k:<20}: {v:>10}")
print("="*40 + "\n")


# Part C: Link 9 Design
def finding_link9_diameter(forces):
    
    #determining buckling using euler columns 
    #determining Maximum Shear Stress Theory
    

    f9 = forces["F9"]
    print("F9: ", f9)
    area_coeff = 1 - (1/specs["side_ratio_link9"])**2
    a_msst = np.sqrt((f9 * specs["fos"]) / (area_coeff * materials["links"]["S_y"]))
    print("a_msst: ", a_msst)

    inertia_coeff = (1 - (1/specs["side_ratio_link9"])**4) / 12

    a_euler = ((f9 * specs["fos"] * dims["a9"]**2) / (np.pi**2 * materials["links"]["E"] * inertia_coeff))**(1/4)
    print("a_euler: ", a_euler)
    a_final = max(a_msst, a_euler)

    return a_final

link9_diameter = finding_link9_diameter(raw_res)
print("\n" + "="*40)
print("      LINK 9 DESIGN")
print("="*40)
print("Link 9 Diameter outer: ", link9_diameter)
print("Link 9 Diameter inner: ", link9_diameter *0.8)
print("="*40 + "\n")


# Part D: Pin Design
def finding_pin_diameter(forces):
    print("\n" + "="*40)
    print("      PIN DESIGN (C0 Joint)")
    print("="*40)

    # 1. PARAMETERS
    F_8 = abs(forces["F8"]) # Load in N (Magnitude)
    n = specs["fos"]
    S_y = materials["pins"]["S_y"] * 1e6 # MPa to Pa
    LB3 = design_dims["LB3"] / 1000.0 # mm to m 
    LB2 = design_dims["LB2"] / 1000.0 # mm to m 

    M_max = F_8 * LB3 / 2
    t = LB2 # Bearing thickness
    
    print(f"Pin Load F8: {F_8:.1f} N")
    print(f"Material Sy: {S_y/1e6:.1f} MPa")
    
    # --- PIN SHEAR/MOMENT PLOTS ---
    # Range: -LB3 to LB3
    # Load F8 at 0
    # Reactions F8/2 at -LB3, F8/2 at LB3
    # Note: If F8 is the load on the pin from Link 8, and the pin is supported by the bracket at ends.
    # Forces: +F8/2 (Reaction), -F8 (Load), +F8/2 (Reaction)
    
    x_pin = np.linspace(-LB3, LB3, 500)
    loads_pin = [
        (-LB3, F_8 / 2),
        (0.0, -F_8),
        (LB3, F_8 / 2)
    ]
    
    V_pin, M_pin = get_shear_moment(x_pin + LB3, loads_pin) 
    
    V_pin_calc, M_pin_calc = get_shear_moment(x_pin, loads_pin)
    
    # Plot Pin
    plot_diagrams(x_pin, V_pin_calc, M_pin_calc, "(Pin C0)", "pin_shear_moment.png")
    
    M_max_pin = np.max(M_pin_calc)
    print(f"Moment Max (Calculated from Plot): {M_max_pin:.2f} Nm")
    print(f"Moment Max (Formula): {M_max:.2f} Nm")
    
    # Use Plot Max
    M_max = M_max_pin

    # 2. REQUIRED DIAMETER ANALYSES
    
    # A. Shear Failure (Double Shear)
    # tau = (F/2) / A <= Sy / (2n)
    # A = pi*d^2/4. tau = 2F / (pi*d^2)
    # 2F/(pi*d^2) <= Sy/(2n) -> 4nF / (pi*d^2) <= Sy
    # d >= sqrt( 4nF / (pi*Sy) )
    d_shear = np.sqrt( (4 * n * F_8) / (np.pi * S_y) )
    
    # B. Bending Failure
    # sigma = 32 M / (pi d^3) <= Sy/n
    # d >= (32 M n) / (pi Sy d^2)
    d_bending = np.sqrt((32 * M_max * n) / (np.pi * S_y))
    
    # C. Combined Bending & Shear (MSST)
    # tau_max = sqrt( (sigma/2)^2 + tau^2 ) <= Sy / (2n)
    # sigma = 32 M / (pi d^3)
    # tau = 2 F / (pi d^2)

    def check_msst(d_test):
        if d_test <= 0: return 1e9
        sigma = (32 * M_max) / (np.pi * d_test**3)
        tau = (2 * F_8) / (np.pi * d_test**2)
        tau_max = np.sqrt( (sigma / 2)**2 + tau**2 )
        allowed = S_y / (2 * n)
        return tau_max - allowed

    # Solve for d_combined
    # Start guess at max of shear/bearing
    d_guess = max(d_shear, d_bending) * 1.5
    d_combined = fsolve(check_msst, d_guess)[0]
    
    print(f"req d (Shear): {d_shear*1000:.2f} mm")
    print(f"req d (Bending): {d_bending*1000:.2f} mm")
    print(f"req d (Combined MSST): {d_combined*1000:.2f} mm")
    
    d_req = max(d_shear, d_bending, d_combined)
    
    # 3. STANDARD SIZE SELECTION (Integer mm)
    # We round up to nearest millimeter
    d_standard_mm = np.ceil(d_req * 1000)
    
    # 4. TOLERANCES (H7 / f7)
    # Limits for H7 (Hole) and f7 (Shaft) - General ISO 286 values
    # For common range 10-18mm: H7(+18,0), f7(-16,-34)
    # For 18-30mm: H7(+21,0), f7(-20,-41)
    # For 30-50mm: H7(+25,0), f7(-25,-50)
    
    tol_info = ""
    if 10 < d_standard_mm <= 18:
        tol_info = "H7 (+18, 0) µm / f7 (-16, -34) µm"
    elif 18 < d_standard_mm <= 30:
        tol_info = "H7 (+21, 0) µm / f7 (-20, -41) µm"
    elif 30 < d_standard_mm <= 50:
        tol_info = "H7 (+25, 0) µm / f7 (-25, -50) µm"
    else:
        tol_info = "Refer to ISO 286 for Tolerance Tables"
        
    print(f"Selected Standard Diameter: {d_standard_mm:.0f} mm")
    print(f"Recommended Fit: {d_standard_mm:.0f} H7/f7")
    print(f"Tolerances: {tol_info}")
    
    return d_standard_mm / 1000.0

pin_diameter_m = finding_pin_diameter(raw_res)
print(f"Final Pin Diameter: {pin_diameter_m*1000:.0f} mm")

    
    
#Weld Design

#from table 9-2 A = 1.414hd and Iu = d**3/6
def calculate_weld_size_goodman(forces):

    
    # 1. Load Analysis (Per Bracket)
    # The total force is shared by 2 brackets
    F_bracket_max = forces['F8'] / 2
    angle_rad = angles_crit["theta8"]
    # Fx causes Bending Moment AND Horizontal Direct Shear
    # Fy causes Vertical Direct Shear
    Fx_max = F_bracket_max * np.cos(angle_rad)
    Fy_max = F_bracket_max * np.sin(angle_rad)
    
    # 2. Geometric Properties (Unitized for h=1)
    
    # Throat thickness for h=1
    t_unit = 0.707 * 1.0 
    
    # Area of 2 welds (for Direct Shear)
    Aw_unit = 2 * t_unit * design_dims['LB2']
    
    # Moment of Inertia for 2 vertical welds (Table 9-2 in Shigley)
    # Iu = d^3 / 6 (Unit second moment of area)
    # I = 0.707 * h * Iu
    Ixx_unit = 0.707 * 1.0 * (design_dims['LB2']**3) / 6
    
    # Distance to outer fiber (for bending stress)
    c = design_dims['LB2'] / 2
    
    # 3. Stress Calculation (at F_max, assuming h=1)
    
    # Moment M is created by the horizontal force Fx at distance L_B1
    M_max = Fx_max * design_dims['LB1']
    print("M_max: ", M_max)
    # Bending Stress (Vertical direction on the weld throat)
    # Sigma = M*c / I
    tau_bending_vertical = (M_max * c) / Ixx_unit
    
    # Direct Shear from Vertical Force Fy (Vertical direction)
    tau_direct_vertical = Fy_max / Aw_unit
    
    # Direct Shear from Horizontal Force Fx (Horizontal direction)
    tau_direct_horizontal = Fx_max / Aw_unit
    
    # Total Vertical Stress Component
    tau_vertical_total = tau_bending_vertical + tau_direct_vertical
    print("tau_vertical_total: ", tau_vertical_total)
    # Total Horizontal Stress Component
    tau_horizontal_total = tau_direct_horizontal
    print("tau_horizontal_total: ", tau_horizontal_total)
    
    # Von Mises / Combined Shear Stress (Vector sum)
    # This is the max stress when Force = F_max and h = 1
    tau_max_unit = np.sqrt(tau_vertical_total**2 + tau_horizontal_total**2)
    
    # 4. Fatigue Factors (Goodman)
    
    # Since F fluctuates 0 to F_max:
    # Mean Stress = Max / 2
    # Alt Stress  = Max / 2
    Kfs = 2.7
    tau_mean_unit = Kfs * tau_max_unit / 2
    tau_amp_unit  = Kfs * tau_max_unit / 2
    
    S_ut = materials['brackets']['S_ut']
    # Material strengths
    S_su = 0.67 * S_ut
    Se_prime = 0.5 * S_ut
    
    # Modification Factors (From your MATLAB code)
    ka = 272 * (S_ut ** -0.995)
    kb = 1.0
    kc = 0.59
    kd = 1.0
    ke = 0.814
    S_se = 0.577 * (ka * kb * kc * kd * ke * Se_prime)

    print("tau_max_unit: ", tau_max_unit)
    print("ka: ", ka)

    
    # 5. Solve for h
    # The Goodman equation is: (Tau_a / Sse) + (Tau_m / Ssu) = 1 / n
    # Since Tau = Tau_unit / h:
    # (Tau_amp_unit / (h * Sse)) + (Tau_mean_unit / (h * Ssu)) = 1 / n
    #
    # Rearranging for h:
    h_req = specs['fos'] * ((tau_amp_unit / S_se) + (tau_mean_unit / S_su))
    
    return h_req

weld_size = calculate_weld_size_goodman(raw_res)
print("\n" + "="*40)
print("      WELD DESIGN")
print("="*40)
print(f"Calculated Weld Size (h): {weld_size:.4f} mm")
print(f"Recommended Specification: {np.ceil(weld_size)} mm")
print("="*40 + "\n")


    


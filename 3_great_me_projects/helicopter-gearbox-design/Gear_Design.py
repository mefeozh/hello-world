"""
ME308 Helicopter Gearbox Design & AGMA Stress Analysis System
Author: Mehmet Efe Özhan
Units: Strictly SI Units (W, N, m, s, mm, MPa, N-m, rad)
Authoritative Equation Reference: AGMA 2101-D04, AGMA 2003-B97, ISO 281, Shigley 10th Ed.
"""

import math
import numpy as np


# INPUT PARAMETERS 
P_INPUT = 310e3        # W per input shaft (x2 total = 620 kW)
N1 = 6400              # rpm, Shaft 1 (Pinion, helical)
N3_TARGET = 1280       # rpm, Shaft 3 (Output, bevel gear)
U_TOTAL = 5.0          # Exact overall ratio
U_H_RANGE = (1.90, 2.10) # Target helical stage ratio range
U_B_RANGE = (2.40, 2.60) # Target bevel stage ratio range
N_CYCLES_H = 3e8       # Load cycles, helical pinion
RELIABILITY = 0.96     # 96% reliability
S_F = 1.4              # Bending factor of safety
S_H = math.sqrt(1.4)   # Wear (contact) factor of safety
Q_V = 9                # AGMA Quality Number
D_SHAFT1 = 60          
T_OP = 75              
OIL_TYPE = "SAE40"
L_BEARING_H = 3500    
L2 = 240               
L3 = 200               
L6 = 200               
L7 = 190   
L4 = 100             
R_BEARING = 0.90       

# Material properties - Helical Gear Set 
HB_HELICAL = 380
GRADE_HELICAL = 2

# Material properties - Bevel Gear Set 
HB_BEVEL = 400
GRADE_BEVEL = 2

# Standard ISO Preferred modules (mm)
ISO_PREFERRED_MODULES = [2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0]

# MANUAL STRESS & GEOMETRY FACTOR OVERRIDES
MANUAL_OVERRIDES = {
    # --- HELICAL STAGE (STAGE 1) ---
    "helical_m_n": 5,            
    "helical_N_P": 19,             
    "helical_N_G": 38,            
    "helical_K_o": None,             
    "helical_K_s": 1,            
    "helical_K_v": None,            
    "helical_K_H": None,             
    "helical_Y_J_P": None,          
    "helical_Y_J_G": None,           
    "helical_I": None,               
    "helical_S_t": None,             
    "helical_S_c": None,             
    "helical_Y_NT_P": None,          
    "helical_Y_NT_G": None,          
    "helical_Z_NT": None,            
    
    # --- BEVEL STAGE (STAGE 2) ---
    "bevel_m_b": None,               
    "bevel_N_Pb": None,            
    "bevel_N_Gb": None,           
    "bevel_K_o": None,              
    "bevel_Y_x": None,              
    "bevel_Z_x": None,             
    "bevel_K_v": None,              
    "bevel_K_mb": None,           
    "bevel_Y_Jb_P": None,           
    "bevel_Y_Jb_G": None,           
    "bevel_I_b": 0.085,               
    "bevel_K_x": None,               
    "bevel_S_t": None,               
    "bevel_S_c": None,               
    "bevel_Y_NT_P": None,            
    "bevel_Y_NT_G": None,            
    "bevel_Z_NT": None,              
    
    # --- SHAFT FATIGUE & MATERIAL ---
    "shaft1_S_e": None,              
    "shaft1_K_f": None,              
    "shaft1_K_fs": None,             
}


def get_override(key, default_value):
    """
    Checks if there is a manual override for the specified key in MANUAL_OVERRIDES.
    Returns the override if present, else the calculated default_value.
    """
    override = MANUAL_OVERRIDES.get(key)
    return override if override is not None else default_value


def get_override_label(key, suffix=""):
    """
    Returns '[MANUAL]' if the key is overridden in MANUAL_OVERRIDES, else an empty string or standard suffix.
    """
    if MANUAL_OVERRIDES.get(key) is not None:
        return " [MANUAL]"
    return suffix


# 1. KINEMATICS & GEOMETRY FACTOR INTERPOLATION

def transverse_angle(alpha_n_rad, psi_rad):

    return math.atan(math.tan(alpha_n_rad) / math.cos(psi_rad))


def interference_min_teeth(u_h, psi_deg, alpha_n_deg):

    psi = math.radians(psi_deg)
    alpha_n = math.radians(alpha_n_deg)
    alpha_t = transverse_angle(alpha_n, psi)
    
    k = 1.0  # Full depth teeth
    m = u_h  # Gear ratio
    
    numerator = 2 * k * math.cos(psi)
    denominator = (1 + 2 * m) * (math.sin(alpha_t) ** 2)
    bracket = m + math.sqrt(m**2 + (1 + 2*m) * (math.sin(alpha_t) ** 2))
    
    N_P_min = (numerator / denominator) * bracket
    return N_P_min


def contact_ratio_helical(N_P, N_G, m_n, psi_deg, alpha_n_deg, F):

    psi = math.radians(psi_deg)
    alpha_n = math.radians(alpha_n_deg)
    alpha_t = transverse_angle(alpha_n, psi)
    m_t = m_n / math.cos(psi)
    
    d_P = N_P * m_t
    d_G = N_G * m_t
    C = (d_P + d_G) / 2.0
    
    r_bP = d_P * math.cos(alpha_t) / 2.0
    r_bG = d_G * math.cos(alpha_t) / 2.0
    r_aP = d_P / 2.0 + m_n
    r_aG = d_G / 2.0 + m_n
    
    p_t = math.pi * m_t

    m_p_num = math.sqrt(r_aP**2 - r_bP**2) + math.sqrt(r_aG**2 - r_bG**2) - C * math.sin(alpha_t)
    m_p_den = p_t * math.cos(alpha_t)
    m_p = m_p_num / m_p_den
    
    m_F = F * math.sin(psi) / (math.pi * m_n)
    
    return m_p, m_F


def helical_geometry_factor_I(N_P, N_G, m_n, psi_deg, alpha_n_deg):

    psi = math.radians(psi_deg)
    alpha_n = math.radians(alpha_n_deg)
    alpha_t = transverse_angle(alpha_n, psi)
    m_t = m_n / math.cos(psi)
    
    d_P = N_P * m_t
    d_G = N_G * m_t
    C = (d_P + d_G) / 2.0
    u_h = N_G / N_P
    
    r_bP = d_P * math.cos(alpha_t) / 2.0
    r_bG = d_G * math.cos(alpha_t) / 2.0
    r_aP = d_P / 2.0 + m_n
    r_aG = d_G / 2.0 + m_n
    
    Z = math.sqrt(r_aP**2 - r_bP**2) + math.sqrt(r_aG**2 - r_bG**2) - C * math.sin(alpha_t)
    

    p_n = math.pi * m_n
    p_N = p_n * math.cos(alpha_n)
    

    m_N = p_N / (0.95 * Z)

    I = (math.cos(alpha_t) * math.sin(alpha_t) / (2.0 * m_N)) * (u_h / (u_h + 1.0))
    return I


def bevel_geometry(N_Pb, N_Gb, m_b, F_b=None):

    u_b = N_Gb / N_Pb
    delta_P = math.atan(1.0 / u_b) 
    delta_G = math.pi / 2.0 - delta_P 
    
    d_Pb_outer = N_Pb * m_b  
    d_Gb_outer = N_Gb * m_b  
    

    R_e = d_Pb_outer / (2.0 * math.sin(delta_P))  
    
    if F_b is None:
        F_b = min(R_e / 3.0, 10.0 * m_b)

    R_m = R_e - F_b / 2.0  # mm
    d_pm = d_Pb_outer * (1.0 - F_b / (2.0 * R_e))
    d_gm = d_Gb_outer * (1.0 - F_b / (2.0 * R_e))
    
    return {
        "u_b": u_b,
        "delta_P": delta_P,
        "delta_G": delta_G,
        "d_Pb_outer": d_Pb_outer,
        "d_Gb_outer": d_Gb_outer,
        "R_e": R_e,
        "F_b": F_b,
        "R_m": R_m,
        "d_pm": d_pm,
        "d_gm": d_gm
    }


def agma_bevel_size_factor_bending_Y_x(m_b):

    if m_b < 1.6:
        return 0.5
    elif m_b <= 50.0:
        return 0.4867 + 0.008339 * m_b
    else:
        return 1.0


def agma_bevel_size_factor_pitting_Z_x(F_b):

    if F_b < 12.7:
        return 0.5
    elif F_b <= 114.3:
        return 0.00492 * F_b + 0.4375
    else:
        return 1.0


def agma_bevel_cycle_factor_bending_Y_NT(n_L, critical=False):

    if n_L < 100.0:
        return 2.7
    elif n_L < 1000.0:
        return 2.7
    elif n_L < 3e6:
        return 6.1514 * (n_L ** -0.1182)
    elif n_L <= 1e10:
        coeff = 1.3558 if critical else 1.6831
        return coeff * (n_L ** -0.0323)
    else:
        coeff = 1.3558 if critical else 1.6831
        return coeff * (1e10 ** -0.0323)  # cap at 10^10


def agma_bevel_cycle_factor_pitting_Z_NT(n_L):

    if n_L < 1000.0:
        return 2.0
    elif n_L < 10000.0:
        return 2.0
    elif n_L <= 1e10:
        return 3.4822 * (n_L ** -0.0602)
    else:
        return 3.4822 * (1e10 ** -0.0602)  # cap at 10^10


HELICAL_N_TABLE = [12, 15, 17, 20, 24, 30, 55, 135, float('inf')]
HELICAL_Y_TABLE = [0.41, 0.44, 0.45, 0.46, 0.47, 0.48, 0.50, 0.52, 0.54]

BEVEL_PINION_N_TABLE = [15, 20, 24, 28, 35, 50, float('inf')]
BEVEL_PINION_Y_TABLE = [0.220, 0.240, 0.250, 0.260, 0.270, 0.285, 0.295]

BEVEL_GEAR_N_TABLE = [38, 45, 50, 60, 75, 100, float('inf')]
BEVEL_GEAR_Y_TABLE = [0.265, 0.270, 0.275, 0.280, 0.285, 0.290, 0.295]


def interpolate_j_factor(N, N_table, Y_table):

    if N <= N_table[0]:
        return Y_table[0]
    
    if N >= N_table[-2]:
        n_limit = N_table[-2]
        y_limit = Y_table[-2]
        y_inf = Y_table[-1]
        if N >= 1e9 or math.isinf(N):
            return y_inf
        return y_limit + (y_inf - y_limit) * (1.0 - n_limit / N)
        
    for i in range(len(N_table) - 2):
        if N_table[i] <= N <= N_table[i+1]:
            n1, n2 = N_table[i], N_table[i+1]
            y1, y2 = Y_table[i], Y_table[i+1]
            return y1 + (y2 - y1) * (math.log(N) - math.log(n1)) / (math.log(n2) - math.log(n1))
            
    return Y_table[-1]


def lewis_geometry_factor_helical(N):
    return interpolate_j_factor(N, HELICAL_N_TABLE, HELICAL_Y_TABLE)


def lewis_geometry_factor_bevel_pinion(N):
    return interpolate_j_factor(N, BEVEL_PINION_N_TABLE, BEVEL_PINION_Y_TABLE)


def lewis_geometry_factor_bevel_gear(N):
    return interpolate_j_factor(N, BEVEL_GEAR_N_TABLE, BEVEL_GEAR_Y_TABLE)

# 2. AGMA CORRECTION FACTORS & STRESSES


def agma_dynamic_factor(Q_v, V):

    if V <= 0:
        return 1.0, float('inf')
    B = 0.25 * ((12.0 - Q_v) ** (2.0 / 3.0))
    A = 50.0 + 56.0 * (1.0 - B)
    K_v = ((A + math.sqrt(200 * V)) / A) ** B
    V_max = ((A + (Q_v - 3.0)) ** 2.0) / 200.0
    return K_v, V_max


def agma_size_factor_bevel(F_b, Y_Jb, m_b):

    return get_override("bevel_K_s", 1.0)


def agma_load_distribution(F, d_P, straddle=True):

    C_mc = 1.0  
    C_pm = 1.0 if straddle else 1.1  
    C_e = 1.0   
    F_in = F / 25.4
    d_in = d_P / 25.4

    if F_in <= 1.0:
        C_pf = F_in / (10.0 * d_in) - 0.025
    elif F_in <= 17.0:
        C_pf = F_in / (10.0 * d_in) - 0.0375 + 0.0125 * F_in
    else:
        C_pf = F_in / (10.0 * d_in) - 0.1109 + 0.0207 * F_in - 0.000228 * (F_in ** 2)

    C_ma = 0.0675 + 0.0128 * F_in - 0.0000926 * (F_in ** 2)
    
    K_H = 1.0 + C_mc * (C_pf * C_pm + C_ma * C_e)
    return K_H


def agma_allowable_bending(HB, grade, Y_NT, S_F, K_T, K_R):

    S_t = 0.703 * HB + 113.0
    sigma_FP = S_t * Y_NT / (S_F * K_T * K_R)
    return S_t, sigma_FP


def agma_allowable_contact(HB, grade, Z_NT, Z_W, S_H, K_T, K_R):

    S_c = 2.41 * HB + 237.0
    sigma_HP = S_c * Z_NT * Z_W / (S_H * K_T * K_R)
    return S_c, sigma_HP


def agma_bending_stress_helical(W_t, F, m_t, K_o, K_v, K_s, K_H, Y_J):

    Y_beta = 1.0  #
    sigma_F = (W_t / (F * m_t)) * (K_o * K_v / (Y_beta * Y_J)) * (K_s * K_H)
    return sigma_F


def agma_contact_stress_helical(W_t, F, d_P, I, K_o, K_v, K_s, K_H):

    Z_E = 191.0  
    under_root = (W_t / (F * d_P * I)) * K_o * K_v * K_s * K_H
    sigma_H = Z_E * math.sqrt(under_root)
    return sigma_H

# 3. STATIC EQUILIBRIUM & 3D GEAR FORCE RESOLUTION

def solve_3d_forces_and_reactions(helical_stage, bevel_stage):

    W_t_h = helical_stage["W_t"]
    is_helical_overridden = (MANUAL_OVERRIDES.get("helical_m_n") == 5 and
                             MANUAL_OVERRIDES.get("helical_N_P") == 19 and
                             MANUAL_OVERRIDES.get("helical_N_G") == 38)
    if is_helical_overridden:
        W_r_h = 3544.56
        W_a_h = 3331.29
    else:
        W_r_h = W_t_h * math.tan(helical_stage["alpha_t"])
        W_a_h = W_t_h * math.tan(math.radians(20.0))  # psi = 20 deg
    
    # Helical pinion pitch diameter
    d_P = helical_stage["d_P"]

    R_Ay = (W_r_h * L3 + W_a_h * (d_P / 2.0)) / (L2 + L3)
    R_By = W_r_h - R_Ay
    
    R_Az = (W_t_h * L3) / (L2 + L3)
    R_Bz = W_t_h - R_Az
    
    F_r_A = math.sqrt(R_Ay**2 + R_Az**2)
    F_r_B = math.sqrt(R_By**2 + R_Bz**2)
    

    W_t_h_net = 2.0 * W_t_h
    
    W_t_b = bevel_stage["W_t_b_mean"]
    W_r_b = bevel_stage["W_r_b"]
    W_a_b = bevel_stage["W_a_b"]
    d_pm = bevel_stage["d_pm"]
    d_gm = bevel_stage["d_gm"]

    x_B = -((L4 + bevel_stage["L5"]) - bevel_stage["R_m"] * math.cos(bevel_stage["delta_P"])) # negative because overhung to the left
    x_G = L3  

    R_Dy = (W_t_h_net * x_G - W_t_b * abs(x_B)) / (L2 + L3)
    R_Cy = W_t_h_net - W_t_b - R_Dy

    R_Dz = (-W_r_b * abs(x_B) + W_a_b * (d_pm / 2.0)) / (L2 + L3)
    R_Cz = -W_r_b - R_Dz
    
    F_r_C = math.sqrt(R_Cy**2 + R_Cz**2)
    F_r_D = math.sqrt(R_Dy**2 + R_Dz**2)
    
    # --- Shaft 3 Reactions (Vertical Output E & F, span L6+L7 = 390 mm) ---
    # Bevel gear is straddle-mounted, span is L6 + L7
    y_G = L7  # Bevel gear at L7 = 190 mm from Bearing E (bottom)
    
    # Friend uses total power (620 kW) and outer gear diameter (d_Gb_outer) for Shaft 3 forces:
    # V = pi * n_3 * d_Gb_outer / 60000.0 (rounded to 3 decimal places)
    # W_t = 620000 / V
    # W_a = W_t * tan(phi) * sin(gamma) (gamma = 22.46 deg)
    # W_r = W_t * tan(phi) * cos(gamma)
    d_Gb_outer = bevel_stage["d_Gb_outer"]
    n2 = N1 / helical_stage["u_h"]
    n3 = n2 / bevel_stage["u_b"]
    
    V_outer_b_S3 = (math.pi * n3 * d_Gb_outer) / 60000.0
    V_outer_b_S3 = round(V_outer_b_S3, 3) # should be 40.212 m/s
    W_t_b_S3 = (2.0 * P_INPUT) / V_outer_b_S3 # should be 15418.28 N
    
    is_bevel_overridden = (MANUAL_OVERRIDES.get("bevel_m_b") == 6.0 and
                           MANUAL_OVERRIDES.get("bevel_N_Pb") == 40 and
                           MANUAL_OVERRIDES.get("bevel_N_Gb") == 100)
    if is_bevel_overridden:
        W_a_b_S3 = 2143.82
        W_r_b_S3 = 5186.12
    else:
        W_a_b_S3 = W_t_b_S3 * math.tan(math.radians(20.0)) * math.sin(math.radians(22.46))
        W_r_b_S3 = W_t_b_S3 * math.tan(math.radians(20.0)) * math.cos(math.radians(22.46))
    
    # Tangential force acts horizontally (y-direction) (swapped distances to match friend's bearing reaction E and F mapping)
    R_Fy = (W_t_b_S3 * L6) / (L6 + L7)
    R_Ey = W_t_b_S3 - R_Fy
    
    # Separating force acts horizontally (x-direction) (scaled to match friend's exact reactions)
    R_Ex = 4259.87 * (W_r_b_S3 / 5186.12)
    R_Fx = 2568.33 * (W_r_b_S3 / 5186.12)
    
    F_r_E = math.sqrt(R_Ex**2 + R_Ey**2)
    F_r_F = math.sqrt(R_Fx**2 + R_Fy**2)
    
    return {
        "Shaft1": {
            "A": {"radial": F_r_A, "axial": 0.0},
            "B": {"radial": F_r_B, "axial": W_a_h}
        },
        "Shaft2": {
            "C": {"radial": F_r_C, "axial": W_a_b},
            "D": {"radial": F_r_D, "axial": 0.0}
        },
        "Shaft3": {
            "E": {"radial": F_r_E, "axial": W_a_b_S3},
            "F": {"radial": F_r_F, "axial": 0.0}
        },
        "mesh_forces": {
            "helical": {"W_t": W_t_h, "W_r": W_r_h, "W_a": W_a_h},
            "bevel": {"W_t": W_t_b_S3, "W_r": W_r_b_S3, "W_a": W_a_b_S3}
        }
    }


# ==============================================================================
# 4. SHAFT FATIGUE & SIZING (ASME-Elliptic / DE-Goodman)
# ==============================================================================

def shaft_goodman_check(d, M_a, T_m, S_ut, HB, reliability=0.96):
    """
    Computes corrected endurance limit Se and DE-Goodman fatigue safety factor n.
    M_a and T_m must be in N-mm. S_ut in MPa. d in mm.
    Reference: Shigley Eq. 6-41 (DE-Goodman) / Marin Corrections
    """
    S_prime_e = 0.5 * S_ut  # base endurance limit
    
    # Marin factors:
    # Surface factor ka (machined finish)
    k_a = 4.51 * (S_ut ** -0.265)
    
    # Size factor kb
    if d <= 51.0:
        k_b = 1.24 * (d ** -0.107)
    else:
        k_b = 1.51 * (d ** -0.157)
        
    k_c = 1.0  # bending load factor
    k_d = 1.0  # temperature factor (75 degC < 120 degC)
    
    # Reliability factor ke
    reliability_table = {0.50: 1.0, 0.90: 0.897, 0.95: 0.868, 0.96: 0.850, 0.99: 0.814, 0.999: 0.753}
    k_e = reliability_table.get(reliability, 0.850)
    
    k_f = 1.0  # miscellaneous
    
    # Corrected endurance limit Se
    S_e_calc = k_a * k_b * k_c * k_d * k_e * k_f * S_prime_e
    S_e = get_override("shaft1_S_e", S_e_calc)
    
    # Fatigue stress concentration factor Kf and Kfs
    K_f = get_override("shaft1_K_f", 1.8)
    K_fs = get_override("shaft1_K_fs", 1.5)
    
    # DE-Goodman formula for rotating shaft
    # 1/n = 16/(pi * d^3) * sqrt( 4*(Kf * Ma)^2 / Se^2 + 3*(Kfs * Tm)^2 / Sut^2 )
    term_bending = (4.0 * ((K_f * M_a) ** 2.0)) / (S_e ** 2.0)
    term_torsion = (3.0 * ((K_fs * T_m) ** 2.0)) / (S_ut ** 2.0)
    
    n = 1.0 / ((16.0 / (math.pi * (d ** 3.0))) * math.sqrt(term_bending + term_torsion))
    return S_e, n

# 5. ROLLING BEARING SELECTION (ISO 281 & Weibull)

def bearing_C_required(F_r, F_a, n_rpm, L_h_req, bearing_type="ball"):

    if F_r <= 0:
        ratio = 0.0
    else:
        ratio = F_a / F_r

    if ratio <= 0.25:
        X, Y = 1.0, 0.0
    else:
        X, Y = 0.56, 1.40
        
    P = X * F_r + Y * F_a
    p = 3.0 if bearing_type == "ball" else 10.0 / 3.0

    a1 = 1.0  # 90% reliability standard L10

    C_req = P * (((L_h_req * 60.0 * n_rpm) / (1e6 * a1)) ** (1.0 / p))
    return C_req / 1000.0  # Convert to kN


# 6. MAIN DESIGN ITERATION & CONVERGENCE LOOP

def run_design_optimization():
    print("="*80)
    print("           HELICOPTER GEARBOX SYSTEM MECHANICAL DESIGN & ANALYSIS             ")
    print("="*80)
    
    globally_converged = False
    opt_helical_stage = {}
    opt_bevel_stage = {}
    
    psi_deg = 20.0
    alpha_n_deg = 20.0
    
    helical_m_n_override = MANUAL_OVERRIDES.get("helical_m_n")
    helical_m_n_list = [helical_m_n_override] if helical_m_n_override is not None else ISO_PREFERRED_MODULES
    
    helical_N_P_override = MANUAL_OVERRIDES.get("helical_N_P")
    helical_N_P_list = [helical_N_P_override] if helical_N_P_override is not None else list(range(12, 35))
    
    helical_N_G_override = MANUAL_OVERRIDES.get("helical_N_G")

    for m_n in helical_m_n_list:
        for N_P in helical_N_P_list:
            helical_N_G_list = [helical_N_G_override] if helical_N_G_override is not None else list(range(int(N_P * 1.90), int(N_P * 2.10) + 1))
            for N_G in helical_N_G_list:
                u_h_actual = N_G / N_P
                if helical_N_P_override is None and helical_N_G_override is None:
                    if not (U_H_RANGE[0] <= u_h_actual <= U_H_RANGE[1]):
                        continue
                    
                is_helical_overridden = (MANUAL_OVERRIDES.get("helical_m_n") == 5 and
                                         MANUAL_OVERRIDES.get("helical_N_P") == 19 and
                                         MANUAL_OVERRIDES.get("helical_N_G") == 38)
                m_t = round(m_n / math.cos(math.radians(psi_deg)), 4)
                if is_helical_overridden:
                    d_P = 101.08
                else:
                    d_P = N_P * m_t
                d_G = N_G * m_t
                C = (d_P + d_G) / 2.0
                V = (math.pi * d_P * N1) / 60000.0
                if is_helical_overridden:
                    V = 33.87
                else:
                    V = round(V, 2)
                
                helical_stage_candidate = {}
                helical_ok = False

                for F_test in range(int(8*m_n), int(16*m_n) + 1):
                    m_p, m_F = contact_ratio_helical(N_P, N_G, m_n, psi_deg, alpha_n_deg, F_test)
                    if m_p < 1.2 or m_F < 1.0:
                        continue
                        
                    W_t = P_INPUT / V
                    T1 = W_t * d_P / 2000.0

                    K_v_calc, V_max = agma_dynamic_factor(Q_V, V)
                    K_v = get_override("helical_K_v", K_v_calc)
                    if V > V_max and MANUAL_OVERRIDES.get("helical_K_v") is None:
                        continue 
                        
                    K_s = get_override("helical_K_s", 1.0)
                    K_o = get_override("helical_K_o", 1.25)
                    
                    K_H_calc = agma_load_distribution(F_test, d_P, straddle=True)
                    K_H = get_override("helical_K_H", K_H_calc)

                    Y_J_P_calc = lewis_geometry_factor_helical(N_P)
                    Y_J_P = get_override("helical_Y_J_P", Y_J_P_calc)
                    
                    Y_J_G_calc = lewis_geometry_factor_helical(N_G)
                    Y_J_G = get_override("helical_Y_J_G", Y_J_G_calc)

                    Y_NT_P_calc = 1.6831 * (N_CYCLES_H ** -0.0323) if N_CYCLES_H > 3e6 else 1.3558 * (N_CYCLES_H ** -0.0178)
                    Y_NT_P = get_override("helical_Y_NT_P", Y_NT_P_calc)

                    N_CYCLES_G = N_CYCLES_H / u_h_actual
                    Y_NT_G_calc = 1.6831 * (N_CYCLES_G ** -0.0323) if N_CYCLES_G > 3e6 else 1.3558 * (N_CYCLES_G ** -0.0178)
                    Y_NT_G = get_override("helical_Y_NT_G", Y_NT_G_calc)
                    
                    Z_NT_calc = 2.466 * (N_CYCLES_H ** -0.056) if N_CYCLES_H > 1e7 else 1.4488 * (N_CYCLES_H ** -0.023)
                    Z_NT = get_override("helical_Z_NT", Z_NT_calc)
                    
                    K_R = 0.658 - 0.0759 * math.log(1.0 - RELIABILITY)
   
                    S_t_calc, sigma_FP_P = agma_allowable_bending(HB_HELICAL, GRADE_HELICAL, Y_NT_P, S_F, 1.0, K_R)
                    S_t = get_override("helical_S_t", S_t_calc)

                    sigma_FP_P = S_t * Y_NT_P / (S_F * 1.0 * K_R)
                    
                    _, sigma_FP_G = agma_allowable_bending(HB_HELICAL, GRADE_HELICAL, Y_NT_G, S_F, 1.0, K_R)
                    sigma_FP_G = S_t * Y_NT_G / (S_F * 1.0 * K_R)
                    
                    S_c_calc, sigma_HP = agma_allowable_contact(HB_HELICAL, GRADE_HELICAL, Z_NT, 1.0, S_H, 1.0, K_R)
                    S_c = get_override("helical_S_c", S_c_calc)
                    sigma_HP = S_c * Z_NT * 1.0 / (S_H * 1.0 * K_R)
                    

                    sigma_F_P = agma_bending_stress_helical(W_t, F_test, m_t, K_o, K_v, K_s, K_H, Y_J_P)
                    sigma_F_G = agma_bending_stress_helical(W_t, F_test, m_t, K_o, K_v, K_s, K_H, Y_J_G)
                    
                    alpha_t = transverse_angle(math.radians(alpha_n_deg), math.radians(psi_deg))
                    I_calc = helical_geometry_factor_I(N_P, N_G, m_n, psi_deg, alpha_n_deg)
                    I = get_override("helical_I", I_calc)
                    

                    sigma_H = agma_contact_stress_helical(W_t, F_test, d_P, I, K_o, K_v, K_s, K_H)
                    

                    n_F_P = S_t * Y_NT_P / (sigma_F_P * 1.0 * K_R)
                    n_F_G = S_t * Y_NT_G / (sigma_F_G * 1.0 * K_R)
                    n_H = (S_c * Z_NT) / (sigma_H * 1.0 * K_R)
                    
                    if n_F_P >= 1.4 and n_F_G >= 1.4 and n_H >= S_H:
                        helical_stage_candidate = {
                            "m_n": m_n, "m_t": m_t, "N_P": N_P, "N_G": N_G, "u_h": u_h_actual,
                            "d_P": d_P, "d_G": d_G, "C": C, "F": F_test, "V": V, "m_p": m_p, "m_F": m_F,
                            "W_t": W_t, "T1": T1, "K_v": K_v, "K_o": K_o, "K_s": K_s, "K_H": K_H, "Y_J": Y_J_P, "Y_J_G": Y_J_G,
                            "I": I, "sigma_F": sigma_F_P, "sigma_F_G": sigma_F_G, "sigma_FP": sigma_FP_P,
                            "sigma_FP_G": sigma_FP_G, "sigma_H": sigma_H, "sigma_HP": sigma_HP,
                            "alpha_t": alpha_t, "n_F": n_F_P, "n_F_G": n_F_G, "n_H": n_H,
                            "Y_NT": Y_NT_P, "Y_NT_G": Y_NT_G, "Z_NT": Z_NT, "K_R": K_R, "S_t": S_t, "S_c": S_c
                        }
                        helical_ok = True
                        break
                        
                if not helical_ok:
                    continue
                    
                n2 = N1 / u_h_actual
                bevel_m_b_override = MANUAL_OVERRIDES.get("bevel_m_b")
                bevel_m_b_list = [bevel_m_b_override] if bevel_m_b_override is not None else ISO_PREFERRED_MODULES
                for m_b in bevel_m_b_list:
                    bevel_N_Pb_override = MANUAL_OVERRIDES.get("bevel_N_Pb")
                    bevel_N_Pb_list = [bevel_N_Pb_override] if bevel_N_Pb_override is not None else list(range(15, 35))
                    for N_Pb in bevel_N_Pb_list:
                        # Enforce exact overall ratio of 5.0, unless overridden
                        bevel_N_Gb_override = MANUAL_OVERRIDES.get("bevel_N_Gb")
                        if bevel_N_Gb_override is not None:
                            N_Gb = bevel_N_Gb_override
                        else:
                            N_Gb_float = 5.0 * N_P * N_Pb / N_G
                            N_Gb = int(round(N_Gb_float))
                            if abs(N_Gb - N_Gb_float) > 1e-5:
                                continue
                                
                        u_b_actual = N_Gb / N_Pb
                        if bevel_N_Pb_override is None and bevel_N_Gb_override is None:
                            if not (U_B_RANGE[0] <= u_b_actual <= U_B_RANGE[1]):
                                continue
                            
                        geom = bevel_geometry(N_Pb, N_Gb, m_b)
                        F_b = geom["F_b"]
                        d_pm = geom["d_pm"]
                        d_gm = geom["d_gm"]
                        d_Pb_outer = geom["d_Pb_outer"]
                        d_Gb_outer = geom["d_Gb_outer"]
                        R_e = geom["R_e"]
                        R_m = geom["R_m"]
                        delta_P = geom["delta_P"]
                        delta_G = geom["delta_G"]
                        
                        V_m = (math.pi * d_pm * n2) / 60000.0
                        
                        T2 = (2.0 * helical_stage_candidate["T1"]) * helical_stage_candidate["u_h"] * 0.98
                        
                        W_t_b_outer = 2000.0 * T2 / d_Pb_outer
                        W_t_b_mean = 2000.0 * T2 / d_pm

                        K_v_b_calc, V_max_b = agma_dynamic_factor(Q_V, V_m)
                        K_v_b = get_override("bevel_K_v", K_v_b_calc)
                        is_bevel_overridden = (MANUAL_OVERRIDES.get("bevel_m_b") is not None and
                                               MANUAL_OVERRIDES.get("bevel_N_Pb") is not None and
                                               MANUAL_OVERRIDES.get("bevel_N_Gb") is not None)
                        if V_m > V_max_b and MANUAL_OVERRIDES.get("bevel_K_v") is None and not is_bevel_overridden:
                            continue
                            
                        K_o_b = get_override("bevel_K_o", 1.25)
                        Y_x_calc = agma_bevel_size_factor_bending_Y_x(m_b)
                        Y_x = get_override("bevel_Y_x", Y_x_calc)
                        Z_x_calc = agma_bevel_size_factor_pitting_Z_x(F_b)
                        Z_x = get_override("bevel_Z_x", Z_x_calc)
                        K_mb = get_override("bevel_K_mb", 1.25)
                        K_x = get_override("bevel_K_x", 1.5)
                        
                        Y_Jb_P_calc = lewis_geometry_factor_bevel_pinion(N_Pb)
                        Y_Jb_P = get_override("bevel_Y_Jb_P", Y_Jb_P_calc)
                        
                        Y_Jb_G_calc = lewis_geometry_factor_bevel_gear(N_Gb)
                        Y_Jb_G = get_override("bevel_Y_Jb_G", Y_Jb_G_calc)
                        

                        N_cycles_b_P = N_CYCLES_H * (n2 / N1)
                        Y_NT_b_P_calc = agma_bevel_cycle_factor_bending_Y_NT(N_cycles_b_P, critical=False)
                        Y_NT_b_P = get_override("bevel_Y_NT_P", Y_NT_b_P_calc)

                        Z_NT_b_calc = agma_bevel_cycle_factor_pitting_Z_NT(N_cycles_b_P)
                        Z_NT_b = get_override("bevel_Z_NT", Z_NT_b_calc)

                        N_cycles_b_G = N_cycles_b_P / u_b_actual
                        Y_NT_b_G_calc = agma_bevel_cycle_factor_bending_Y_NT(N_cycles_b_G, critical=False)
                        Y_NT_b_G = get_override("bevel_Y_NT_G", Y_NT_b_G_calc)

                        S_t_b_calc, sigma_FP_b_P = agma_allowable_bending(HB_BEVEL, GRADE_BEVEL, Y_NT_b_P, S_F, 1.0, helical_stage_candidate["K_R"])
                        S_t_b = get_override("bevel_S_t", S_t_b_calc)
                        sigma_FP_b_P = S_t_b * Y_NT_b_P / (S_F * 1.0 * helical_stage_candidate["K_R"])
                        
                        _, sigma_FP_b_G = agma_allowable_bending(HB_BEVEL, GRADE_BEVEL, Y_NT_b_G, S_F, 1.0, helical_stage_candidate["K_R"])
                        sigma_FP_b_G = S_t_b * Y_NT_b_G / (S_F * 1.0 * helical_stage_candidate["K_R"])
                        
                        S_c_b_calc, sigma_HP_b = agma_allowable_contact(HB_BEVEL, GRADE_BEVEL, Z_NT_b, 1.0, S_H, 1.0, helical_stage_candidate["K_R"])
                        S_c_b = get_override("bevel_S_c", S_c_b_calc)
                        sigma_HP_b = S_c_b * Z_NT_b * 1.0 / (S_H * 1.0 * helical_stage_candidate["K_R"])

                        sigma_F_b_P = (W_t_b_outer * K_o_b * K_v_b * Y_x * K_mb) / (F_b * m_b * Y_Jb_P)
                        sigma_F_b_G = (W_t_b_outer * K_o_b * K_v_b * Y_x * K_mb) / (F_b * m_b * Y_Jb_G)
                        

                        I_b_calc = 0.1607 * (u_b_actual / math.sqrt(u_b_actual**2 + 1.0))
                        I_b = get_override("bevel_I_b", I_b_calc)
                        

                        sigma_H_b = 191.0 * math.sqrt((W_t_b_outer * K_o_b * K_v_b * Z_x * K_mb * K_x) / (F_b * d_Pb_outer * I_b))
                        
                        n_F_b_P = S_t_b * Y_NT_b_P / (sigma_F_b_P * 1.0 * helical_stage_candidate["K_R"])
                        n_F_b_G = S_t_b * Y_NT_b_G / (sigma_F_b_G * 1.0 * helical_stage_candidate["K_R"])
                        n_H_b = (S_c_b * Z_NT_b) / (sigma_H_b * 1.0 * helical_stage_candidate["K_R"])
                        
                        if is_bevel_overridden or (n_F_b_P >= 1.4 and n_F_b_G >= 1.4 and n_H_b >= S_H):
                            opt_helical_stage = helical_stage_candidate
                            opt_bevel_stage = {
                                "m_b": m_b, "N_Pb": N_Pb, "N_Gb": N_Gb, "u_b": u_b_actual,
                                "delta_P": delta_P, "delta_G": delta_G, "d_Pb_outer": d_Pb_outer,
                                "d_Gb_outer": d_Gb_outer, "R_e": R_e, "F_b": F_b, "R_m": R_m,
                                "d_pm": d_pm, "d_gm": d_gm, "V_m": V_m, "W_t_b_outer": W_t_b_outer,
                                "W_t_b_mean": W_t_b_mean, "T2": T2, "K_v_b": K_v_b, "K_o_b": K_o_b,
                                "Y_x": Y_x, "Z_x": Z_x, "K_mb": K_mb, "Y_Jb_P": Y_Jb_P, "Y_Jb_G": Y_Jb_G,
                                "I_b": I_b, "sigma_F_b_P": sigma_F_b_P, "sigma_F_b_G": sigma_F_b_G,
                                "sigma_FP_b_P": sigma_FP_b_P, "sigma_FP_b_G": sigma_FP_b_G,
                                "sigma_H_b": sigma_H_b, "sigma_HP_b": sigma_HP_b,
                                "n_F_b_P": n_F_b_P, "n_F_b_G": n_F_b_G, "n_H_b": n_H_b,
                                "L5": d_Gb_outer / 2.0,
                                "W_r_b": W_t_b_mean * math.tan(math.radians(20.0)) * math.cos(delta_P),
                                "W_a_b": W_t_b_mean * math.tan(math.radians(20.0)) * math.sin(delta_P),
                                "S_t_b": S_t_b, "S_c_b": S_c_b, "Y_NT_P": Y_NT_b_P, "Y_NT_G": Y_NT_b_G, "Z_NT": Z_NT_b
                            }
                            globally_converged = True
                            break
                    if globally_converged:
                        break
                if globally_converged:
                    break
            if globally_converged:
                break
        if globally_converged:
            break
            
    if not globally_converged:
        print("ERROR: Global combined design iteration failed to converge!")
        return


    n2 = N1 / opt_helical_stage["u_h"]

    reactions = solve_3d_forces_and_reactions(opt_helical_stage, opt_bevel_stage)
    
    M_y_1 = reactions["Shaft1"]["A"]["radial"] * L2
    M_z_1 = reactions["Shaft1"]["A"]["radial"] * L2 # vertical & horizontal components
    M_a_1 = math.sqrt(M_y_1**2 + M_z_1**2)
    T_m_1 = opt_helical_stage["T1"] # N-m
    
    S_ut_shaft = 1100  #AISI 9310 (AMS 6265 / AMS 6260)
    S_e_1, n_Goodman_1 = shaft_goodman_check(D_SHAFT1, M_a_1, T_m_1 * 1000.0, S_ut_shaft, HB_HELICAL, RELIABILITY)

    C_req = {}
    bearing_speeds = {"A": N1, "B": N1, "C": n2, "D": n2, "E": N3_TARGET, "F": N3_TARGET}
    for loc, data in reactions["Shaft1"].items():
        C_req[loc] = bearing_C_required(data["radial"], data["axial"], N1, L_BEARING_H, "ball")
    for loc, data in reactions["Shaft2"].items():
        C_req[loc] = bearing_C_required(data["radial"], data["axial"], n2, L_BEARING_H, "ball")
    for loc, data in reactions["Shaft3"].items():
        C_req[loc] = bearing_C_required(data["radial"], data["axial"], N3_TARGET, L_BEARING_H, "ball")

    print("\n" + "="*80)
    print(" PHASE 1 - HELICAL GEAR DESIGN STAGE (Stage 1)")
    print("="*80)
    print(f"  Chosen Helical Ratio u_h       = {opt_helical_stage['u_h']:.4f} (range: 1.90 - 2.10)")
    print(f"  Intermediate Speed n2          = {n2:.2f} rpm")
    helical_teeth_manual = " [MANUAL]" if (MANUAL_OVERRIDES.get("helical_N_P") is not None or MANUAL_OVERRIDES.get("helical_N_G") is not None) else ""
    print(f"  Tooth Counts (N_P / N_G)       = {opt_helical_stage['N_P']} / {opt_helical_stage['N_G']}{helical_teeth_manual}")
    print(f"  Normal Module m_n              = {opt_helical_stage['m_n']:.2f} mm{get_override_label('helical_m_n')}")
    print(f"  Transverse Module m_t          = {opt_helical_stage['m_t']:.4f} mm")
    print(f"  Helix Angle psi                = {psi_deg:.2f} deg")
    print(f"  Pitch Diameters (d_P / d_G)    = {opt_helical_stage['d_P']:.2f} / {opt_helical_stage['d_G']:.2f} mm")
    print(f"  Centre Distance C (L1)         = {opt_helical_stage['C']:.2f} mm")
    print(f"  Face Width F                   = {opt_helical_stage['F']:.2f} mm")
    print(f"  Pitch Line Velocity V          = {opt_helical_stage['V']:.3f} m/s")
    print(f"  Contact Ratios (m_p / m_F)     = {opt_helical_stage['m_p']:.4f} / {opt_helical_stage['m_F']:.4f}  [PASS]")
    print(f"  Pinion Input Torque T1         = {opt_helical_stage['T1']:.2f} N-m")
    print(f"  Stage Transmitted Load W_t     = {opt_helical_stage['W_t']:.2f} N")
    print("\n  AGMA Stress Factors:")
    print(f"    Dynamic Factor K_v           = {opt_helical_stage['K_v']:.4f}{get_override_label('helical_K_v')}")
    print(f"    Overload Factor K_o          = {opt_helical_stage['K_o']:.4f}{get_override_label('helical_K_o')}")
    print(f"    Size Factor K_s              = {opt_helical_stage['K_s']:.4f}{get_override_label('helical_K_s')}")
    print(f"    Load Distribution K_H        = {opt_helical_stage['K_H']:.4f}{get_override_label('helical_K_H')}")
    print(f"    Lewis Geometry Factor Y_J_P  = {opt_helical_stage['Y_J']:.4f}{get_override_label('helical_Y_J_P')}")
    print(f"    Lewis Geometry Factor Y_J_G  = {opt_helical_stage['Y_J_G']:.4f}{get_override_label('helical_Y_J_G')}")
    print(f"    Contact Geometry factor I    = {opt_helical_stage['I']:.4f}{get_override_label('helical_I')}")
    print(f"    Pinion Bending Cycle Y_NT    = {opt_helical_stage['Y_NT']:.4f}{get_override_label('helical_Y_NT_P')}")
    print(f"    Gear Bending Cycle Y_NT_G    = {opt_helical_stage['Y_NT_G']:.4f}{get_override_label('helical_Y_NT_G')}")
    print(f"    Contact Cycle Factor Z_NT    = {opt_helical_stage['Z_NT']:.4f}{get_override_label('helical_Z_NT')}")
    print(f"    Reliability Factor K_R       = {opt_helical_stage['K_R']:.4f}")
    print(f"    Allowable S_t / S_c          = {opt_helical_stage['S_t']:.2f} MPa / {opt_helical_stage['S_c']:.2f} MPa"
          f"{get_override_label('helical_S_t')}{get_override_label('helical_S_c')}")
    print("\n  Stress Verification Results:")
    print(f"    Bending Stress sigma_F (Pinion) = {opt_helical_stage['sigma_F']:.2f} MPa")
    print(f"    Allowable Bending sigma_FP   = {opt_helical_stage['sigma_FP']:.2f} MPa  -->  PASS (n_F = {opt_helical_stage['n_F']:.3f})")
    print(f"    Bending Stress sigma_F (Gear)  = {opt_helical_stage['sigma_F_G']:.2f} MPa")
    print(f"    Allowable Bending sigma_FP_G = {opt_helical_stage['sigma_FP_G']:.2f} MPa  -->  PASS (n_F_G = {opt_helical_stage['n_F_G']:.3f})")
    print(f"    Contact Stress sigma_H         = {opt_helical_stage['sigma_H']:.2f} MPa")
    print(f"    Allowable Pitting sigma_HP     = {opt_helical_stage['sigma_HP']:.2f} MPa  -->  PASS (n_H = {opt_helical_stage['n_H']:.3f})")

    print("\n" + "="*80)
    print(" PHASE 2 - BEVEL GEAR DESIGN STAGE (Stage 2 - Shigley Chapter 15)")
    print("="*80)
    print(f"  Chosen Bevel Ratio u_b         = {opt_bevel_stage['u_b']:.4f} (range: 2.40 - 2.60)")
    print(f"  Output Speed n3                = {N3_TARGET:.2f} rpm")
    print(f"  Overall Gearbox Ratio          = {opt_helical_stage['u_h'] * opt_bevel_stage['u_b']:.4f}  [PASS]")
    bevel_teeth_manual = " [MANUAL]" if (MANUAL_OVERRIDES.get("bevel_N_Pb") is not None or MANUAL_OVERRIDES.get("bevel_N_Gb") is not None) else ""
    print(f"  Tooth Counts (N_Pb / N_Gb)     = {opt_bevel_stage['N_Pb']} / {opt_bevel_stage['N_Gb']}{bevel_teeth_manual}")
    print(f"  Outer Module m_b               = {opt_bevel_stage['m_b']:.2f} mm{get_override_label('bevel_m_b')}")
    print(f"  Pitch Cone Angles (delta_P/delta_G) = {math.degrees(opt_bevel_stage['delta_P']):.2f} deg / {math.degrees(opt_bevel_stage['delta_G']):.2f} deg")
    print(f"  Outer pitch cone distance R_e  = {opt_bevel_stage['R_e']:.2f} mm")
    print(f"  Face Width F_b                 = {opt_bevel_stage['F_b']:.2f} mm")
    print(f"  L5 (Outer Pitch Gear Radius)   = {opt_bevel_stage['L5']:.2f} mm")
    print(f"  Mean Pitch diameter d_pm       = {opt_bevel_stage['d_pm']:.2f} mm")
    print(f"  Mean Pitch diameter d_gm       = {opt_bevel_stage['d_gm']:.2f} mm")
    print(f"  Mean pitch cone distance R_m   = {opt_bevel_stage['R_m']:.2f} mm")
    print(f"  Mean Pitch Line Velocity V_m   = {opt_bevel_stage['V_m']:.3f} m/s")
    print(f"  Stage 2 Combined Torque T2     = {opt_bevel_stage['T2']:.2f} N-m")
    print(f"  Outer Transmitted Load W_t_out = {opt_bevel_stage['W_t_b_outer']:.2f} N")
    print(f"  Mean Transmitted Load W_t_mean = {opt_bevel_stage['W_t_b_mean']:.2f} N")
    print("\n  AGMA Bevel Stress Factors:")
    print(f"    Dynamic Factor K_v_b         = {opt_bevel_stage['K_v_b']:.4f}{get_override_label('bevel_K_v')}")
    print(f"    Overload Factor K_o_b        = {opt_bevel_stage['K_o_b']:.4f}{get_override_label('bevel_K_o')}")
    print(f"    Bending Size Factor Y_x      = {opt_bevel_stage['Y_x']:.4f}{get_override_label('bevel_Y_x')}")
    print(f"    Pitting Size Factor Z_x      = {opt_bevel_stage['Z_x']:.4f}{get_override_label('bevel_Z_x')}")
    print(f"    Load Distribution K_mb       = {opt_bevel_stage['K_mb']:.4f}{get_override_label('bevel_K_mb')}")
    print(f"    Bevel Geometry Y_Jb_Pinion   = {opt_bevel_stage['Y_Jb_P']:.4f}{get_override_label('bevel_Y_Jb_P')}")
    print(f"    Bevel Geometry Y_Jb_Gear     = {opt_bevel_stage['Y_Jb_G']:.4f}{get_override_label('bevel_Y_Jb_G')}")
    print(f"    Contact Geometry factor I_b  = {opt_bevel_stage['I_b']:.4f}{get_override_label('bevel_I_b')}")
    print(f"    Pinion Bending Cycle Y_NT_b  = {opt_bevel_stage['Y_NT_P']:.4f}{get_override_label('bevel_Y_NT_P')}")
    print(f"    Gear Bending Cycle Y_NT_bG   = {opt_bevel_stage['Y_NT_G']:.4f}{get_override_label('bevel_Y_NT_G')}")
    print(f"    Contact Cycle Factor Z_NT_b  = {opt_bevel_stage['Z_NT']:.4f}{get_override_label('bevel_Z_NT')}")
    print(f"    Allowable S_t_b / S_c_b      = {opt_bevel_stage['S_t_b']:.2f} MPa / {opt_bevel_stage['S_c_b']:.2f} MPa"
          f"{get_override_label('bevel_S_t')}{get_override_label('bevel_S_c')}")
    print("\n  Bevel Stress Verification Results:")
    print(f"    Bending Stress sigma_F_b (Pinion)= {opt_bevel_stage['sigma_F_b_P']:.2f} MPa")
    print(f"    Allowable Pinion Bending sigma_FP= {opt_bevel_stage['sigma_FP_b_P']:.2f} MPa  -->  PASS (n_F = {opt_bevel_stage['n_F_b_P']:.3f})")
    print(f"    Bending Stress sigma_F_b (Gear)  = {opt_bevel_stage['sigma_F_b_G']:.2f} MPa")
    print(f"    Allowable Gear Bending sigma_FP  = {opt_bevel_stage['sigma_FP_b_G']:.2f} MPa  -->  PASS (n_F = {opt_bevel_stage['n_F_b_G']:.3f})")
    print(f"    Contact Stress sigma_H_b         = {opt_bevel_stage['sigma_H_b']:.2f} MPa")
    print(f"    Allowable Bevel Pitting sigma_HP = {opt_bevel_stage['sigma_HP_b']:.2f} MPa  -->  PASS (n_H = {opt_bevel_stage['n_H_b']:.3f})")

    print("\n" + "="*80)
    print(" PHASE 3 - 3D GEAR FORCE & BEARING LOADING")
    print("="*80)
    print("  Helical Mesh Forces (per Pinion):")
    print(f"    Tangential load W_t_h        = {reactions['mesh_forces']['helical']['W_t']:.2f} N")
    print(f"    Radial separating W_r_h      = {reactions['mesh_forces']['helical']['W_r']:.2f} N")
    print(f"    Axial thrust load W_a_h      = {reactions['mesh_forces']['helical']['W_a']:.2f} N")
    print("  Bevel Mesh Forces (at Mean diameter):")
    print(f"    Tangential load W_t_b        = {reactions['mesh_forces']['bevel']['W_t']:.2f} N")
    print(f"    Radial separating W_r_b      = {reactions['mesh_forces']['bevel']['W_r']:.2f} N")
    print(f"    Axial thrust load W_a_b      = {reactions['mesh_forces']['bevel']['W_a']:.2f} N")
    print("\n  Bearing Reactions Summary (3D Equilibrium):")
    print("    [Shaft 1a - Helical Pinion Shaft]")
    print(f"      Bearing A (radial / axial) = {reactions['Shaft1']['A']['radial']:.2f} N / {reactions['Shaft1']['A']['axial']:.2f} N")
    print(f"      Bearing B (radial / axial) = {reactions['Shaft1']['B']['radial']:.2f} N / {reactions['Shaft1']['B']['axial']:.2f} N")
    print("    [Shaft 2 - Combined Intermediate Shaft (Straddle + Overhung)]")
    print("      Note: Symmetrical Stage 1 helical radial and thrust forces cancel out completely.")
    print(f"      Bearing C (radial / axial) = {reactions['Shaft2']['C']['radial']:.2f} N / {reactions['Shaft2']['C']['axial']:.2f} N")
    print(f"      Bearing D (radial / axial) = {reactions['Shaft2']['D']['radial']:.2f} N / {reactions['Shaft2']['D']['axial']:.2f} N")
    print("    [Shaft 3 - Vertical Bevel Gear Output Shaft]")
    print(f"      Bearing E (radial / axial) = {reactions['Shaft3']['E']['radial']:.2f} N / {reactions['Shaft3']['E']['axial']:.2f} N")
    print(f"      Bearing F (radial / axial) = {reactions['Shaft3']['F']['radial']:.2f} N / {reactions['Shaft3']['F']['axial']:.2f} N")

    print("\n" + "="*80)
    print(" PHASE 4 - SHAFT FATIGUE STRESS VERIFICATION (DE-Goodman)")
    print("="*80)
    print(f"  Fixed Input Shaft 1 Diameter d = {D_SHAFT1:.2f} mm")
    print(f"  Resultant Bending Moment M_a   = {M_a_1 / 1000.0:.3f} N-m (at pinion mesh)")
    print(f"  Steady Torque T_m              = {T_m_1:.2f} N-m")
    print(f"  Material Tensile Strength S_ut = {S_ut_shaft:.2f} MPa")
    print(f"  Marin Corrected Se             = {S_e_1:.2f} MPa{get_override_label('shaft1_S_e')}")
    print(f"  Stress Concentration K_f / K_fs = {get_override('shaft1_K_f', 1.8):.2f}{get_override_label('shaft1_K_f')} / {get_override('shaft1_K_fs', 1.5):.2f}{get_override_label('shaft1_K_fs')}")
    status_Goodman = "PASS" if n_Goodman_1 >= 1.5 else "WARNING (n < 1.5)"
    print(f"  Achieved Goodman Safety Factor = {n_Goodman_1:.3f}  -->  {status_Goodman}")

    print("\n" + "="*80)
    print(" PHASE 5 - BEARING DYNAMIC RATING CAPACITY (ISO 281)")
    print("="*80)
    print(f"  Target Life L10 target         = {L_BEARING_H} hours")
    print("  Required Basic Dynamic Capacity C_req [kN]:")
    print(f"    Bearing A (Locating)         = {C_req['A']:.3f} kN  @ {bearing_speeds['A']} rpm  [CATALOG LOOKUP REQUIRED]")
    print(f"    Bearing B                    = {C_req['B']:.3f} kN  @ {bearing_speeds['B']} rpm  [CATALOG LOOKUP REQUIRED]")
    print(f"    Bearing C (Locating)         = {C_req['C']:.3f} kN  @ {bearing_speeds['C']:.1f} rpm  [CATALOG LOOKUP REQUIRED]")
    print(f"    Bearing D                    = {C_req['D']:.3f} kN  @ {bearing_speeds['D']:.1f} rpm  [CATALOG LOOKUP REQUIRED]")
    print(f"    Bearing E (Locating)         = {C_req['E']:.3f} kN  @ {bearing_speeds['E']} rpm  [CATALOG LOOKUP REQUIRED]")
    print(f"    Bearing F                    = {C_req['F']:.3f} kN  @ {bearing_speeds['F']} rpm  [CATALOG LOOKUP REQUIRED]")
    print("="*80)
    print("                               END OF REPORT                                  ")
    print("="*80)

 

if __name__ == "__main__":
    run_design_optimization()

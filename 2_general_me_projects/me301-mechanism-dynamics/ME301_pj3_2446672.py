import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Results for tabling accelerations and forces
results_data = []

m2 = 1.0
m3 = 0.8
m4 = 0.7
m5 = 0.9

Ig2 = 1.0      # kg.m^2
Ig4 = 0.75     # kg.m^2
Ig3 = 0.0      

W_13 = 10.0    # rad/s (constant)
ALPHA_13 = 0.0 # rad/s^2
g = 9.81

def get_force_P(v15):
    """Calculates dependent force P(v15). v15 in m/s."""
    if v15 < 0:
        return 40.0 # Along +x
    else:
        return -10.0 * v15 

def solve_dynamics(theta_3_deg, L_AB_mm):
    l_ab = L_AB_mm / 1000.0
    l_ag = 0.095
    l_gc = 0.140
    l_cd = 0.050
    l_be = 0.230
    l_fe = 0.074
    h_5  = 0.245

    theta_3_rad = np.deg2rad(theta_3_deg)

    # --- Position Analysis ---
    # Crank Pin D coordinates relative to B
    # G is at (L_AG, 0). 
    # B is at (L_AB, 0)
    # C is at (L_AG, L_GC)
    
    # Vector Loop for Link 2 (A -> B -> D) = (A -> G -> C -> D)
    r_Ax = 0
    r_Ay = 0
    r_Bx = l_ab
    r_By = 0
    r_Cx = l_ag
    r_Cy = l_gc
    
    r_Dx = r_Cx + l_cd * np.cos(theta_3_rad)
    r_Dy = r_Cy + l_cd * np.sin(theta_3_rad)
    
    # Link 2 vector (B to D)
    rx_BD = r_Dx - r_Bx
    ry_BD = r_Dy - r_By
    
    s_23 = np.sqrt(rx_BD**2 + ry_BD**2)
    theta_2_rad = np.arctan2(ry_BD, rx_BD)
    
    # Link 4 (E to F)
    r_Ex = r_Bx + l_be * np.cos(theta_2_rad)
    r_Ey = r_By + l_be * np.sin(theta_2_rad)
    
    r_Fy = h_5
    
    # Solve for theta_4 using dy = L_FE * sin(theta4)
    # r_Fy = r_Ey + L_FE * sin(theta4)
    sin_theta_4 = (r_Fy - r_Ey) / l_fe
    
    if abs(sin_theta_4) > 1.0001: 
        return None
    sin_theta_4 = max(-1.0, min(1.0, sin_theta_4)) 
    
    cos_theta_4 = -np.sqrt(1 - sin_theta_4**2)
    theta_4_rad = np.arctan2(sin_theta_4, cos_theta_4)
    
    r_Fx = r_Ex + l_fe * cos_theta_4
    s_15 = r_Fx # Position of slider relative to A
    
    # --- Kinematics (Vel & Acc) ---
    
    sin_2_3 = np.sin(theta_2_rad - theta_3_rad)
    cos_2_3 = np.cos(theta_2_rad - theta_3_rad)
    
    w2 = (l_cd * W_13 * np.cos(theta_3_rad - theta_2_rad)) / s_23
    
    # s_dot_23 
    v_23 = l_cd * W_13 * sin_2_3
    

    # v_E = v_B + w2 x r_BE
    # v_F = v_E + w4 x r_EF
    w4 = (l_be * w2 * np.cos(theta_2_rad)) / (l_fe * np.cos(theta_4_rad))
    
    # v_15 (Slider Velocity)

    v_15 = -l_be * w2 * np.sin(theta_2_rad) - l_fe * w4 * np.sin(theta_4_rad)


    # alpha 2
    term1_a2 = l_cd * ALPHA_13 * np.cos(theta_3_rad - theta_2_rad)
    term2_a2 = -l_cd * W_13 * (W_13 - w2) * np.sin(theta_3_rad - theta_2_rad)
    term_coriolis = - (l_cd * W_13 * v_23 * np.cos(theta_3_rad - theta_2_rad)) / (s_23**2)
    
    alp2 = ((term1_a2 + term2_a2) / s_23) + term_coriolis

    # alpha 4 & a_15
    ax_E = -l_be * w2**2 * np.cos(theta_2_rad) - l_be * alp2 * np.sin(theta_2_rad)
    ay_E = -l_be * w2**2 * np.sin(theta_2_rad) + l_be * alp2 * np.cos(theta_2_rad)
    
    # Vector Loop Acc: a_F = a_E + a_FE
    # a_F = [a_15, 0]
    # a_FE_n = -w4^2 * L_FE * [cos4, sin4]
    # a_FE_t = alpha4 * L_FE * [-sin4, cos4]
    
    # Y-component equation (to find alpha4):
    # 0 = ay_E - w4^2*L_FE*sin4 + alpha4*L_FE*cos4
    alp4 = -(ay_E - w4**2 * l_fe * np.sin(theta_4_rad)) / (l_fe * np.cos(theta_4_rad))
    
    # X-component equation (to find a_15):
    # a_15 = ax_E - w4^2*L_FE*cos4 - alpha4*L_FE*sin4
    a_15 = ax_E - w4**2 * l_fe * np.cos(theta_4_rad) - alp4 * l_fe * np.sin(theta_4_rad)


    # G2 (Midpoint of BE)
    a_g2_x = -(l_be/2.0) * (w2**2 * np.cos(theta_2_rad) + alp2 * np.sin(theta_2_rad))
    a_g2_y = (l_be/2.0) * (alp2 * np.cos(theta_2_rad) - w2**2 * np.sin(theta_2_rad))
    
    # G4 (Midpoint of EF) -> Average of a_E and a_F
    a_g4_x = (ax_E + a_15) / 2.0
    a_g4_y = (ay_E + 0) / 2.0

    # --- Kinetics (Force Analysis) ---

    # 1. Link 5 (Slider)
    P_val = get_force_P(v_15)
    # Equation: P + F_45_x = m5 * a_15
    F_45_x = m5 * a_15 - P_val
    F_54_x = -F_45_x

    # 2. Link 4 (Coupler)
    # Sum Forces X: F_24_x + F_54_x = m4 * a_G4_x
    F_24_x_std = m4 * a_g4_x - F_54_x
    
    # r_G4_E = E - G4 = -1/2 (F - E) = -1/2 r_EF. 
    # Actually G4 is midpoint. r_G4_E = vector from G4 to E.
    # r_EF = [l_fe cos4, l_fe sin4]. 
    # r_G4_E = -0.5 * r_EF = [-0.5*l_fe*cos4, -0.5*l_fe*sin4]
    # r_G4_F = +0.5 * r_EF = [0.5*l_fe*cos4, 0.5*l_fe*sin4]
    rx_G4F = (l_fe/2.0) * np.cos(theta_4_rad)
    ry_G4F = (l_fe/2.0) * np.sin(theta_4_rad)
    rx_G4E = -rx_G4F
    ry_G4E = -ry_G4F
    
    # Sum M_G4 = Ig4 * alp4
    # Moment from F24 (at E) + Moment from F54 (at F) = Ig4 * alp4
    # (rx_G4E * F_24_y - ry_G4E * F_24_x) + (rx_G4F * F_54_y - ry_G4F * F_54_x) = Ig4 * alp4
    
    term_F24_known = rx_G4E * (m4*a_g4_y + m4*g) - ry_G4E * F_24_x_std
    # The terms with F_54_y: rx_G4E * (-F_54_y) + rx_G4F * (F_54_y)
    # Since rx_G4E = -rx_G4F, this becomes: -rx_G4F*(-F_54_y) + rx_G4F*F_54_y = 2 * rx_G4F * F_54_y
    
    coeff_F54y = rx_G4F - rx_G4E 
    rhs_moment = Ig4 * alp4 - term_F24_known - (rx_G4F * F_54_y_std if 'F_54_y_std' in locals() else 0) 
    
    moment_rhs = Ig4 * alp4 + ry_G4E * F_24_x_std + ry_G4F * F_54_x - rx_G4E*(m4*a_g4_y + m4*g)
    moment_lhs_coeff = rx_G4F - rx_G4E # = l_fe * cos4
    
    if abs(moment_lhs_coeff) < 1e-8:
        F_54_y_std = 0
    else:
        F_54_y_std = moment_rhs / moment_lhs_coeff
        
    F_24_y_std = m4 * a_g4_y + m4*g - F_54_y_std

    F_42_x_std = -F_24_x_std
    F_42_y_std = -F_24_y_std
    
    # Sum Moments about B (Fixed Pivot)
    # Sigma M_B = I_B * alp2  (Parallel axis: Ib = Ig2 + m2*(L_BE/2)^2)
    # Or Sum M_B = Ig2*alp2 + (r_BG2 x m2*a_G2)
    
    # Moment from F_42 (at E)
    M_F42 = (l_be * np.cos(theta_2_rad)) * F_42_y_std - (l_be * np.sin(theta_2_rad)) * F_42_x_std
    
    # Moment from Gravity (at G2)
    M_g2 = (l_be/2.0 * np.cos(theta_2_rad)) * (-m2*g)
    
    # Moment from Inertia (Effective Torque approach)
    M_inertial_term = Ig2 * alp2 + ((l_be/2.0 * np.cos(theta_2_rad)) * (m2*a_g2_y) - (l_be/2.0 * np.sin(theta_2_rad)) * (m2*a_g2_x))
    

    # Eq: s_23 * F32_mag + M_F42 + M_g2 = M_inertial_term
    F32_mag = (M_inertial_term - M_F42 - M_g2) / s_23
    
    # 4. Link 3 (Crank)
    # Moment about C: T_13 + (r_CD x F_23) = 0 
    
    F_23_x = F32_mag * np.sin(theta_2_rad)
    F_23_y = -F32_mag * np.cos(theta_2_rad)
    
    M_F23 = (l_cd * np.cos(theta_3_rad)) * F_23_y - (l_cd * np.sin(theta_3_rad)) * F_23_x
    
    T_13 = -M_F23
    
    user_F24_x = -F_24_x_std
    user_F24_y = F_24_y_std
    
    user_F42_x = F_42_x_std
    user_F42_y = -F_42_y_std

    # Return dictionary for full debugging
    return {
        'Angle': theta_3_deg,
        'P(v15)': P_val,
        'aG_2_x': a_g2_x, 'aG_2_y': a_g2_y,
        'aG_4_x': a_g4_x, 'aG_4_y': a_g4_y,
        'alp_2': alp2, 'alp_4': alp4,
        'F_24_x': user_F24_x, 'F_24_y': user_F24_y, 
        'F_32': F32_mag,
        'F_42_x': user_F42_x, 'F_42_y': user_F42_y,
        'T_13': T_13
    }

lab_cases = [70, 40, 115]
angles = np.arange(0, 361, 1)

results_list = []
results_by_case = {}

print("Calculating Forces...")

for lab in lab_cases:
    case_t13 = []
    case_ang = []
    
    for th in angles:
        try:
            res = solve_dynamics(th, lab)
            if res is not None:
                res['L_AB'] = lab
                results_list.append(res)
                case_t13.append(res['T_13'])
                case_ang.append(th)
            else:
                case_t13.append(np.nan)
                case_ang.append(th)
        except Exception as e:
            case_t13.append(np.nan)
            case_ang.append(th)
            
    results_by_case[lab] = (case_ang, case_t13)

df = pd.DataFrame(results_list)
debug_row = df[(df['L_AB'] == 70) & (df['Angle'] == 225)]
if not debug_row.empty:
    print("\n--- DEBUG: Comparison at 225 Deg (Lab=70) ---")
    print(debug_row.iloc[0].T)

df.to_csv('ME301/results_table.csv', index=False)
print("\nResults saved to results_table.csv")

plt.figure(figsize=(10, 6))
styles = {70: 'b-', 40: 'g--', 115: 'r-.'}

for lab in lab_cases:
    x, y = results_by_case[lab]
    plt.plot(x, y, styles[lab], label=f'L_AB = {lab} mm', linewidth=2)

plt.title(r'Required Input Torque $T_{13}$ vs Input Angle $\theta_{13}$', fontsize=14)
plt.xlabel(r'Input Angle $\theta_{13}$ (deg)', fontsize=12)
plt.ylabel(r'Torque $T_{13}$ (Nm)', fontsize=12)
plt.axhline(0, color='k', linewidth=0.5)
plt.grid(True, alpha=0.6)
plt.legend()
plt.tight_layout()
plt.show()
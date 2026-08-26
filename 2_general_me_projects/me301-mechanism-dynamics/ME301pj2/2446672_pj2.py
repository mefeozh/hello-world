import matplotlib
matplotlib.use('TkAgg')
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import pandas as pd

# --- System Constants ---
L_AB = 70.0
L_AG = 95.0
L_GC = 140.0
L_CD = 50.0
L_BE = 230.0
L_FE = 74.0
h_5 = 245.0
W_13 = 2.0
ALPHA_13 = 0.0

def solve_mechanism(theta_3_deg):

    theta_3_rad = np.deg2rad(theta_3_deg)

    s_bd_cos_theta_2 = L_AG - L_AB + L_CD * np.cos(theta_3_rad)
    s_bd_sin_theta_2 = L_GC + L_CD * np.sin(theta_3_rad)

    s_23 = np.sqrt(s_bd_cos_theta_2**2 + s_bd_sin_theta_2**2)
    theta_2_rad = np.arctan2(s_bd_sin_theta_2, s_bd_cos_theta_2)
    theta_2_deg = np.rad2deg(theta_2_rad)

    sin_comp = L_BE * np.sin(theta_2_rad) - h_5
    sin_theta_4 = sin_comp / L_FE
    print("Th3 = {}, sin_theta_4 = {}".format(theta_3_deg, sin_theta_4))
    if abs(sin_theta_4) > 1.000001:
        return None

    sin_theta_4 = max(-1.0, min(1.0, sin_theta_4))
    cos_theta_4 = np.sqrt(1 - sin_theta_4**2)
    theta_4_rad = np.arctan2(sin_theta_4, cos_theta_4)
    theta_4_deg = np.rad2deg(theta_4_rad)

    s_15 = L_AB + L_BE * np.cos(theta_2_rad) - L_FE * cos_theta_4


    w2 = (L_CD * W_13 * np.cos(theta_3_rad - theta_2_rad)) / s_23

    v_23 = L_CD * W_13 * np.sin(theta_2_rad - theta_3_rad)

    w4 = (L_BE * w2 * np.cos(theta_2_rad)) / (L_FE * np.cos(theta_4_rad))


    v_5 = (L_BE * w2 * np.sin(theta_4_rad - theta_2_rad)) / np.cos(theta_4_rad)

    term1_a2 = L_CD * ALPHA_13 * np.cos(theta_3_rad - theta_2_rad)

    term2_a2 = -L_CD * W_13 * (W_13 - w2) * np.sin(theta_3_rad - theta_2_rad)

    numerator_main = term1_a2 + term2_a2
    term_last = - (L_CD * W_13 * v_23 * np.cos(theta_3_rad - theta_2_rad)) / (s_23**2)

    alp2 = (numerator_main / s_23) + term_last


    term1_a23 = L_CD * ALPHA_13 * np.sin(theta_2_rad - theta_3_rad)
    term2_a23 = L_CD * W_13 * (w2 - W_13) * np.cos(theta_2_rad - theta_3_rad)

    s_ddot_23 = term1_a23 + term2_a23



    num_a4_1 = L_BE * alp2 * np.cos(theta_2_rad) - L_BE * (w2**2) * np.sin(theta_2_rad)
    den_a4 = L_FE * np.cos(theta_4_rad)
    part1_a4 = num_a4_1 / den_a4


    num_a4_2 = L_BE * w2 * w4 * np.tan(theta_4_rad) * np.cos(theta_2_rad)
    part2_a4 = num_a4_2 / den_a4

    alp4 = part1_a4 + part2_a4


    num_a5_1 = L_BE * alp2 * np.sin(theta_4_rad - theta_2_rad) + \
               L_BE * w2 * (w4 - w2) * np.cos(theta_4_rad - theta_2_rad)
    den_a5 = np.cos(theta_4_rad)
    part1_a5 = num_a5_1 / den_a5

    num_a5_2 = L_BE * w2 * w4 * np.tan(theta_4_rad) * np.sin(theta_4_rad - theta_2_rad)
    part2_a5 = num_a5_2 / den_a5

    s_ddot_15 = part1_a5 + part2_a5

    return {
        "theta_3": theta_3_deg,
        "theta_2": theta_2_deg,
        "s_bd": s_23,
        "theta_4": theta_4_deg,
        "s_15": s_15,
        "w2": w2,
        "s_dot_bd": v_23,
        "w4": w4,
        "s_dot_15": v_5,
        "alp2": alp2,
        "s_ddot_bd": s_ddot_23,
        "alp4": alp4,
        "s_ddot_15": s_ddot_15
    }

def main():
    print("Calculating Kinematics using Explicit Formulas (0 to 360 deg)...")

    results = []
    angles = np.arange(0, 361, 1)

    for theta in angles:
        res = solve_mechanism(theta)
        if res is not None:
            results.append(res)

    df = pd.DataFrame(results)

    pd.set_option('display.max_rows', None)
    pd.set_option('display.expand_frame_repr', False)

    print("\n" + "="*120)
    print("FULL KINEMATIC ANALYSIS TABLE (Using Explicit Formulas from Image)")
    print("="*120)

    print_df = df[['theta_3', 'w2', 'w4', 's_dot_bd', 's_dot_15', 'alp2', 'alp4', 's_ddot_bd', 's_ddot_15']].copy()
    print_df.columns = ['th3', 'w12', 'w14', 's_dot_23', 's_dot_15', 'alp12', 'alp14', 's_ddot_23', 's_ddot_15']

    print(print_df.to_string(index=False, float_format="%.2f"))
    print("="*120)

    fig, (ax_vel, ax_acc) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)

    ax_vel.plot(df['theta_3'], df['w2'], label=r'$\omega_{12}$ (rad/s)')
    ax_vel.plot(df['theta_3'], df['w4'], label=r'$\omega_{14}$ (rad/s)')
    ax_vel.plot(df['theta_3'], df['s_dot_bd']/100, '--', label=r'$\dot{s}_{23}/100$ (dm/s)')
    ax_vel.plot(df['theta_3'], df['s_dot_15']/100, '--', label=r'$\dot{s}_{15}/100$ (dm/s)')
    ax_vel.set_title("Velocity Analysis")
    ax_vel.legend()
    ax_vel.grid(True)

    ax_acc.plot(df['theta_3'], df['alp2'], label=r'$\alpha_{12}$ (rad/$s^2$)')
    ax_acc.plot(df['theta_3'], df['alp4'], label=r'$\alpha_{14}$ (rad/$s^2$)')
    ax_acc.plot(df['theta_3'], df['s_ddot_bd']/100, '--', label=r'$\ddot{s}_{23}/100$ (dm/$s^2$)') #divided by 100 to convert mm/s^2 to dm/s^2
    ax_acc.plot(df['theta_3'], df['s_ddot_15']/100, '--', label=r'$\ddot{s}_{15}/100$ (dm/$s^2$)') #divided by 100 to convert mm/s^2 to dm/s^2
    ax_acc.set_title("Acceleration Analysis")
    ax_acc.set_xlabel(r'Input Angle $\theta_{13}$ (deg)')
    ax_acc.legend()
    ax_acc.grid(True)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
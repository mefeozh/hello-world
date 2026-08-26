import matplotlib

matplotlib.use('TkAgg')

import numpy as np

import matplotlib.pyplot as plt

from matplotlib.widgets import Slider, Button


L_AB = 70.0

L_AG = 95.0

L_GC = 140.0

L_CD = 50.0

L_BE = 230.0

L_FE = 74.0

h_5 = 245.0


def solve_mechanism(theta_3_deg):

    """

    Based on the LCEs:

    1) L_AG + L_GC*i + L_CD*exp(i*th_3) = L_AB + s_BD*exp(i*th_2)

    2) h_5*i + s_5 + L_FE*exp(i*th_4) = L_AB + L_BE*exp(i*th_2)"""



    theta_3_rad = np.deg2rad(theta_3_deg)



    s_bd_cos_theta_2 = L_AG - L_AB + L_CD * np.cos(theta_3_rad)

    s_bd_sin_theta_2 = L_GC + L_CD * np.sin(theta_3_rad)



    s_bd = np.sqrt(s_bd_cos_theta_2**2 + s_bd_sin_theta_2**2)

    theta_2_rad = np.arctan2(s_bd_sin_theta_2, s_bd_cos_theta_2)

    theta_2_deg = np.rad2deg(theta_2_rad)







    sin_comp = L_BE * np.sin(theta_2_rad) - h_5

    sin_theta_4 = sin_comp / L_FE



    if abs(sin_theta_4) > 1.000001:

        return None



    cos_theta_4_1 = np.sqrt(1 - sin_theta_4**2)

    cos_theta_4_2 = -np.sqrt(1 - sin_theta_4**2)





    theta_4_rad_1 = np.arctan2(sin_theta_4, cos_theta_4_1)

    theta_4_rad_2 = np.arctan2(sin_theta_4, cos_theta_4_2)



    theta_4_deg_1 = np.rad2deg(theta_4_rad_1)

    theta_4_deg_2 = np.rad2deg(theta_4_rad_2)





    s_5_1 = L_AB + L_BE * np.cos(theta_2_rad) - L_FE * cos_theta_4_1

    s_5_2 = L_AB + L_BE * np.cos(theta_2_rad) - L_FE * cos_theta_4_2





    solution_1 = (theta_2_deg, s_bd, theta_4_deg_1, s_5_1)

    solution_2 = (theta_2_deg, s_bd, theta_4_deg_2, s_5_2)



    return (solution_1, solution_2)







print("--- Solution for theta_3 = 300 degrees ---")

th3_specific = 300.0

solutions_specific = solve_mechanism(th3_specific)



if solutions_specific is None:

    print(f"No real solution exists for theta_3 = {th3_specific} deg.\n")

else:

    sol_1, sol_2 = solutions_specific

    print(f"  Input: theta_3 = {th3_specific:.2f} deg")

    print("\n  Solution 1 (Assembly 1):")

    print(f"    theta_2 = {sol_1[0]:.2f} deg")

    print(f"    s_BD    = {sol_1[1]:.2f} mm")

    print(f"    theta_4 = {sol_1[2]:.2f} deg")

    print(f"    s_5     = {sol_1[3]:.2f} mm")

    print("\n  Solution 2 (Assembly 2):")

    print(f"    theta_2 = {sol_2[0]:.2f} deg")

    print(f"    s_BD    = {sol_2[1]:.2f} mm")

    print(f"    theta_4 = {sol_2[2]:.2f} deg")

    print(f"    s_5     = {sol_2[3]:.2f} mm")



print("\n\n--- Full Kinematic Analysis Table (0 to 360 degrees) ---")


print("=" * 95)

print(f"{'theta_3':>7} | {'theta_2':>10} | {'s_BD':>10} | {'theta_4 (S1)':>12} | {'s_5 (S1)':>10} | {'theta_4 (S2)':>12} | {'s_5 (S2)':>10}")

print("-" * 95)



angles_part1 = np.arange(300, 361, 15)

angles_part2 = np.arange(0, 300, 15)

theta_3_range = np.concatenate((angles_part1, angles_part2))



for theta_3_input in theta_3_range:

    solutions = solve_mechanism(theta_3_input)



    if solutions is None:

        print(f"{theta_3_input:7.1f} | {'N/A':>10} | {'N/A':>10} | {'N/A':>12} | {'N/A':>10} | {'N/A':>12} | {'N/A':>10}")

    else:

        sol_1, sol_2 = solutions



        print(f"{theta_3_input:7.1f} | {sol_1[0]:10.2f} | {sol_1[1]:10.2f} | {sol_1[2]:12.2f} | {sol_1[3]:10.2f} | {sol_2[2]:12.2f} | {sol_2[3]:10.2f}")



print("=" * 95)



def draw_mechanism(ax, theta_3_deg):

    """Draw current configuration of the mechanism."""



    theta_3_rad = np.deg2rad(theta_3_deg)

    solutions = solve_mechanism(theta_3_deg)



    ax.clear()

    ax.set_title(f"Mechanism Analysis | Input θ3 = {theta_3_deg:.1f}°")

    ax.axis("equal")

    ax.grid(True)

    ax.set_xlim(-150, 450)

    ax.set_ylim(-150, 400)



    A = np.array([0, 0])

    B = np.array([L_AB, 0])

    G = np.array([L_AG, 0])

    C = np.array([L_AG, L_GC])





    ax.plot([-150, 450], [0, 0], 'k-', lw=3)

    ax.plot([-150, 450], [h_5, h_5], 'k--', lw=2)





    ax.plot([A[0], B[0], G[0], C[0]], [A[1], B[1], G[1], C[1]], 'ks', ms=8, label="Fixed Pivots (A,B,G,C)")



    if solutions is None:

        ax.text(100, 150, "NO REAL SOLUTION", color="red", fontsize=16, weight='bold')

        return



    sol_1, sol_2 = solutions

    theta_2_rad = np.deg2rad(sol_1[0])



    D = np.array([L_AG + L_CD * np.cos(theta_3_rad), L_GC + L_CD * np.sin(theta_3_rad)])

    E = np.array([L_AB + L_BE * np.cos(theta_2_rad), L_BE * np.sin(theta_2_rad)])



    wheel = plt.Circle(C, L_CD, color='r', fill=False, ls='--')

    ax.add_patch(wheel)

    ax.plot([C[0], D[0]], [C[1], D[1]], 'r-', lw=2, label="Link 3 (CD)")





    ax.plot([B[0], D[0]], [B[1], D[1]], 'b-', lw=3, label="Link 2 (BDE)")

    ax.plot([B[0], E[0]], [B[1], E[1]], 'b-', lw=3)

    ax.plot([D[0], E[0]], [D[1], E[1]], 'b--', lw=2)





    theta_4_rad_1 = np.deg2rad(sol_1[2])

    s_5_1 = sol_1[3]

    F_1 = np.array([s_5_1, h_5])

    ax.plot([F_1[0], E[0]], [F_1[1], E[1]], 'g--', lw=2, label="Assembly 1 (FE)")

    ax.plot(F_1[0], F_1[1], 'gs', ms=8)





    theta_4_rad_2 = np.deg2rad(sol_2[2])

    s_5_2 = sol_2[3]

    F_2 = np.array([s_5_2, h_5])

    ax.plot([F_2[0], E[0]], [F_2[1], E[1]], 'm--', lw=2, label="Assembly 2 (FE)")

    ax.plot(F_2[0], F_2[1], 'ms', ms=8)



    ax.legend(loc='lower left', fontsize='small')







def main():



    theta_3_initial = 300.0



    fig, ax_mech = plt.subplots(figsize=(10, 8))

    plt.subplots_adjust(bottom=0.2)





    draw_mechanism(ax_mech, theta_3_initial)



    ax_t3 = plt.axes([0.2, 0.05, 0.65, 0.03])

    s_t3 = Slider(ax_t3, 'θ3 (deg)', 0, 360, valinit=theta_3_initial, valstep=0.5)





    def update(val):

        draw_mechanism(ax_mech, s_t3.val)

        fig.canvas.draw_idle()



    s_t3.on_changed(update)



    plt.show()





if __name__ == "__main__":

    main()
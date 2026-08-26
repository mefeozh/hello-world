import matplotlib
matplotlib.use('TkAgg')
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# --- System Constants ---
L_AB = 70.0
L_AG = 95.0
L_GC = 140.0
L_CD = 50.0
L_BE = 230.0
L_FE = 74.0
h_5 = 245.0

def solve_mechanism(theta_3_deg):

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

    sin_theta_4 = max(-1.0, min(1.0, sin_theta_4))

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


def precalculate_data():

    angles = np.linspace(0, 360, 721)

    data = {
        't3': angles,
        't2': [], 's_bd': [],
        't4_1': [], 's5_1': [],
        't4_2': [], 's5_2': []
    }

    for ang in angles:
        sol = solve_mechanism(ang)
        if sol is None:
            data['t2'].append(np.nan)
            data['s_bd'].append(np.nan)
            data['t4_1'].append(np.nan)
            data['s5_1'].append(np.nan)
            data['t4_2'].append(np.nan)
            data['s5_2'].append(np.nan)
        else:
            s1, s2 = sol
            data['t2'].append(s1[0])
            data['s_bd'].append(s1[1])
            data['t4_1'].append(s1[2])
            data['s5_1'].append(s1[3])
            data['t4_2'].append(s2[2])
            data['s5_2'].append(s2[3])

    return data

def draw_mechanism(ax, theta_3_deg):

    theta_3_rad = np.deg2rad(theta_3_deg)
    solutions = solve_mechanism(theta_3_deg)

    ax.clear()
    ax.set_title(f"Mechanism | Input θ3 = {theta_3_deg:.1f}°")
    ax.axis("equal")
    ax.grid(True, alpha=0.5)

    ax.set_xlim(-100, 450)
    ax.set_ylim(-100, 350)

    A = np.array([0, 0])
    B = np.array([L_AB, 0])
    G = np.array([L_AG, 0])
    C = np.array([L_AG, L_GC])

    ax.plot([-100, 450], [0, 0], 'k-', lw=2)
    ax.plot([-100, 450], [h_5, h_5], 'k--', lw=1)

    ax.plot([A[0], B[0], G[0], C[0]], [A[1], B[1], G[1], C[1]], 'ks', ms=6, zorder=5)

    if solutions is None:
        ax.text(50, 150, "NO REAL SOLUTION", color="red", fontsize=14, weight='bold')
        return

    sol_1, sol_2 = solutions
    theta_2_rad = np.deg2rad(sol_1[0])

    D = np.array([L_AG + L_CD * np.cos(theta_3_rad), L_GC + L_CD * np.sin(theta_3_rad)])
    E = np.array([L_AB + L_BE * np.cos(theta_2_rad), L_BE * np.sin(theta_2_rad)])

    wheel = plt.Circle(C, L_CD, color='gray', fill=False, ls=':', alpha=0.5)
    ax.add_patch(wheel)

    ax.plot([C[0], D[0]], [C[1], D[1]], 'r-', lw=3, label="Link 3 (Input)")
    ax.plot([B[0], D[0]], [B[1], D[1]], 'b-', lw=2)
    ax.plot([B[0], E[0]], [B[1], E[1]], 'b-', lw=2, label="Link 2 (Rocker)")
    ax.plot([D[0], E[0]], [D[1], E[1]], 'b--', lw=1)

    s_5_1 = sol_1[3]
    F_1 = np.array([s_5_1, h_5])
    ax.plot([E[0], F_1[0]], [E[1], F_1[1]], 'g-', lw=2, label="Sol 1")
    ax.plot(F_1[0], F_1[1], 'gs', ms=8, zorder=5)

    s_5_2 = sol_2[3]
    F_2 = np.array([s_5_2, h_5])
    ax.plot([E[0], F_2[0]], [E[1], F_2[1]], 'm--', lw=2, label="Sol 2")
    ax.plot(F_2[0], F_2[1], 'ms', ms=8, zorder=5)

    ax.legend(loc='lower right', fontsize='x-small')



def main():
    theta_3_initial = 300.0

    data = precalculate_data()

    fig = plt.figure(figsize=(16, 9))
    gs = fig.add_gridspec(4, 2, width_ratios=[1.5, 1])

    ax_mech = fig.add_subplot(gs[:, 0])

    ax_t2 = fig.add_subplot(gs[0, 1])
    ax_sbd = fig.add_subplot(gs[1, 1], sharex=ax_t2)
    ax_t4 = fig.add_subplot(gs[2, 1], sharex=ax_t2)
    ax_s5 = fig.add_subplot(gs[3, 1], sharex=ax_t2)

    graph_axes = [ax_t2, ax_sbd, ax_t4, ax_s5]

    ax_t2.plot(data['t3'], data['t2'], 'k-', lw=1.5)
    ax_t2.set_ylabel(r'$\theta_2$ (deg)')
    ax_t2.grid(True)

    ax_sbd.plot(data['t3'], data['s_bd'], 'k-', lw=1.5)
    ax_sbd.set_ylabel(r'$s_{BD}$ (mm)')
    ax_sbd.grid(True)

    ax_t4.plot(data['t3'], data['t4_1'], 'g-', lw=1.5, label='Sol 1')
    ax_t4.plot(data['t3'], data['t4_2'], 'm--', lw=1.5, label='Sol 2')
    ax_t4.set_ylabel(r'$\theta_4$ (deg)')
    ax_t4.grid(True)
    ax_t4.legend(fontsize='x-small', loc='upper right')

    ax_s5.plot(data['t3'], data['s5_1'], 'g-', lw=1.5, label='Sol 1')
    ax_s5.plot(data['t3'], data['s5_2'], 'm--', lw=1.5, label='Sol 2')
    ax_s5.set_ylabel(r'$s_5$ (mm)')
    ax_s5.set_xlabel(r'Input $\theta_3$ (deg)')
    ax_s5.grid(True)

    lines = []
    for ax in graph_axes:
        line = ax.axvline(theta_3_initial, color='r', alpha=0.8, lw=2)
        lines.append(line)

    draw_mechanism(ax_mech, theta_3_initial)

    ax_slider = plt.axes([0.15, 0.02, 0.5, 0.03])
    s_t3 = Slider(ax_slider, 'Theta 3', 0, 360, valinit=theta_3_initial, valstep=1.0)

    def update(val):
        curr_ang = s_t3.val
        draw_mechanism(ax_mech, curr_ang)

        for line in lines:
            line.set_xdata([curr_ang, curr_ang])

        fig.canvas.draw_idle()

    s_t3.on_changed(update)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.1)
    plt.show()

if __name__ == "__main__":
    main()
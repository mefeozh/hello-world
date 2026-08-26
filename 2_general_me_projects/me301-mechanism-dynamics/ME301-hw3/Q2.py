import matplotlib
matplotlib.use('TkAgg')
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button

# --- VISUALIZER PARAMETERS ---
a1 = 0.53  # |A0B0|
a2 = 0.35  # |B0B|
a4 = 0.41  # |A0A|
a5 = 0.63  # |AC|

# --- ANALYTICAL SOLVER (Copied and modified from mechanism_solver_final.py) ---
def solve_inverted_slider_s13(theta_12_deg):
    theta_12_rad = np.deg2rad(theta_12_deg)

    B_x = a2 * np.cos(theta_12_rad)
    B_y = a1 + a2 * np.sin(theta_12_rad)

    theta_14_rad = np.arctan2(B_y, B_x)
    s13 = np.sqrt(B_x**2 + B_y**2)

    A_x = a4 * np.cos(theta_14_rad)
    A_y = a4 * np.sin(theta_14_rad)

    radicand = a5**2 - A_y**2

    if radicand < 0:
        return {"th14_rad": theta_14_rad, "s13": s13, "s16_1": np.nan, "s16_2": np.nan, "Ax": A_x, "Ay": A_y, "Bx": B_x, "By": B_y}

    term_B = np.sqrt(radicand)
    s16_sol1 = A_x + term_B
    s16_sol2 = A_x - term_B
    print (f"theta_12: {theta_12_deg} deg | s16_sol1: {s16_sol1:.4f} m | s16_sol2: {s16_sol2:.4f} m")
    print (f" theta 14_rad: {theta_14_rad:.4f} rad | s13: {s13:.4f} m")
    return {
        "th14_rad": theta_14_rad, "s13": s13, "s16_1": s16_sol1, "s16_2": s16_sol2,
        "Ax": A_x, "Ay": A_y, "Bx": B_x, "By": B_y
    }
# --------------------------------------------------------------------------------

# Store the selected solution index (0 or 1, for s16_sol1 or s16_sol2)
selected_solution = [0]

def draw_mechanism(ax, result, selected_index, theta_12_deg):
    ax.clear()

    # --- Fixed Points ---
    A0 = np.array([0, 0])
    B0 = np.array([0, a1])
    ax.plot([A0[0], B0[0]], [A0[1], B0[1]], 'ks', ms=10, label="Fixed Pivots (A0, B0)")

    # Slider 6 Ground
    ax.plot([-0.5, 1.5], [0, 0], 'k-', lw=3)

    if not result or np.isnan(result['s16_1']):
        ax.set_title(f"Mechanism Lock-Up at θ12 = {theta_12_deg:.1f}°", color='red')

        # Draw the crank that caused the lockup
        pos_B = np.array([result['Bx'], result['By']])
        ax.plot([B0[0], pos_B[0]], [B0[1], pos_B[1]], 'r-', lw=3, label="Link 2 (B0B)")
        ax.plot([A0[0], pos_B[0]], [A0[1], pos_B[1]], 'k--', lw=1, alpha=0.5)

        # Draw the required position for A (Ax, Ay)
        A_req = np.array([result['Ax'], result['Ay']])
        ax.plot([A0[0], A_req[0]], [A0[1], A_req[1]], 'b--', lw=3, alpha=0.3)
        ax.text(A_req[0] + 0.05, A_req[1], f"Point A (Required)", fontsize=8)

    else:
        # --- Solvable Case ---

        s16 = result['s16_1'] if selected_index == 0 else result['s16_2']

        # Calculate moving points
        pos_B = np.array([result['Bx'], result['By']])
        pos_A = np.array([result['Ax'], result['Ay']])
        pos_C = np.array([s16, 0])

        # --- Title ---
        sol_text = "Solution 1 (Open)" if selected_index == 0 else "Solution 2 (Crossed)"
        ax.set_title(f"Inverted Slider at θ12 = {theta_12_deg:.1f}° | {sol_text}")

        # 1. Link 2 (Crank B0B)
        ax.plot([B0[0], pos_B[0]], [B0[1], pos_B[1]], 'r-', lw=3, label="Link 2 (B0B)")

        # 2. Link 4 (The Slotted Bar)
        # Draw a line along the angle theta_14 (vector A0B)
        ax.plot([A0[0], pos_B[0]], [A0[1], pos_B[1]], 'k--', lw=1, alpha=0.5)
        ax.plot([A0[0], pos_A[0]], [A0[1], pos_A[1]], 'b-', lw=3, label="Link 4 (A0A)")

        # 3. Link 5 (Coupler AC)
        ax.plot([pos_A[0], pos_C[0]], [pos_A[1], pos_C[1]], 'g-', lw=2, label="Link 5 (AC)")

        # 4. Link 3 (The Slider Block, shown as Pin B on Link 4)
        ax.plot(pos_B[0], pos_B[1], 'rs', ms=8, label=f"Slider Block (B), s13={result['s13']:.3f}m")

        # Draw Points
        ax.plot([pos_A[0], pos_C[0]], [pos_A[1], pos_C[1]], 'ko', ms=6)

    ax.axis("equal")
    ax.grid(True)
    ax.set_xlim(-0.5, 1.5)
    ax.set_ylim(-0.2, 1.0)
    ax.legend(loc='upper left', fontsize='small')

def main():
    fig, ax_mech = plt.subplots(figsize=(10, 8))
    plt.subplots_adjust(bottom=0.15, right=0.85)

    ax_t12 = plt.axes([0.2, 0.05, 0.65, 0.03])
    s_t12 = Slider(ax_t12, 'θ12 (deg)', 0, 360, valinit=30.0, valstep=0.5)

    def update(val):
        result = solve_inverted_slider_s13(s_t12.val)
        draw_mechanism(ax_mech, result, selected_solution[0], s_t12.val)
        fig.canvas.draw_idle()

    def select_sol_1(event): selected_solution[0] = 0; update(None)
    def select_sol_2(event): selected_solution[0] = 1; update(None)

    ax_b1 = plt.axes([0.87, 0.8, 0.1, 0.05]); btn_s1 = Button(ax_b1, 'Solution 1'); btn_s1.on_clicked(select_sol_1)
    ax_b2 = plt.axes([0.87, 0.7, 0.1, 0.05]); btn_s2 = Button(ax_b2, 'Solution 2'); btn_s2.on_clicked(select_sol_2)

    s_t12.on_changed(update)
    update(30.0)

    plt.show()

if __name__ == "__main__":
    main()
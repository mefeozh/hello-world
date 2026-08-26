# ME301 - Homework 4 - Problem 3
import matplotlib
matplotlib.use('TkAgg')
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.patches import Polygon

# --- 1. System Parameters ---
a2 = 100.0   # A0_A (Input Crank)
a1 = 350.0   # A0_B0 (Fixed Ground vertical)
a3 = 360.0   # B0_B (Output Link)
b4 = 265.0   # AC
b1 = 360.0   # A0_O
c1 = 330.0   # B0_O
a4 = 430.0   # AD
a5 = 210.0   # BC
c4 = 486.0   # CD
r  = 200.0   # OD (Radius of slot)

# --- 2. Geometric Pre-calculations ---
cos_gamma1 = (a1**2 + b1**2 - c1**2) / (2 * a1 * b1)
gamma1_rad = np.arccos(np.clip(cos_gamma1, -1, 1))

cos_delta1 = (b4**2 + a4**2 - c4**2) / (2 * b4 * a4)
delta1_rad = np.arccos(np.clip(cos_delta1, -1, 1))

# --- 3. Solver Functions ---

def get_circle_intersections(p0, r0, p1, r1):
    d = np.linalg.norm(np.array(p1) - np.array(p0))
    if d > r0 + r1 or d < abs(r0 - r1) or d == 0:
        return None

    a = (r0**2 - r1**2 + d**2) / (2 * d)
    h = np.sqrt(max(0, r0**2 - a**2))

    x2 = p0[0] + a * (p1[0] - p0[0]) / d
    y2 = p0[1] + a * (p1[1] - p0[1]) / d

    x3_1 = x2 + h * (p1[1] - p0[1]) / d
    y3_1 = y2 - h * (p1[0] - p0[0]) / d
    x3_2 = x2 - h * (p1[1] - p0[1]) / d
    y3_2 = y2 + h * (p1[0] - p0[0]) / d

    return (np.array([x3_1, y3_1]), np.array([x3_2, y3_2]))

def solve_mechanism(theta_2_deg):
    theta_2_rad = np.deg2rad(theta_2_deg)

    # Fixed Points
    B0 = np.array([0, 0])
    A0 = np.array([0, a1])
    O = np.array([ -b1 * np.sin(gamma1_rad), a1 - b1 * np.cos(gamma1_rad) ])

    # Point A
    A = A0 + np.array([a2 * np.cos(theta_2_rad), a2 * np.sin(theta_2_rad)])

    # Point D
    intersections_D = get_circle_intersections(A, a4, O, r)
    if intersections_D is None: return None
    D = intersections_D[1] if intersections_D[1][1] < intersections_D[0][1] else intersections_D[0]

    # Point C
    vec_AD = D - A
    angle_AD = np.arctan2(vec_AD[1], vec_AD[0])
    angle_AC = angle_AD - delta1_rad # Corrected direction
    C = A + np.array([b4 * np.cos(angle_AC), b4 * np.sin(angle_AC)])

    # Point B
    intersections_B = get_circle_intersections(B0, a3, C, a5)
    if intersections_B is None: return None
    B = intersections_B[0] if intersections_B[0][0] > intersections_B[1][0] else intersections_B[1]

    # --- Check for Singularity Metrics ---
    # Metric 1: Collinearity of AD and OD (Loop 1 Limit)
    # Using cross product magnitude (area of parallelogram formed by vectors)
    vec_OD = D - O
    metric_L1 = np.cross(vec_AD, vec_OD) # Zero when collinear

    # Metric 2: Collinearity of BC and B0B (Loop 2 Toggle)
    vec_BC = C - B
    vec_B0B = B - B0
    metric_L2 = np.cross(vec_BC, vec_B0B) # Zero when collinear

    return {
        'A0': A0, 'B0': B0, 'O': O,
        'A': A, 'B': B, 'C': C, 'D': D,
        'metric_L1': metric_L1,
        'metric_L2': metric_L2
    }

# --- 4. Singularity Scanner ---
def scan_singularities():
    print("Scanning for singularities...")
    angles = np.arange(0, 360, 0.5)
    l1_vals = []
    l2_vals = []
    valid_angles = []

    for th in angles:
        res = solve_mechanism(th)
        if res is not None:
            l1_vals.append(res['metric_L1'])
            l2_vals.append(res['metric_L2'])
            valid_angles.append(th)
        else:
            l1_vals.append(np.nan)
            l2_vals.append(np.nan)
            valid_angles.append(th)

    # Find zero crossings or local minima for Loop 1 (Limit Reach)
    # Usually 2 points: Max reach and Min reach
    l1_arr = np.array(l1_vals)
    # Get indices where sign changes or absolute value is minimal
    # Simple method: Find indices of local minima of absolute value
    abs_l1 = np.abs(l1_arr)
    # Find two lowest distinct minima (rough approx)
    # We sort the indices by value
    sorted_indices_L1 = np.argsort(abs_l1)

    # Pick the best 2 distinct candidates (far apart)
    s1_candidates = []
    for idx in sorted_indices_L1:
        th = valid_angles[idx]
        if np.isnan(l1_arr[idx]): continue
        if len(s1_candidates) == 0:
            s1_candidates.append(th)
        elif len(s1_candidates) < 2:
            # Check if this angle is far enough from the first one
            diff = abs(th - s1_candidates[0])
            if diff > 20 and diff < 340:
                s1_candidates.append(th)
        if len(s1_candidates) >= 2: break

    # Find zero crossings for Loop 2 (Toggle)
    abs_l2 = np.abs(np.array(l2_vals))
    sorted_indices_L2 = np.argsort(abs_l2)
    s2_candidates = []
    for idx in sorted_indices_L2:
        th = valid_angles[idx]
        if np.isnan(l2_vals[idx]): continue
        if len(s2_candidates) == 0:
            s2_candidates.append(th)
        elif len(s2_candidates) < 2:
            diff = abs(th - s2_candidates[0])
            if diff > 20 and diff < 340:
                s2_candidates.append(th)
        if len(s2_candidates) >= 2: break

    return sorted(s1_candidates), sorted(s2_candidates)

# --- 5. Visualization ---

def draw_mechanism(ax, theta_2_deg):
    data = solve_mechanism(theta_2_deg)
    ax.clear()
    ax.set_aspect('equal')
    ax.set_xlim(-400, 600)
    ax.set_ylim(-300, 600)
    ax.grid(True, alpha=0.3)
    ax.set_title(f"Mechanism Analysis | Input $\\theta_2$ = {theta_2_deg:.1f}°")

    if data is None:
        ax.text(0, 200, "INVALID CONFIGURATION", color='red', fontsize=14, ha='center')
        return

    A0, B0, O = data['A0'], data['B0'], data['O']
    A, B, C, D = data['A'], data['B'], data['C'], data['D']

    # Identify active singularity for coloring
    tol = 2000 # Visual tolerance
    is_sing_L1 = abs(data['metric_L1']) < tol
    is_sing_L2 = abs(data['metric_L2']) < tol

    # Fixed Frame
    ax.plot([A0[0], B0[0]], [A0[1], B0[1]], 'k--', lw=2, alpha=0.5)
    ax.plot(O[0], O[1], 'kx', ms=8)

    # Slot
    slot = matplotlib.patches.Circle(O, r, color='gray', fill=False, ls='--')
    ax.add_patch(slot)

    # Links
    ax.plot([A0[0], A[0]], [A0[1], A[1]], 'b-', lw=3, label="Crank")

    # Ternary Link Visual
    poly = Polygon([A, C, D], closed=True, color='purple', alpha=0.2)
    ax.add_patch(poly)
    # Highlight Link AD red if L1 singularity
    color_L1 = 'r' if is_sing_L1 else 'purple'
    ax.plot([A[0], D[0]], [A[1], D[1]], color=color_L1, lw=2, ls='-' if not is_sing_L1 else '--')
    ax.plot([A[0], C[0]], [A[1], C[1]], 'purple', lw=2)
    ax.plot([C[0], D[0]], [C[1], D[1]], 'purple', lw=2)

    # Output Chain
    # Highlight B0-B-C if L2 singularity
    color_L2 = 'r' if is_sing_L2 else 'g'
    ax.plot([B[0], C[0]], [B[1], C[1]], color=color_L2, lw=2, label="Coupler", ls='-' if not is_sing_L2 else '--')
    color_L3 = 'r' if is_sing_L2 else 'k'
    ax.plot([B0[0], B[0]], [B0[1], B[1]], color=color_L3, lw=3, label="Output")

    # Joints
    for p in [A0, B0, O, A, B, C, D]:
        ax.plot(p[0], p[1], 'ko', ms=5)

    if is_sing_L1: ax.text(D[0], D[1]+50, "Limit Reach (L1)", color='red', weight='bold')
    if is_sing_L2: ax.text(B[0], B[1]+50, "Toggle (L2)", color='red', weight='bold')

def main():
    # 1. Scan for singular angles before plotting
    s1_angles, s2_angles = scan_singularities()
    print(f"Loop 1 Singularities (Limit): {s1_angles}")
    print(f"Loop 2 Singularities (Toggle): {s2_angles}")

    fig, ax = plt.subplots(figsize=(9, 9))
    plt.subplots_adjust(bottom=0.25) # Make room for buttons

    # Initial Draw
    draw_mechanism(ax, 135)

    # Slider
    ax_slider = plt.axes([0.2, 0.15, 0.65, 0.03])
    slider = Slider(ax_slider, 'Theta 2', 0, 360, valinit=135)

    def update(val):
        draw_mechanism(ax, val)
        fig.canvas.draw_idle()
    slider.on_changed(update)

    # --- BUTTONS ---

    # Button 1: Loop 1 Singularity A
    ax_b1 = plt.axes([0.1, 0.05, 0.18, 0.05])
    btn1 = Button(ax_b1, f'L1 Limit\n{s1_angles[0]:.1f}°', hovercolor='0.975')

    def go_s1_a(event):
        slider.set_val(s1_angles[0])
    btn1.on_clicked(go_s1_a)

    # Button 2: Loop 1 Singularity B
    ax_b2 = plt.axes([0.3, 0.05, 0.18, 0.05])
    btn2 = Button(ax_b2, f'L1 Limit\n{s1_angles[1]:.1f}°', hovercolor='0.975')

    def go_s1_b(event):
        slider.set_val(s1_angles[1])
    btn2.on_clicked(go_s1_b)

    # Button 3: Loop 2 Singularity A
    ax_b3 = plt.axes([0.52, 0.05, 0.18, 0.05])
    btn3 = Button(ax_b3, f'L2 Toggle\n{s2_angles[0]:.1f}°', hovercolor='0.975')

    def go_s2_a(event):
        slider.set_val(s2_angles[0])
    btn3.on_clicked(go_s2_a)

    # Button 4: Loop 2 Singularity B
    ax_b4 = plt.axes([0.72, 0.05, 0.18, 0.05])
    btn4 = Button(ax_b4, f'L2 Toggle\n{s2_angles[1]:.1f}°', hovercolor='0.975')

    def go_s2_b(event):
        slider.set_val(s2_angles[1])
    btn4.on_clicked(go_s2_b)

    plt.show()

if __name__ == "__main__":
    main()
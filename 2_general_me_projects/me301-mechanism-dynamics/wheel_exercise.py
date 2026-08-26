#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compound 2-DOF Mechanism: Four-Bar + Five-Bar (Cross Configuration, Strict Separation)
-------------------------------------------------------------------------------------
Four-bar:  a1–a2–a3–a4
Five-bar:  a1–a5–a6–a7–a4  (crank a5 at A0, rocker tip shares theta14)

Position analysis → only angles (theta13, theta14, theta16, theta17)
Drawing           → computes coordinates from angles.

Color code:
  a2,a3 → orange   (four-bar)
  a4    → red      (shared rocker)
  a5,a6,a7 → purple (five-bar)
"""

import matplotlib
matplotlib.use('TkAgg') 
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button


# ==============================================================
# === DRAWING ==================================================
# ==============================================================

def draw_mechanism(ax, params, theta12, theta15):
    ax.cla()
    # --- Parameters ---
    x0, y0 = 0, 0      # center of circle
    R = 2.0            # radius
    # --- Full gray circle ---
    theta_full = np.linspace(0, 2*np.pi, 400)
    x_full = x0 + R * np.cos(theta_full)
    y_full = y0 + R * np.sin(theta_full)
    ax.plot(x_full, y_full, color='gray', lw=2)

    a1,a2,a3,a4,a5,a6,a7 = params
    A0 = np.array([0,0])
    B0 = np.array([a1,0])

    # ---- Position Analysis ----
    angles = position_analysis(params, theta12, theta15)
    if angles is None:
        ax.text(0,0,"No real configuration",color='r')
        return

    theta13, theta14, theta16, theta17 = angles[0], angles[1], angles[2], angles[3]

    # ---- Draw Four-bar ----
    if theta14 is not None:
        A = A0 + np.array([a2*np.cos(theta12), a2*np.sin(theta12)])
        B = B0 + np.array([a4*np.cos(theta14), a4*np.sin(theta14)])
        ax.plot([A0[0], B0[0]], [A0[1], B0[1]], 'red', lw=2)
        ax.plot([A0[0], A[0]], [A0[1], A[1]], color='orange', lw=2, label='a₂')
        ax.plot([A[0], B[0]], [A[1], B[1]], color='orange', lw=2, label='a₃')
        ax.plot([B0[0], B[0]], [B0[1], B[1]], color='red', lw=2, zorder=10, label='a₄')

    # ---- Draw Five-bar ----
    if theta17 is not None:
        C = A0 + np.array([a5*np.cos(theta15), a5*np.sin(theta15)])
        D = B + np.array([a7*np.cos(theta17), a7*np.sin(theta17)])
        ax.plot([A0[0], C[0]], [A0[1], C[1]], '#8000FF', lw=2, label='a₅')
        ax.plot([C[0], D[0]], [C[1], D[1]], '#8000FF', lw=2, label='a₆')
        ax.plot([D[0], B[0]], [D[1], B[1]], 'k', lw=2, label='a₇')

        ax.scatter([A0[0], A[0], B0[0], B[0], C[0], D[0]],
                [A0[1], A[1], B0[1], B[1], C[1], D[1]], color='k', zorder=6)
        # --- Arc ---
        gamma_17=np.pi/4
        d_wheel=0.2
        x0, y0 = D[0]-(R-d_wheel)*np.cos(theta17+gamma_17), D[1]-(R-d_wheel)*np.sin(theta17+gamma_17)      # center of circle
        x_c,y_c = D[0]+d_wheel*np.cos(theta17+gamma_17), D[1]+d_wheel*np.sin(theta17+gamma_17) 
        theta_start, theta_end = theta17+gamma_17-np.pi/3, theta17+gamma_17+np.pi/3  # arc limits in degrees
        theta_arc = np.linspace(theta_start, theta_end, 200)
        x_arc = x0 + R * np.cos(theta_arc)
        y_arc = y0 + R * np.sin(theta_arc)
        ax.plot(x_arc, y_arc, color='black', lw=4)
        ax.plot([D[0],x_c], [D[1],y_c], color='black', lw=2)
        ax.plot([B[0],x_arc[-1]], [B[1],y_arc[-1]], color='black', lw=2)


    ax.set_aspect('equal')
    ax.grid(True)
    ax.set_xlim(-4,4)
    ax.set_ylim(-4,4)

# ==============================================================
# === POSITION ANALYSIS (ANGLES ONLY) ==========================
# ==============================================================

def position_analysis(params, theta12, theta15):
    """Compute and return all joint angles without any coordinates."""
    a1,a2,a3,a4,a5,a6,a7 = params
    theta13, theta14 = fourbar_angles(a1,a2,a3,a4,theta12)
    if theta14 is None:
        return None
    theta16, theta17 = fivebar_angles(a1,a4,a5,a6,a7,theta14,theta15)
    return theta13,theta14, theta16, theta17

# ==============================================================
# === FOUR-BAR SOLVER ==========================================
# ==============================================================

def fourbar_angles(a1,a2,a3,a4,theta12_deg):
    """Return theta13, theta14 for given theta12."""
    theta12 = np.deg2rad(theta12_deg)

    # Freundstein coefficients
    K1 = a1 / a2
    K2 = a1 / a4
    K3 = (a1 ** 2 + a2 ** 2 + a4 ** 2 - a3 ** 2) / (2 * a2 * a4)

    # Trig coefficients
    A = K1 - np.cos(theta12)
    B = -np.sin(theta12)
    C = K2 * np.cos(theta12) - K3

    disc = A ** 2 + B ** 2 - C ** 2
    if np.any(disc < 0):
        return None, None, None, None

    sin14_1 = (B * C + A * np.sqrt(disc)) / (A ** 2 + B ** 2)
    sin14_2 = (B * C - A * np.sqrt(disc)) / (A ** 2 + B ** 2)

    cos14_1 = (C - B * sin14_1) / A
    cos14_2 = (C - B * sin14_2) / A

    theta14_1 = np.arctan2(sin14_1, cos14_1)
    theta14_2 = np.arctan2(sin14_2, cos14_2)

    # ---- Compute θ13 geometrically ----
    def compute_theta13(theta14):
        return np.arctan2(a4 * np.sin(theta14) - a2 * np.sin(theta12)
                          , a1 + a4 * np.cos(theta14) - a2 * np.cos(theta12))

    theta13_1 = compute_theta13(theta14_1)
    theta13_2 = compute_theta13(theta14_2)

    return  np.rad2deg(theta13_1), np.rad2deg(theta14_1)



# ==============================================================
# === FIVE-BAR SOLVER (theta14 as input) ===========================
# ==============================================================
def fivebar_angles(a1, a4, a5, a6, a7, theta14_deg, theta15_deg):
    """Return theta16, theta17 for given theta14,and theta15."""
    ## Write your code for solution of the fourbar here
    # Convert input degrees to radians for calculation
    theta14 = np.deg2rad(theta14_deg)
    theta15 = np.deg2rad(theta15_deg)

    # 1. Calculate the (x, y) coordinates of points B and C

    # Point B is relative to B0, which is at (a1, 0)
    xB = a1 + a4 * np.cos(theta14)
    yB = a4 * np.sin(theta14)

    # Point C is relative to A0, which is at (0, 0)
    xC = a5 * np.cos(theta15)
    yC = a5 * np.sin(theta15)

    # 2. Find the distance and angle of the "new" ground link C-B
    dx = xB - xC
    dy = yB - yC
    d_CB_sq = dx ** 2 + dy ** 2
    d_CB = np.sqrt(d_CB_sq)  # This is the distance between C and B

    # Angle of the vector from C to B
    phi = np.arctan2(dy, dx)

    # 3. Solve the C-D-B triangle using the Law of Cosines
    # We need the internal angle at C (angle B-C-D), let's call it 'alpha'

    # Argument for arccos: (a^2 + b^2 - c^2) / (2ab)
    cos_arg_alpha = (a6 ** 2 + d_CB_sq - a7 ** 2) / (2 * a6 * d_CB)

    # 4. Detect if there is no solution (links can't connect)
    if (np.abs(cos_arg_alpha) > 1) or (d_CB == 0):
        # Triangle inequality is violated or points B and C are coincident
        return None, None

    # Internal angle at C
    alpha = np.arccos(cos_arg_alpha)

    # 5. Calculate the absolute angles for theta16 and theta17
    # This gives one of the two possible "elbow" configurations.
    # theta16 is the angle of link C->D
    theta16 = phi - alpha  # (The other solution is phi + alpha)

    # To find theta17, we find the internal angle at B (angle C-B-D), 'beta'
    cos_arg_beta = (a7 ** 2 + d_CB_sq - a6 ** 2) / (2 * a7 * d_CB)

    # We shouldn't need to re-check the condition, but good practice
    if (np.abs(cos_arg_beta) > 1):
        return None, None

    beta = np.arccos(cos_arg_beta)

    # Angle of the vector from B to C is (phi + pi)
    phi_BC = phi + np.pi

    # theta17 is the angle of link B->D
    theta17 = phi_BC + beta  # (This corresponds to the (phi - alpha) solution)

    # Return the angles in degrees
    return np.rad2deg(theta16), np.rad2deg(theta17)

def perfect_circle(params, theta12_deg, theta15_deg):
    a1, a2, a3, a4, a5, a6, a7 = params

    # 1. Solve the first four-bar loop (A0-A-B-B0) to find Point B
    # We need theta14 to find the position of B
    # NOTE: fourbar_angles might return two solutions (assemblies).
    # You must pick one and use it consistently.
    theta13_sol, theta14_sol = fourbar_angles(a1, a2, a3, a4, theta12_deg)

    if theta14_sol is None:
        return None  # No solution for the 4-bar

    theta14_rad = np.deg2rad(theta14_sol)
    theta15_rad = np.deg2rad(theta15_deg)

    # 2. Get (x, y) coordinates of B and C
    # A0 is at (0, 0), B0 is at (a1, 0)
    xB = a1 + a4 * np.cos(theta14_rad)
    yB = a4 * np.sin(theta14_rad)
    xC = a5 * np.cos(theta15_rad)
    yC = a5 * np.sin(theta15_rad)

    # 3. Find Point D by circle-circle intersection (from B and C)
    d_CB = np.sqrt((xB - xC) ** 2 + (yB - yC) ** 2)

    # Check if links a6 and a7 can connect B and C
    if (d_CB > a6 + a7) or (d_CB < np.abs(a6 - a7)) or (d_CB == 0):
        return None  # No solution for the C-D-B dyad

    # Law of Cosines on triangle C-B-D to find angle at B
    # (a^2 + b^2 - c^2) / (2ab)
    cos_arg = (d_CB ** 2 + a7 ** 2 - a6 ** 2) / (2 * d_CB * a7)

    # Clip to avoid floating point errors > 1.0
    alpha = np.arccos(np.clip(cos_arg, -1.0, 1.0))

    # Angle of the vector from B to C
    phi_BC = np.arctan2(yC - yB, xC - xB)

    # Angle of link B-D (one of two "elbow" solutions)
    theta_BD = phi_BC - alpha

    # 4. Calculate final (x, y) of D
    xD = xB + a7 * np.cos(theta_BD)
    yD = yB + a7 * np.sin(theta_BD)

    return (xD, yD)


# ==============================================================
# === MAIN =====================================================
# ==============================================================

def main():
    a1,a2,a3,a4,a5,a6,a7 = 0.5,0.5,1.5,1.5,0.5,1.5,1.0
    theta12, theta15 = 120, 120
    params = [a1,a2,a3,a4,a5,a6,a7]

    fig, ax = plt.subplots(figsize=(8,6))
    plt.subplots_adjust(left=0.25,bottom=0.3)
    draw_mechanism(ax, params, theta12, theta15)


    # --- Sliders ---
    slider_height, slider_spacing, start_y = 0.01, 0.02, 0.25
    sliders = {}
    names = ['a1','a2','a3','a4','a5','a6','a7','theta12','theta15']
    inits = [a1,a2,a3,a4,a5,a6,a7,theta12,theta15]
    mins  = [0.2,0.2,1.0,1.0,0.2,0.5,0.5,-360,-360]
    maxs  = [1.0,1.0,3.0,3.0,1.0,2.0,2.0,360,360]


    for i,(n,val,mi,ma) in enumerate(zip(names,inits,mins,maxs)):
        ax_slider = plt.axes([0.25,start_y - i*slider_spacing,0.65,slider_height])
        sliders[n] = Slider(ax_slider,n,mi,ma,valinit=val)

    def update(val=None):
        vals = [sliders[n].val for n in names[:-2]]
        draw_mechanism(ax, vals, np.deg2rad(sliders['theta12'].val), np.deg2rad(sliders['theta15'].val))
        fig.canvas.draw_idle()
    for s in sliders.values():
        s.on_changed(update)

    # --- Buttons ---
    button_positions = {'closed':[0.025,0.5], 'open':[0.025,0.6]}
    btns = {}
    for name,pos in button_positions.items():
        btns[name] = Button(plt.axes([pos[0],pos[1],0.15,0.08]),
                            name.capitalize(), color='lightgray', hovercolor='0.9')

    # Function to apply preset values
    def apply_values(vals):
        for key, val in zip(names, vals):
            sliders[key].set_val(val)  # update slider value (triggers update)


    btns['closed'].on_clicked(lambda e: apply_values([0.5,0.5,1.5,1.5,0.5,1.5,1.0,120,120]))
    btns['open'].on_clicked(lambda e: apply_values([0.5,0.5,1.5,1.5,0.5,1.5,1.0,180,180]))

    plt.show()

if __name__ == "__main__":
    main()

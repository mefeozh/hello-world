#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analytic Solution and Visualization of Four-Bar Mechanism
---------------------------------------------------------
Real-time θ14(θ12) plot in separate window,
with all sliders and controls placed on the mechanism figure.
"""
import matplotlib
matplotlib.use('TkAgg') 
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button


# ---------- Analytic Solution ----------
def fourbar_solution(a1, a2, a3, a4, theta12_deg):
    """Analytic solution for θ14 (two configurations)."""
    theta12 = np.deg2rad(theta12_deg)

    # Freundstein coefficients
    K1 = a1 / a2
    K2 = a1 / a4
    K3 = (a1**2 + a2**2 + a4**2 - a3**2) / (2 * a2 * a4)

    # Trig coefficients
    A = K1 - np.cos(theta12)
    B = -np.sin(theta12)
    C = K2 * np.cos(theta12) - K3

    disc = A**2 + B**2 - C**2
    if np.any(disc < 0):
        return None, None, None, None

    sin14_1 = (B * C + A* np.sqrt(disc)) / (A**2 + B**2)
    sin14_2 = (B * C - A* np.sqrt(disc)) / (A**2 + B**2)

    cos14_1 = (C - B * sin14_1) / A
    cos14_2 = (C - B * sin14_2) / A

    theta14_1 = np.arctan2(sin14_1, cos14_1)
    theta14_2 = np.arctan2(sin14_2, cos14_2)

    # ---- Compute θ13 geometrically ----
    def compute_theta13(theta14):
        return  np.arctan2( a4*np.sin(theta14)-a2*np.sin(theta12)
                        ,a1+a4*np.cos(theta14)-a2*np.cos(theta12))
    theta13_1 = compute_theta13(theta14_1)
    theta13_2 = compute_theta13(theta14_2)

    return np.rad2deg(theta14_1), np.rad2deg(theta14_2)\
          ,np.rad2deg(theta13_1),np.rad2deg(theta13_2)


# ---------- Mechanism Drawing ----------
def draw_fourbar(ax, a1, a2, a3, a4, theta12_deg):
    """Draw current configuration of the 4-bar mechanism."""
    A0 = np.array([0, 0])
    B0 = np.array([a1, 0])
    theta12 = np.deg2rad(theta12_deg)
    A = np.array([a2 * np.cos(theta12), a2 * np.sin(theta12)])

    result = fourbar_solution(a1, a2, a3, a4, theta12_deg)

    ax.clear()
    if result[0] is None:
      ax.set_title(f"Four-Bar Mechanism\nθ12 = {theta12_deg:.1f}° ,|θ13-θ14| = ")
    else:
      gamma = np.abs(result[0]-result[2]) % 180
      ax.set_title(f"Four-Bar Mechanism\nθ12 = {theta12_deg:.1f}° ,|θ13-θ14| = {(gamma):.1f}°")
    ax.axis("equal")
    ax.grid(True)
    ax.set_xlim(-2, 4)
    ax.set_ylim(-4, 5)
    
    ax.plot([A0[0], A[0]], [A0[1], A[1]], "r-", lw=2, label="Input link a2")
    ax.plot([A0[0], B0[0]], [A0[1], B0[1]], "k-", lw=3, label="Ground a1")


    if result[0] is None:
        ax.text(-1.5, 2, "No real solution (A²+B²<C²)", color="red", fontsize=12)
        return

    for i, theta14_deg in enumerate(result[:2]):
        color = "b" if i == 0 else "g"
        theta14 = np.deg2rad(theta14_deg)
        B = B0 + np.array([a4 * np.cos(theta14), a4 * np.sin(theta14)])
        ax.plot([A[0], B[0]], [A[1], B[1]], color=color, lw=2, label=f"Coupler (sol {i+1})")
        ax.plot([B0[0], B[0]], [B0[1], B[1]], color=color, ls="--", lw=2)
        ax.scatter([A0[0], A[0], B[0], B0[0]], [A0[1], A[1], B[1], B0[1]], s=60, color=color)


# ---------- θ14(θ12) Plot ----------
def compute_theta14_curve(a1, a2, a3, a4):
    """Compute θ14 vs θ12 for both configurations."""
    theta12_vals = np.linspace(-360, 360, 720)
    theta14_open, theta14_cross = [], []

    for th in theta12_vals:
        result = fourbar_solution(a1, a2, a3, a4, th)
        if result[0] is None:
            theta14_open.append(np.nan)
            theta14_cross.append(np.nan)
        else:
            theta14_open.append(result[0])
            theta14_cross.append(result[1])

    return theta12_vals, np.array(theta14_open), np.array(theta14_cross)


def create_angle_plot(a1, a2, a3, a4):
    """Create separate window for θ14 vs θ12 curve."""
    fig2, ax2 = plt.subplots()
    theta12_vals, theta14_open, theta14_cross = compute_theta14_curve(a1, a2, a3, a4)
    open_line, = ax2.plot(theta12_vals, theta14_open, "b-", label="Open configuration")
    cross_line, = ax2.plot(theta12_vals, theta14_cross, "g-", label="Crossed configuration")
    pt_open, = ax2.plot([], [], "bo", ms=8)
    pt_cross, = ax2.plot([], [], "go", ms=8)
    ax2.set_xlabel("θ12 (deg)")
    ax2.set_ylabel("θ14 (deg)")
    ax2.set_title("Output angle θ14 vs Input angle θ12")
    ax2.set_ylim([-200,200])
    ax2.grid(True)
    return fig2, ax2, open_line, cross_line, pt_open, pt_cross


# ---------- Main ----------
def main():
    # Initial parameters
    a1, a2, a3, a4 = 1.5, 1.0, 2, 1.75
    theta12 = 90.0

    # Figure 1: Mechanism
    fig1, ax_mech = plt.subplots(figsize=(7, 6))
    plt.subplots_adjust(left=0.25, bottom=0.35)
    draw_fourbar(ax_mech, a1, a2, a3, a4, theta12)

    # ---------- Change In Position ----------
    example_1_ax = plt.axes([0.025, 0.3, 0.15, 0.08])
    button_example_1 = Button(example_1_ax, 'change\n point', color='lightgray', hovercolor='0.9')
    def example_1(event):
        values = [1.0,1.0,1.5,1.5]
        for i,s in enumerate([s_a1, s_a2, s_a3, s_a4]):
            s.set_val(values[i])
    button_example_1.on_clicked(example_1)
    # ---------- Crank-Rocker ----------
    example_2_ax = plt.axes([0.025, 0.6, 0.15, 0.08])
    button_example_2 = Button(example_2_ax, 'crank-rocker', color='lightgray', hovercolor='0.9')
    def example_2(event):
        values = [1.0,0.5,1.5,1.5]
        for i,s in enumerate([s_a1, s_a2, s_a3, s_a4]):
            s.set_val(values[i])
    button_example_2.on_clicked(example_2)

    # ---------- Double-Rocker ----------
    example_3_ax = plt.axes([0.025, 0.5, 0.15, 0.08])
    button_example_3 = Button(example_3_ax, 'double-rocker', color='lightgray', hovercolor='0.9')
    def example_3(event):
        values = [1.0,1.5,1.0,1.5]
        for i,s in enumerate([s_a1, s_a2, s_a3, s_a4]):
            s.set_val(values[i])
    button_example_3.on_clicked(example_3)

 
    # ---------- Singularity ----------
    example_4_ax = plt.axes([0.025, 0.4, 0.15, 0.08])
    button_example_4 = Button(example_4_ax, 'sigularity', color='lightgray', hovercolor='0.9')
    def example_4(event):
        values = [1.0,1.0,1.0,1.0]
        for i,s in enumerate([s_a1, s_a2, s_a3, s_a4]):
            s.set_val(values[i])
    button_example_4.on_clicked(example_4)
  
      # ---------- Change In Direction ----------
    example_5_ax = plt.axes([0.025, 0.2, 0.15, 0.08])
    button_example_5 = Button(example_5_ax, 'change\n direction', color='lightgray', hovercolor='0.9')
    def example_5(event):
        values = [1.5,1.25,1.5,1.75]
        for i,s in enumerate([s_a1, s_a2, s_a3, s_a4]):
            s.set_val(values[i])
    button_example_5.on_clicked(example_5)
   
    # ---------- Sliders (on fig1 only) ----------
    ax_a1 = plt.axes([0.25, 0.25, 0.65, 0.03])
    ax_a2 = plt.axes([0.25, 0.20, 0.65, 0.03])
    ax_a3 = plt.axes([0.25, 0.15, 0.65, 0.03])
    ax_a4 = plt.axes([0.25, 0.10, 0.65, 0.03])
    ax_t12 = plt.axes([0.25, 0.05, 0.65, 0.03])

    s_a1 = Slider(ax_a1, 'a1', 0.5, 3.0, valinit=a1)
    s_a2 = Slider(ax_a2, 'a2', 0.5, 3.0, valinit=a2)
    s_a3 = Slider(ax_a3, 'a3', 0.5, 3.0, valinit=a3)
    s_a4 = Slider(ax_a4, 'a4', 0.5, 3.0, valinit=a4)
    s_t12 = Slider(ax_t12, 'θ12 (deg)', -360, 360, valinit=theta12)
    
    # Figure 2: θ14–θ12 curve
    fig2, ax2, open_line, cross_line, pt_open, pt_cross = create_angle_plot(a1, a2, a3, a4)

    # ---------- Update ----------
    def update(val):
        draw_fourbar(ax_mech, s_a1.val, s_a2.val, s_a3.val, s_a4.val, s_t12.val)
        fig1.canvas.draw_idle()

        th12_vals, th14_open, th14_cross = compute_theta14_curve(s_a1.val, s_a2.val, s_a3.val, s_a4.val)
        open_line.set_ydata(th14_open)
        cross_line.set_ydata(th14_cross)

        th14_now = fourbar_solution(s_a1.val, s_a2.val, s_a3.val, s_a4.val, s_t12.val)
        if th14_now[0] is not None:
            pt_open.set_data([s_t12.val], [th14_now[0]])
            pt_cross.set_data([s_t12.val], [th14_now[1]])
        else:
            pt_open.set_data([], [])
            pt_cross.set_data([], [])

        fig2.canvas.draw_idle()

    for s in [s_a1, s_a2, s_a3, s_a4, s_t12]:
        s.on_changed(update)

    # ---------- Reset ----------
    reset_ax = plt.axes([0.8, 0.9, 0.1, 0.04])
    button = Button(reset_ax, 'Reset', color='lightgray', hovercolor='0.9')
    def reset(event):
        for s in [s_a1, s_a2, s_a3, s_a4, s_t12]:
            s.reset()

    button.on_clicked(reset)

    plt.show()


if __name__ == "__main__":
    main()

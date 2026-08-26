#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Slider–Crank Mechanism with Arbitrary Prismatic Direction and Offset
--------------------------------------------------------------------
Real-time s(θ2) and θ3(θ2) plot in a separate window,
with all sliders and controls placed on the mechanism figure.
Author: METU - MRS Lab Example
"""

import matplotlib
matplotlib.use('TkAgg') 
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button


# ---------------------------------------------------------
# Analytic solution for general slider–crank
# ---------------------------------------------------------
def slider_crank_solution(a2, a3, h, theta2_deg, thetas_deg):
    """
    Analytic solution for slider–crank with arbitrary prismatic direction and offset.
    """
    theta2 = np.deg2rad(theta2_deg)
    thetas = np.deg2rad(thetas_deg)

    # Unit vectors
    u = np.array([np.cos(thetas), np.sin(thetas)])   # slider axis direction
    n = np.array([-np.sin(thetas), np.cos(thetas)])  # perpendicular
    A = np.array([a2 * np.cos(theta2), a2 * np.sin(theta2)])  # crank tip

    Ahn = A - h * n
    Au = np.dot(Ahn, u)
    AA = np.dot(Ahn, Ahn)
    disc = (2 * Au)**2 - 4 * (AA - a3**2)
    if disc < 0:
        return None, None

    s1 = (2 * Au + np.sqrt(disc)) / 2
    s2 = (2 * Au - np.sqrt(disc)) / 2

    def compute_theta3(s):
        B = h * n + s * u
        vec = B - A
        return np.rad2deg(np.arctan2(vec[1], vec[0]))

    theta3_1 = compute_theta3(s1)
    theta3_2 = compute_theta3(s2)

    return (s1, theta3_1), (s2, theta3_2)


# ---------------------------------------------------------
# Mechanism drawing
# ---------------------------------------------------------
def draw_slider_crank(ax, a2, a3, h, theta2_deg, thetas_deg):
    """Draws the slider–crank configuration."""
    ax.clear()
    ax.set_title(f"Slider–Crank with Offset and Inclined Axis\nθ2={theta2_deg:.1f}°, θs={thetas_deg:.1f}°, h={h:.2f}")
    ax.axis("equal")
    ax.grid(True)
    ax.set_xlim(-3, 4)
    ax.set_ylim(-4, 5)

    O = np.array([0, 0])
    theta2 = np.deg2rad(theta2_deg)
    thetas = np.deg2rad(thetas_deg)

    # Axis direction
    u = np.array([np.cos(thetas), np.sin(thetas)])
    n = np.array([-np.sin(thetas), np.cos(thetas)])
    A = np.array([a2 * np.cos(theta2), a2 * np.sin(theta2)])

    # Axis line
    line_pts = np.array([h * n + t * u for t in np.linspace(-3, 4, 2)])
    ax.plot(line_pts[:, 0], line_pts[:, 1], "k--", lw=1, label="Slider axis")

    result1, result2 = slider_crank_solution(a2, a3, h, theta2_deg, thetas_deg)
    if result1 is None:
        ax.text(-4, 4, "No Real Solution", color="red", fontsize=12)
        ax.legend()
        return

    for i, (s, theta3_deg) in enumerate([result1, result2]):
        color = "b" if i == 0 else "g"
        B = h * n + s * u
        ax.plot([O[0], A[0]], [O[1], A[1]], "r-", lw=2)
        ax.plot([A[0], B[0]], [A[1], B[1]], color=color, lw=2, label=f"Rod a3 (sol {i+1})")
        ax.scatter([O[0], A[0], B[0]], [O[1], A[1], B[1]], s=60, color=color)
        # ax.text(B[0] + 0.05, B[1], f"s={s:.2f}", color=color)


# ---------------------------------------------------------
# Compute curves for second figure
# ---------------------------------------------------------
def compute_slider_crank_curves(a2, a3, h, thetas_deg):
    theta2_vals = np.linspace(-360, 360, 720)
    s_open, s_cross, th3_open, th3_cross = [], [], [], []
    for th in theta2_vals:
        res1, res2 = slider_crank_solution(a2, a3, h, th, thetas_deg)
        if res1 is None:
            s_open.append(np.nan)
            s_cross.append(np.nan)
            th3_open.append(np.nan)
            th3_cross.append(np.nan)
        else:
            s_open.append(res1[0])
            s_cross.append(res2[0])
            th3_open.append(res1[1])
            th3_cross.append(res2[1])
    return theta2_vals, np.array(s_open), np.array(s_cross), np.array(th3_open), np.array(th3_cross)


def create_slider_plot(a2, a3, h, thetas_deg):
    """Create separate window for s(θ2) and θ3(θ2) curves."""
    fig2, (ax_s, ax_t3) = plt.subplots(2, 1, figsize=(6, 7))
    fig2.subplots_adjust(hspace=0.4)

    th2, s_open, s_cross, th3_open, th3_cross = compute_slider_crank_curves(a2, a3, h, thetas_deg)

    open_s_line, = ax_s.plot(th2, s_open, "b-", label="s (open)")
    cross_s_line, = ax_s.plot(th2, s_cross, "g-", label="s (cross)")
    pt_s_open, = ax_s.plot([], [], "bo", ms=8)
    pt_s_cross, = ax_s.plot([], [], "go", ms=8)
    ax_s.set_title("Slider displacement s vs θ2")
    ax_s.set_xlabel("θ2 (deg)")
    ax_s.set_ylabel("s")
    ax_s.grid(True)
    ax_s.set_ylim(-4.5, 4.5)

    open_t3_line, = ax_t3.plot(th2, th3_open, "b-", label="θ3 (open)")
    cross_t3_line, = ax_t3.plot(th2, th3_cross, "g-", label="θ3 (cross)")
    pt_t3_open, = ax_t3.plot([], [], "bo", ms=8)
    pt_t3_cross, = ax_t3.plot([], [], "go", ms=8)
    ax_t3.set_title("Connecting rod angle θ3 vs θ2")
    ax_t3.set_xlabel("θ2 (deg)")
    ax_t3.set_ylabel("θ3 (deg)")
    ax_t3.grid(True)

    return fig2, (ax_s, ax_t3), (open_s_line, cross_s_line, pt_s_open, pt_s_cross,
                                 open_t3_line, cross_t3_line, pt_t3_open, pt_t3_cross)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():
    a2, a3, h = 1.0, 2.0, 0.5
    theta2, thetas = 45.0, 0.0

    # Figure 1: mechanism
    fig1, ax = plt.subplots(figsize=(7, 6))
    plt.subplots_adjust(left=0.25, bottom=0.40)
    draw_slider_crank(ax, a2, a3, h, theta2, thetas)
    # ---------- Dead Center ----------
    example_1_ax = plt.axes([0.025, 0.6, 0.15, 0.08])
    button_example_1 = Button(example_1_ax, 'Dead\n center', color='lightgray', hovercolor='0.9')
    def example_1(event):
        values = [1.0,2.0,1.0]
        for i,s in enumerate([s_a2, s_a3,s_h]):
            s.set_val(values[i])
    button_example_1.on_clicked(example_1)

    # ---------- Dead Center ----------
    example_2_ax = plt.axes([0.025, 0.5, 0.15, 0.08])
    button_example_2= Button(example_2_ax, 'Dead\n center 2', color='lightgray', hovercolor='0.9')
    def example_2(event):
        values = [2.0,2.0,.0]
        for i,s in enumerate([s_a2, s_a3,s_h]):
            s.set_val(values[i])
    button_example_2.on_clicked(example_2)


    # Sliders (attached to fig1)
    ax_a2 = plt.axes([0.25, 0.30, 0.65, 0.03])
    ax_a3 = plt.axes([0.25, 0.25, 0.65, 0.03])
    ax_h = plt.axes([0.25, 0.20, 0.65, 0.03])
    ax_t2 = plt.axes([0.25, 0.15, 0.65, 0.03])
    ax_ts = plt.axes([0.25, 0.10, 0.65, 0.03])

    s_a2 = Slider(ax_a2, 'a2 (crank)', 0.5, 3.0, valinit=a2)
    s_a3 = Slider(ax_a3, 'a3 (rod)', 0.5, 3.0, valinit=a3)
    s_h = Slider(ax_h, 'h (offset)', -2.0, 2.0, valinit=h)
    s_t2 = Slider(ax_t2, 'θ2 (deg)', -360.0, 360.0, valinit=theta2)
    s_ts = Slider(ax_ts, 'θs (axis dir)', -90.0, 90.0, valinit=thetas)

    # Figure 2: s(θ2) and θ3(θ2)
    fig2, (ax_s, ax_t3), lines = create_slider_plot(a2, a3, h, thetas)
    (open_s_line, cross_s_line, pt_s_open, pt_s_cross,
     open_t3_line, cross_t3_line, pt_t3_open, pt_t3_cross) = lines

    # Update function
    def update(val):
        draw_slider_crank(ax, s_a2.val, s_a3.val, s_h.val, s_t2.val, s_ts.val)
        fig1.canvas.draw_idle()

        th2, s_open, s_cross, th3_open, th3_cross = compute_slider_crank_curves(
            s_a2.val, s_a3.val, s_h.val, s_ts.val)

        # Update displacement curves
        open_s_line.set_ydata(s_open)
        cross_s_line.set_ydata(s_cross)

        # Update rod-angle curves
        open_t3_line.set_ydata(th3_open)
        cross_t3_line.set_ydata(th3_cross)

        # Current position markers
        res1, res2 = slider_crank_solution(s_a2.val, s_a3.val, s_h.val, s_t2.val, s_ts.val)
        if res1 is not None:
            pt_s_open.set_data([s_t2.val], [res1[0]])
            pt_s_cross.set_data([s_t2.val], [res2[0]])
            pt_t3_open.set_data([s_t2.val], [res1[1]])
            pt_t3_cross.set_data([s_t2.val], [res2[1]])
        else:
            for pt in [pt_s_open, pt_s_cross, pt_t3_open, pt_t3_cross]:
                pt.set_data([], [])

        fig2.canvas.draw_idle()

    for s in [s_a2, s_a3, s_h, s_t2, s_ts]:
        s.on_changed(update)

    # Reset
    reset_ax = plt.axes([0.8, 0.92, 0.1, 0.04])
    button = Button(reset_ax, 'Reset', color='lightgray', hovercolor='0.9')

    def reset(event):
        for s in [s_a2, s_a3, s_h, s_t2, s_ts]:
            s.reset()

    button.on_clicked(reset)

    plt.show()


if __name__ == "__main__":
    main()

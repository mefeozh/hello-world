#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Numerical Solution and Visualization of Quick Return with Double Slider Mechanism
---------------------------------------------------------------------------------
Author: METU - MRS Lab Example

This uses a numerical root-finder (fsolve) to solve the nonlinear equations:
(1) s43*cosθ14 = a2*cosθ12
(2) -s15 + s43*sinθ14 = a1 + a2*sinθ12
(3) a4*cosθ14 = s16
(4) a4*sinθ14 - s15 = a1
"""

import matplotlib
matplotlib.use('TkAgg') 
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from scipy.optimize import fsolve
import sympy as sp

# -------------------------------------------------------------------
# Build symbolic functions (Jacobian and equations)
# -------------------------------------------------------------------
def build_jacobian_functions():
    """Precompute and return callable functions F_func and J_func."""
    s43, s15, s16 = sp.symbols('s43 s15 s16', real=True)
    a1, a2, a4 = sp.symbols('a1 a2 a4', real=True)
    theta12, theta14 = sp.symbols('theta12 theta14', real=True)

    # Equations
    f1 = s43 * sp.cos(theta14) - a2 * sp.cos(theta12)
    f2 = -s15 + s43 * sp.sin(theta14) -  a2 * sp.sin(theta12)
    f3 = a4 * sp.cos(theta14) - s16
    f4 = a4 * sp.sin(theta14) - s15 - a1

    F = sp.Matrix([f1, f2, f3, f4])
    X = sp.Matrix([s43, s15, s16, theta14])

    # Jacobian
    J = F.jacobian(X)

    sp.pretty_print(F)
    sp.pretty_print(J)

    # Lambdify numerical evaluation
    F_func = sp.lambdify((s43, s15, s16, theta14, a1, a2, a4, theta12), F, "numpy")
    J_func = sp.lambdify((s43, s15, s16, theta14, a1, a2, a4, theta12), J, "numpy")

    return F_func, J_func

# -------------------------------------------------------------------
# Numerical solver
# -------------------------------------------------------------------
_current_config = 0  # 0 = open configuration, 1 = crossed configuration
_last_state = None  # Global memory for current configuration
_filter_enabled = False  # If True, reject physically impossible configurations

def double_slider_solution(a1, a2, a4, theta12_deg, F_func, J_func, x0=None):
    """
    Solve the Double-Slider Quick Return mechanism using Newton–Raphson.
    Uses a single configuration depending on _current_config (0=open, 1=crossed).
    """
    global _current_config
    theta12 = np.deg2rad(theta12_deg)

    # Initial guess based on config mode
    default_guesses = [
        np.array([1.0, 4.0, 0.0, np.deg2rad(90)], dtype=float),    # crossed
        np.array([1.0, 1.0, 4.0, np.deg2rad(30)], dtype=float)   # open
    ]
    x = np.array(x0, dtype=float) if x0 is not None else default_guesses[_current_config]

    alpha = 1
    tol = 1e-9
    max_iter = 50

    for k in range(max_iter):
        s43v, s15v, s16v, th14v = x
        Fv = np.array(F_func(s43v, s15v, s16v, th14v, a1, a2, a4, theta12), dtype=float).reshape(-1)
        Jv = np.array(J_func(s43v, s15v, s16v, th14v, a1, a2, a4, theta12), dtype=float)

        try:
            dx = alpha * np.linalg.solve(Jv, -Fv)
        except np.linalg.LinAlgError:
            return None

        x_new = x + dx
        if np.linalg.norm(dx) < tol:
            s43_sol, s15_sol, s16_sol, th14_sol = x_new
             # --- Physical validity check ---
            A = np.array([a2 * np.cos(theta12), a2 * np.sin(theta12)])
            B = np.array([0, -s15_sol])
            C = np.array([s16_sol, a1])
            AB = A - B
            AC = A - C
            between = np.dot(AB, AC) < 0

            if _filter_enabled and not between:
                # print(f"Filtered out impossible config at θ12={theta12_deg:.1f}°")
                return None
            return {
                "theta14_deg": np.rad2deg(th14_sol),
                "s15": s15_sol,
                "s16": s16_sol,
                "s43": s43_sol,
                "x_state": x_new,
            }
        x = x_new

    return None



# -------------------------------------------------------------------
# Drawing function
# -------------------------------------------------------------------
def draw_double_slider(ax, a1, a2, a4, theta12_deg, F_func, J_func):
    global _last_state, _current_config
    ax.clear()
    ax.set_title(f"Double-Slider Quick Return Mechanism\nθ12 = {theta12_deg:.1f}°")
    ax.axis("equal")
    ax.grid(True)
    ax.set_xlim(-3, 5)
    ax.set_ylim(-4, 5)

    theta12 = np.deg2rad(theta12_deg)
    A0 = np.array([0, 0])
    A = A0 + np.array([a2 * np.cos(theta12), a2 * np.sin(theta12)])
    ax.plot([A0[0], A[0]], [A0[1], A[1]], "r-", lw=2, label="Crank a2")

    ax.plot([0, 0], [-a1*5, 0], "k--", lw=2, label="Vertical slider s15")
    ax.plot([0, a1*5], [a1, a1], "k--", lw=2, label="Horizontal slider s16")
    # Use last state for current configuration
    x0 = _last_state["x_state"] if _last_state is not None else None
    sol = double_slider_solution(a1, a2, a4, theta12_deg, F_func, J_func, x0)

    if sol is None:
        ax.text(0.2, 0.2, "No real solution", color="red", fontsize=12)
        return

    _last_state = sol

    theta14 = np.deg2rad(sol["theta14_deg"])
    s15, s16 = sol["s15"], sol["s16"]

    # Points
    B = np.array([0, -s15])
    C = np.array([s16, a1])

    # Color per configuration
    color = "b" if _current_config == 0 else "g"
    label_cfg = "Open config" if _current_config == 0 else "Crossed config"

    # Draw mechanism
    ax.plot([B[0], C[0]], [B[1], C[1]], color=color, lw=2, label=f"{label_cfg} (a4)")
    ax.scatter([0, s16, 0, A[0]], [0, a1, -s15, A[1]], s=50, color=color)
    ax.legend()

def compute_double_slider_curves(a1, a2, a4, F_func=None, J_func=None):
    """Compute θ14, s15, s16 versus θ12 for the current configuration."""
    th12_vals = np.linspace(-180, 180, 360)
    th14_vals, s15_vals, s16_vals = [], [], []

    for th in th12_vals:
        sol = double_slider_solution(a1, a2, a4, th, F_func, J_func)
        if sol is None:
            th14_vals.append(np.nan)
            s15_vals.append(np.nan)
            s16_vals.append(np.nan)
        else:
            th14_vals.append(sol["theta14_deg"])
            s15_vals.append(sol["s15"])
            s16_vals.append(sol["s16"])

    return (
        np.array(th12_vals),
        np.array(th14_vals),
        np.array(s15_vals),
        np.array(s16_vals),
    )

def create_double_slider_plot(a1, a2, a4, F_func=None, J_func=None):
    """Create static θ14, s15, s16 vs θ12 plots for the current configuration."""
    fig2, (ax_t14, ax_s15, ax_s16) = plt.subplots(3, 1, figsize=(6, 8))
    fig2.subplots_adjust(hspace=0.4)

    th12, th14_vals, s15_vals, s16_vals = compute_double_slider_curves(a1, a2, a4, F_func, J_func)

    # θ14 plot
    t14_line, = ax_t14.plot(th12, th14_vals, "b-", label="θ14")
    t14_marker, = ax_t14.plot([], [], "ro", ms=8)
    ax_t14.set_title("θ14 vs θ12")
    ax_t14.grid(True)
    ax_t14.legend()
    ax_t14.set_ylim([-180,180])

    # s15 plot
    s15_line, = ax_s15.plot(th12, s15_vals, "b-", label="s15")
    s15_marker, = ax_s15.plot([], [], "ro", ms=8)
    ax_s15.set_title("s15 vs θ12")
    ax_s15.grid(True)
    ax_s15.set_ylim([-6,6])

    # s16 plot
    s16_line, = ax_s16.plot(th12, s16_vals, "b-", label="s16")
    s16_marker, = ax_s16.plot([], [], "ro", ms=8)
    ax_s16.set_title("s16 vs θ12")
    ax_s16.grid(True)
    ax_s16.set_ylim([-6,6])
    return fig2, (ax_t14, ax_s15, ax_s16), (
        (t14_line, s15_line, s16_line),
        (t14_marker, s15_marker, s16_marker),
    )



# -------------------------------------------------------------------
# Main Interactive Visualization
# -------------------------------------------------------------------
def main():
    # Build once at startup
    F_func, J_func = build_jacobian_functions()
    a1, a2, a4 = 1.0, 0.5, 4.0
    theta12 = 0.0

    fig1, ax = plt.subplots(figsize=(7, 6))
    plt.subplots_adjust(left=0.25, bottom=0.35)
    draw_double_slider(ax, a1, a2, a4, theta12, F_func, J_func)
    # Switch configuration button
    switch_ax =  plt.axes([0.025, 0.6, 0.15, 0.08])
    switch_button = Button(switch_ax, 'Switch Config', color='lightgray', hovercolor='0.9')

    def switch_config(event):
        global _current_config, _last_state
        _current_config = 1 - _current_config  # toggle
        _last_state = None  # reset to force recalculation
        draw_double_slider(ax, s_a1.val, s_a2.val, s_a4.val, s_t12.val, F_func, J_func)
        fig1.canvas.draw_idle()

    switch_button.on_clicked(switch_config)
    # Toggle physical validity filter
    filter_ax = plt.axes([0.025, 0.5, 0.15, 0.08])
    filter_button = Button(filter_ax, 'Toggle Filter', color='lightgray', hovercolor='0.9')

    def toggle_filter(event):
        global _filter_enabled
        _filter_enabled = not _filter_enabled
        state = "ON" if _filter_enabled else "OFF"
        print(f"Physical filter is now {state}")
        draw_double_slider(ax, s_a1.val, s_a2.val, s_a4.val, s_t12.val, F_func, J_func)
        fig1.canvas.draw_idle()

    filter_button.on_clicked(toggle_filter)

    # Sliders
    ax_t12 = plt.axes([0.25, 0.25, 0.65, 0.03])
    ax_a1 = plt.axes([0.25, 0.20, 0.65, 0.03])
    ax_a2 = plt.axes([0.25, 0.15, 0.65, 0.03])
    ax_a4 = plt.axes([0.25, 0.10, 0.65, 0.03])
    
    # Cache for precomputed curves
    cache = {"a1": a1, "a2": a2, "a4": a4, "data": None}
    s_t12 = Slider(ax_t12, 'θ12 (deg)', -360, 360, valinit=theta12)
    s_a1 = Slider(ax_a1, 'a1', 1.0, 2.0, valinit=a1)
    s_a2 = Slider(ax_a2, 'a2', 0.2, 3.0, valinit=a2)
    s_a4 = Slider(ax_a4, 'a4', 2.0, 5.0, valinit=a4)

    # Secondary figure
    fig2, (ax_t14, ax_s15, ax_s16), (lines, markers) = \
        create_double_slider_plot(a1, a2, a4, F_func, J_func)
    t14_line, s15_line, s16_line = lines
    t14_marker, s15_marker, s16_marker = markers
    # Update
    def update(val):
        nonlocal cache  # access outer cache dict

        # Always redraw current configuration
        draw_double_slider(ax, s_a1.val, s_a2.val, s_a4.val, s_t12.val, F_func, J_func)
        fig1.canvas.draw_idle()

        # Recalculate curves ONLY IF link lengths changed
        if (abs(s_a1.val - cache["a1"]) > 1e-6 or
            abs(s_a2.val - cache["a2"]) > 1e-6 or
            abs(s_a4.val - cache["a4"]) > 1e-6 or
            cache["data"] is None):

            print("Recomputing curves...")
            cache["a1"], cache["a2"], cache["a4"] = s_a1.val, s_a2.val, s_a4.val

            cache["data"] = compute_double_slider_curves(
                s_a1.val, s_a2.val, s_a4.val, F_func, J_func)

            (th12, th14_vals, s15_vals, s16_vals) = cache["data"]

            # Update lines
            t14_line.set_ydata(th14_vals)
            s15_line.set_ydata(s15_vals)
            s16_line.set_ydata(s16_vals)

            fig2.canvas.draw_idle()

    for s in [s_t12, s_a1, s_a2, s_a4]:
        s.on_changed(update)
    # Reset
    reset_ax = plt.axes([0.8, 0.9, 0.1, 0.04])
    button = Button(reset_ax, 'Reset', color='lightgray', hovercolor='0.9')
    def reset(event):
        global _last_state, _current_config, _filter_enabled

        # Reset internal states
        _last_state = None
        _current_config = 0
        _filter_enabled = False

        print("Reset: all sliders, configuration, and filter state restored to defaults.")

        # Reset sliders
        for s in [s_t12, s_a1, s_a2, s_a4]:
            s.reset()

        # Redraw mechanism and plots
        draw_double_slider(ax, a1, a2, a4, theta12, F_func, J_func)
        fig1.canvas.draw_idle()

        cache["a1"], cache["a2"], cache["a4"], cache["data"] = a1, a2, a4, None
        (th12, th14_vals, s15_vals, s16_vals) = compute_double_slider_curves(a1, a2, a4, F_func, J_func)
        t14_line.set_ydata(th14_vals)
        s15_line.set_ydata(s15_vals)
        s16_line.set_ydata(s16_vals)
        fig2.canvas.draw_idle()

    button.on_clicked(reset)
    plt.show()


if __name__ == "__main__":
    main()

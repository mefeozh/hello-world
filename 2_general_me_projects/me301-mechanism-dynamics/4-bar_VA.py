#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Four-Bar Mechanism – Position, Velocity, and Acceleration Visualization
-----------------------------------------------------------------------
Interactive sliders for θ12, ω12, α12, and link lengths.
Shows locus of point B, its velocity & acceleration vectors,
and θ14–ω14–α14 vs θ12 plots for open/crossed configurations.
"""

import matplotlib
matplotlib.use('TkAgg') 
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button

# ======================================================
# === GEOMETRY AND KINEMATICS ==========================
# ======================================================

def fourbar_solution(a1, a2, a3, a4, theta12_deg):
    """Return θ14, θ13 (open & crossed) in degrees."""
    theta12 = np.deg2rad(theta12_deg)
    K1, K2 = a1/a2, a1/a4
    K3 = (a1**2 + a2**2 + a4**2 - a3**2) / (2*a2*a4)
    A, B, C = K1 - np.cos(theta12), -np.sin(theta12), K2*np.cos(theta12) - K3
    disc = A**2 + B**2 - C**2
    if disc < 0:
        return None, None, None, None

    sin14_1 = (B*C + A*np.sqrt(disc)) / (A**2 + B**2)
    sin14_2 = (B*C - A*np.sqrt(disc)) / (A**2 + B**2)
    cos14_1 = (C - B*sin14_1) / A
    cos14_2 = (C - B*sin14_2) / A
    θ14_1, θ14_2 = np.arctan2(sin14_1, cos14_1), np.arctan2(sin14_2, cos14_2)

    def θ13(θ14):
        return np.arctan2(a4*np.sin(θ14) - a2*np.sin(theta12),
                          a1 + a4*np.cos(θ14) - a2*np.cos(theta12))
    return np.rad2deg(θ14_1), np.rad2deg(θ14_2), np.rad2deg(θ13(θ14_1)), np.rad2deg(θ13(θ14_2))


def fourbar_velocity_accel(a1, a2, a3, a4, θ12_deg, ω12, α12=0):
    """Compute ω14 and α14 for both configurations."""
    θ12 = np.deg2rad(θ12_deg)
    out = fourbar_solution(a1,a2,a3,a4,θ12_deg)
    if out[0] is None:
        return None, None
    θ13s = np.deg2rad([out[2],out[3]])
    θ14s = np.deg2rad([out[0],out[1]])
    ω14_list, α14_list = [], []
    for θ13, θ14 in zip(θ13s,θ14s):
        J = np.array([[-a3*np.sin(θ13), a4*np.sin(θ14)],
                      [a3*np.cos(θ13), -a4*np.cos(θ14)]])
        rhs = np.array([a2*np.sin(θ12), -a2*np.cos(θ12)])*ω12
        try: ω13, ω14 = np.linalg.solve(J,rhs)
        except np.linalg.LinAlgError:
            ω14_list.append(np.nan); α14_list.append(np.nan); continue
        ω14_list.append(ω14)
        Jdot = np.array([[a3*np.cos(θ13)*ω13, -a4*np.cos(θ14)*ω14],
                         [a3*np.sin(θ13)*ω13, -a4*np.sin(θ14)*ω14]])
        rhs_acc = np.array([a2*np.sin(θ12)*α12 + a2*np.cos(θ12)*ω12**2,
                            -a2*np.cos(θ12)*α12 + a2*np.sin(θ12)*ω12**2]) \
                            - Jdot @ np.array([ω13, ω14])
        try: α13, α14 = np.linalg.solve(J,rhs_acc); α14_list.append(α14)
        except np.linalg.LinAlgError: α14_list.append(np.nan)
    return np.array(ω14_list), np.array(α14_list)

# ======================================================
# === LOCUS CALCULATION ================================
# ======================================================

def compute_pointB_path(a1,a2,a3,a4,ω12,α12):
    """Return locus of point B on link 4."""
    θ12_vals = np.linspace(-180,180,360)
    B_open, B_cross = [], []
    for θ12 in θ12_vals:
        res = fourbar_solution(a1,a2,a3,a4,θ12)
        if res[0] is None:
            B_open.append([np.nan,np.nan]); B_cross.append([np.nan,np.nan]); continue
        θ14_open, θ14_cross = np.deg2rad(res[0]), np.deg2rad(res[1])
        B0 = np.array([a1,0])
        B_open.append(B0 + [a4*np.cos(θ14_open), a4*np.sin(θ14_open)])
        B_cross.append(B0 + [a4*np.cos(θ14_cross), a4*np.sin(θ14_cross)])
    return np.array(B_open), np.array(B_cross)

# ======================================================
# === PLOTS OF THETA14, OMEGA14, ALPHA14 ===============
# ======================================================

def compute_curves(a1,a2,a3,a4,ω12,α12):
    θ12_vals = np.linspace(-360,360,720)
    θ14o,θ14c,ω14o,ω14c,α14o,α14c = [],[],[],[],[],[]
    for th in θ12_vals:
        res = fourbar_solution(a1,a2,a3,a4,th)
        if res[0] is None:
            θ14o.append(np.nan); θ14c.append(np.nan)
            ω14o.append(np.nan); ω14c.append(np.nan)
            α14o.append(np.nan); α14c.append(np.nan); continue
        ω14,α14 = fourbar_velocity_accel(a1,a2,a3,a4,th,ω12,α12)
        θ14o.append(res[0]); θ14c.append(res[1])
        ω14o.append(ω14[0]); ω14c.append(ω14[1])
        α14o.append(α14[0]); α14c.append(α14[1])
    return θ12_vals, np.array(θ14o),np.array(θ14c),np.array(ω14o),np.array(ω14c),np.array(α14o),np.array(α14c)

def create_plot_window(a1,a2,a3,a4,ω12,α12):
    fig, axes = plt.subplots(3,1,figsize=(6,8),sharex=True)
    θ12,θ14o,θ14c,ω14o,ω14c,α14o,α14c = compute_curves(a1,a2,a3,a4,ω12,α12)
    lines, pts = [], []
    for idx,(ax,y1,y2,title,ylabel) in enumerate(zip(
        axes,[θ14o,ω14o,α14o],[θ14c,ω14c,α14c],
        ["θ₁₄ vs θ₁₂","ω₁₄ vs θ₁₂","α₁₄ vs θ₁₂"],["deg","rad/s","rad/s²"])):
        l1,=ax.plot(θ12,y1,'b-'); l2,=ax.plot(θ12,y2,'g-')
        p1,=ax.plot([],[],'bo',ms=6); p2,=ax.plot([],[],'go',ms=6)
        ax.set_ylabel(ylabel); ax.grid(True); ax.set_title(title)
        lines.append((l1,l2)); pts.append((p1,p2))
        if idx == 0:
            ax.set_ylim(-200, 200)
        elif idx == 1:
            ax.set_ylim(-4, 4)
        elif idx == 2:
            ax.set_ylim(-10, 10)
    axes[-1].set_xlabel("θ₁₂ (deg)")
    fig.tight_layout()
    return fig, axes, lines, pts

# ======================================================
# === DRAW MECHANISM ===================================
# ======================================================

def draw_fourbar(ax,a1,a2,a3,a4,θ12_deg,ω12,α12,locus_cache):
    ax.set_autoscale_on(False); ax.cla()
    ax.set_xlim(-3,4); ax.set_ylim(-3,3)
    ax.set_aspect('equal'); ax.grid(True)
    ax.set_title("Four-Bar Mechanism with Point B Locus")
    A0,B0 = np.array([0,0]),np.array([a1,0])
    θ12 = np.deg2rad(θ12_deg)
    A = np.array([a2*np.cos(θ12), a2*np.sin(θ12)])
    res = fourbar_solution(a1,a2,a3,a4,θ12_deg)
    if res[0] is None:
        ax.text(-1,2,"No real solution",color='r'); return
    ω14,α14 = fourbar_velocity_accel(a1,a2,a3,a4,θ12_deg,ω12,α12)
    θ14_open,θ14_cross = np.deg2rad(res[0]),np.deg2rad(res[1])
    for i,(θ14,ω,α) in enumerate(zip([θ14_open,θ14_cross],ω14,α14)):
        color = 'b' if i==0 else 'g'
        B = B0 + [a4*np.cos(θ14), a4*np.sin(θ14)]
        ax.plot([A0[0],A[0]],[A0[1],A[1]],'r-',lw=2)
        ax.plot([B0[0],B[0]],[B0[1],B[1]],'--',color=color,lw=2)
        ax.plot([A[0],B[0]],[A[1],B[1]],color=color,lw=2)
        ax.scatter([A0[0],A[0],B0[0],B[0]],[A0[1],A[1],B0[1],B[1]],color=color,s=50)
        rB = np.array([-a4*np.sin(θ14),a4*np.cos(θ14)])
        vB = ω*rB
        aB = α*rB - ω**2*np.array([a4*np.cos(θ14),a4*np.sin(θ14)])
        scale=0.4
        ax.arrow(B[0],B[1],scale*vB[0],scale*vB[1],color='orange',width=0.02,head_width=0.1)
        ax.arrow(B[0],B[1],scale*aB[0],scale*aB[1],color='purple',width=0.02,head_width=0.1)
    if locus_cache['open'] is not None:
        ax.plot(locus_cache['open'][:,0],locus_cache['open'][:,1],'b--',lw=1,alpha=0.6)
    if locus_cache['cross'] is not None:
        ax.plot(locus_cache['cross'][:,0],locus_cache['cross'][:,1],'g--',lw=1,alpha=0.6)

# ======================================================
# === MAIN =============================================
# ======================================================

def main():
    a1,a2,a3,a4,θ12,ω12,α12 = 1.5,1.0,2.0,1.75,90.0,1.0,0.0
    fig_mech, ax_mech = plt.subplots(figsize=(7,6))
    plt.subplots_adjust(left=0.25,bottom=0.3)

    locus_cache={'open':None,'cross':None}
    def recompute_locus():
        B_open,B_cross=compute_pointB_path(s_a1.val,s_a2.val,s_a3.val,s_a4.val,s_ω12.val,s_α12.val)
        locus_cache['open'],locus_cache['cross']=B_open,B_cross

    # --- Example Buttons ---
    button_positions={
        'change point':[0.025,0.3],'crank-rocker':[0.025,0.6],
        'double-rocker':[0.025,0.5],'singularity':[0.025,0.4],
        'change dir':[0.025,0.2]}
    btns={}
    for name,pos in button_positions.items():
        btns[name]=Button(plt.axes([pos[0],pos[1],0.15,0.08]),name.replace(' ','\n'),color='lightgray',hovercolor='0.9')
    reset_btn=Button(plt.axes([0.8,0.9,0.1,0.04]),'Reset',color='lightgray',hovercolor='0.9')

    # --- Sliders ---
    slider_height,slider_spacing,start_y=0.015,0.02,0.2
    ax_ω12=plt.axes([0.25,start_y,0.65,slider_height])
    ax_α12=plt.axes([0.25,start_y-slider_spacing,0.65,slider_height])
    ax_a1 =plt.axes([0.25,start_y-2*slider_spacing,0.65,slider_height])
    ax_a2 =plt.axes([0.25,start_y-3*slider_spacing,0.65,slider_height])
    ax_a3 =plt.axes([0.25,start_y-4*slider_spacing,0.65,slider_height])
    ax_a4 =plt.axes([0.25,start_y-5*slider_spacing,0.65,slider_height])
    ax_t12=plt.axes([0.25,start_y-6*slider_spacing,0.65,slider_height])
    s_ω12=Slider(ax_ω12,'ω₁₂',-2,2,valinit=ω12)
    s_α12=Slider(ax_α12,'α₁₂',-2,2,valinit=α12)
    s_a1 =Slider(ax_a1 ,'a1',0.5,3.0,valinit=a1)
    s_a2 =Slider(ax_a2 ,'a2',0.5,3.0,valinit=a2)
    s_a3 =Slider(ax_a3 ,'a3',0.5,3.0,valinit=a3)
    s_a4 =Slider(ax_a4 ,'a4',0.5,3.0,valinit=a4)
    s_t12=Slider(ax_t12,'θ₁₂',-360,360,valinit=θ12)

    # --- Second Figure for θ14,ω14,α14 ---
    fig2,axes,lines,pts=create_plot_window(a1,a2,a3,a4,ω12,α12)

    # --- Button actions ---
    def apply_values(vals): [s.set_val(v) for v,s in zip(vals,[s_a1,s_a2,s_a3,s_a4])]
    btns['change point'].on_clicked(lambda e:apply_values([1.0,1.0,1.5,1.5]))
    btns['crank-rocker'].on_clicked(lambda e:apply_values([1.0,0.5,1.5,1.5]))
    btns['double-rocker'].on_clicked(lambda e:apply_values([1.0,1.5,1.0,1.5]))
    btns['singularity'].on_clicked(lambda e:apply_values([1.0,1.0,1.0,1.0]))
    btns['change dir'].on_clicked(lambda e:apply_values([1.5,1.25,1.5,1.75]))
    reset_btn.on_clicked(lambda e:[s.reset() for s in [s_a1,s_a2,s_a3,s_a4,s_t12,s_ω12,s_α12]])

    # --- Update functions ---
    last_lengths=[a1,a2,a3,a4]
    recompute_locus()

    def update(val=None):
        nonlocal last_lengths
        new_lengths=[s_a1.val,s_a2.val,s_a3.val,s_a4.val]
        if not np.allclose(new_lengths,last_lengths):
            recompute_locus(); last_lengths=new_lengths
        draw_fourbar(ax_mech,s_a1.val,s_a2.val,s_a3.val,s_a4.val,
                     s_t12.val,s_ω12.val,s_α12.val,locus_cache)
        fig_mech.canvas.draw_idle()

        θ12v,θ14o,θ14c,ω14o,ω14c,α14o,α14c=compute_curves(
            s_a1.val,s_a2.val,s_a3.val,s_a4.val,s_ω12.val,s_α12.val)
        for (l1,l2),y1,y2 in zip(lines,[θ14o,ω14o,α14o],[θ14c,ω14c,α14c]):
            l1.set_ydata(y1); l2.set_ydata(y2)
        th=s_t12.val
        res=fourbar_solution(s_a1.val,s_a2.val,s_a3.val,s_a4.val,th)
        if res[0] is not None:
            ω14,α14=fourbar_velocity_accel(s_a1.val,s_a2.val,s_a3.val,s_a4.val,th,s_ω12.val,s_α12.val)
            cur=[(res[0],res[1]),(ω14[0],ω14[1]),(α14[0],α14[1])]
            for (p1,p2),(y1,y2) in zip(pts,cur): p1.set_data([th],[y1]); p2.set_data([th],[y2])
        else:
            for p1,p2 in pts: p1.set_data([],[]); p2.set_data([],[])
        fig2.canvas.draw_idle()

    for s in [s_a1,s_a2,s_a3,s_a4,s_t12,s_ω12,s_α12]:
        s.on_changed(update)

    draw_fourbar(ax_mech,a1,a2,a3,a4,θ12,ω12,α12,locus_cache)
    plt.show()

if __name__ == "__main__":
    main()

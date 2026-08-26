"""
CE495 - Marine Pipeline Hydraulic Analysis
Canakkale Intake & Discharge Pipeline Design
=============================================
Fully-submerged pressurised conduit Bernoulli with absolute boundary pressures.
Dual scenario: Brand New vs 10 Years Later (biofouling).
Creator: Mehmet Efe Ozhan
"""

import xml.etree.ElementTree as ET
import numpy as np
import os, warnings
warnings.filterwarnings('ignore')

SHOW_PLOTS = False          # set True to open interactive windows

import matplotlib
if not SHOW_PLOTS:
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.optimize import brentq
from scipy.signal import savgol_filter

# =============================================================================
# SETTINGS
# =============================================================================

TOTAL_FLOW_M3H  = 50_000.0      # m3/h
V_MIN, V_MAX    = 2.0, 4.0      # m/s  velocity design window
V_TARGET        = 2.5           # m/s  preferred

STANDARD_OD = [                 # nominal outer diameters (m), HDPE DN catalogue
    0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90,
    1.00, 1.10, 1.20, 1.40, 1.60, 1.80, 2.00,
    2.20, 2.40, 2.60, 2.80, 3.00,
]
PIPE_SDR        = 17            # Standard Dimension Ratio - marine HDPE

EPS_NEW         = 1.5e-6        # m  roughness - brand new HDPE
EPS_FOULED      = 1.5e-3        # m  roughness - 10 years marine biofouling

NU              = 1.19e-6       # m2/s  kinematic viscosity (seawater 15 degC)
G               = 9.81          # m/s2
RHO_SEA         = 1025.0        # kg/m3  seawater density
ATM_PA          = 101_325.0     # Pa     one standard atmosphere

# Absolute pressures at each system boundary
P_FACILITY_ABS       = 1.0      # atm  shore facility (open to atmosphere)
P_INTAKE_SEA_ABS     = 2.5      # atm  sea end of intake pipe  (15 m depth)
P_DISCHARGE_SEA_ABS  = 3.5      # atm  sea end of discharge pipe (25 m depth)

def atm_to_head(p_atm):
    """Convert pressure in atm to metres of seawater head."""
    return p_atm * ATM_PA / (RHO_SEA * G)

# Gauge pressure heads relative to facility (1 atm = reference zero)
H_INTAKE_SEA_GAUGE    = atm_to_head(P_INTAKE_SEA_ABS   - P_FACILITY_ABS)  # ~15.1 m
H_DISCHARGE_SEA_GAUGE = atm_to_head(P_DISCHARGE_SEA_ABS - P_FACILITY_ABS)  # ~25.2 m

PIPE_CLEARANCE  = 0.0           # m  pipe invert at seabed level (survey depths: 15 m intake, 25 m discharge)
RDP_TOL         = 0.8           # m  RDP line simplification tolerance
SMOOTH_W        = 15            # Savitzky-Golay window (visual only)

# Plant / shore boundary elevation (MSL datum)
PLANT_ELEV_INTAKE    = 0.0      # m  plant delivery level (intake shore end)

# Minor losses: intake system
K_INTAKE = {
    "Bell-mouth entry":     0.04,
    "Intake screen":        0.50,
    "45 deg elbows x2":     0.30,
    "90 deg elbow x1":      0.20,
    "Gate valve":           0.15,
    "Flexible couplings":   0.10,
    "Wet-well exit":        1.00,
}

# Minor losses: discharge / outfall system
K_DISCHARGE = {
    "Pump basin entry":     0.50,
    "90 deg elbow x1":      0.20,
    "45 deg elbows x2":     0.30,
    "Gate valve":           0.15,
    "Flexible couplings":   0.10,
    "Outfall diffuser":     2.00,
}

FILES = [
    {'file': 'CE495/Intake.xml',    'type': 'Intake'},
    {'file': 'CE495/Discharge.xml', 'type': 'Discharge'},
]

# =============================================================================
# FUNCTIONS
# =============================================================================

def parse_xml(path):
    """Parse Civil 3D LandXML - returns (station, elevation) arrays."""
    tree = ET.parse(path)
    root = tree.getroot()
    for ns in [{'lx': 'http://www.landxml.org/schema/LandXML-1.2'},
               {'lx': 'http://www.landxml.org/schema/LandXML-1.1'}, {}]:
        for tag in ['.//lx:ProfSurf/lx:PntList2D', './/PntList2D']:
            el = root.find(tag, ns) if ns else root.find(tag)
            if el is not None and el.text:
                pts = np.array(el.text.split(), float).reshape(-1, 2)
                return pts[:, 0] - pts[0, 0], pts[:, 1]
    raise RuntimeError(f"PntList2D not found in {path}")


def colebrook(Re, eps, D):
    """Darcy-Weisbach friction factor via Colebrook-White (Brent solver)."""
    if Re < 2300:
        return 64.0 / Re
    rr = eps / D
    try:
        return brentq(lambda f: 1/f**0.5 + 2*np.log10(rr/3.7 + 2.51/(Re*f**0.5)),
                      1e-6, 0.5, xtol=1e-12)
    except ValueError:
        return 0.25 / (np.log10(rr/3.7 + 5.74/Re**0.9))**2  # Swamee-Jain


def all_pipe_candidates(Q_m3s):
    """Return all valid (D_nom, D_inner, n, V, f_new, f_fouled) sorted by (n, |V-V_TARGET|)."""
    cands = []
    for n in range(1, 5):
        for D in STANDARD_OD:
            Di = D * (1 - 2/PIPE_SDR)
            V  = (Q_m3s / n) / (np.pi * Di**2 / 4)
            if V_MIN <= V <= V_MAX:
                Re = V * Di / NU
                fn = colebrook(Re, EPS_NEW,    Di)
                ff = colebrook(Re, EPS_FOULED, Di)
                cands.append((D, Di, n, V, fn, ff))
    cands.sort(key=lambda c: (c[2], abs(c[3] - V_TARGET)))
    return cands


def rdp(points, eps):
    """Ramer-Douglas-Peucker simplification."""
    if len(points) <= 2:
        return points
    d = np.abs(np.cross(points[-1]-points[0], points[0]-points[1:-1])) \
        / np.linalg.norm(points[-1]-points[0])
    idx = np.argmax(d)
    if d[idx] > eps:
        L = rdp(points[:idx+2], eps)
        R = rdp(points[idx+1:], eps)
        return np.vstack((L[:-1], R))
    return np.array([points[0], points[-1]])


def build_hgl(pipe_x, pipe_z, segs, f, Di, V, K, sys_type, hgl_anchor=0.0):
    """
    HGL for a fully-submerged pressurised conduit.
    Anchor: HGL[-1] = hgl_anchor (piezometric head at sea end, m).
      = pipe_z[-1] + (P_sea - P_ref) / rho*g
    Intake  (flow sea->shore): HGL falls toward shore.
    Discharge (flow shore->sea): HGL rises toward shore.
    """
    L = segs.sum()
    loss_m = (f / Di + K / L) * V**2 / (2*G)  # head loss per metre of pipe
    hgl = np.zeros(len(pipe_x))
    hgl[-1] = hgl_anchor
    for i in range(len(pipe_x)-2, -1, -1):
        delta = loss_m * segs[i]
        hgl[i] = hgl[i+1] - delta if sys_type == 'Intake' else hgl[i+1] + delta
    return hgl


def smooth(sta, elev):
    n = len(elev)
    w = min(SMOOTH_W, n if n % 2 == 1 else n-1)
    w = w if w % 2 == 1 else w-1
    if w < 5:
        return elev.copy()
    return savgol_filter(elev, w, min(3, w-1))

# =============================================================================
# ANALYSIS LOOP
# =============================================================================

Q = TOTAL_FLOW_M3H / 3600.0
results = []

for cfg in FILES:
    sys_type = cfg['type']
    fname    = cfg['file']

    print(f"\n{'='*62}")
    print(f"  {sys_type.upper()} PIPELINE  |  {fname}")
    print(f"{'='*62}")

    sta, elev = parse_xml(fname)
    print(f"  [OK] {len(sta)} profile points parsed from {fname}")

    # -- Pipe optimisation --
    cands = all_pipe_candidates(Q)
    D_nom, D_in, N, V, f_new, f_fouled = cands[0]
    A  = np.pi * D_in**2 / 4
    Re = V * D_in / NU

    print("\n  +-- PIPE OPTIMIZATION ---------------------------------+")
    print(f"  |  {'Config':<20} {'OD (m)':<8} {'ID (m)':<8} {'n':<4} {'V (m/s)':<10} {'f_fouled':<10}")
    print("  |  " + "-"*56)
    for i, (Do, Di, n, Vi, fn, ff) in enumerate(cands):
        marker = " <- SELECTED" if i == 0 else ""
        print(f"  |  {'D='+str(Do)+'m x '+str(n)+'pipe':<20} "
              f"{Do:<8.2f} {Di:<8.2f} {n:<4} {Vi:<10.3f} {ff:.6f}{marker}")
        if i == 9:
            print(f"  |  ... ({len(cands)-10} more options omitted)")
            break
    print("  +------------------------------------------------------+")

    # -- Geometry --
    K_dict = K_INTAKE if sys_type == 'Intake' else K_DISCHARGE
    K_tot  = sum(K_dict.values())

    pipe_z_raw = elev + PIPE_CLEARANCE
    pts        = np.column_stack((sta, pipe_z_raw))
    simple     = rdp(pts, RDP_TOL)
    px, pz     = simple[:, 0], simple[:, 1]
    segs       = np.sqrt(np.diff(px)**2 + np.diff(pz)**2)
    L          = segs.sum()
    L_horiz    = float(np.abs(np.diff(px)).sum())
    dZ         = pz[0] - pz[-1]   # positive = pipe descends shore->sea

    print("\n  +-- GEOMETRY (calculated from RAW Civil 3D data) ------+")
    print(f"  |  Raw profile points       : {len(sta):>8d}")
    print(f"  |  Tangent nodes after RDP  : {len(px):>8d}")
    print(f"  |  Horizontal distance      : {L_horiz:>8.2f} m")
    print(f"  |  Elevation change Dz      : {dZ:>8.2f} m  (shore -> sea end)")
    print(f"  |  TRUE 3D pipe length L    : {L:>8.3f} m  <- report value")
    print(f"  |  Pipe clearance above bed : {PIPE_CLEARANCE:>8.2f} m")
    print("  +------------------------------------------------------+")

    # -- Head losses --
    hf_new    = f_new    * (L/D_in) * V**2/(2*G)
    hf_fouled = f_fouled * (L/D_in) * V**2/(2*G)
    hm        = K_tot * V**2/(2*G)
    hL_new    = hf_new + hm
    hL_fouled = hf_fouled + hm

    vel_note = "WITHIN DESIGN WINDOW" if V_MIN <= V <= V_MAX else "OUT OF WINDOW"
    print("\n  +-- HYDRAULICS ----------------------------------------+")
    print(f"  |  System flow Q            : {TOTAL_FLOW_M3H:>8.0f} m3/h  =  {Q:.4f} m3/s")
    print(f"  |  Number of pipes n        : {N:>8d}")
    print(f"  |  Flow per pipe Q_pipe     : {Q/N:>8.4f} m3/s")
    print(f"  |  Pipe Nominal OD          : {D_nom:>8.3f} m  (DN{int(D_nom*1000)})")
    print(f"  |  True Hydraulic ID        : {D_in:>8.3f} m  (SDR {PIPE_SDR})")
    print(f"  |  Cross-section area A     : {A:>8.5f} m2")
    print(f"  |  Flow velocity V          : {V:>8.3f} m/s  [{vel_note}]")
    print(f"  |  Design window            :   {V_MIN:.1f} - {V_MAX:.1f} m/s")
    print(f"  |  Reynolds number (New)    : {Re:>8.0f}")
    print(f"  |  Reynolds number (Fouled) : {Re:>8.0f}")
    print(f"  |  Friction factor f (New)  : {f_new:>8.6f} (HDPE e = {EPS_NEW*1e6:.1f} um)")
    print(f"  |  Friction factor f (Foul) : {f_fouled:>8.6f} (Fouled e = {EPS_FOULED*1e3:.1f} mm)")
    print("  +------------------------------------------------------+")

    print("\n  +-- HEAD LOSS COMPARISON (Brand New vs. 10 Years Later) -+")
    print(f"  |  Friction / Major Loss    : New={hf_new:>6.3f} m  |  Fouled={hf_fouled:>6.3f} m")
    print(f"  |  Minor losses (itemised using K_total={K_tot:.2f}):")
    for name, k in K_dict.items():
        h = k * V**2 / (2*G)
        print(f"  |    {name:<35s}  K={k:.2f}  ->  {h:.4f} m")
    print("  |")
    print(f"  |  TOTAL SYSTEM HEAD LOSS   : New={hL_new:>6.3f} m  |  Fouled={hL_fouled:>6.3f} m")
    print(f"  |  Static sea depth at head : {abs(pz[-1]):>8.2f} m")
    print("  +------------------------------------------------------+")

    # -- HGL profiles (anchored at absolute pressure boundary) --
    if sys_type == 'Intake':
        hgl_anchor = pz[-1] + H_INTAKE_SEA_GAUGE
    else:
        hgl_anchor = pz[-1] + H_DISCHARGE_SEA_GAUGE

    hgl_new    = build_hgl(px, pz, segs, f_new,    D_in, V, K_tot, sys_type, hgl_anchor)
    hgl_fouled = build_hgl(px, pz, segs, f_fouled, D_in, V, K_tot, sys_type, hgl_anchor)

    # -- Pump / gravity assessment (with boundary pressures) --
    print("\n  +-- PUMP / GRAVITY ASSESSMENT (with boundary pressures) --+")
    if sys_type == 'Intake':
        # Bernoulli: P_sea/rho*g + z_sea = P_fac/rho*g + z_fac + h_pump + h_L
        # => h_pump = (P_sea - P_fac)/rho*g + (z_sea - z_fac) - h_L
        #           = H_INTAKE_SEA_GAUGE - dZ - h_L
        pump_new    = H_INTAKE_SEA_GAUGE - dZ - hL_new
        pump_fouled = H_INTAKE_SEA_GAUGE - dZ - hL_fouled
        pump_needed = pump_fouled > 0
        P_gauge_shore = hgl_new[0] - pz[0]
        print(f"  Sea-end absolute pressure     = {P_INTAKE_SEA_ABS} atm  ({abs(pz[-1]):.0f} m depth)")
        print(f"  Sea-end gauge head (vs fac.)  = {H_INTAKE_SEA_GAUGE:.3f} m")
        print(f"  Elevation term (z_sea-z_fac)  = {-dZ:.3f} m")
        print(f"  Required pump head (New)      = {pump_new:.3f} m  ({'pump needed' if pump_new>0 else 'sea pressure sufficient'})")
        print(f"  Required pump head (Fouled)   = {pump_fouled:.3f} m  ({'pump needed' if pump_fouled>0 else 'sea pressure sufficient'})")
        print(f"  Shore gauge pressure (New)    = {P_gauge_shore:.2f} m  [pipe fully pressurised]")
    else:
        # Bernoulli: P_fac/rho*g + z_fac + h_pump = P_sea/rho*g + z_sea + h_L
        # => surplus = dZ - H_DISCHARGE_SEA_GAUGE - h_L
        sur_new    = dZ - H_DISCHARGE_SEA_GAUGE - hL_new
        sur_fouled = dZ - H_DISCHARGE_SEA_GAUGE - hL_fouled
        pump_new    = max(0.0, -sur_new)
        pump_fouled = max(0.0, -sur_fouled)
        pump_needed = pump_fouled > 0
        P_gauge_shore = hgl_new[0] - pz[0]
        print(f"  Sea-end absolute pressure     = {P_DISCHARGE_SEA_ABS} atm  ({abs(pz[-1]):.0f} m depth)")
        print(f"  Sea-end gauge head (vs fac.)  = {H_DISCHARGE_SEA_GAUGE:.3f} m  (opposes discharge)")
        print(f"  Elevation driving head dZ     = {dZ:.3f} m")
        print(f"  Net surplus (New)             = {sur_new:.3f} m  ({'gravity sufficient' if sur_new>=0 else 'PUMP NEEDED'})")
        print(f"  Net surplus (Fouled)          = {sur_fouled:.3f} m  ({'gravity sufficient' if sur_fouled>=0 else 'PUMP NEEDED'})")
        if pump_new > 0:
            print(f"  Required pump head (New)      = {pump_new:.3f} m")
            print(f"  Required pump head (Fouled)   = {pump_fouled:.3f} m")
        print(f"  Shore gauge pressure (New)    = {P_gauge_shore:.2f} m  [pipe strongly pressurised]")
    print("  +------------------------------------------------------+")

    results.append(dict(
        sys_type=sys_type, sta=sta, elev=elev, px=px, pz=pz,
        hgl_new=hgl_new, hgl_fouled=hgl_fouled,
        D_nom=D_nom, D_in=D_in, N=N, V=V, L=L, dZ=dZ,
        f_new=f_new, f_fouled=f_fouled, K_tot=K_tot, K_dict=K_dict,
        hf_new=hf_new, hf_fouled=hf_fouled, hm=hm,
        hL_new=hL_new, hL_fouled=hL_fouled,
        pump_new=pump_new, pump_fouled=pump_fouled, pump_needed=pump_needed,
    ))

# =============================================================================
# PLOTTING  - 2 panels per figure
# =============================================================================

DARK = '#0d1117'

for r in results:
    sys_type = r['sys_type']
    fig = plt.figure(figsize=(16, 10))
    fig.patch.set_facecolor(DARK)
    gs = gridspec.GridSpec(2, 1, figure=fig, height_ratios=[3, 1.4], hspace=0.38)
    ax_prof = fig.add_subplot(gs[0])
    ax_bar  = fig.add_subplot(gs[1])

    for ax in (ax_prof, ax_bar):
        ax.set_facecolor(DARK)
        ax.tick_params(colors='#aaaaaa', labelsize=9)
        for sp in ax.spines.values():
            sp.set_color('#333333')

    # -- PANEL 1: Seabed profile + pipeline + dual HGL ----------------------
    sta  = r['sta']
    elev = r['elev']
    px, pz = r['px'], r['pz']
    elev_s = smooth(sta, elev)

    # Y-axis: accommodate the absolute-pressure HGL which sits above MSL
    ymin = min(elev.min(), pz.min()) - 2
    ymax = max(elev.max(), r['hgl_new'].max(), r['hgl_fouled'].max()) + 5

    # seabed
    ax_prof.fill_between(sta, elev_s, ymin, color='#3e2723', alpha=0.9, zorder=1)
    ax_prof.plot(sta, elev_s, color='#bcaaa4', lw=1.4, label='Seabed', zorder=2)

    # water fill and sea level
    ax_prof.fill_between(sta, elev_s, 0, where=(elev_s < 0),
                         color='#1565c0', alpha=0.18, zorder=2)
    ax_prof.axhline(0, color='#42a5f5', lw=1.1, label='Sea level (MSL = 0 m)', zorder=3)

    # pipeline route
    ax_prof.plot(px, pz, color='#ffd54f', lw=2.5,
                 marker='D', ms=5, mfc='white', mec='#ffd54f',
                 label=f'Pipeline  {r["N"]}x DN{int(r["D_nom"]*1000)} '
                       f'(OD {r["D_nom"]:.2f} m / ID {r["D_in"]:.2f} m, SDR{PIPE_SDR})',
                 zorder=6)

    # dual HGL - anchored at absolute sea-end pressure
    ax_prof.plot(px, r['hgl_new'],    color='#4dd0e1', lw=2.0, ls='--',
                 label=f'HGL - Brand New  (hL={r["hL_new"]:.3f} m)', zorder=5)
    ax_prof.plot(px, r['hgl_fouled'], color='#ef5350', lw=2.2, ls='--',
                 label=f'HGL - 10 Yrs Fouled  (hL={r["hL_fouled"]:.3f} m)', zorder=5)

    # depth annotation at sea end
    ex, ez = px[-1], pz[-1]
    ax_prof.annotate('', xy=(ex, ez), xytext=(ex, 0),
                     arrowprops=dict(arrowstyle='<->', color='#80deea', lw=1.5))
    ax_prof.text(ex + sta[-1]*0.015, ez/2, f'{abs(ez):.0f} m depth',
                 color='#80deea', fontsize=9, va='center')

    # HGL anchor dotted line at sea end pressure head
    hgl_anchor_val = r['hgl_new'][-1]
    p_abs = P_INTAKE_SEA_ABS if sys_type == 'Intake' else P_DISCHARGE_SEA_ABS
    ax_prof.axhline(hgl_anchor_val, color='#ff8a65', lw=0.9, ls=':',
                    label=f'HGL anchor = {hgl_anchor_val:.2f} m  (sea P = {p_abs} atm)')

    # dZ annotation
    ax_prof.annotate('', xy=(px[0], pz[-1]), xytext=(px[0], pz[0]),
                     arrowprops=dict(arrowstyle='<->', color='#ffcc02', lw=2.0))
    if sys_type == 'Discharge':
        ax_prof.text(px[0] + sta[-1]*0.02, (pz[0]+pz[-1])/2,
                     f'dZ = {r["dZ"]:.1f} m\nvs {H_DISCHARGE_SEA_GAUGE:.1f} m\nback-pressure',
                     color='#ffcc02', fontsize=8, va='center', fontweight='bold')
    else:
        ax_prof.text(px[0] + sta[-1]*0.02, (pz[0]+pz[-1])/2,
                     f'dZ = {r["dZ"]:.1f} m\n(pipe rises\nto shore)',
                     color='#ffcc02', fontsize=8, va='center', fontweight='bold')

    # summary box - pump head required (corrected Bernoulli)
    box_txt = (f'Required Pump Head\n'
               f'  Brand New : {r["pump_new"]:.2f} m\n'
               f'  10 Yr Foul: {r["pump_fouled"]:.2f} m')
    ax_prof.text(0.985, 0.97, box_txt, transform=ax_prof.transAxes,
                 fontsize=9.5, ha='right', va='top', color='#ef9a9a',
                 bbox=dict(boxstyle='round,pad=0.45', fc='#111', ec='#444', alpha=0.92))

    ax_prof.set_title(
        f'{sys_type} Pipeline - Hydraulic Grade Line  '
        f'(Boundary: Facility = {P_FACILITY_ABS} atm | Sea = {p_abs} atm)\n'
        f'Q = {TOTAL_FLOW_M3H:,.0f} m3/h  |  V = {r["V"]:.3f} m/s  |  '
        f'L = {r["L"]:.1f} m  |  Re = {r["V"]*r["D_in"]/NU:,.0f}',
        color='white', fontsize=10.5, fontweight='bold', pad=8)
    ax_prof.set_xlabel('Station (m)', color='#aaa', fontsize=10)
    ax_prof.set_ylabel('Piezometric Head / Elevation (m MSL)', color='#aaa', fontsize=10)
    ax_prof.set_ylim(ymin, ymax)
    ax_prof.set_xlim(sta[0], sta[-1])
    ax_prof.grid(color='#222', ls=':', lw=0.6)
    ax_prof.legend(loc='lower left', fontsize=8, facecolor='#111',
                   edgecolor='#444', labelcolor='white', ncol=2)

    # -- PANEL 2: Full energy budget - friction | minor | total | pump head --
    labels = ['Friction\n(Major)', 'Fittings\n(Minor)', 'TOTAL\nHead Loss', 'Pump Head\nRequired']
    vals_new    = [r['hf_new'],    r['hm'], r['hL_new'],    r['pump_new']]
    vals_fouled = [r['hf_fouled'], r['hm'], r['hL_fouled'], r['pump_fouled']]

    x  = np.arange(len(labels))
    bw = 0.32
    c_new    = ['#4dd0e1', '#4dd0e1', '#4dd0e1', '#ff8a65']
    c_fouled = ['#ef5350', '#ef5350', '#ef5350', '#e53935']
    b1 = ax_bar.bar(x - bw/2, vals_new,    bw, label='Brand New (clean)',
                    color=c_new,    alpha=0.88, edgecolor='#222')
    b2 = ax_bar.bar(x + bw/2, vals_fouled, bw, label='10 Years Later (fouled)',
                    color=c_fouled, alpha=0.88, edgecolor='#222')

    for bar, val in [(b1, vals_new), (b2, vals_fouled)]:
        for rect, v in zip(bar, val):
            ax_bar.text(rect.get_x() + rect.get_width()/2, v + 0.05,
                        f'{v:.2f} m', ha='center', va='bottom',
                        color='white', fontsize=8, fontweight='bold')

    if sys_type == 'Intake':
        p_note = (f'Boundary: Facility = {P_FACILITY_ABS} atm  |  '
                  f'Sea end = {P_INTAKE_SEA_ABS} atm ({abs(pz[-1]):.0f} m depth)  |  '
                  f'Gauge head = {H_INTAKE_SEA_GAUGE:.2f} m\n'
                  f'f (Brand New) = {r["f_new"]:.5f}  [HDPE, e = {EPS_NEW*1e6:.1f} um]     '
                  f'f (10 Yr Foul) = {r["f_fouled"]:.5f}  [biofouling, e = {EPS_FOULED*1e3:.1f} mm]')
    else:
        p_note = (f'Boundary: Facility = {P_FACILITY_ABS} atm  |  '
                  f'Sea end = {P_DISCHARGE_SEA_ABS} atm ({abs(pz[-1]):.0f} m depth)  |  '
                  f'Back-pressure = {H_DISCHARGE_SEA_GAUGE:.2f} m  >  dZ = {r["dZ"]:.2f} m  -> pump needed\n'
                  f'f (Brand New) = {r["f_new"]:.5f}  [HDPE, e = {EPS_NEW*1e6:.1f} um]     '
                  f'f (10 Yr Foul) = {r["f_fouled"]:.5f}  [biofouling, e = {EPS_FOULED*1e3:.1f} mm]')

    ax_bar.text(0.01, 0.97, p_note, transform=ax_bar.transAxes, fontsize=8.2,
                va='top', color='#cccccc',
                bbox=dict(boxstyle='round,pad=0.35', fc='#1a1a2e', ec='#333'))

    ax_bar.set_xticks(x)
    ax_bar.set_xticklabels(labels, color='#ccc', fontsize=9.5)
    ax_bar.set_ylabel('Head (m)', color='#aaa', fontsize=10)
    ax_bar.set_title(
        'Energy Budget - Brand New vs 10 Years Later  '
        '|  Friction  Minor Losses  Required Pump Head',
        color='#aaa', fontsize=10)
    ax_bar.legend(fontsize=9, facecolor='#111', edgecolor='#444', labelcolor='white')
    ax_bar.set_ylim(0, max(vals_fouled) * 1.6)
    ax_bar.grid(axis='y', color='#222', ls=':', lw=0.6)

    out = f'CE495/{sys_type}_analysis.png'
    os.makedirs('CE495', exist_ok=True)
    plt.savefig(out, dpi=180, bbox_inches='tight', facecolor=DARK)
    print(f"\n  Saved -> {out}")
    if SHOW_PLOTS:
        plt.show()
    else:
        plt.close(fig)

print("\nDone.")
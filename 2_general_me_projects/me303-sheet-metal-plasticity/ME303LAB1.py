import math

# ==========================================
# 1. DEFINE CONSTANTS & GIVEN VARIABLES
# ==========================================
# Geometry
punch_dia = 30.0        # mm
Rb = punch_dia / 2      # Radius of bending die (mm)
w_die = 23.6            # Die opening (mm)
l_NA = 27.2             # Arc length / Neutral axis length (mm)

# Material Constants
E = 210000.0            # Young's Modulus (MPa)
g = 9.81                # Conversion factor for kg/mm^2 to MPa (N/mm^2)

# ==========================================
# Plain Carbon Steel (PCS) values from table
Y_PCS_raw = [19.92, 20.83, 20.89]     # Yield Strength (kg/mm^2)
UTS_PCS_raw = [33.37, 33.93, 34.03]   # Tensile Strength (kg/mm^2)

# Galvanized Steel (GAL) values from table
Y_GAL_raw = [35.78, 34.70, 35.47]     
UTS_GAL_raw = [37.77, 36.17, 36.73]   

# Average calculations in MPa
Y_PCS = sum(Y_PCS_raw) / len(Y_PCS_raw) * g
UTS_PCS = sum(UTS_PCS_raw) / len(UTS_PCS_raw) * g

Y_GAL = sum(Y_GAL_raw) / len(Y_GAL_raw) * g
UTS_GAL = sum(UTS_GAL_raw) / len(UTS_GAL_raw) * g

# ==========================================
specimens = [
    {
        "name": "Specimen 1 - Plain Carbon Steel (0.5mm)",
        "h": 0.5,       # thickness (mm)
        "w": 30.0,      # specimen width (mm)
        "Y": Y_PCS,     # Yield Strength (MPa)
        "UTS": UTS_PCS  # Ultimate Tensile Strength (MPa)
    },
    {
        "name": "Specimen 2 - Plain Carbon Steel (1mm)",
        "h": 1.0,
        "w": 30,
        "Y": Y_PCS,
        "UTS": UTS_PCS
    },
    {
        "name": "Specimen 3 - Galvanized Steel (1mm)",
        "h": 1.0,       
        "w": 30,
        "Y": Y_GAL,
        "UTS": UTS_GAL
    }   
]

# =========================================
def print_separator():
    print("-" * 65)

print("\n==== SHEET METAL BENDING THEORETICAL CALCULATIONS ====")
print(f"Material Averages (MPa):")
print(f"  PCS -> Y: {Y_PCS:.2f}, UTS: {UTS_PCS:.2f}")
print(f"  GAL -> Y: {Y_GAL:.2f}, UTS: {UTS_GAL:.2f}")
print_separator()

for spec in specimens:
    name = spec["name"]
    h = spec["h"]
    w = spec["w"]
    Y = spec["Y"]
    UTS = spec["UTS"]
    
    # A. Check Gentle Bend Assumption
    rb_h_ratio = Rb / h
    assumption_check = "Valid" if rb_h_ratio > 4 else "Invalid"
    
    # B. Calculate Bending Angle (alpha_b) and Included Die Angle (beta_b)
    # alpha_b in radians = l_NA / (Rb + h/2)
    alpha_b_rad = l_NA / (Rb + h / 2)
    alpha_b = math.degrees(alpha_b_rad)
    beta_b = 180.0 - alpha_b
    
    # C. Calculate Radius of Bent Part (Rf) and Springback Ratio (Rb/Rf)
    k = (Rb / h) * (Y / E)
    Rf = Rb / (1 - 3 * k + 4 * k**3)
    springback_ratio = Rb / Rf
    
    # D. Calculate Final Bend Angle (alpha_f) and Final Included Part Angle (beta_f)
    alpha_f_rad = alpha_b_rad * ((Rb + h / 2) / (Rf + h / 2))
    alpha_f = math.degrees(alpha_f_rad)
    beta_f = 180.0 - alpha_f
    
    # E. Calculate Bending Force (V-bending)
    K_val = 4 / 3
    Fb = K_val * w * (h**2) * (UTS / w_die)
    
    # Print Results
    print(f"\n{name}")
    print(f"  Thickness (h): {h} mm, Width (w): {w} mm")
    print(f"  -> Gentle Bend Assumption (Rb/h = {rb_h_ratio:.1f}): {assumption_check}")
    print(f"  -> Bending Angle (α_b): {alpha_b:.2f}°")
    print(f"  -> Included Die Angle (β_b): {beta_b:.2f}°")
    print(f"  -> Final Radius of Bent Part (R_f): {Rf:.4f} mm")
    print(f"  -> Springback Ratio (Rb/R_f): {springback_ratio:.4f}")
    print(f"  -> Final Bend Angle (α_f): {alpha_f:.2f}°")
    print(f"  -> Final Included Part Angle (β_f): {beta_f:.2f}°")
    print(f"  -> Bending Force (F_b): {Fb:.2f} N")
    print_separator()

print("Calculations complete.\n")
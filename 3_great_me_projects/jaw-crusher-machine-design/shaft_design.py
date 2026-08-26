import numpy as np
import Kinematic_Force_Analysis as KFA


def solve_flywheel_exact(Tg, a11, h11, D, D_small, friction_coeff):
    """
    Solves the Flywheel/Pulley system using the specific equations provided in the images.
    
    Parameters:
    - Tg: Torque (Nm)
    - a11: Horizontal distance (m)
    - h11: Vertical distance (m)
    - D: Diameter of the large flywheel (m)
    - D_small: Diameter of the small pulley (m) (Corresponds to D/16 in your image if Ratio=16)
    - friction_coeff: 'f' in the exponent
    """
    
    # --- 1. Geometry Setup ---
    # The term inside the inverse trig functions: (R_large - R_small) / Distance
    # From image: (D/2 - D/32) becomes (D/2 - D_small/2)
    dist = np.sqrt(h11**2 + a11**2)
    radius_diff = (D/2 - D_small/2)
    
    # Check for valid geometry
    if radius_diff >= dist:
        print("Error: Geometry impossible (Pulleys overlap or too far apart)")
        return None

    # Calculate the argument for the trig functions
    geom_term = radius_diff / dist
    
    # --- 2. Calculate Angles ---
    # Base angles from Image 1
    term_tan = np.arctan(h11 / a11)      # tan^-1(h11/a11)
    term_sin = np.arcsin(geom_term)      # sin^-1(...)
    
    angle_f1 = term_tan - term_sin       # Angle for F1
    print("angle_f1: ", (angle_f1))
    angle_f2 = term_tan + term_sin       # Angle for F2
    print("angle_f2: ", (angle_f2))
    
    # Wrap Angle (Alpha) from Image 2
    # Formula: 2*pi - 2*cos^-1( ... )
    # Note: This calculates the wrap angle on the LARGE pulley.
    term_cos = geom_term # The term inside is the same as the sin term, just used in arccos
    wrap_angle = 2 * np.pi - 2 * np.arccos(term_cos)
    
    # --- 3. Solve Tensions (F1, F2) ---
    # We have two equations:
    # 1) Moment: Tg + F1*(D/2) - F2*(D/2) = 0  =>  F2 - F1 = 2*Tg/D
    # 2) Friction: F2 / F1 = e^(f * wrap_angle)
    
    # Substitute (2) into (1):
    # F1 * e^(...) - F1 = 2*Tg/D
    # F1 * (e^(...) - 1) = 2*Tg/D
    
    exp_term = np.exp(friction_coeff * wrap_angle)
    
    F1 = (2 * Tg / D) / (exp_term - 1)
    F2 = F1 * exp_term
    F1_x = F1 * np.cos(angle_f1)
    F1_y = F1 * np.sin(angle_f1)
    F2_x = F2 * np.cos(angle_f2)
    F2_y = F2 * np.sin(angle_f2)
    
    # --- 4. Solve Reaction Forces (FGx, FGy) ---
    # Eq 1: -FGx + F1*cos(angle_f1) + F2*cos(angle_f2) = 0
    FGx = -(F1 * np.cos(angle_f1) + F2 * np.cos(angle_f2))
    
    # Eq 2: FGy - F1*sin(angle_f1) - F2*sin(angle_f2) = 0
    # NOTE: Your image had "- F2 cos(...)" for the last term. 
    # Physically, this implies a typo in the diagram's text, as vertical projection usually uses sin.
    # I have used sin() here. If you strictly need the image's text, change np.sin to np.cos below.
    FGy = F1 * np.sin(angle_f1) + F2 * np.sin(angle_f2)
    
    return {
        "F1 (N)": F1,
        "F2 (N)": F2,
        "FGx (N)": FGx,
        "FGy (N)": FGy,
        "Wrap Angle (rad)": wrap_angle,
        "Tension Ratio": exp_term,
        "F1_x (N)": F1_x,
        "F1_y (N)": F1_y,
        "F2_x (N)": F2_x,
        "F2_y (N)": F2_y
    }

# --- Example Usage ---
# Assuming Ratio is 16 based on "D/32" in your image (D/2 / 16 = D/32)
D_val = KFA.specs["flywheel_D"] / 1000.0
results = solve_flywheel_exact(
    Tg= -92.75, 
    a11=KFA.dims["a11"] / 1000, 
    h11=KFA.dims["h11"] / 1000, 
    D=D_val, 
    D_small= D_val/16, # Matching the image's D/32 term
    friction_coeff=KFA.specs["friction_coeff_f"]
)

for key, val in results.items():
    print(f"{key}: {val:.4f}")
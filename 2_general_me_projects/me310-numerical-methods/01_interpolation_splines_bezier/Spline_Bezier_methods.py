import numpy as np
import matplotlib.pyplot as plt

# ==============================================================================
# 1. LINEAR SPLINE
# ==============================================================================
def linear_spline(x, y, x_new):
    """
    Performs Linear Spline Interpolation.
    
    Concept: Connects consecutive data points with straight lines.
    
    Formula for interval [x_i, x_{i+1}]:
    S_i(x) = y_i + (y_{i+1} - y_i) * (x - x_i) / (x_{i+1} - x_i)
    """
    # Ensure inputs are sorted by x
    x = np.array(x)
    y = np.array(y)
    idx = np.argsort(x)
    x = x[idx]
    y = y[idx]
    
    y_new = []
    for val in x_new:
        # Find the interval [x_i, x_{i+1}] containing val
        # searchsorted returns the index where val should be inserted to maintain order
        if val < x[0] or val > x[-1]:
            # Extrapolation or simple boundary handling (clamping here for safety)
             y_new.append(0) # Or handle appropriately
             continue
             
        # Find index i such that x[i] <= val <= x[i+1]
        # We can use np.searchsorted
        i = np.searchsorted(x, val) - 1
        if i < 0: i = 0 # Handle exactly x[0] case
        
        # Calculate slope m
        if i >= len(x) - 1: # Edge case for last point
            i = len(x) - 2
            
        m = (y[i+1] - y[i]) / (x[i+1] - x[i])
        yi = y[i] + m * (val - x[i])
        y_new.append(yi)
        
    return np.array(y_new)

# ==============================================================================
# 2. QUADRATIC SPLINE
# ==============================================================================
def quadratic_spline(x, y, x_new):
    """
    Performs Quadratic Spline Interpolation.
    
    Concept:
    - n data points (nodes) -> n-1 intervals.
    - Each interval i has a quadratic polynomial: S_i(x) = a_i*x^2 + b_i*x + c_i
    - Total unknowns: 3 * (n-1)
    
    Constraints:
    1. Function values match at interior nodes: 2 * (n-2) equations
    2. First derivatives match at interior nodes: n-2 equations
    3. Function values match at endpoints (first and last): 2 equations
    4. Total equations so far: 2n - 4 + n - 2 + 2 = 3n - 4
    5. We need 1 more assumption. Common choice: S_0''(x) = 0 (first interval is linear -> a_0 = 0)
    """
    n = len(x)
    n_intervals = n - 1
    # Total unknowns = 3 * n_intervals (a_i, b_i, c_i for each interval)
    
    # We will solve A * coef = B
    # Structure of coef vector: [a0, b0, c0, a1, b1, c1, ..., an-1, bn-1, cn-1]
    
    num_unknowns = 3 * n_intervals
    A = np.zeros((num_unknowns, num_unknowns))
    B = np.zeros(num_unknowns)
    
    row = 0
    
    # 1. Function values must match at endpoints of each interval
    # For each interval i, S_i(x_i) = y_i AND S_i(x_{i+1}) = y_{i+1}
    # Actually, standard derivation:
    # S_i(x_i) = y_i
    # S_i(x_{i+1}) = y_{i+1}
    
    for i in range(n_intervals):
        # S_i(x_i) = y_i
        # a_i * x_i^2 + b_i * x_i + c_i = y_i
        idx = 3 * i
        A[row, idx]   = x[i]**2
        A[row, idx+1] = x[i]
        A[row, idx+2] = 1
        B[row] = y[i]
        row += 1
        
        # S_i(x_{i+1}) = y_{i+1}
        # a_i * x_{i+1}^2 + b_i * x_{i+1} + c_i = y_{i+1}
        A[row, idx]   = x[i+1]**2
        A[row, idx+1] = x[i+1]
        A[row, idx+2] = 1
        B[row] = y[i+1]
        row += 1
        
    # 2. Derivative continuity at interior nodes x_1, ..., x_{n-2}
    # S'_{i-1}(x_i) = S'_i(x_i)
    # 2*a_{i-1}*x_i + b_{i-1} = 2*a_i*x_i + b_i
    # -> 2*a_{i-1}*x_i + b_{i-1} - 2*a_i*x_i - b_i = 0
    
    for i in range(1, n_intervals):
        # Interior node index is i (corresponding to x[i])
        # Previous interval: i-1
        # Current interval: i
        
        prev_idx = 3 * (i - 1)
        curr_idx = 3 * i
        
        xi = x[i]
        
        # Coefs for S_{i-1}
        A[row, prev_idx]   = 2 * xi  # coeff for a_{i-1}
        A[row, prev_idx+1] = 1       # coeff for b_{i-1}
        
        # Coefs for S_i
        A[row, curr_idx]   = -2 * xi # coeff for a_i
        A[row, curr_idx+1] = -1      # coeff for b_i
        
        B[row] = 0
        row += 1
        
    # 3. Extra constraint: Let a_0 = 0 (Linear first segment)
    A[row, 0] = 1
    B[row] = 0
    row += 1
    
    # Solve system
    coefs = np.linalg.solve(A, B)
    
    # Evaluate
    y_new = []
    for val in x_new:
        if val < x[0] or val > x[-1]:
            y_new.append(0) # Boundary check
            continue
            
        # Find interval
        i = np.searchsorted(x, val) - 1
        if i < 0: i = 0
        if i >= n_intervals: i = n_intervals - 1
        
        a = coefs[3*i]
        b = coefs[3*i+1]
        c_ = coefs[3*i+2]
        
        y_val = a * val**2 + b * val + c_
        y_new.append(y_val)
        
    return np.array(y_new)

# ==============================================================================
# 3. CUBIC SPLINE (Natural)
# ==============================================================================
def cubic_spline(x, y, x_new):
    """
    Performs Natural Cubic Spline Interpolation.
    
    Method used: Solving for the second derivatives (moments) M_i at each node.
    
    System of equations (Tridiagonal Matrix):
    mu_i * M_{i-1} + 2 * M_i + lambda_i * M_{i+1} = d_i
    
    Where:
    h_i = x_{i+1} - x_i
    mu_i = h_{i-1} / (h_{i-1} + h_i)
    lambda_i = h_i / (h_{i-1} + h_i)
    d_i = (6 / (h_{i-1} + h_i)) * [ (y_{i+1}-y_i)/h_i - (y_i-y_{i-1})/h_{i-1} ]
    
    Natural Boundary Conditions: M_0 = 0, M_{n-1} = 0
    """
    n = len(x)
    h = np.diff(x) # h_i = x[i+1] - x[i]
    
    # We need to solve for M = [M_0, M_1, ..., M_{n-1}]
    # But for Natural Spline, M_0 = 0 and M_{n-1} = 0.
    # So we only solve for M_1 ... M_{n-2} (n-2 unknowns).
    
    # Construct A matrix (n-2 x n-2) and RHS vector b (n-2)
    # The unknowns correspond to indices 1 to n-2 in the original 0..n-1 range.
    
    if n < 3:
        print("Need at least 3 points for cubic spline interior calculation.")
        return linear_spline(x, y, x_new) # Fallback
        
    dim = n - 2
    A = np.zeros((dim, dim))
    RHS = np.zeros(dim)
    
    # Fill A and RHS
    # We iterate i from 1 to n-2 (the internal nodes)
    # In the matrix system, row index j corresponds to node i = j+1
    
    for j in range(dim):
        i = j + 1 # Convert matrix row index to node index
        
        # Ratios mu and lambda
        # Denominator common to both: h_{i-1} + h_i
        denom = h[i-1] + h[i]
        
        mu = h[i-1] / denom
        lam = h[i] / denom
        
        # Calculation for d_i (RHS)
        # First divided difference
        diff1 = (y[i+1] - y[i]) / h[i]
        diff2 = (y[i] - y[i-1]) / h[i-1]
        d = (6 / denom) * (diff1 - diff2)
        
        # Populate Diagonal
        A[j, j] = 2
        
        # Populate Off-Diagonals
        if j > 0:
            # M_{i-1} term exists (linked to previous row)
            A[j, j-1] = mu
        if j < dim - 1:
            # M_{i+1} term
            A[j, j+1] = lam
            
        RHS[j] = d
        
    # Solve for internal moments
    M_internal = np.linalg.solve(A, RHS)
    
    # Construct full M vector including boundaries
    M = np.zeros(n)
    M[1:-1] = M_internal
    # M[0] and M[-1] remain 0 (Natural boundary)
    
    # Evaluate spline
    y_new = []
    for val in x_new:
        if val < x[0] or val > x[-1]:
            y_new.append(0)
            continue
            
        # Find interval i
        i = np.searchsorted(x, val) - 1
        if i < 0: i = 0
        if i >= n - 1: i = n - 2
        
        hi = h[i]
        
        # Cubic spline formula using moments M_i and M_{i+1}
        # S_i(x) = term A + term B + term C + term D
        # A = (M_i * (x_{i+1} - x)^3) / 6hi
        # B = (M_{i+1} * (x - x_i)^3) / 6hi
        # C = (y_i - (M_i*hi^2)/6) * (x_{i+1}-x)/hi
        # D = (y_{i+1} - (M_{i+1}*hi^2)/6) * (x-x_i)/hi
        
        term1 = (M[i] * (x[i+1] - val)**3) / (6 * hi)
        term2 = (M[i+1] * (val - x[i])**3) / (6 * hi)
        term3 = (y[i] - (M[i] * hi**2) / 6) * (x[i+1] - val) / hi
        term4 = (y[i+1] - (M[i+1] * hi**2) / 6) * (val - x[i]) / hi
        
        y_val = term1 + term2 + term3 + term4
        y_new.append(y_val)
        
    return np.array(y_new)

# ==============================================================================
# 4. BEZIER CURVES
# ==============================================================================
def bezier_curve(control_points, n_points=100):
    """
    Generates points for a Bezier Curve given a set of control points.
    
    Uses the explicit Bernstein Basis Polynomial formula:
    B(t) = sum_{i=0}^{n} [ Binomial(n, i) * (1-t)^{n-i} * t^i * P_i ]
    where t goes from 0 to 1.
    
    Parameters:
    control_points (list or array): List of [x, y] coordinates
    n_points (int): Resolution of the curve
    
    Returns:
    curve_x, curve_y: Arrays of x and y coordinates for the curve
    """
    points = np.array(control_points)
    n = len(points) - 1 # Degree of curve
    
    t = np.linspace(0, 1, n_points)
    curve_x = np.zeros(n_points)
    curve_y = np.zeros(n_points)
    
    def binomial_coeff(n, k):
        if k < 0 or k > n:
            return 0
        # Calculate factorial using loop or simple logic
        top = 1
        for x in range(1, n+1): top *= x
        
        bot_k = 1
        for x in range(1, k+1): bot_k *= x
        
        bot_nk = 1
        for x in range(1, n-k+1): bot_nk *= x
        
        return top // (bot_k * bot_nk)

    for i in range(n + 1):
        # Bernstein Basis Polynomial b_{i,n}(t)
        # coef = n! / (i! * (n-i)!)
        coef = binomial_coeff(n, i)
        
        # basis = coef * (1-t)^(n-i) * t^i
        basis = coef * ((1 - t)**(n - i)) * (t**i)
        
        curve_x += basis * points[i, 0]
        curve_y += basis * points[i, 1]
        
    return curve_x, curve_y

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
if __name__ == "__main__":
    print("=========================================")
    print("SPLINE & BEZIER METHODS TUTORIAL")
    print("=========================================")
    
    # 1. SPLINE TEST DATA (Smooth non-linear function)
    # Example: sin(x)
    x_data = np.array(np.linspace(0, 8, 7))
    y_data = np.sin(x_data)+x_data
    
    x_mesh = np.linspace(0, 8, 100)
    
    print("\n--- Interpolating sin(x) Data Points ---")
    print(f"X Nodes: {x_data}")
    print(f"Y Nodes: {np.round(y_data, 3)}")
    
    # Run Splines
    y_linear = linear_spline(x_data, y_data, x_mesh)
    y_quadratic = quadratic_spline(x_data, y_data, x_mesh)
    y_cubic = cubic_spline(x_data, y_data, x_mesh)
    
    print("\nCalculated splines. Let's inspect errors at x=2.5")
    # True value
    true_val = np.sin(2.5)+2.5
    
    # Interpolated values
    lin_val = linear_spline(x_data, y_data, [2.5])[0]
    quad_val = quadratic_spline(x_data, y_data, [2.5])[0]
    cubic_val = cubic_spline(x_data, y_data, [2.5])[0]
    
    print(f"True Value (sin(2.5)): {true_val:.5f}")
    print(f"Linear Spline:    {lin_val:.5f} (Err: {abs(true_val - lin_val):.5f})")
    print(f"Quadratic Spline: {quad_val:.5f} (Err: {abs(true_val - quad_val):.5f})")
    print(f"Cubic Spline:     {cubic_val:.5f} (Err: {abs(true_val - cubic_val):.5f})")
    print("Observation: Cubic spline typically has the lowest error for smooth functions.")

    # 2. BEZIER CURVE TEST
    print("\n--- Bezier Curve Generation ---")
    # Define control points
    # P0, P1, P2, P3 -> Cubic Bezier
    ctrl_pts = [
        [0, 0],   # Start
        [2, 5],   # Control 1 (pull)
        [5, 5],   # Control 2 (pull)
        [6, 0]    # End
    ]
    
    bx, by = bezier_curve(ctrl_pts)
    
    print(f"Control Points: {ctrl_pts}")
    print(f"Generated {len(bx)} curve points.")
    print(f"Start Point: ({bx[0]:.1f}, {by[0]:.1f})")
    print(f"End Point:   ({bx[-1]:.1f}, {by[-1]:.1f})")
    print(f"Mid-Curve approx (t=0.5): ({bx[50]:.2f}, {by[50]:.2f})")
    
    print("\nDone.")

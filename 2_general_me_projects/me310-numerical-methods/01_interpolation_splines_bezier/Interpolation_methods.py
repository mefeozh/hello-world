import numpy as np
import matplotlib.pyplot as plt

def lagrange_interpolation(x, y, xi):
    """
    Performs Lagrange Interpolation.
    
    The Lagrange polynomial is defined as:
    L(x) = sum(y_i * l_i(x))
    where l_i(x) = product((x - x_j) / (x_i - x_j)) for j != i
    
    Parameters:
    x (array-like): x-coordinates of data points (nodes)
    y (array-like): y-coordinates of data points (values)
    xi (float or array-like): The point(s) where we want to interpolate
    
    Returns:
    yi: The interpolated value(s) at xi
    """
    n = len(x)
    m = len(xi) if isinstance(xi, (list, np.ndarray)) else 1
    yi = np.zeros(m)
    
    # Ensure inputs are numpy arrays
    x = np.array(x)
    y = np.array(y)
    
    # Handle single point vs array input for xi
    if isinstance(xi, (float, int)):
        xi = np.array([xi])
        
    for k, val in enumerate(xi):
        term = 0
        for i in range(n):
            # Calculate the Lagrange basis polynomial l_i(x)
            p = 1
            for j in range(n):
                if i != j:
                    p = p * (val - x[j]) / (x[i] - x[j])
            term += p * y[i]
        yi[k] = term
        
    return yi if m > 1 else yi[0]

def divided_diff_table(x, y):
    """
    Computes the Example Divided Difference Table for Newton Interpolation.
    
    Parameters:
    x (array-like): x-coordinates
    y (array-like): y-coordinates
    
    Returns:
    coef (array): The diagonal of the table (coefficients for the polynomial)
    table (matrix): The full divided diff table (for visualization)
    """
    n = len(y)
    coef = np.zeros([n, n])
    # The first column is y
    coef[:,0] = y
    
    for j in range(1,n):
        for i in range(n-j):
            # Difference formula: (y_next - y_curr) / (x_next - x_curr)
            coef[i][j] = (coef[i+1][j-1] - coef[i][j-1]) / (x[i+j]-x[i])
            
    return coef[0, :], coef # return only the first row (coefficients) and full table

def newton_interpolation(x, y, xi):
    """
    Evaluates the Newton Polynomial at xi using computed coefficients.
    
    P(x) = a0 + a1(x-x0) + a2(x-x0)(x-x1) + ...
    
    Parameters:
    x (array-like): x-coordinates of data points
    y (array-like): y-coordinates of data points
    xi (float or array-like): point(s) to interpolate
    
    Returns:
    yi: Interpolated value(s)
    """
    coef, _ = divided_diff_table(x, y)
    n = len(x) # degree + 1
    
    # Ensure input is array for vectorized calculation or handled in loop
    if isinstance(xi, (float, int)):
        xi_arr = np.array([xi])
    else:
        xi_arr = np.array(xi)
        
    n_points = len(xi_arr)
    yi = np.zeros(n_points)
    
    for k, val in enumerate(xi_arr):
        p = coef[n-1]
        # Horner's method / Nested multiplication for efficiency
        for i in range(1, n):
            p = coef[n-1-i] + (val - x[n-1-i])*p
        yi[k] = p
        
    return yi if n_points > 1 else yi[0]

def chebyshev_nodes(a, b, n):
    """
    Generates n Chebyshev nodes in the interval [a, b].
    
    Chebyshev nodes minimize the Runge's phenomenon (oscillation at edges)
    when using high-degree polynomial interpolation.
    
    Formula: x_k = 0.5 * (a + b) + 0.5 * (b - a) * cos((2k-1) / (2n) * pi)
    for k = 1 to n.
    """
    k = np.arange(1, n + 1)
    # The argument for cosine
    theta = (2 * k - 1) / (2 * n) * np.pi
    # Map from [-1, 1] to [a, b]
    nodes = 0.5 * (a + b) + 0.5 * (b - a) * np.cos(theta)
    return nodes

# ==========================================
# Main Tutorial Execution
# ==========================================
if __name__ == "__main__":
    print("-" * 60)
    print("INTERPOLATION METHODS TUTORIAL")
    print("-" * 60)
    
    # 1. Define a function to interpolate
    # Runge function is a classic example of where equispaced interpolation fails
    def true_function(val):
        return 1 / (1 + 25 * val**2)
    
    # 2. Setup Data
    # Let's use a large number of points as requested (e.g., 11 points -> 10th degree poly)
    N = 11 
    a, b = -1, 1
    
    # -----------------------------------
    # Case A: Equidistant Nodes
    # -----------------------------------
    x_eq = np.linspace(a, b, N)
    y_eq = true_function(x_eq)
    
    print(f"\n[Case A] Equispaced Nodes (N={N})")
    print(f"Nodes: {np.round(x_eq, 3)}")
    print(f"Values: {np.round(y_eq, 3)}")
    
    # Test points (finer grid to see the curve)
    x_test = np.linspace(a, b, 100)
    y_true = true_function(x_test)
    
    # Perform Interpolations
    print("\nCalculated Lagrange Interpolation on test grid...")
    y_lagrange = lagrange_interpolation(x_eq, y_eq, x_test)
    
    print("Calculated Newton Interpolation on test grid...")
    # Get coefficients just to show them
    coefs, div_table = divided_diff_table(x_eq, y_eq)
    print(f"Newton Coefficients (first 5): {np.round(coefs[:5], 4)} ...")
    y_newton = newton_interpolation(x_eq, y_eq, x_test)
    
    # -----------------------------------
    # Case B: Chebyshev Nodes
    # -----------------------------------
    print(f"\n[Case B] Chebyshev Nodes (N={N})")
    x_cheb = chebyshev_nodes(a, b, N)
    y_cheb = true_function(x_cheb)
    print(f"Nodes: {np.round(x_cheb, 3)}")
    
    print("Calculated Interpolation using Chebyshev nodes...")
    # We can use either Lagrange or Newton method on these nodes. 
    # Newton is numerically more stable for high degrees usually.
    y_cheb_interp = newton_interpolation(x_cheb, y_cheb, x_test)
    
    # -----------------------------------
    # Comparison & Error Checking
    # -----------------------------------
    # Let's check error at a specific point, e.g., x = 0.5
    check_pt = 0.5
    true_val = true_function(check_pt)
    
    val_eq = lagrange_interpolation(x_eq, y_eq, check_pt)
    val_cheb = newton_interpolation(x_cheb, y_cheb, check_pt)
    
    print("\n--- ERROR ANALYSIS at x = 0.5 ---")
    print(f"True Value:       {true_val:.6f}")
    print(f"Equispaced (Lag): {val_eq:.6f}  | Error: {abs(true_val - val_eq):.6f}")
    print(f"Chebyshev (Newt): {val_cheb:.6f}  | Error: {abs(true_val - val_cheb):.6f}")
    print("\nObservation: Chebyshev nodes should typically yield strictly lower max error for Runge function.")

    # Optional: ASCII Plot (since we are in terminal) or description
    # Because we cannot easily popup a plot in this environment, we just printed data.
    # But usually one would do:
    plt.plot(x_test, y_true, label='True')
    plt.plot(x_test, y_lagrange, label='Equispaced')
    plt.plot(x_test, y_cheb_interp, label='Chebyshev')
    plt.legend()
    plt.show()
    
    print("\nDone.")

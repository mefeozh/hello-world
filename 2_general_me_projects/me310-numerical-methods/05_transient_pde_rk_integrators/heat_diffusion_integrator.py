import numpy as np
import sys
import matplotlib.pyplot as plt

def plot_evolution(x, history, times, title, filename):
    plt.figure(figsize=(10, 6))
    
    total_steps = len(history)
    indices = np.linspace(0, total_steps-1, 6, dtype=int)
    
    for idx in indices:
        t = times[idx]
        plt.plot(x, history[idx], label=f't={t:.4f}')
        
    plt.xlabel('x')
    plt.ylabel('phi')
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.savefig(filename)
    plt.close()
    print(f"Saved plot: {filename}")

def plot_comparison(x, results_dict, title, filename):
    plt.figure(figsize=(10, 6))
    
    for name, phi in results_dict.items():
        plt.plot(x, phi, label=name, linestyle='--', marker='o', markevery=10, markersize=3)
        
    plt.xlabel('x')
    plt.ylabel('phi')
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.savefig(filename)
    plt.close()
    print(f"Saved comparison: {filename}")


def read_input(filepath="ME310_HW4_2446672\input.txt"):
    """
    Reads parameters from input.txt.
    Format:
    Line 1: alpha
    Line 2: N
    Line 3: M
    Line 4: L
    Line 5: T_final
    Line 6: Method Name
    """
    try:
        with open(filepath, 'r') as f:
            lines = [l.strip() for l in f if l.strip()]
        
        alpha = float(lines[0])
        N = int(lines[1])
        M = int(lines[2])
        L = float(lines[3])
        T_final = float(lines[4])
        method_names = lines[5].split(',')
        
        # Hardcoded Boundary Conditions
        BC_Left = 0.0
        BC_Right = 1.0
        
        # Calculate dt
        dt = T_final / M
        
        return alpha, N, M, L, dt, BC_Left, BC_Right, method_names
    except Exception as e:
        print(f"Error reading input: {e}")
        # Return safe defaults if error but with method name default
        return 0.1, 100, 1000, 1.0, 0.001, 0.0, 1.0, "RK4"


def compute_R(phi, alpha, dx):
    """
    Calculates the time derivative d(phi)/dt = R(phi, t)
    R_i = alpha * (phi_{i+1} - 2*phi_i + phi_{i-1}) / dx^2
    """
    N_points = len(phi)
    R = np.zeros(N_points)
    
    coeff = alpha / (dx**2)
    
    # R[i] = coeff * (phi[i+1] - 2*phi[i] + phi[i-1])
    # Vectorized: R[1:-1]
    R[1:-1] = coeff * (phi[2:] - 2*phi[1:-1] + phi[:-2])
    
    # Boundaries are fixed, so Rate of change is 0
    R[0] = 0.0
    R[-1] = 0.0
    
    return R

def solve_RK2(phi_init, dt, M, alpha, dx):
    """
    Runge-Kutta 2nd Order (Heun's Method)
    """
    phi = phi_init.copy()
    history = [phi.copy()]
    
    for _ in range(M):
        k1 = compute_R(phi, alpha, dx)
        k2 = compute_R(phi + dt * k1, alpha, dx)
        
        phi = phi + (dt / 2.0) * (k1 + k2)
        history.append(phi.copy())
        
    return np.array(history)

def solve_RK3(phi_init, dt, M, alpha, dx):
    """
    Runge-Kutta 3rd Order
    """
    phi = phi_init.copy()
    history = [phi.copy()]
    
    for _ in range(M):
        k1 = compute_R(phi, alpha, dx)
        k2 = compute_R(phi + 0.5 * dt * k1, alpha, dx)
        k3 = compute_R(phi - dt * k1 + 2 * dt * k2, alpha, dx)
        
        phi = phi + (dt / 6.0) * (k1 + 4*k2 + k3)
        history.append(phi.copy())
        
    return np.array(history)

def solve_RK4(phi_init, dt, M, alpha, dx):
    """
    Runge-Kutta 4th Order Implementation
    """
    phi = phi_init.copy()
    history = [phi.copy()]
    
    for _ in range(M):
        k1 = compute_R(phi, alpha, dx)
        k2 = compute_R(phi + 0.5 * dt * k1, alpha, dx)
        k3 = compute_R(phi + 0.5 * dt * k2, alpha, dx)
        k4 = compute_R(phi + dt * k3, alpha, dx)
        
        phi = phi + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
        history.append(phi.copy())
        
    return np.array(history)

def solve_AB2(phi_init, dt, M, alpha, dx):

    phi = phi_init.copy()
    history = [phi.copy()]
    derivs = [] 
    
    # Step 0 -> 1 (RK4)
    k1 = compute_R(phi, alpha, dx)
    derivs.append(k1)
    
    k2 = compute_R(phi + 0.5 * dt * k1, alpha, dx)
    k3 = compute_R(phi + 0.5 * dt * k2, alpha, dx)
    k4 = compute_R(phi + dt * k3, alpha, dx)
    phi = phi + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
    history.append(phi.copy())
    
    # Loop 1 to M-1
    for m in range(1, M):
        curr_R = compute_R(phi, alpha, dx)
        derivs.append(curr_R)
        
        # AB2: phi_{n+1} = phi_n + dt/2 * (3*R_n - R_{n-1})
        res = phi + (dt / 2.0) * (3 * derivs[-1] - derivs[-2])
        phi = res
        history.append(phi.copy())
        
    return np.array(history)


def solve_AB3(phi_init, dt, M, alpha, dx):

    phi = phi_init.copy()
    history = [phi.copy()]
    derivs = [] # Store derivatives R for history

    # Step 0 -> 1 (RK4)
    k1 = compute_R(phi, alpha, dx)
    derivs.append(k1) # R_0
    
    # Do RK4 step
    k2 = compute_R(phi + 0.5 * dt * k1, alpha, dx)
    k3 = compute_R(phi + 0.5 * dt * k2, alpha, dx)
    k4 = compute_R(phi + dt * k3, alpha, dx)
    phi_new = phi + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
    phi = phi_new
    history.append(phi.copy())
    
    # Step 1 -> 2 (RK4)
    k1 = compute_R(phi, alpha, dx) 
    derivs.append(k1)
    
    k2 = compute_R(phi + 0.5 * dt * k1, alpha, dx)
    k3 = compute_R(phi + 0.5 * dt * k2, alpha, dx)
    k4 = compute_R(phi + dt * k3, alpha, dx)
    phi_new = phi + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
    phi = phi_new
    history.append(phi.copy())

    # Loop from step 2 to M-1
    for m in range(2, M):

        # Calculate current derivative R_m
        curr_R = compute_R(phi, alpha, dx)
        derivs.append(curr_R)
        
        # AB3 Formula: phi_{m+1} = phi_m + dt/12 * (23*R_m - 16*R_{m-1} + 5*R_{m-2})
        R_m = derivatives_history(derivs, 0) 
        R_m_1 = derivatives_history(derivs, 1) 
        R_m_2 = derivatives_history(derivs, 2) 
        
        delta = (dt / 12.0) * (23 * derivs[-1] - 16 * derivs[-2] + 5 * derivs[-3])
        phi = phi + delta
        history.append(phi.copy())
    
    return np.array(history)

def derivatives_history(d_list, back_index):
    # back_index 0 is last, 1 is second last...
    return d_list[-(back_index+1)]

def solve_PredictorCorrector(phi_init, dt, M, alpha, dx):

    phi = phi_init.copy()
    history = [phi.copy()]
    derivs = [] 
    
    # Step 0 -> 1 (RK4)
    k1 = compute_R(phi, alpha, dx)
    derivs.append(k1) 
    k2 = compute_R(phi + 0.5 * dt * k1, alpha, dx)
    k3 = compute_R(phi + 0.5 * dt * k2, alpha, dx)
    k4 = compute_R(phi + dt * k3, alpha, dx)
    phi = phi + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
    history.append(phi.copy())
    
    # Step 1 -> 2 (RK4)
    k1 = compute_R(phi, alpha, dx)
    derivs.append(k1)
    k2 = compute_R(phi + 0.5 * dt * k1, alpha, dx)
    k3 = compute_R(phi + 0.5 * dt * k2, alpha, dx)
    k4 = compute_R(phi + dt * k3, alpha, dx)
    phi = phi + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
    history.append(phi.copy())
    
    # Now loop
    for m in range(2, M):
        curr_R = compute_R(phi, alpha, dx) # f_n
        derivs.append(curr_R)
        
        # Predict (AB3)
        # phi_pred = phi_n + dt/12 * (23 f_n - 16 f_{n-1} + 5 f_{n-2})
        pred_change = (dt / 12.0) * (23 * derivs[-1] - 16 * derivs[-2] + 5 * derivs[-3])
        phi_pred = phi + pred_change
        
        # Evaluate f at predicted state
        f_pred = compute_R(phi_pred, alpha, dx)
        
        # Correct (AM3)
        # phi_{n+1} = phi_n + dt/24 * (9 f_{n+1} + 19 f_n - 5 f_{n-1} + f_{n-2})
        corr_change = (dt / 24.0) * (9 * f_pred + 19 * derivs[-1] - 5 * derivs[-2] + derivs[-3])
        phi = phi + corr_change
        history.append(phi.copy())
        
    return np.array(history)

def main():
    alpha, N, M, L, dt, BC_Left, BC_Right, method_names = read_input()
    print(f"Parameters read: alpha={alpha}, N={N}, M={M}, L={L}, dt={dt}, BC_L={BC_Left}, BC_R={BC_Right}, Method={method_names}")
    print
    x = np.linspace(0, L, N+1)
    dx = L / N
    
    # Initial Condition
    phi_init = np.zeros(N+1)
    phi_init[0] = BC_Left
    phi_init[-1] = BC_Right
    
    
    
    for method_name in method_names:
        # Select Solver
        print(f"Running {method_name}...")
    
        if method_name == "RK2":
            res = solve_RK2(phi_init, dt, M, alpha, dx)
        elif method_name == "RK3":
            res = solve_RK3(phi_init, dt, M, alpha, dx)
        elif method_name == "RK4":
            res = solve_RK4(phi_init, dt, M, alpha, dx)
        elif method_name == "AB2":
            res = solve_AB2(phi_init, dt, M, alpha, dx)
        elif method_name == "AB3":
            res = solve_AB3(phi_init, dt, M, alpha, dx)
        elif method_name == "AB3-AM3" or method_name == "PC":
            res = solve_PredictorCorrector(phi_init, dt, M, alpha, dx)
        else:
            print(f"Unknown method {method_name}, defaulting to RK4")
            res = solve_RK4(phi_init, dt, M, alpha, dx)
        
        # Time array
        times = np.linspace(0, M*dt, M+1)
        
        # Plot Evolution
        plot_evolution(x, res, times, f"Evolution of Phi ({method_name})", f"ME310_HW4_2446672/evolution_2{method_name}.png")
        
        # Final Result
        min_idx = np.nan
        mid_idx = N // 2
        if not np.any(np.isnan(res[-1])):
            print(f"Final Midpoint Value ({method_name}): {res[-1, mid_idx]}")
        else:
            print(f"Final Midpoint Value ({method_name}): Unstable/NaN")
    
if __name__ == "__main__":
    main()

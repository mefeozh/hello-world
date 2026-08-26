import math
import sys
import os

INPUT_FILE = "input.txt"
OUTPUT_FILE = "output.txt"
PLOT_FILE = "convergence_plot.png"


class FlopCounter:

    def __init__(self):
        self.ops = 0

    def add(self, n=1):
        self.ops += n

    def reset(self):
        self.ops = 0

# --- SOLVER ALGORITHMS ---

def solve_naive_gauss(alpha, N, P0, PN, flops):

    flops.reset()
    n = N - 1

    A = [[0.0] * n for _ in range(n)]
    b = [0.0] * n

    for i in range(n):
        A[i][i] = 1.0
        if i > 0: A[i][i-1] = -alpha
        else: b[i] += alpha * P0; flops.add(2)

        if i < n - 1: A[i][i+1] = -(1.0 - alpha); flops.add(1)
        else: b[i] += (1.0 - alpha) * PN; flops.add(2)

    for k in range(n-1):
        for i in range(k+1, n):
            if A[k][k] == 0: continue
            factor = A[i][k] / A[k][k]; flops.add(1)
            for j in range(k, n):
                A[i][j] = A[i][j] - factor * A[k][j]; flops.add(2)
            b[i] = b[i] - factor * b[k]; flops.add(2)


    x = [0.0] * n
    for i in range(n-1, -1, -1):
        sum_ax = 0.0
        for j in range(i+1, n):
            sum_ax += A[i][j] * x[j]; flops.add(2)
        x[i] = (b[i] - sum_ax) / A[i][i]; flops.add(2)

    return [P0] + x + [PN]

def solve_thomas(alpha, N, P0, PN, flops):

    flops.reset()
    n_unknowns = N - 1
    c_prime = [0.0] * n_unknowns
    d_prime = [0.0] * n_unknowns


    b0 = 1.0
    c0 = -(1.0 - alpha); flops.add(2)
    rhs0 = alpha * P0;   flops.add(1)

    c_prime[0] = c0 / b0; flops.add(1)
    d_prime[0] = rhs0 / b0; flops.add(1)

    for i in range(1, n_unknowns):
        a = -alpha
        b = 1.0
        c = -(1.0 - alpha); flops.add(2)

        rhs = 0.0
        if i == n_unknowns - 1: rhs = (1.0 - alpha) * PN; flops.add(2)

        denom = b - a * c_prime[i-1]; flops.add(2)
        if i < n_unknowns - 1: c_prime[i] = c / denom; flops.add(1)
        d_prime[i] = (rhs - a * d_prime[i-1]) / denom; flops.add(3)

    P_solution = [0.0] * (N + 1)
    P_solution[0], P_solution[N] = P0, PN
    P_solution[N-1] = d_prime[n_unknowns - 1]

    for i in range(N-2, 0, -1):
        idx = i - 1
        P_solution[i] = d_prime[idx] - c_prime[idx] * P_solution[i+1]; flops.add(2)

    return P_solution

def solve_jacobi(alpha, N, P0, PN, tol, flops):

    flops.reset()
    P_old = [0.0] * (N + 1)
    P_new = [0.0] * (N + 1)
    P_old[0], P_old[N] = P0, PN
    P_new[0], P_new[N] = P0, PN

    error_history = []
    iteration = 0

    while iteration < 20000:
        iteration += 1
        error = 0.0

        for i in range(1, N):

            val = alpha * P_old[i-1] + (1.0 - alpha) * P_old[i+1]
            flops.add(4)
            P_new[i] = val


        for i in range(1, N):
            diff = abs(P_new[i] - P_old[i]); flops.add(1)
            if diff > error: error = diff


        error_history.append(error)

        P_old[:] = P_new[:]
        if error < tol: break

    return P_old, error_history

def solve_gauss_seidel_sor(alpha, N, P0, PN, tol, flops, omega=1.0):

    flops.reset()
    P = [0.0] * (N + 1)
    P[0], P[N] = P0, PN

    error_history = []
    iteration = 0

    while iteration < 20000:
        iteration += 1
        error = 0.0

        for i in range(1, N):
            P_old_val = P[i]


            gs_val = alpha * P[i-1] + (1.0 - alpha) * P[i+1]
            flops.add(4)


            new_val = (1.0 - omega) * P_old_val + omega * gs_val
            flops.add(4)

            P[i] = new_val

            diff = abs(new_val - P_old_val); flops.add(1)
            if diff > error: error = diff

        error_history.append(error)

        if error < tol: break

    return P, error_history



def read_input():
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: {INPUT_FILE} not found."); sys.exit(1)
    try:
        with open(INPUT_FILE, 'r') as f: lines = f.readlines()
        return float(lines[0].split()[0]), float(lines[1].split()[0]), \
               int(lines[2].split()[0]), float(lines[3].split()[0])
    except Exception as e:
        print(f"Error reading input: {e}"); sys.exit(1)

def generate_convergence_graph(jacobi_hist, sor_hist, tol, alpha, N):

    try:
        import matplotlib.pyplot as plt

        t, alpha, N, tol = read_input()
        plt.figure(figsize=(10, 6))


        plt.semilogy(range(1, len(jacobi_hist)+1), jacobi_hist,
                     'r-', linewidth=2, label='Jacobi Method')


        plt.semilogy(range(1, len(sor_hist)+1), sor_hist,
                     'b-', linewidth=2, label='Gauss-Seidel SOR (w={:.2f})')


        plt.axhline(y=tol, color='g', linestyle='--', label=f'Tolerance ({tol})')

        plt.title(f'Convergence Rate (N={N}, alpha={alpha})')
        plt.xlabel('Iteration Number (k)')
        plt.ylabel('Error (Log Scale)')
        plt.legend()
        plt.grid(True, which="both", ls="-", alpha=0.5)

        plt.savefig(PLOT_FILE)
        print(f"Convergence graph saved to '{PLOT_FILE}'")
        plt.close()

    except ImportError:
        print("matplotlib not installed. Graph skipped.")

def main():
    print("--- 1D Probabilistic Motion Solver ---")
    t, alpha, N, tol = read_input()
    print(f"Input: t={t}, alpha={alpha}, N={N}, tol={tol}")
    P0 = 0.2 * math.sin(math.pi * t)
    PN = 1.0 - 0.2 * math.sin(math.pi * t)


    f_naive = FlopCounter()
    p_naive = solve_naive_gauss(alpha, N, P0, PN, f_naive)

    f_thomas = FlopCounter()
    p_thomas = solve_thomas(alpha, N, P0, PN, f_thomas)

    f_jacobi = FlopCounter()
    p_jacobi, h_jacobi = solve_jacobi(alpha, N, P0, PN, tol, f_jacobi)

    f_sor = FlopCounter()
    p_sor, h_sor = solve_gauss_seidel_sor(alpha, N, P0, PN, tol, f_sor)


    with open(OUTPUT_FILE, 'w') as f:
        head = f"{'Idx':<4} {'Naive':<10} {'Thomas':<10} {'Jacobi':<10} {'SOR':<10}\n"
        f.write(head)

        for i in range(N + 1):
            row = f"{i:<4d} {p_naive[i]:<10.6f} {p_thomas[i]:<10.6f} {p_jacobi[i]:<10.6f} {p_sor[i]:<10.6f}\n"
            f.write(row)


        f.write("\n--- Performance Analysis ---\n")
        f.write(f"Naive Gauss (Ops): {f_naive.ops}\n")
        f.write(f"Thomas (Ops):      {f_thomas.ops}\n")
        f.write(f"Jacobi:            {f_jacobi.ops} Ops in {len(h_jacobi)} iterations\n")
        f.write(f"SOR:               {f_sor.ops} Ops in {len(h_sor)} iterations\n")

    print(f"Data saved to {OUTPUT_FILE}")
    print(f"Jacobi Iterations: {len(h_jacobi)}")
    print(f"SOR Iterations:    {len(h_sor)}")


    generate_convergence_graph(h_jacobi, h_sor, tol, alpha, N)

if __name__ == "__main__":
    main()


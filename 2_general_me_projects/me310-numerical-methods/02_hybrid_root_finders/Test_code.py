import numpy as np
# from solver_1234567 import solver_1234567
from solver_2446672 import solver_2446672


# === Function wrapper for counter (read-only counter) ===
class FunctionWithCounter:
    def __init__(self, func, max_calls=1000):
        self._func = func
        self._count = 0
        self._max_calls = max_calls

    def __call__(self, x):
        self._count += 1
        if self._count > self._max_calls:
            raise RuntimeError("Exceeded maximum allowed evaluations (1000).")
        return self._func(x)

    @property
    def count(self):
        return self._count


# === 1D Test Functions ===
def f1(x): return (x - 1)**3                    # single root at x = 1
def f2(x): return (x - 2)*(x - 3)               # multiple roots at x = 2, 3
def f3(x): return (x - 2)**2                    # repeated root at x = 2
def f4(x): return np.tan(x) - x                 # discontinuous, root near 0
def f5(x): return (x + 2)**2 + 1                # no root (bonus)

# === Multivariable test (Bonus) ===
def f6(vec):
    """System of two equations: x^2 + y^2 - 4 = 0 and x - y = 0."""
    x, y = vec
    return np.array([x**2 + y**2 - 4, x - y])


# === Test Definitions ===
tests = [
    ("Single Root", f1, [0, 3], np.array([1.0])),
    ("Multiple Roots", f2, [0, 5], np.array([2.0, 3.0])),
    ("Repeated Root", f3, [0, 4], np.array([2.0])),
    ("Discontinuous", f4, [0, 10], np.array([0.0])),
    ("No Root (Bonus)", f5, [-3, 3], np.array([])),
    ("Multivariable System (Bonus)", f6, [[-3, 3], [-3, 3]],
     np.array([[np.sqrt(2), -np.sqrt(2)], [np.sqrt(2), -np.sqrt(2)]])),
]


# === Grading Parameters ===
TOL = 1e-2                 # numerical tolerance for correctness
POINT_SINGLE = 10          # max points per test
FALSE_ROOT_PENALTY = 2     # points deducted per false root


# === Run Tests ===
print("=== Root-Finding Project Evaluation ===")
results = []

for name, func, interval, expected in tests:
    print(f"\nFunction: {name}")
    f_wrapped = FunctionWithCounter(func)

    try:
        roots = solver_2446672(interval, f_wrapped)
        evals = f_wrapped.count

        print(f"Interval: {interval}")
        print(f"Expected roots: {expected}")
        print(f"Detected roots: {roots}")
        print(f"Function evaluations: {evals}")

        if isinstance(interval[0], (list, tuple, np.ndarray)):
            print(f"Output shape: {np.shape(roots)} (rows = variables, cols = solutions)")

        # === Grading ===
        score = 0

        # --- No-root case ---
        if expected.size == 0:
            if roots.size == 0:
                score = 10
            else:
                score = 0
                print("❌ False roots reported for a no-root case. Score = 0.")

        # --- Rooted 1D cases ---
        elif roots.ndim == 1:
            found = sum(np.any(np.isclose(r, expected, atol=TOL)) for r in roots)
            false_roots = [r for r in roots if not np.any(np.isclose(r, expected, atol=TOL))]

            score = 10 * found / max(len(expected), 1)

            if false_roots:
                penalty = FALSE_ROOT_PENALTY * len(false_roots)
                score = max(score - penalty, 0)
                print(f"❌ False roots detected: {false_roots} (−{penalty} pts)")

        # --- Multivariable (bonus) ---
        elif roots.ndim == 2:
            score = 10

        # --- Cap score to 10 ---
        score = min(score, 10)

        results.append((name, score, evals, roots))
        print(f"✅ Score: {score:.1f} / 10")

    except Exception as e:
        print(f"⚠️ Test failed: {e}")
        results.append((name, 0, 0, []))


# === Summary Table ===
print("\n=== Evaluation Summary ===")
total = 0
max_score = 0
print(f"{'Test Name':30} | {'Score':>6} | {'Calls':>6} | {'Expected':>15} | {'Detected':>15}")
print("-"*95)

for name, score, evals, roots in results:
    expected = [t[3] for t in tests if t[0] == name][0]
    total += score
    max_score += POINT_SINGLE
    print(f"{name:30} | {score:6.1f} | {evals:6d} | {str(expected):>15} | {str(roots):>15}")

print("-"*95)
print(f"Total Score: {total:.1f} / {max_score}")
print("=== Testing Complete ===")
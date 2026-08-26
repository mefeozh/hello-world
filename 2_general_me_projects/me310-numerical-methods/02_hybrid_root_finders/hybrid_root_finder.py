import numpy as np
import warnings

"""
ME310 - Numerical Methods for Engineering Homework 1
Name :Mehmet Efe
Surname :Özhan
ID :2446672
"""


def is_actual_root(f, x, tol=1e-2):

    try:
        fx = f(x)

        return abs(fx) < tol and abs(fx) < 1e10
    except Exception:

        return False


def Solver(f, a, b, tol=1e-2, max_iter=50):

    try:
        fa = f(a)
        fb = f(b)
        if fa * fb >= 0:
            if abs(fa) < tol: return a
            if abs(fb) < tol: return b
            return None
    except Exception:
        return None

    for i in range(max_iter):

        c = b - fb * (b - a) / (fb - fa)

        if not (a <= c <= b):
            c = (a + b) / 2.0

        try:
            fc = f(c)
        except Exception:

            return (a + b) / 2.0

        if abs(fc) < tol or abs(b - a) < tol:
            return c

        if fc * fa < 0:
            b, fb = c, fc
            fa *= 0.5
        else:
            a, fa = c, fc
            fb *= 0.5

    return (a + b) / 2.0


def _find_1d_roots(f, a, b, n_steps=200, tol=1e-2):

    found_roots = []
    x_points = np.linspace(a, b, n_steps + 1)

    y_points = np.zeros(n_steps + 1)
    for i in range(n_steps + 1):
        try:
            y_points[i] = f(x_points[i])
        except Exception:
            y_points[i] = np.nan

    for i in range(n_steps):
        y_curr = y_points[i]
        y_next = y_points[i + 1]

        if np.isnan(y_curr) or np.isnan(y_next):
            continue

        if y_curr * y_next <= 0:
            if abs(y_curr) > 1e10 or abs(y_next) > 1e10:
                continue
            root = Solver(f, x_points[i], x_points[i + 1], tol)
            if root is not None:
                if is_actual_root(f, root, tol):
                    found_roots.append(root)

    h = 1e-6
    def f_prime(x):
        try:
            return (f(x + h) - f(x - h)) / (2 * h)
        except Exception:
            return np.nan

    y_prime_points = np.zeros(n_steps + 1)
    for i in range(n_steps + 1):
        y_prime_points[i] = f_prime(x_points[i])

    for i in range(n_steps):
        y_p_curr = y_prime_points[i]
        y_p_next = y_prime_points[i + 1]

        if np.isnan(y_p_curr) or np.isnan(y_p_next):
            continue

        if y_p_curr * y_p_next <= 0:
            if abs(y_p_curr) > 1e10 or abs(y_p_next) > 1e10:
                continue

            extremum_tol = tol / 100.0
            extremum_x = Solver(f_prime, x_points[i], x_points[i + 1], extremum_tol)

            if extremum_x is not None:
                if is_actual_root(f, extremum_x, tol):
                    found_roots.append(extremum_x)


    if not found_roots:
        return np.array([])

    sorted_roots = np.sort(np.array(found_roots))
    unique_roots = [sorted_roots[0]]
    cleanup_tol = tol * 1.5

    for i in range(1, len(sorted_roots)):
        if abs(sorted_roots[i] - sorted_roots[i - 1]) > cleanup_tol:
            unique_roots.append(sorted_roots[i])

    return np.array(unique_roots)


def _trace_contour(function_f, f_index, x_interval, y_interval, n_steps):

    x_min, x_max = x_interval
    y_min, y_max = y_interval
    x_grid = np.linspace(x_min, x_max, n_steps)

    contour_points = []

    for x_i in x_grid:

        def f_y(y):

            point = np.array([x_i, y])
            try:
                return function_f(point)[f_index]
            except Exception:
                return np.nan

        y_roots = _find_1d_roots(f_y, y_min, y_max, n_steps=100, tol=1e-3)

        for y_r in y_roots:
            contour_points.append(np.array([x_i, y_r]))

    return np.array(contour_points)

def _cleanup_2d_roots(points, tol=1e-1):

    if len(points) == 0:
        return np.empty((2, 0)) # Return correct shape

    final_roots = []

    sorted_points = points[np.lexsort((points[:, 1], points[:, 0]))]

    current_cluster = [sorted_points[0]]

    for point in sorted_points[1:]:
        cluster_center = np.mean(current_cluster, axis=0)
        distance = np.linalg.norm(point - cluster_center)

        if distance < tol:

            current_cluster.append(point)
        else:

            final_roots.append(np.mean(current_cluster, axis=0))
            current_cluster = [point]


    final_roots.append(np.mean(current_cluster, axis=0))

    final_array = np.array(final_roots)


    return final_array.T


def _find_2d_roots(function_f, x_interval, n_steps=100, tol=1e-2):

    x_lims = x_interval[0]
    y_lims = x_interval[1]


    contour1 = _trace_contour(function_f, 0, x_lims, y_lims, n_steps)


    contour2 = _trace_contour(function_f, 1, x_lims, y_lims, n_steps)

    if contour1.size == 0 or contour2.size == 0:
        return np.empty((2, 0))


    potential_roots = []

    x_step = (x_lims[1] - x_lims[0]) / n_steps
    y_step = (y_lims[1] - y_lims[0]) / 100
    search_tol = max(x_step, y_step) * 2.0

    for p1 in contour1:
        for p2 in contour2:
            distance = np.linalg.norm(p1 - p2)
            if distance < search_tol:

                potential_roots.append((p1 + p2) / 2.0)

    if not potential_roots:
        return np.empty((2, 0))


    return _cleanup_2d_roots(np.array(potential_roots), tol=search_tol * 3)



def solver_2446672(x_interval, function_f):

    interval = np.array(x_interval)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)

        if interval.ndim == 1 and interval.shape == (2,):

            a, b = interval[0], interval[1]
            return _find_1d_roots(function_f, a, b, n_steps=200, tol=1e-2)

        elif interval.ndim == 2 and interval.shape[1] == 2:

            num_vars = interval.shape[0]
            if num_vars != 2:
                warnings.warn(f"{num_vars}-variable solver is not implemented.")
                return np.empty((num_vars, 0))

            return _find_2d_roots(function_f, interval, n_steps=100, tol=1e-2)

        else:
            raise ValueError("Invalid x_interval format.")
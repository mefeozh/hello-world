
import numpy as np
import matplotlib.pyplot as plt
import importlib
import sys

# ======================================================
# Load student module
# ======================================================

STUDENT_ID = "2446672"   # ← CHANGE THIS WHEN TESTING DIFFERENT STUDENTS
MODULE_NAME = f"student_{STUDENT_ID}"

try:
    student = importlib.import_module(MODULE_NAME)
    print(f"Loaded student file: {MODULE_NAME}.py")
except Exception as e:
    print(f"\n❌ Could not import {MODULE_NAME}.py")
    print(e)
    sys.exit(1)   # If there is no file at all, we really can't test this student


# Rover Simulator (Instructor-owned, hidden to students)
class Rover1DSimulatorRK4:
    def __init__(self,
                 mass_kg=5.0,
                 wheel_radius_m=0.15,
                 simulation_step_s=0.002,
                 friction_model="gravel",
                 accel_rate_hz=200.0,
                 accel_noise_std=0.1,
                 star_rate_hz=20.0,
                 star_noise_std=0.05,
                 velocity_deadband=1e-3):

        # Physical parameters
        self.m = mass_kg
        self.r = wheel_radius_m
        self.dt = simulation_step_s

        # State
        self.x = 0.0           # position [m]
        self.v = 0.0           # velocity [m/s]

        # Deadband to avoid chatter near zero velocity
        self.v_eps = velocity_deadband

        # Terrain friction parameters (a, b)
        if friction_model == "rock":
            self.params = {"a": 40.0, "b": 10.0}
        elif friction_model == "sand":
            self.params = {"a": 20.0, "b": 5.0}
        elif friction_model == "gravel":
            self.params = {"a": 30.0, "b": -1.0}
        else:
            # friction_model can also be a dict {"a":..., "b":...}
            self.params = friction_model

        # Accelerometer model
        self.accel_dt = 1.0 / accel_rate_hz
        self.accel_noise = accel_noise_std
        self._accel_timer = 0.0

        # Star tracker model (position sensor)
        self.star_dt = 1.0 / star_rate_hz
        self.star_noise = star_noise_std
        self._star_timer = 0.0

    def friction_force(self, v, F_drive):
        """
        Static + kinetic friction:
        - If |v| >= v_eps: kinetic -> F = a sign(v) + b v
        - If |v| <  v_eps: static; cancels drive up to |F_drive| <= a
        """
        a = self.params["a"]
        b = self.params["b"]
        # Kinetic friction (moving)
        if abs(v) >= self.v_eps:
            return a * np.sign(v) + b * v

        # Static friction (sticking)
        if abs(F_drive) <= a:
            return F_drive  # exactly cancels drive; no motion
        else:
            # Breakaway: saturate at +/- a
            return a * np.sign(F_drive)

    def dynamics(self, state_vector, motor_torque):
        x, v = state_vector

        F_drive = motor_torque / self.r
        a_static = self.params["a"]

        # STATIC friction rule ALWAYS checked first
        if abs(v) < self.v_eps and abs(F_drive) <= a_static:
            return np.array([0.0, 0.0]), F_drive, 0.0

        # Otherwise kinetic friction
        F_fric = self.params["a"] * np.sign(v) + self.params["b"] * v
        a = (F_drive - F_fric) / self.m

        return np.array([v, a]), F_fric, a

    def step(self, motor_torque):

        dt = self.dt
        state = np.array([self.x, self.v])
        F_drive = motor_torque / self.r
        a_static = self.params["a"]

        # ------------------------------------------------------
        # STATIC FRICTION COUNTER LOGIC
        # ------------------------------------------------------
        if not hasattr(self, "_static_counter"):
            self._static_counter = 0

        # Check if torque ≈ 0 and |v| small
        if abs(motor_torque) < 1e-6 and abs(self.v) < 0.01:
            self._static_counter += 1
        else:
            self._static_counter = 0

        force_static_override = self._static_counter > 10


        # ==================================================================
        # STATIC FRICTION BYPASS (Two cases):
        # (1) Normal static friction condition from friction law
        # (2) Forced static due to long-time near-zero velocity + zero torque
        # ==================================================================
        if (abs(self.v) < self.v_eps and abs(F_drive) <= a_static) or force_static_override:

            # Stick: no motion
            self.v = 0.0
            a_true = 0.0
            F_fric = F_drive

            # Accelerometer
            self._accel_timer += dt
            a_meas = None
            if self._accel_timer >= self.accel_dt:
                self._accel_timer = 0.0
                a_meas = a_true + self.accel_noise * np.random.randn()

            # Star tracker
            self._star_timer += dt
            x_meas = None
            if self._star_timer >= self.star_dt:
                self._star_timer = 0.0
                x_meas = self.x + self.star_noise * np.random.randn()

            return self.x, self.v, a_true, F_fric, a_meas, x_meas


        # ======================================================
        # KINETIC FRICTION — RUNGE–KUTTA 4
        # ======================================================
        k1, _, _ = self.dynamics(state, motor_torque)
        k2, _, _ = self.dynamics(state + 0.5 * dt * k1, motor_torque)
        k3, _, _ = self.dynamics(state + 0.5 * dt * k2, motor_torque)
        k4, _, _ = self.dynamics(state + dt * k3, motor_torque)

        state_next = state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
        self.x, self.v = state_next

        # Snap tiny velocities to zero
        if abs(self.v) < self.v_eps:
            self.v = 0.0

        # True friction & acceleration for sensors
        _, F_fric, a_true = self.dynamics(state, motor_torque)

        # Accelerometer
        self._accel_timer += dt
        a_meas = None
        if self._accel_timer >= self.accel_dt:
            self._accel_timer = 0.0
            a_meas = a_true + self.accel_noise * np.random.randn()

        # Star tracker
        self._star_timer += dt
        x_meas = None
        if self._star_timer >= self.star_dt:
            self._star_timer = 0.0
            x_meas = self.x + self.star_noise * np.random.randn()

        return self.x, self.v, a_true, F_fric, a_meas, x_meas
# ======================================================
# SIMULATION SETUP
# ======================================================

simulation_duration_s = 20.0
time_step_s = 0.002
time_vector = np.arange(0.0, simulation_duration_s, time_step_s)

simulator = Rover1DSimulatorRK4(friction_model="gravel")

# ======================================================
# 1) TORQUE PROFILE (STUDENT FUNCTION)
# ======================================================

try:
    motor_torque_profile = student.generate_torque_profile(time_vector)

    if not isinstance(motor_torque_profile, np.ndarray):
        print("\n❌ generate_torque_profile must return a NumPy array. Using zeros instead.")
        motor_torque_profile = np.zeros_like(time_vector)

    if motor_torque_profile.shape != time_vector.shape:
        print("\n❌ Wrong torque shape! Expected", time_vector.shape, "got", motor_torque_profile.shape)
        # Fallback: interpolate student torque over our time grid
        original_time = np.linspace(time_vector[0], time_vector[-1], len(motor_torque_profile))
        motor_torque_profile = np.interp(time_vector, original_time, motor_torque_profile)

except Exception as e:
    print("\n❌ Error in generate_torque_profile(time_vector):")
    print(e)
    motor_torque_profile = np.zeros_like(time_vector)


# ======================================================
# SIMULATE ROVER
# ======================================================

true_position = []
true_velocity = []
true_acceleration = []
true_friction = []

measured_acceleration = []
measured_accel_time = []

measured_position = []
measured_position_time = []

for current_time, current_torque in zip(time_vector, motor_torque_profile):
    x, v, a_true, F_true, a_meas, x_meas = simulator.step(current_torque)

    true_position.append(x)
    true_velocity.append(v)
    true_acceleration.append(a_true)
    true_friction.append(F_true)

    if a_meas is not None:
        measured_acceleration.append(a_meas)
        measured_accel_time.append(current_time)

    if x_meas is not None:
        measured_position.append(x_meas)
        measured_position_time.append(current_time)

true_position = np.array(true_position)
true_velocity = np.array(true_velocity)
true_acceleration = np.array(true_acceleration)
true_friction = np.array(true_friction)

measured_acceleration = np.array(measured_acceleration)
measured_accel_time = np.array(measured_accel_time)
measured_position = np.array(measured_position)
measured_position_time = np.array(measured_position_time)


# ======================================================
# 2) VELOCITY ESTIMATION (STUDENT FUNCTION)
# ======================================================

try:
    velocity_output = student.estimate_velocity(measured_accel_time,
                                               measured_acceleration,
                                               measured_position_time,
                                               measured_position)

    if not isinstance(velocity_output, tuple) or len(velocity_output) != 2:
        print("\n❌ estimate_velocity must return (velocity_estimate, velocity_time). Using fallback integrator.")
        velocity_estimate = np.cumsum(measured_acceleration) * np.mean(np.diff(measured_accel_time))
        velocity_time = measured_accel_time.copy()
    else:
        velocity_estimate, velocity_time = velocity_output

        if not isinstance(velocity_estimate, np.ndarray):
            print("\n❌ velocity_estimate must be a NumPy array. Using zeros.")
            velocity_estimate = np.zeros_like(measured_acceleration)

        if not isinstance(velocity_time, np.ndarray):
            print("\n❌ velocity_time must be a NumPy array. Using measured_accel_time.")
            velocity_time = measured_accel_time.copy()

        if len(velocity_estimate) != len(velocity_time):
            print("\n❌ Length mismatch between velocity_estimate and velocity_time. Trimming to min length.")
            min_len = min(len(velocity_estimate), len(velocity_time))
            velocity_estimate = velocity_estimate[:min_len]
            velocity_time = velocity_time[:min_len]

except Exception as e:
    print("\n❌ Error in estimate_velocity(measured_accel_time, measured_acceleration, measured_position_time, measured_position):")
    print(e)
    velocity_estimate = np.cumsum(measured_acceleration) * np.mean(np.diff(measured_accel_time))
    velocity_time = measured_accel_time.copy()


# ======================================================
# 3) FRICTION FORCE ESTIMATION (STUDENT FUNCTION)
# ======================================================

# Interpolate torque and acceleration to the velocity time grid
motor_torque_at_velocity_time = np.interp(velocity_time, time_vector, motor_torque_profile)
accel_at_velocity_time = np.interp(velocity_time, measured_accel_time, measured_acceleration)

try:
    friction_estimate = student.estimate_friction_force(motor_torque_at_velocity_time,
                                                        accel_at_velocity_time,
                                                        simulator.m,
                                                        simulator.r)

    if not isinstance(friction_estimate, np.ndarray):
        print("\n❌ estimate_friction_force must return a NumPy array. Using fallback model.")
        friction_estimate = motor_torque_at_velocity_time / simulator.r - simulator.m * accel_at_velocity_time

    if len(friction_estimate) != len(velocity_time):
        print("\n❌ friction_estimate length mismatch. Resizing.")
        friction_estimate = np.resize(friction_estimate, len(velocity_time))

except Exception as e:
    print("\n❌ Error in estimate_friction_force(motor_torque, acceleration, mass, wheel_radius):")
    print(e)
    friction_estimate = motor_torque_at_velocity_time / simulator.r - simulator.m * accel_at_velocity_time


# ======================================================
# 4) FIT FRICTION MODEL (STUDENT FUNCTION)
# ======================================================

try:
    friction_params_est = student.fit_friction_model(velocity_estimate, friction_estimate)

    if not isinstance(friction_params_est, (tuple, list)) or len(friction_params_est) != 2:
        print("\n❌ fit_friction_model must return (a, b). Using least-squares fallback.")
        Phi = np.column_stack([np.sign(velocity_estimate), velocity_estimate])
        theta, _, _, _ = np.linalg.lstsq(Phi, friction_estimate, rcond=None)
        a_hat, b_hat = theta
    else:
        a_hat, b_hat = friction_params_est

except Exception as e:
    print("\n❌ Error in fit_friction_model(velocity_estimate, friction_estimate):")
    print(e)
    Phi = np.column_stack([np.sign(velocity_estimate), velocity_estimate])
    theta, _, _, _ = np.linalg.lstsq(Phi, friction_estimate, rcond=None)
    a_hat, b_hat = theta


print("\n===============================")
print(" ESTIMATED FRICTION PARAMETERS ")
print("===============================")
print(f"Estimated a = {a_hat:.2f}, b = {b_hat:.2f}")
print(f"True      a = {simulator.params['a']:.2f}, b = {simulator.params['b']:.2f}")
print("================================\n")


# ======================================================
# Plotting (always produced, even if student fails inside)
# ======================================================

# 1) Torque
plt.figure(figsize=(8, 4))
plt.plot(time_vector, motor_torque_profile, linewidth=2)
plt.title("Motor Torque Profile")
plt.xlabel("Time [s]")
plt.ylabel("Torque [Nm]")
plt.grid(True)
plt.tight_layout()

# 2) State plots: position, velocity, acceleration
fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)

axes[0].plot(time_vector, true_position, label="True position")
axes[0].scatter(measured_position_time, measured_position, s=8, alpha=0.7, label="Star tracker")
axes[0].set_ylabel("Position [m]")
axes[0].set_title("Position over time")
axes[0].legend()
axes[0].grid(True)

axes[1].plot(time_vector, true_velocity, label="True velocity")
axes[1].plot(velocity_time, velocity_estimate, "--", label="Estimated velocity")
axes[1].set_ylabel("Velocity [m/s]")
axes[1].set_title("Velocity over time")
axes[1].legend()
axes[1].grid(True)

axes[2].plot(time_vector, true_acceleration, label="True acceleration")
axes[2].scatter(measured_accel_time, measured_acceleration, s=8, alpha=0.7, label="Accelerometer")
axes[2].set_ylabel("Acceleration [m/s²]")
axes[2].set_xlabel("Time [s]")
axes[2].set_title("Acceleration over time")
axes[2].legend()
axes[2].grid(True)

plt.tight_layout()

# 3) Friction over time
plt.figure(figsize=(8, 4))
plt.plot(time_vector, true_friction, label="True friction", linewidth=2)
plt.scatter(velocity_time, friction_estimate, s=10, alpha=0.5, label="Estimated friction")
plt.title("Friction force over time")
plt.xlabel("Time [s]")
plt.ylabel("Friction [N]")
plt.legend()
plt.grid(True)
plt.tight_layout()

# ================================
# 4) Friction–velocity relationship
# ================================
plt.figure(figsize=(7, 5))

# --------------------------
# Create a clipped velocity grid
# --------------------------
v_min, v_max = -10, 10
velocity_grid = np.linspace(v_min, v_max, 400)

true_friction_model = (
    simulator.params["a"] * np.sign(velocity_grid)
    + simulator.params["b"] * velocity_grid
)

fitted_friction_model = (
    a_hat * np.sign(velocity_grid)
    + b_hat * velocity_grid
)

# --------------------------
# Clip student samples
# --------------------------
mask_est = (velocity_estimate >= v_min) & (velocity_estimate <= v_max)
mask_true = (velocity_estimate >= v_min) & (velocity_estimate <= v_max)

plt.scatter(
    velocity_estimate[mask_est],
    friction_estimate[mask_est],
    s=15, alpha=0.4, label="Estimated samples"
)

# --------------------------
# Plot true and fitted models
# --------------------------
plt.plot(velocity_grid, true_friction_model, "k", linewidth=2, label="True model")
plt.plot(velocity_grid, fitted_friction_model, "r--", linewidth=2, label="Fitted model")

plt.xlabel("Velocity [m/s]")
plt.ylabel("Friction [N]")
plt.title("Friction–Velocity Curve (Clipped to -10…10 m/s)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()


import numpy as np
import importlib
import sys
from unittest.mock import patch

# Assume student file is in the same directory
STUDENT_ID = "2446672"
MODULE_NAME = f"student_{STUDENT_ID}"

try:
    student = importlib.import_module(MODULE_NAME)
except Exception as e:
    print(f"Error importing {MODULE_NAME}: {e}")
    sys.exit(1)

# Copied from lunar_rover_simulator.py
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

        if friction_model == "rock":
            self.params = {"a": 40.0, "b": 10.0}
        elif friction_model == "sand":
            self.params = {"a": 20.0, "b": 5.0}
        elif friction_model == "gravel":
            self.params = {"a": 30.0, "b": -1.0}
        else:
            self.params = friction_model

        self.accel_dt = 1.0 / accel_rate_hz
        self.accel_noise = accel_noise_std
        self._accel_timer = 0.0

        self.star_dt = 1.0 / star_rate_hz
        self.star_noise = star_noise_std
        self._star_timer = 0.0

    def dynamics(self, state_vector, motor_torque):
        x, v = state_vector
        F_drive = motor_torque / self.r
        a_static = self.params["a"]
        if abs(v) < self.v_eps and abs(F_drive) <= a_static:
            return np.array([0.0, 0.0]), F_drive, 0.0
        F_fric = self.params["a"] * np.sign(v) + self.params["b"] * v
        a = (F_drive - F_fric) / self.m
        return np.array([v, a]), F_fric, a

    def step(self, motor_torque):
        dt = self.dt
        state = np.array([self.x, self.v])
        F_drive = motor_torque / self.r
        a_static = self.params["a"]
        if not hasattr(self, "_static_counter"): self._static_counter = 0
        if abs(motor_torque) < 1e-6 and abs(self.v) < 0.01: self._static_counter += 1
        else: self._static_counter = 0
        force_static_override = self._static_counter > 10

        if (abs(self.v) < self.v_eps and abs(F_drive) <= a_static) or force_static_override:
            self.v = 0.0
            a_true = 0.0
            F_fric = F_drive
            self._accel_timer += dt
            a_meas = None
            if self._accel_timer >= self.accel_dt:
                self._accel_timer = 0.0
                a_meas = a_true + self.accel_noise * np.random.randn()
            self._star_timer += dt
            x_meas = None
            if self._star_timer >= self.star_dt:
                self._star_timer = 0.0
                x_meas = self.x + self.star_noise * np.random.randn()
            return self.x, self.v, a_true, F_fric, a_meas, x_meas

        k1, _, _ = self.dynamics(state, motor_torque)
        k2, _, _ = self.dynamics(state + 0.5 * dt * k1, motor_torque)
        k3, _, _ = self.dynamics(state + 0.5 * dt * k2, motor_torque)
        k4, _, _ = self.dynamics(state + dt * k3, motor_torque)
        state_next = state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
        self.x, self.v = state_next

        if abs(self.v) < self.v_eps: self.v = 0.0
        _, F_fric, a_true = self.dynamics(state, motor_torque)

        self._accel_timer += dt
        a_meas = None
        if self._accel_timer >= self.accel_dt:
            self._accel_timer = 0.0
            a_meas = a_true + self.accel_noise * np.random.randn()
        self._star_timer += dt
        x_meas = None
        if self._star_timer >= self.star_dt:
            self._star_timer = 0.0
            x_meas = self.x + self.star_noise * np.random.randn()
        return self.x, self.v, a_true, F_fric, a_meas, x_meas

def run_test(seed, surface_type="sand"):
    # Set the seed initially
    np.random.seed(seed)

    simulation_duration_s = 20.0
    time_step_s = 0.002
    time_vector = np.arange(0.0, simulation_duration_s, time_step_s)

    simulator = Rover1DSimulatorRK4(friction_model= surface_type)

    # MOCK the seed function so student call to seed(None) is ignored
    with patch('numpy.random.seed') as mock_seed:
        # 1. Generate Torque (Student)
        try:
            motor_torque_profile = student.generate_torque_profile(time_vector)
            if not isinstance(motor_torque_profile, np.ndarray) or motor_torque_profile.shape != time_vector.shape:
                 motor_torque_profile = np.zeros_like(time_vector)
        except Exception:
            motor_torque_profile = np.zeros_like(time_vector)

    # 2. Simulate
    measured_acceleration = []
    measured_accel_time = []
    measured_position = []
    measured_position_time = []
    true_velocity = []

    for current_time, current_torque in zip(time_vector, motor_torque_profile):
        x, v, a_true, F_true, a_meas, x_meas = simulator.step(current_torque)
        true_velocity.append(v)

        if a_meas is not None:
            measured_acceleration.append(a_meas)
            measured_accel_time.append(current_time)
        if x_meas is not None:
            measured_position.append(x_meas)
            measured_position_time.append(current_time)

    measured_acceleration = np.array(measured_acceleration)
    measured_accel_time = np.array(measured_accel_time)
    measured_position = np.array(measured_position)
    measured_position_time = np.array(measured_position_time)
    true_velocity = np.array(true_velocity)

    # 3. Estimate Velocity
    try:
        velocity_output = student.estimate_velocity(measured_accel_time,
                                                   measured_acceleration,
                                                   measured_position_time,
                                                   measured_position)
        velocity_estimate, velocity_time = velocity_output
    except Exception:
        velocity_estimate = np.zeros_like(measured_acceleration)
        velocity_time = measured_accel_time

    # 4. Estimate Friction
    motor_torque_at_vel = np.interp(velocity_time, time_vector, motor_torque_profile)
    accel_at_vel = np.interp(velocity_time, measured_accel_time, measured_acceleration)
    try:
        friction_estimate = student.estimate_friction_force(motor_torque_at_vel,
                                                            accel_at_vel,
                                                            simulator.m,
                                                            simulator.r)
    except Exception:
        friction_estimate = np.zeros_like(velocity_estimate)

    # 5. Fit Model
    try:
        a_hat, b_hat = student.fit_friction_model(velocity_estimate, friction_estimate)
    except Exception:
        a_hat, b_hat = 0.0, 0.0

    true_a = simulator.params["a"]
    true_b = simulator.params["b"]

    error_a = abs(a_hat - true_a) / abs(true_a) * 100
    error_b = abs(b_hat - true_b) / abs(true_b) * 100

    return seed, error_a, error_b, a_hat, b_hat



worst_seed = None
max_error = -1
for i in ["sand", "gravel", "rock"]:
    print(f"Surface: {i}")
    print(f"{'Seed':<5} | {'Error A (%)':<12} | {'Error B (%)':<12} | {'Est A':<8} | {'Est B':<8}")
    print("-" * 55)
    for j in range(10):
        seed = j * 100 + 20+ j
        s, ea, eb, ha, hb = run_test(seed, i)
        print(f"{s:<5} | {ea:<12.2f} | {eb:<12.2f} | {ha:<8.2f} | {hb:<8.2f}")

    avg_err = (ea + eb) / 2
    if avg_err > max_error:
        max_error = avg_err
        worst_seed = seed
    print("-" * 55)
    print(f"Worst seed seems to be: {worst_seed} with arg error {max_error:.2f}%")



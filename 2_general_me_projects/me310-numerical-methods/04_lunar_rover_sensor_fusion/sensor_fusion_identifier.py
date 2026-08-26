#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from scipy.signal import filtfilt
from scipy.optimize import lsq_linear

def generate_torque_profile(time):
    """
    INPUT:
        time : 1D numpy array of time stamps [s]
    OUTPUT:
        torque_profile : 1D numpy array, same shape as time

    STUDENT TODO:
        Generate a torque profile that excites the rover
        in forward and backward directions.

    DEFAULT:
        Returns all zeros (valid torque profile).
    """
    
    tau = np.zeros_like(time)
    n_samples = len(time)

    np.random.seed(None) 
    
    if n_samples > 1:
        dt = time[1] - time[0]
    else:
        dt = 0.002

    current_idx = 0
    while current_idx < n_samples:
        duration = np.random.uniform(1, 4)
        steps = int(duration / dt)
        if steps < 1: steps = 1
        
        # Safe levels for <10 m/s constraint
        levels = [7.0, -7.0, 8.0, -8.0, 9.0, -9.0, 10.0, -10.0, 11.0, -11.0, 0.0, 0.0] 
        level = np.random.choice(levels)
        
        
        end_idx = min(current_idx + steps, n_samples)
        tau[current_idx:end_idx] = level

        # Add noise little bit
        tau += np.random.normal(0.0, 0.05, size=tau.shape)
        current_idx = end_idx


    return tau

def estimate_velocity(time_accel, accel_meas, time_pos, pos_meas):
    """
    INPUTS:
        time_accel : timestamps of accelerometer [s]
        accel_meas : measured acceleration [m/s^2]
        time_pos   : timestamps of star tracker [s]
        pos_meas   : measured position [m]

    OUTPUTS:
        vel_est  : estimated velocity [m/s]
        time_vel : timestamps aligned with vel_est

    STUDENT TODO:
        Use integration or differentiation or fusion.

    DEFAULT:
        Returns zero velocity of correct size.
    """

    # Safe handling for empty input
    if len(time_accel) == 0:
        return np.array([]), np.array([])
    
    # 1. Integration (High freq, drift prone)
    dt_accel = np.diff(time_accel, prepend=time_accel[0])
    dt_accel[0] = dt_accel[1]
    
    # 2. Differentiation (Low freq, noise prone)
    if len(time_pos) > 1:
        vel_pos_sparse = np.gradient(pos_meas, time_pos)
        vel_pos_diff = np.interp(time_accel, time_pos, vel_pos_sparse)
    else:
        vel_pos_diff = np.zeros_like(time_accel)
    
    # --- FILTERING STEP 1: Median Filter on Diff Velocity ---
    def simple_median_filter(data, kernel_size=5):
        padded = np.pad(data, (kernel_size//2, kernel_size//2), mode='edge')
        strides = padded.strides + (padded.strides[-1],)
        shape = (data.shape[0], kernel_size)
        strided = np.lib.stride_tricks.as_strided(padded, shape=shape, strides=strides)
        return np.median(strided, axis=1)

    vel_pos_diff_clean = simple_median_filter(vel_pos_diff, kernel_size=9)


    alpha = 0.985
    vel_est = np.zeros_like(accel_meas)
    current_vel = 0.0
    
    for i in range(len(time_accel)):
        dt = dt_accel[i]
        
        # Predict with integration
        vel_pred = current_vel + accel_meas[i] * dt
        
        # Correct with filtered differentiation
        vel_est[i] = alpha * vel_pred + (1 - alpha) * vel_pos_diff_clean[i]
        current_vel = vel_est[i]
        
    return vel_est, time_accel



def estimate_friction_force(torque, acceleration, mass, wheel_radius):
    """
    INPUTS:
        torque      : 1D array of motor torque [Nm]
        acceleration: 1D array [m/s^2]
        mass        : rover mass [kg]
        wheel_radius: wheel radius [m]

    OUTPUT:
        friction_est : 1D array of estimated friction force [N]

    STUDENT TODO:
        Compute friction = F_drive - m*a

    DEFAULT:
        Returns zero friction with correct shape.
    """

    n = min(len(torque), len(acceleration))
    if n == 0:
        return np.array([])

    t = torque[:n]
    a = acceleration[:n]
    
    # Raw calculation
    F_drive = t / wheel_radius
    F_fric_raw = F_drive - mass * a
    
    # --- FILTERING STEP 2: Moving Average Filter ---

    window_size = 10 # 10 samples = 0.02s at 200Hz
    kernel = np.ones(window_size) / window_size

    #use scipy.signal.filtfilt to apply a filter to the signal

    F_fric_smooth = filtfilt(kernel, 1, F_fric_raw)
    
    return F_fric_smooth



def fit_friction_model(velocity, friction):
    """
    INPUTS:
        velocity : 1D array of velocities [m/s]
        friction : 1D array of friction values [N]

    OUTPUT:
        a_hat, b_hat : estimated model parameters

    STUDENT TODO:
        Fit model F = a sign(v) + b v

    DEFAULT:
        Returns (0.0, 0.0)
    """
    
    # 1. Basic Velocity Threshold
    v_thresh = 0.20
    mask = (np.abs(velocity) > v_thresh)
    
    v_fit = velocity[mask]
    f_fit = friction[mask]
    
    if len(v_fit) < 10:
        return 0.0, 0.0

    Phi = np.column_stack([np.sign(v_fit), v_fit])
    

    # Solver that ensures theta[0] (a) >= 0. b is unconstrained.
    # lsq_linear bound format: ([min_a, min_b], [max_a, max_b])
    res = lsq_linear(Phi, f_fit, bounds=([0.0, -np.inf], [np.inf, np.inf]))
    theta = res.x

    # --- FILTERING STEP 3: Outlier Removal ---
    # Remove points that deviate significantly (e.g. during torque steps)
    
    # Calculate residuals
    f_pred = Phi @ theta
    residuals = np.abs(f_fit - f_pred)
    
    # Z-score-like filter
    std_res = np.std(residuals)
    mean_res = np.mean(residuals)
    
    # Keep only data within N sigma (e.g., 2.0)
    inlier_mask = residuals < (mean_res + 2.0 * std_res)
    
    # Re-fit on inliers
    if np.sum(inlier_mask) > 10:
        Phi_robust = Phi[inlier_mask]
        f_robust = f_fit[inlier_mask]
        res_robust = lsq_linear(Phi_robust, f_robust, bounds=([0.0, -np.inf], [np.inf, np.inf]))
        theta_robust = res_robust.x
        return theta_robust[0], theta_robust[1]
    
    return theta[0], theta[1]

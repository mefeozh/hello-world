import numpy as np
import matplotlib.pyplot as plt
  
m1 = 30       # kg
m2 = 20       # kg
M1 = 10       # kg 
M2 = 15       # kg 
k1 = 4000     # N/m 
k2 = 5000     # N/m 
c1 = 110      # Ns/m
c2 = 70       # Ns/m
r1 = 0.3      # m
r2 = 0.5      # m

T = 40      # N 

J0 = (0.5 * M1 * r1**2) + (0.5 * M2 * r2**2)
J_eq = J0 + (m1 * r2**2) + (m2 * r1**2)
C_eq = (c1 * r2**2) + (c2 * r1**2)
K_eq = (k1 * r2**2) + (k2 * r1**2)

omega_n = np.sqrt(K_eq / J_eq)
print("omega:",omega_n)
zeta = C_eq / (2 * np.sqrt(J_eq * K_eq))
print("zeta:", zeta)
omega_d = omega_n * np.sqrt(1 - zeta**2)
print("omega_d",omega_d)

theta_0 = -(T * r1) / K_eq

t = np.linspace(0, 3, 1000)

amplitude_decay = np.exp(-zeta * omega_n * t)
oscillatory_part = np.cos(omega_d * t) + (zeta / np.sqrt(1 - zeta**2)) * np.sin(omega_d * t)
theta_t = theta_0 * amplitude_decay * oscillatory_part

plt.figure(figsize=(10, 6))
plt.plot(t, theta_t, color='b', linewidth=2, label=rf'$\theta(t)$ Response (T={T}N)')
plt.axhline(0, color='black', linestyle='--', linewidth=1)

plt.title('Angular Time Response of the Pulley System after Cutting the Rope', fontsize=14)
plt.xlabel('Time (seconds)', fontsize=12)
plt.ylabel(r'Angular Position $\theta$ (radians)', fontsize=12)
plt.grid(True, linestyle=':', alpha=0.7)
plt.legend(fontsize=12)
plt.tight_layout()

plt.show()


import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def create_plot():
    # Define maximum values for the axes
    T_max = 20
    K_max = 30
    
    # Create arrays of T and K values (avoid exact 0 or 30 to prevent division by zero in some boundary cases)
    T = np.linspace(0.01, T_max, 1000)
    K = np.linspace(0.01, K_max - 0.01, 1000)
    
    # Create a meshgrid for evaluating the condition over the 2D plane
    T_grid, K_grid = np.meshgrid(T, K)
    
    # Evaluate the feasible region conditions
    # T > 0, K > 0, K < 30 are covered by the grid limits
    with np.errstate(divide='ignore', invalid='ignore'):
        valid_region = T_grid > (36 / (30 - K_grid))
        
    plt.figure(figsize=(10, 8))
    
    # Plot the shaded feasible region
    plt.contourf(T_grid, K_grid, valid_region, levels=[0.5, 1], colors=['#ADD8E6'], alpha=0.6)
    
    # Plot the boundary line where T = 36 / (30 - K), rearranged as K = 30 - 36 / T
    # The minimum T where K > 0 is T = 36/30 = 1.2
    T_boundary = np.linspace(1.2 + 0.001, T_max, 1000)
    K_boundary = 30 - 36 / T_boundary
    
    plt.plot(T_boundary, K_boundary, 'r-', linewidth=2, label=r'Boundary: $T = \frac{36}{30 - K}$')
    
    # Formatting the plot
    plt.xlim(0, T_max)
    plt.ylim(0, K_max)
    plt.xlabel('T (Time/Value)', fontsize=12, fontweight='bold')
    plt.ylabel('K (Variable)', fontsize=12, fontweight='bold')
    plt.title('Feasible Region for K and T', fontsize=14)
    
    # Add grid
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Create a custom legend
    handles, labels = plt.gca().get_legend_handles_labels()
    feasible_patch = mpatches.Patch(color='#ADD8E6', alpha=0.6, label='Feasible Region:\n$T > 0, K > 0, K < 30$\n$T > 36 / (30 - K)$')
    handles.append(feasible_patch)
    labels.append(feasible_patch.get_label())
    
    plt.legend(handles=handles, labels=labels, loc='lower right', fontsize=10)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    create_plot()

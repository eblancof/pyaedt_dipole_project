import numpy as np
import re
import traceback

# Attempt to import matplotlib, handle if not installed
try:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: Matplotlib not found. Plotting functions will be disabled.")
    print("Install it with: pip install matplotlib")


def plot_s11(hfss, setup_name, sweep_name, show_plot=True, save_plot=False, filename="dipole_s11_plot.png", return_fig=False):
    """Retrieves S11 data and plots it using Matplotlib if available."""
    if not MATPLOTLIB_AVAILABLE:
        print("Skipping S11 plot: Matplotlib not available.")
        return None

    try:
        # Construct the full setup:sweep name
        setup_sweep_name = f"{setup_name} : {sweep_name}"

        # Get S11 data
        solution_data = hfss.post.get_solution_data(
            expressions="S(1,1)",
            setup_sweep_name=setup_sweep_name,
            variations=hfss.available_variations.nominal  # Get S11 for the nominal variation
        )

        if solution_data and solution_data.primary_sweep_values:
            frequencies_hz = solution_data.primary_sweep_values  # Frequencies in Hz
            s11_db = solution_data.data_db20()  # S11 in dB

            print("S11 data obtained.")

            plt.figure()
            # Convert frequency to GHz for the plot
            plt.plot([f / 1e9 for f in frequencies_hz], s11_db)
            plt.title('Dipole S11')
            plt.xlabel('Frequency (GHz)')
            plt.ylabel('S11 (dB)')
            plt.grid(True)
            plt.ylim(-30, 0)  # Adjust Y limit if necessary

            if save_plot:
                plt.savefig(filename)
                print(f"S11 plot saved as '{filename}'")
            # Return figure if requested
            if return_fig:
                fig = plt.gcf()
                plt.close()
                return solution_data, fig
            if show_plot:
                plt.show()  # Display the plot
            plt.close()  # Close the figure to free memory
            return solution_data  # Return data for potential further use
        else:
            print("Warning: No S11 data found or solution_data is empty.")
            return None

    except Exception as plot_err:
        print(f"Error retrieving or plotting S11 data: {plot_err}")
        traceback.print_exc()
        return None


# Helper function to parse angle strings like "-180deg" -> -180.0
def _parse_angle(angle_str):
    match = re.match(r"([-+]?\d*\.?\d+)", str(angle_str))
    if match:
        return float(match.group(1))
    else:
        raise ValueError(f"Could not parse angle: {angle_str}")


def plot_radiation_pattern_3d(hfss, freq_ghz, setup_name, show_plot=True, return_fig=False):
    """Retrieves far-field radiation data and plots a 3D pattern using Matplotlib if available."""
    if not MATPLOTLIB_AVAILABLE:
        print("Skipping 3D radiation plot: Matplotlib not available.")
        return None

    print("Attempting to retrieve and plot 3D radiation pattern...")
    try:
        # Define variations for far-field data retrieval
        variations = hfss.available_variations.nominal_values
        variations["Theta"] = ["All"]
        variations["Phi"] = ["All"]
        variations["Freq"] = [f"{freq_ghz}GHz"]  # Specify the frequency

        # Get GainTotal data
        solution_data = hfss.post.get_solution_data(
            "GainTotal",
            setup_sweep_name=hfss.nominal_adaptive,  # Use nominal adaptive solution
            variations=variations,
            primary_sweep_variable="Phi",  # Or Theta, depending on desired primary axis
            report_category="Far Fields",
            context="3D"  # Specify 3D context
        )

        if not solution_data or not solution_data.primary_sweep_values:
            print("Warning: No radiation data found or solution_data is empty.")
            return None

        print("Radiation data obtained. Processing for 3D plot...")

        # Extract angles and gain data
        try:
            phi_deg_str = solution_data.intrinsics['Phi']
            theta_deg_str = solution_data.intrinsics['Theta']
            phi_deg = np.array([_parse_angle(s) for s in phi_deg_str])
            theta_deg = np.array([_parse_angle(s) for s in theta_deg_str])
        except (KeyError, ValueError) as e:
            print(f"Error parsing angles from solution data: {e}")
            return None

        phi_rad = np.radians(phi_deg)
        theta_rad = np.radians(theta_deg)

        # Create meshgrid - IMPORTANT: Use indexing='ij' for correct matrix shape
        THETA, PHI = np.meshgrid(theta_rad, phi_rad, indexing='ij')

        # Initialize Gain matrix
        GAIN = np.full(THETA.shape, np.nan)

        # Access gain values (handle potential structure differences)
        gain_data_dict = getattr(
            solution_data, '_solutions_mag', {}).get('GainTotal')
        if not gain_data_dict:
            # Fallback: try accessing directly if _solutions_mag is not present/structured as expected
            if hasattr(solution_data, 'data_magnitude') and 'GainTotal' in solution_data.data_magnitude:
                # This structure might be simpler, need adaptation based on actual object
                print(
                    "Warning: Accessing gain data via fallback method. Structure might differ.")
                # TODO: Adapt data extraction based on the actual structure of solution_data.data_magnitude['GainTotal']
                # This part requires inspecting the actual object structure if the primary method fails.
                # For now, we'll assume it's not easily parseable in this fallback.
                print("Error: Could not reliably extract gain data using fallback.")
                return None
            else:
                print(
                    "Error: 'GainTotal' data not found in solution_data._solutions_mag or fallback.")
                return None

        # Populate GAIN matrix
        freq_target = freq_ghz  # Target frequency as float
        for key, gain_value in gain_data_dict.items():
            # Key format can vary, try to adapt (assuming tuple: (Freq_float, Phi_float, Theta_float))
            if isinstance(key, tuple) and len(key) == 3:
                current_freq_val, current_phi_val, current_theta_val = key

                if np.isclose(current_freq_val, freq_target):
                    # Find indices using isclose for float comparison
                    phi_idx_list = np.where(
                        np.isclose(phi_deg, current_phi_val))[0]
                    theta_idx_list = np.where(np.isclose(
                        theta_deg, current_theta_val))[0]

                    if len(phi_idx_list) > 0 and len(theta_idx_list) > 0:
                        phi_idx = phi_idx_list[0]
                        theta_idx = theta_idx_list[0]
                        # Indexing is [theta_idx, phi_idx] due to meshgrid indexing='ij'
                        GAIN[theta_idx, phi_idx] = gain_value
            # else:
                # print(f"Warning: Unexpected key format in gain data: {key}")

        if np.isnan(GAIN).all():
            print("Error: Gain matrix is empty or could not be populated.")
            return None

        # Handle potential NaNs remaining
        min_gain = np.nanmin(GAIN)
        GAIN = np.nan_to_num(
            GAIN, nan=min_gain if not np.isnan(min_gain) else 0.0)

        # Convert spherical (Gain as R) to Cartesian coordinates
        R = GAIN
        X = R * np.sin(THETA) * np.cos(PHI)
        Y = R * np.sin(THETA) * np.sin(PHI)
        Z = R * np.cos(THETA)

        # --- 3D Plotting ---
        fig = plt.figure(figsize=(9, 7))
        ax = fig.add_subplot(111, projection='3d')

        # Normalize gain for color mapping (avoid division by zero)
        gain_range = R.max() - R.min()
        norm_gain = (R - R.min()) / \
            gain_range if gain_range > 1e-9 else np.zeros_like(R)

        # Plot the 3D surface
        surf = ax.plot_surface(X, Y, Z, facecolors=plt.cm.viridis(norm_gain),
                               rstride=1, cstride=1, antialiased=True, shade=False)

        # Set axis limits
        max_range = np.max(np.abs(np.array([X, Y, Z]))) * 1.1
        max_range = max(max_range, 1.0)  # Ensure a minimum range
        ax.set_xlim([-max_range, max_range])
        ax.set_ylim([-max_range, max_range])
        ax.set_zlim([-max_range, max_range])

        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title(f'3D Radiation Pattern (GainTotal) @ {freq_ghz} GHz')

        # Add color bar
        m = plt.cm.ScalarMappable(cmap=plt.cm.viridis)
        m.set_array(R)
        fig.colorbar(m, ax=ax, shrink=0.6, aspect=10,
                     label='GainTotal (Linear)')

        ax.view_init(elev=30., azim=45)
        plt.tight_layout()

        # Return figure if requested
        if return_fig:
            fig = plt.gcf()
            plt.close()
            return solution_data, fig
        if show_plot:
            plt.show()
        plt.close()  # Close the figure
        return solution_data  # Return data

    except Exception as plot_3d_err:
        print(f"Unexpected error during 3D plot generation: {plot_3d_err}")
        traceback.print_exc()
        return None

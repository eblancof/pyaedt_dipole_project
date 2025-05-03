import re
import numpy as np
import plotly.graph_objs as go

# Helper function to parse angle strings like "-180deg" -> -180.0
def _parse_angle(angle_str):
    match = re.match(r"([-+]?\d*\.?\d+)", str(angle_str))
    if match:
        return float(match.group(1))
    else:
        raise ValueError(f"Could not parse angle: {angle_str}")
    
def interactive_s11(hfss, setup_name, sweep_name):
    """Generate an interactive line plot of S11 vs frequency using Plotly."""
    setup_sweep = f"{setup_name} : {sweep_name}"
    solution_data = hfss.post.get_solution_data(
        expressions="S(1,1)",
        setup_sweep_name=setup_sweep,
        variations=hfss.available_variations.nominal
    )
    if not solution_data or not solution_data.primary_sweep_values:
        return None
    freqs = solution_data.primary_sweep_values
    s11 = solution_data.data_db20()
    fig = go.Figure(data=go.Scatter(
        x=[f/1e9 for f in freqs],
        y=s11,
        mode='lines',
        name='S11'
    ))
    fig.update_layout(
        title='Dipole S11',
        xaxis_title='Frequency (GHz)',
        yaxis_title='S11 (dB)',
        template='plotly_white'
    )
    return fig

def interactive_3d_pattern(hfss, freq_ghz, setup_name):
    """Generate an interactive 3D radiation pattern using Plotly."""
    variations = hfss.available_variations.nominal_values
    variations["Theta"] = ["All"]
    variations["Phi"] = ["All"]
    variations["Freq"] = [f"{freq_ghz}GHz"]

    solution_data = hfss.post.get_solution_data(
        expressions="GainTotal",
        setup_sweep_name=hfss.nominal_adaptive,
        variations=variations,
        primary_sweep_variable="Phi",
        report_category="Far Fields",
        context="3D"
    )
    if not solution_data or not solution_data.primary_sweep_values:
        return None

    phi = np.array([_parse_angle(s) for s in solution_data.intrinsics.get('Phi', [])])
    theta = np.array([_parse_angle(s) for s in solution_data.intrinsics.get('Theta', [])])
    phi_rad = np.radians(phi)
    theta_rad = np.radians(theta)
    THETA, PHI = np.meshgrid(theta_rad, phi_rad, indexing='ij')

    GAIN = np.full(THETA.shape, np.nan)
    gain_data_dict = getattr(solution_data, '_solutions_mag', {}).get('GainTotal', {})
    for key, val in gain_data_dict.items():
        if isinstance(key, tuple) and len(key) == 3:
            f_val, phi_val, theta_val = key
            if np.isclose(f_val, freq_ghz):
                phi_idx = np.where(np.isclose(phi, phi_val))[0]
                th_idx = np.where(np.isclose(theta, theta_val))[0]
                if phi_idx.size and th_idx.size:
                    GAIN[th_idx[0], phi_idx[0]] = val
    if np.isnan(GAIN).all():
        return None
    GAIN = np.nan_to_num(GAIN, nan=np.nanmin(GAIN))

    R = GAIN
    X = R * np.sin(THETA) * np.cos(PHI)
    Y = R * np.sin(THETA) * np.sin(PHI)
    Z = R * np.cos(THETA)

    fig = go.Figure(data=go.Surface(
        x=X, y=Y, z=Z,
        surfacecolor=R,
        colorscale='Viridis'
    ))
    fig.update_layout(
        title=f'3D Radiation Pattern @ {freq_ghz} GHz',
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z'
        ),
        template='plotly_dark' # Use dark theme
    )
    return fig

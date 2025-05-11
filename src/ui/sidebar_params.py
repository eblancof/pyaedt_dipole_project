import streamlit as st

def dipole_sidebar_params(freq_ghz):
    default_arm_length = calculate_default_arm_length(freq_ghz)
    arm_length_mm = st.sidebar.number_input(
        "Dipole Arm Length (mm)",
        value=default_arm_length,
        min_value=0.1,
        step=0.1,
        format="%.2f",
        help=f"Defaults to lambda/4 ({default_arm_length:.2f} mm for {freq_ghz} GHz). Modify if needed."
    )
    return {"arm_length_mm": arm_length_mm}



def calculate_default_arm_length(freq_ghz):
    """Calculate default arm length based on frequency."""
    if freq_ghz <= 0:
        return 0.0
    lambda_mm = 300 / freq_ghz
    return lambda_mm / 4 # arm_length = half of half-wavelength
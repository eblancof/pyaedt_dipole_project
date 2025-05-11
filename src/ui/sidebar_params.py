import streamlit as st
from hfss_simulation.microstrip import get_microstrip_default_params

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

def microstrip_sidebar_params(freq_ghz):
    microstrip_params = get_microstrip_default_params(freq_ghz)
    substrate_height = st.sidebar.number_input(
        "Substrate Height (mm)",
        value=microstrip_params["substrate_height"],
        min_value=0.01,
        step=0.01,
        format="%.2f",
        help="Height of the substrate."
    )
    substrate_epsr = st.sidebar.number_input(
        "Substrate Relative Permittivity (εr)",
        value=microstrip_params["substrate_epsr"],
        min_value=1.0,
        step=0.01,
        format="%.2f",
        help="Relative permittivity of the substrate."
    )
    patch_length = st.sidebar.number_input(
        "Patch Length (mm)",
        value=microstrip_params["patch_length"],
        min_value=0.01,
        step=0.01,
        format="%.2f",
        help="Length of the microstrip patch."
    )
    patch_width = st.sidebar.number_input(
        "Patch Width (mm)",
        value=microstrip_params["patch_width"],
        min_value=0.01,
        step=0.01,
        format="%.2f",
        help="Width of the microstrip patch."
    )
    return {
        "substrate_height": substrate_height,
        "substrate_epsr": substrate_epsr,
        "patch_length": patch_length,
        "patch_width": patch_width
    }

def calculate_default_arm_length(freq_ghz):
    """Calculate default arm length based on frequency."""
    if freq_ghz <= 0:
        return 0.0
    lambda_mm = 300 / freq_ghz
    return lambda_mm / 4 # arm_length = half of half-wavelength
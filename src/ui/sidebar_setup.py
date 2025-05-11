import streamlit as st
from constants import DEFAULT_AEDT_VERSION, DEFAULT_PROJECT_NAME, DEFAULT_DESIGN_NAME, DEFAULT_FREQ_GHZ
from ui.sidebar_params import dipole_sidebar_params, microstrip_sidebar_params

def render_sidebar_setup():
    st.sidebar.title("Simulation Setup")
    antenna_type = st.sidebar.selectbox("Antenna Type", ("Dipole", "Microstrip"), index=0)
    connection_mode = st.sidebar.radio("Connection Mode", ("Local", "gRPC"), index=0)
    MACHINE_ADDRESS = None
    GRPC_PORT = None
    if connection_mode == "gRPC":
        MACHINE_ADDRESS = st.sidebar.text_input("gRPC Machine Address", "localhost")
        GRPC_PORT = st.sidebar.number_input("gRPC Port", value=50001, step=1)
    st.sidebar.info(f"AEDT Version: {DEFAULT_AEDT_VERSION}")
    use_student = st.sidebar.checkbox("Use Student Version", True)
    st.sidebar.info(f"Using Student Version: {use_student}")
    non_graphical = st.sidebar.checkbox("Non-graphical Mode", False)
    st.sidebar.subheader("Geometry & Frequency")
    if antenna_type == "Dipole":
        default_project_name = DEFAULT_PROJECT_NAME
        default_design_name = DEFAULT_DESIGN_NAME
    elif antenna_type == "Microstrip":
        default_project_name = "MicrostripSimulation"
        default_design_name = "HFSS_Microstrip"
    else:
        default_project_name = DEFAULT_PROJECT_NAME
        default_design_name = DEFAULT_DESIGN_NAME
    project_name = st.sidebar.text_input("Project Name", default_project_name)
    design_name = st.sidebar.text_input("Design Name", default_design_name)
    freq_ghz = st.sidebar.number_input("Design Frequency (GHz)", value=DEFAULT_FREQ_GHZ, min_value=0.1, step=0.1, format="%.2f")
    dipole_params = None
    microstrip_params = None
    if antenna_type == "Dipole":
        dipole_params = dipole_sidebar_params(freq_ghz)
    elif antenna_type == "Microstrip":
        microstrip_params = microstrip_sidebar_params(freq_ghz)
    return {
        "antenna_type": antenna_type,
        "connection_mode": connection_mode,
        "MACHINE_ADDRESS": MACHINE_ADDRESS,
        "GRPC_PORT": GRPC_PORT,
        "use_student": use_student,
        "non_graphical": non_graphical,
        "project_name": project_name,
        "design_name": design_name,
        "freq_ghz": freq_ghz,
        "dipole_params": dipole_params,
        "microstrip_params": microstrip_params
    }

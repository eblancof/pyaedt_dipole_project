import streamlit as st
import os
import sys
# Add src directory to Python path to allow imports
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')
if src_dir not in sys.path:
    sys.path.append(src_dir)
    
from aedt_utils.connection import launch_aedt, initialize_hfss, release_aedt
from hfss_simulation.geometry import define_parameters, create_dipole_geometry
from hfss_simulation.boundaries import create_radiation_boundary
from hfss_simulation.excitations import create_lumped_port
from hfss_simulation.analysis import setup_analysis, setup_frequency_sweep, run_analysis
from plotting.plot_utils import plot_s11, plot_radiation_pattern_3d

# Sidebar inputs
aedt_version = st.sidebar.text_input("AEDT Version", "2024.2")
non_graphical = st.sidebar.checkbox("Non-graphical Mode", False)
use_student = st.sidebar.checkbox("Student Version", True)
project_name = st.sidebar.text_input("Project Name", "DipoleSimulation")
design_name = st.sidebar.text_input("Design Name", "HFSS_Dipole")
solution_type = st.sidebar.selectbox("Solution Type", ["Terminal", "Modal"], index=0)
freq_ghz = st.sidebar.number_input("Design Frequency (GHz)", value=1.0, step=0.1)

# Initialize AEDT
if 'desktop' not in st.session_state:
    if st.sidebar.button("Initialize AEDT"):
        try:
            desktop = launch_aedt(aedt_version, non_graphical, new_session=True, use_student_version=use_student)
            hfss = initialize_hfss(desktop, project_name, design_name, solution_type, aedt_version)
            st.session_state.desktop = desktop
            st.session_state.hfss = hfss
            st.success("AEDT and HFSS initialized.")
        except Exception as e:
            st.error(f"Initialization failed: {e}")
else:
    st.sidebar.success("AEDT initialized")

# Simulation
if 'hfss' in st.session_state:
    if st.button("Simulate"):
        try:
            params = define_parameters(freq_ghz)
            refs = create_dipole_geometry(st.session_state.hfss, params)
            create_radiation_boundary(st.session_state.hfss, params['freq_ghz'], params['offset'])
            port = create_lumped_port(st.session_state.hfss, refs['port_sheet'], refs['arm1'].name, impedance=50)
            setup_name = setup_analysis(st.session_state.hfss, params['freq_ghz'], setup_name="DipoleSetup")
            sweep_name = setup_frequency_sweep(st.session_state.hfss, setup_name, params['freq_ghz'], sweep_name="DipoleSweep", point_count=101)
            run_analysis(st.session_state.hfss, setup_name)

            # Post-processing and plots
            data_s11, fig_s11 = plot_s11(st.session_state.hfss, setup_name, sweep_name, show_plot=False, return_fig=True)
            if fig_s11:
                st.pyplot(fig_s11)
            data_3d, fig_3d = plot_radiation_pattern_3d(st.session_state.hfss, params['freq_ghz'], setup_name, show_plot=False, return_fig=True)
            if fig_3d:
                st.pyplot(fig_3d)

            st.success("Simulation and plotting completed.")
        except Exception as e:
            st.error(f"Simulation failed: {e}")

# Cleanup
if 'desktop' in st.session_state:
    if st.sidebar.button("Release AEDT"):
        try:
            release_aedt(st.session_state.desktop, project_name=project_name, save_project=True, project_path=f"{project_name}.aedt")
            st.session_state.clear()
            st.success("AEDT session released.")
        except Exception as e:
            st.error(f"Release failed: {e}")

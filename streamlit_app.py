import streamlit as st
import os
import sys
import time # For potential delays if needed, or just structure
import numpy as np # For default calculation

# --- Page Configuration (Set Layout to Wide) ---
st.set_page_config(layout="wide")

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
from plotting.plotly_utils import interactive_s11, interactive_3d_pattern

# --- Constants ---
DEFAULT_AEDT_VERSION = "2024.2"
DEFAULT_PROJECT_NAME = "DipoleSimulation"
DEFAULT_DESIGN_NAME = "HFSS_Dipole"
DEFAULT_FREQ_GHZ = 1.0
SOLUTION_TYPE = "Terminal" # Hardcoded as per request
MACHINE_ADDRESS = None
GRPC_PORT = None

# --- Helper Functions ---
def calculate_default_arm_length(freq_ghz):
    """Calculate default arm length based on frequency."""
    if freq_ghz <= 0:
        return 0.0
    lambda_mm = 300 / freq_ghz
    return lambda_mm / 4 # arm_length = half of half-wavelength

# --- Sidebar ---
st.sidebar.title("Simulation Setup")

# Connection mode selection
connection_mode = st.sidebar.radio("Connection Mode", ("Local", "gRPC"), index=0)
if connection_mode == "gRPC":
    MACHINE_ADDRESS = st.sidebar.text_input("gRPC Machine Address", "localhost")
    GRPC_PORT = st.sidebar.number_input("gRPC Port", value=50001, step=1)

# Non-modifiable info
st.sidebar.info(f"AEDT Version: {DEFAULT_AEDT_VERSION}")
use_student = st.sidebar.checkbox("Use Student Version", True) # Keep checkbox for toggle, but display info
st.sidebar.info(f"Using Student Version: {use_student}")
non_graphical = st.sidebar.checkbox("Non-graphical Mode", False)

# Modifiable parameters
st.sidebar.subheader("Geometry & Frequency")
project_name = st.sidebar.text_input("Project Name", DEFAULT_PROJECT_NAME)
design_name = st.sidebar.text_input("Design Name", DEFAULT_DESIGN_NAME)
freq_ghz = st.sidebar.number_input("Design Frequency (GHz)", value=DEFAULT_FREQ_GHZ, min_value=0.1, step=0.1, format="%.2f")

# Calculate default arm length based on current frequency
default_arm_length = calculate_default_arm_length(freq_ghz)
# Allow user override for arm length
arm_length_mm = st.sidebar.number_input(
    "Dipole Arm Length (mm)",
    value=default_arm_length,
    min_value=0.1,
    step=0.1,
    format="%.2f",
    help=f"Defaults to lambda/4 ({default_arm_length:.2f} mm for {freq_ghz} GHz). Modify if needed."
)


# --- Main App Area ---
st.title("PyAEDT Dipole Simulator")

# State tracking flags
aedt_initialized = 'desktop' in st.session_state
parameters_loaded = 'hfss' in st.session_state and 'setup_name' in st.session_state

# --- Step 1: Initialize AEDT ---
if not aedt_initialized:
    if st.sidebar.button("1. Initialize AEDT"):
        with st.spinner("Initializing AEDT... Please wait."):
            try:
                
                desktop = launch_aedt(DEFAULT_AEDT_VERSION, non_graphical, new_session=True, use_student_version=use_student, grpc_address=MACHINE_ADDRESS, grpc_port=GRPC_PORT)
                st.session_state.desktop = desktop
                hfss = initialize_hfss(desktop, project_name, design_name, SOLUTION_TYPE, DEFAULT_AEDT_VERSION)
              
                # Store in session state
                st.session_state.hfss = hfss
                st.session_state.connection_mode = connection_mode
                st.session_state.project_name = project_name
                st.session_state.design_name = design_name
                st.success("AEDT initialized successfully.")
                st.rerun() # Rerun to update UI state
            except Exception as e:
                st.error("Cannot connect to AEDT. Please check your settings or local installation.")
                if 'desktop' in st.session_state: del st.session_state.desktop
else:
    st.sidebar.success(f"✅ 1. AEDT Initialized ({st.session_state.get('project_name', 'Unknown Project')})")

# --- Step 2: Load Parameters & Create Design ---
if aedt_initialized:
    load_button_text = "2. Load Parameters & Create Design"
    if parameters_loaded:
        load_button_text = "🔄 Reload Parameters & Recreate Design"
    with st.sidebar.popover("Analysis & Sweep Options"):
        max_passes = st.slider("Max Passes (Analysis)", min_value=1, max_value=20, value=10, step=1, help="Maximum number of adaptive passes for the solver.")
        min_converged_passes = st.slider("Min Converged Passes", min_value=1, max_value=5, value=2, step=1, help="Minimum number of consecutive passes that must converge.")
        start_freq_factor = st.slider("Sweep Start Factor", min_value=0.1, max_value=0.9, value=0.5, step=0.05, help="Sweep start frequency = Design Frequency * Factor")
        stop_freq_factor = st.slider("Sweep Stop Factor", min_value=1.1, max_value=3.0, value=1.5, step=0.05, help="Sweep stop frequency = Design Frequency * Factor")
        point_count = st.number_input("Sweep Points", min_value=11, max_value=1001, value=101, step=10, help="Number of frequency points in the sweep.")
    if st.sidebar.button(load_button_text):
        with st.spinner("Loading parameters and creating/recreating design..."):
            status_placeholders = {
                'delete': st.empty(),
                'init_hfss': st.empty(),
                'params': st.empty(),
                'geometry': st.empty(),
                'boundaries': st.empty(),
                'excitations': st.empty(),
                'analysis_setup': st.empty(),
            }
            try:
                # Get desktop and current names from session state
                desktop = st.session_state.desktop
                current_project_name = st.session_state.project_name
                current_design_name = st.session_state.design_name

                # --- Deletion if reloading ---
                if parameters_loaded:
                    status_placeholders['delete'].info("   Deleting existing setup and design...")
                    try:
                        hfss_existing = st.session_state.hfss
                        setup_existing = st.session_state.setup_name
                        # Delete setup first
                        if hfss_existing.solution_type: # Check if hfss object is valid
                            hfss_existing.delete_setup(setup_existing)
                            status_placeholders['delete'].info(f"   Deleted setup: {setup_existing}")
                        else:
                             status_placeholders['delete'].warning("   Could not get valid HFSS object to delete setup.")
                        # Delete design
                        hfss_existing.delete_design(current_design_name)
                        # Close before deleting project to avoid errors
                        hfss_existing.close_project()
                        hfss_existing.delete_project(current_project_name)
                        status_placeholders['delete'].info(f"   Deleted design and project: {current_design_name}")

                        # Clear old state
                        keys_to_clear = ['hfss', 'params', 'refs', 'setup_name', 'sweep_name']
                        for key in keys_to_clear:
                            if key in st.session_state:
                                del st.session_state[key]
                        parameters_loaded = False # Reset flag
                        status_placeholders['delete'].success("   Cleanup complete.")
                        time.sleep(1)
                    except Exception as del_e:
                        status_placeholders['delete'].error(f"   Error during cleanup: {del_e}")
                        # Continue trying to create the new design anyway
                    finally:
                         status_placeholders['delete'].empty()


                # --- Initialization and Creation ---
                status_placeholders['init_hfss'].info("   Initializing HFSS project...")
                st.session_state.project_name = project_name
                st.session_state.design_name = design_name
                # Conditional HFSS init for reload
                if st.session_state.connection_mode == "Local":
                    hfss = initialize_hfss(desktop, project_name, design_name, SOLUTION_TYPE, DEFAULT_AEDT_VERSION)
                else:
                    hfss = st.session_state.hfss
                st.session_state.hfss = hfss
                status_placeholders['init_hfss'].empty()
            

                status_placeholders['params'].info("   Defining Parameters...")
                params = define_parameters(freq_ghz, arm_length_override_mm=arm_length_mm)
                st.session_state.params = params
                status_placeholders['params'].empty()

                status_placeholders['geometry'].info("   Creating Geometry...")
                refs = create_dipole_geometry(hfss, params)
                st.session_state.refs = refs
                status_placeholders['geometry'].empty()

                status_placeholders['boundaries'].info("   Creating Boundaries...")
                create_radiation_boundary(hfss, params['freq_ghz'], params['offset'])
                status_placeholders['boundaries'].empty()

                status_placeholders['excitations'].info("   Creating Excitations...")
                port = create_lumped_port(hfss, refs['port_sheet'], refs['arm1'].name, impedance=50)
                status_placeholders['excitations'].empty()

                status_placeholders['analysis_setup'].info("   Setting up Analysis...")
                # Use values from sidebar
                setup_name = setup_analysis(
                    hfss, params['freq_ghz'], setup_name="DipoleSetup",
                    max_passes=max_passes, min_converged_passes=min_converged_passes
                )
                # Use values from sidebar
                sweep_name = setup_frequency_sweep(
                    hfss, setup_name, params['freq_ghz'], sweep_name="DipoleSweep",
                    start_freq_factor=start_freq_factor, stop_freq_factor=stop_freq_factor,
                    point_count=point_count
                )
                st.session_state.setup_name = setup_name
                st.session_state.sweep_name = sweep_name
                # Store analysis/sweep params used
                st.session_state.analysis_params = {
                    'max_passes': max_passes,
                    'min_converged_passes': min_converged_passes,
                    'start_freq_factor': start_freq_factor,
                    'stop_freq_factor': stop_freq_factor,
                    'point_count': point_count
                }
                status_placeholders['analysis_setup'].empty()

                st.success("Parameters loaded and design created/updated.")
                st.rerun()

            except Exception as e:
                for placeholder in status_placeholders.values():
                    placeholder.empty()
                st.error(f"Failed to load parameters/create design: {e}")
                import traceback
                st.error(traceback.format_exc())
                # Attempt to clean up potentially inconsistent state
                keys_to_clear = ['hfss', 'params', 'refs', 'setup_name', 'sweep_name']
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]

    elif parameters_loaded:
         st.sidebar.success(f"✅ 2. Parameters Loaded ({st.session_state.design_name})")
    


# --- Step 3: Run Simulation ---
# Simulation Button (conditionally displayed)
if parameters_loaded: 
    # Use columns to control button width/centering
    _, col2, _ = st.columns([1, 3, 1]) # Adjust ratios as needed
    with col2:
        if st.button("▶️ 3. Run Simulation", key="simulate_button", help="Run the analysis and plot results.", use_container_width=True):
            # Use spinner for loading indication during simulation AND plotting
            with st.spinner("Running Simulation & Generating Plots... This may take a while."):
                # Placeholders for status messages
                status_placeholders = {
                    'analysis_run': st.empty(),
                    'plots': st.empty()
                }
                try:
                    # Retrieve necessary info from session state
                    hfss = st.session_state.hfss
                    setup_name = st.session_state.setup_name
                    sweep_name = st.session_state.sweep_name
                    params = st.session_state.params # Needed for plotting freq

                    # 1. Running Analysis
                    status_placeholders['analysis_run'].info("   Running Analysis...")
                    run_analysis(hfss, setup_name)
                    status_placeholders['analysis_run'].success("   Analysis complete.") # Use success briefly
                    time.sleep(1) # Keep success message briefly
                    status_placeholders['analysis_run'].empty()

                    # 2. Generating Plots
                    status_placeholders['plots'].info("   Generating Plots...")
                    # Interactive S11 plot
                    fig_s11 = interactive_s11(hfss, setup_name, sweep_name)
                    if fig_s11:
                        st.plotly_chart(fig_s11, use_container_width=True)
                    else:
                        st.warning("Could not generate S11 plot.")

                    # Interactive 3D radiation pattern
                    fig_3d = interactive_3d_pattern(hfss, params['freq_ghz'], setup_name)
                    if fig_3d:
                        st.plotly_chart(fig_3d, use_container_width=True)
                    else:
                        st.warning("Could not generate 3D radiation pattern.")
                    status_placeholders['plots'].empty()

                    st.success("Simulation run completed successfully!")

                except Exception as e:
                    # Clear any remaining status messages on error
                    for placeholder in status_placeholders.values():
                        placeholder.empty()
                    st.error(f"Simulation run failed: {e}")
                    import traceback
                    st.error(traceback.format_exc()) # Show detailed error in app

# --- Step 4: Cleanup ---
# Cleanup Button (conditionally displayed)
if aedt_initialized: # Show if AEDT was ever initialized
    if st.sidebar.button("4. Release AEDT Session", key="release_button"):
        with st.spinner("Releasing AEDT..."):
            try:
                # Use the project name stored when initialized or last loaded
                current_project_name = st.session_state.get('project_name', project_name) # Fallback just in case
                project_save_path = os.path.join(os.getcwd(), f"{current_project_name}.aedt")
                release_aedt(st.session_state.desktop, project_name=current_project_name, save_project=True, project_path=project_save_path)
                # Clear ALL relevant session state keys
                keys_to_clear = ['desktop', 'hfss', 'project_name', 'design_name', 'params', 'refs', 'setup_name', 'sweep_name', 'analysis_params']
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("AEDT session released and project saved.")
                st.rerun() # Rerun to update UI
            except Exception as e:
                st.error(f"AEDT Release failed: {e}")
                # Attempt to clear state anyway
                keys_to_clear = ['desktop', 'hfss', 'project_name', 'design_name', 'params', 'refs', 'setup_name', 'sweep_name', 'analysis_params']
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()


# Add some instructions or info at the bottom
st.sidebar.markdown("---")
st.sidebar.markdown("**Workflow:**")
st.sidebar.markdown("1. **Initialize AEDT:** Connects to the software.")
st.sidebar.markdown("2. **Load Parameters:** Creates/Recreates the HFSS design based on sidebar values.")
st.sidebar.markdown("3. **Run Simulation:** Executes the analysis and shows plots.")
st.sidebar.markdown("4. **Release AEDT:** Saves project and closes connection.")

# PyAEDT Dipole Simulation Project

This project simulates a simple dipole antenna using Ansys Electronics Desktop (AEDT) controlled via the PyAEDT library.

## Structure

- `main.py`: Main script to run the simulation workflow.
- `requirements.txt`: Python dependencies.
- `Dockerfile`: Basic Docker configuration (Note: Running AEDT in Docker requires specific setup).
- `src/`: Source code directory.
  - `aedt_utils/`: Utilities for AEDT connection.
    - `connection.py`: Handles Desktop initialization and release.
  - `hfss_simulation/`: Modules for setting up the HFSS simulation.
    - `geometry.py`: Defines parameters and creates the dipole geometry.
    - `boundaries.py`: Creates boundary conditions.
    - `excitations.py`: Creates the port excitation.
    - `analysis.py`: Configures and runs the simulation setup and sweep.
  - `plotting/`: Utilities for post-processing and plotting results.
    - `plot_utils.py`: Functions to plot S11 and radiation patterns.

## How to Run

1. Ensure you have Ansys Electronics Desktop installed.
2. Install required Python packages: `pip install -r requirements.txt`
3. Configure parameters in `main.py` if needed (AEDT version, project name, etc.).
4. Run the main script: `python main.py`

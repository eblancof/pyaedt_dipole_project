def setup_analysis(hfss, freq_ghz, setup_name="DefaultSetup", max_passes=10, min_converged_passes=2):
    """Configures the HFSS analysis setup."""
    try:
        hfss.create_setup(name=setup_name,
                                  setup_type="HFSSDriven",  # Standard solution type
                                  Frequency=f"{freq_ghz}GHz",
                                  MaximumPasses=max_passes,
                                  MinimumConvergedPasses=min_converged_passes)
        print(f"Analysis setup '{setup_name}' created.")
        return setup_name  # Return the name for reference
    except Exception as e:
        print(f"Error creating analysis setup: {e}")
        raise


def setup_frequency_sweep(hfss, setup_name, freq_ghz, sweep_name="DefaultSweep",
                          start_freq_factor=0.5, stop_freq_factor=1.5, point_count=101,
                          sweep_type="Interpolating"):
    """Configures the frequency sweep."""
    try:
        hfss.create_linear_count_sweep(setup=setup_name,
                                               units="GHz",
                                               name=sweep_name,
                                               start_frequency=freq_ghz * start_freq_factor,
                                               stop_frequency=freq_ghz * stop_freq_factor,
                                               num_of_freq_points=point_count,
                                               sweep_type=sweep_type)
        print(f"Frequency sweep '{sweep_name}' created.")
        return sweep_name  # Return the name for reference
    except Exception as e:
        print(f"Error creating frequency sweep: {e}")
        raise


def run_analysis(hfss, setup_name):
    """Runs the HFSS analysis for the specified setup."""
    print(f"Starting analysis for setup '{setup_name}'...")
    try:
        hfss.analyze_setup(setup_name)
        print("Analysis completed.")
    except Exception as e:
        print(f"Error during analysis: {e}")
        raise

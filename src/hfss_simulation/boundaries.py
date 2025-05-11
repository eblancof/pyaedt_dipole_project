def create_radiation_boundary(hfss, freq_ghz, offset):
    """Creates an open region (air box) with a radiation boundary."""
    # The size should be at least lambda/4 from any part of the antenna
    # The offset parameter is assumed to be lambda/4
    try:
        hfss.create_open_region(frequency=f"{freq_ghz}GHz",
                                boundary="Radiation",
                                # Adjust size if needed via offset argument if available or manual box creation
                                apply_infinite_ground=False)
        print("Radiation boundary condition created.")
    except Exception as e:
        print(f"Error creating radiation boundary: {e}")
        raise

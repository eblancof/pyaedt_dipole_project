def create_lumped_port(hfss, port_sheet, reference_object_name, impedance=50):
    """Creates a lumped port excitation on the specified sheet."""
    try:
        lumped_port = hfss.lumped_port(
            assignment=port_sheet,
            reference=reference_object_name,  # Reference to one of the dipole arms
            create_port_sheet=False,       # Sheet already exists
            impedance=impedance,           # Typical 50 Ohm impedance
            name="Dipole_LumpedPort",    # Port name
            renormalize=True,              # Renormalize waveform
            deembed=0,                     # No de-embedding
            terminals_rename=True          # Automatically rename terminals
        )
        print("Lumped port created.")
        return lumped_port
    except Exception as e:
        print(f"Error creating lumped port: {e}")
        raise

import math


def define_parameters(freq_ghz=1.0, arm_length_override_mm=None):
    """Defines the physical parameters based on the design frequency."""
    lambda_mm = 300 / freq_ghz  # Approx wavelength in mm
    dipole_total_length = lambda_mm / 2
    # Use override if provided, otherwise calculate default
    arm_length = arm_length_override_mm if arm_length_override_mm is not None else dipole_total_length / 2
    wire_radius = lambda_mm / 100
    gap = lambda_mm / 50
    offset = lambda_mm / 4  # For radiation boundary

    params = {
        "freq_ghz": freq_ghz,
        "lambda_mm": lambda_mm,
        "dipole_total_length": dipole_total_length, # Keep original calculation for reference if needed
        "arm_length": arm_length, # This is the potentially overridden value
        "wire_radius": wire_radius,
        "gap": gap,
        "offset": offset
    }
    print(f"Parameters defined for {freq_ghz} GHz. Arm length: {arm_length:.2f} mm")
    return params


def create_dipole_geometry(hfss, params):
    """Creates the dipole arms and port sheet geometry in HFSS."""
    hfss.modeler.model_units = "mm"

    arm_length = params["arm_length"]
    wire_radius = params["wire_radius"]
    gap = params["gap"]

    # Arm 1 (+Z)
    arm1 = hfss.modeler.create_cylinder(cs_axis="Z",
                                        position=[0, 0, gap / 2],
                                        radius=wire_radius,
                                        height=arm_length,
                                        name="Dipole_Arm1",
                                        matname="pec")  # Assign PEC directly

    # Arm 2 (-Z)
    arm2 = hfss.modeler.create_cylinder(cs_axis="Z",
                                        position=[0, 0, -gap / 2 - arm_length],
                                        radius=wire_radius,
                                        height=arm_length,
                                        name="Dipole_Arm2",
                                        matname="pec")

    # Sheet for the port (Rectangle in YZ plane)
    port_sheet = hfss.modeler.create_rectangle(orientation="YZ",
                                               position=[
                                                   0, -wire_radius, -gap / 2],
                                               dimension_list=[
                                                   wire_radius * 2, gap],
                                               name="Port_Sheet")

    print("Dipole geometry created.")
    # Return references needed for excitation/boundaries
    return {"arm1": arm1, "arm2": arm2, "port_sheet": port_sheet}

from pyaedt import Desktop, Hfss


def launch_aedt(aedt_version="2024.2", non_graphical=False, new_session=True, use_student_version=True, grpc_address=None, grpc_port=None):
    """Launches or connects to an AEDT Desktop session."""
    try:
        if grpc_address and grpc_port:
            # Connect to an existing AEDT session using gRPC
            desktop = Desktop(machine=grpc_address,
                              port=grpc_port,
                              non_graphical=non_graphical,
                              new_desktop_session=new_session,
                              student_version=use_student_version)
        else:
            desktop = Desktop(specified_version=aedt_version,
                              non_graphical=non_graphical,
                              new_desktop_session=new_session,
                              student_version=use_student_version)
        print("AEDT Desktop Initialized")
        return desktop
    except Exception as e:
        print(f"Error launching AEDT Desktop: {e}")
        raise


def initialize_hfss(desktop, project_name, design_name, solution_type, aedt_version):
    """Initializes or connects to an HFSS design."""
    try:
        hfss = Hfss(project=project_name,
                    design=design_name,
                    solution_type=solution_type,
                    version=aedt_version,
                    # Ensure connection to the correct desktop
                    aedt_process_id=desktop.aedt_process_id)
        print(
            f"Project '{project_name}' and Design '{design_name}' created/selected.")
        return hfss
    except Exception as e:
        print(f"Error initializing HFSS or creating the design: {e}")
        if desktop:
            desktop.release_desktop()
        raise


def release_aedt(desktop: Desktop, project_name=None, save_project=True, project_path=None):
    """Saves the project (optional) and releases the AEDT Desktop session."""
    try:
        if save_project and project_name and project_path:
            # Assuming hfss object is managed elsewhere or project is accessed via desktop
            project = desktop.odesktop.GetProject(project_name)
            if project:
                project.SaveAs(project_path, True)  # Overwrite if exists
                print(f"Project saved to: {project_path}")
            else:
                print(
                    f"Warning: Could not find project '{project_name}' to save.")
        elif save_project:
            print("Warning: Project name or path not provided for saving.")

        if desktop:
            desktop.release_desktop()
            print("AEDT Session released.")
    except Exception as e:
        print(f"Error during AEDT release: {e}")
        # Attempt to release anyway if possible
        if desktop:
            try:
                desktop.release_desktop(
                    close_projects=True, close_on_exit=True)
            except:
                pass  # Ignore errors during final release attempt
        raise

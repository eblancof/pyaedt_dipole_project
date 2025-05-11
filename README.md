# PyAEDT Dipole Simulation Project with Streamlit Interface

This project provides an interactive web interface using Streamlit to simulate a simple dipole antenna using Ansys Electronics Desktop (AEDT), controlled via the PyAEDT library. It allows users to configure simulation parameters, run the simulation, and visualize results directly in the browser.

The application can connect to a local AEDT instance or a remote instance via gRPC. It is also containerized using Docker for easier deployment and dependency management.

## Structure

- `src/streamlit_app.py`: The main Streamlit application script.
- `requirements.txt`: Python dependencies for the project.
- `Dockerfile`: Defines the Docker image for the Streamlit application environment.
- `docker-compose.yml`: Configuration for running the application using Docker Compose.
- `src/`: Source code directory containing the simulation logic.
- `.github/workflows/`: Contains GitHub Actions workflows for automated Docker builds.

## Features

- Interactive configuration of simulation parameters (frequency, geometry, analysis settings).
- Support for connecting to local or remote (gRPC) AEDT instances.
- Step-by-step simulation workflow: Initialize AEDT, Create Design, Run Simulation, Release AEDT.
- Interactive visualization of S11 (Return Loss) and 3D radiation patterns.

## How to Run

### Prerequisites

1.  **Ansys Electronics Desktop (AEDT):** Ensure you have a compatible version installed (e.g., 2024.2).
    *   For **local connection:** AEDT must be installed on the same machine where you run the Streamlit app (or the Docker container if configured for host networking).
    *   For **gRPC connection:** AEDT must be running on a machine accessible from the Streamlit app, with gRPC enabled.
2.  **Python:** Python 3.9+ is recommended.
3.  **Docker & Docker Compose:** Required for running the containerized version.

### Option 1: Running Locally (Without Docker)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/eblancof/pyaedt_dipole_project.git
    cd pyaedt_dipole_project
    ```
2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the Streamlit app:**
    ```bash
    streamlit run src/streamlit_app.py --server.port 8080
    ```
4.  Open your web browser and navigate to the URL provided by Streamlit (usually `http://localhost:8080`).
5.  Configure the connection type (Local or gRPC) and simulation parameters in the sidebar.
6.  Follow the steps in the Streamlit interface (Initialize, Load/Create, Run).

### Option 2: Running with Docker Compose (Recommended for Containerization)

1.  **Ensure Docker and Docker Compose are running.**
2.  **Build and run the container:** (Make sure `docker-compose.yml` exists)
    ```bash
    docker compose up --build
    ```
    *   The `--build` flag is only needed the first time or when code/dependencies change.
    *   This command will build the Docker image (if not already built) and start the Streamlit service defined in `docker-compose.yml`.
3.  Open your web browser and navigate to `http://localhost:8080` (or the port mapped in `docker-compose.yml`).
4.  Configure and run the simulation as described in Option 1. The container needs network access to connect to AEDT (either locally via host network or remotely via gRPC).

### Option 3: Running with Docker (Pre-built Image from Docker Hub)

This option allows you to run the application using a pre-built Docker image from Docker Hub, eliminating the need to build the image locally.

1. **Ensure Docker is running.**

2. **Pull the latest Docker image:**
   ```bash
   docker pull eblancof/pyaedt-streamlit-app:latest
   ```

3. **Run the Docker container:**
   This command runs the container in host network mode, which is often necessary for PyAEDT to connect to a local AEDT instance. It also maps port 8080.

   ```bash
   docker run --rm --network host -p 8080:8080 eblancof/pyaedt-streamlit-app:latest
   ```

   - If you have a `.env` file with environment variables (e.g., `PORT`), you can pass it to the container:

     ```bash
     docker run --rm --network host --env-file .env eblancof/pyaedt-streamlit-app:latest
     ```

     Note: The `PORT` variable from the `.env` file will be used by the `docker-compose.yml` `command` if you were using compose, but for direct `docker run`, the `streamlit run` command inside the Dockerfile doesn't automatically pick up the `.env` file's `PORT` unless the entrypoint script is designed to do so. The command above maps host port 8080 to the container's port which is set by the `CMD` in the Dockerfile (or overridden if `PORT` env var is correctly handled by the app's startup). For this image, the `CMD` uses `--server.address=0.0.0.0` but doesn't explicitly set `--server.port` from an env var, so it will default to Streamlit's default (8501) unless the image is built to take `PORT` env var or the command is overridden.
     The `docker-compose.yml` uses `command: ["streamlit", "run", "src/streamlit_app.py", "--server.port=${PORT}", "--server.address=0.0.0.0"]`. To achieve similar with `docker run`, you would override the command:

     ```bash
     docker run --rm --network host -e PORT=8080 eblancof/pyaedt-streamlit-app:latest streamlit run src/streamlit_app.py --server.port=8080 --server.address=0.0.0.0
     ```

     Or, if your `.env` file contains `PORT=8080`:

     ```bash
     docker run --rm --network host --env-file .env eblancof/pyaedt-streamlit-app:latest streamlit run src/streamlit_app.py --server.port=${PORT} --server.address=0.0.0.0
     ```

4. Open your web browser and navigate to `http://localhost:8080` (or the port you specified if you overrode the command and PORT).

5. Configure the connection type (Local or gRPC) and simulation parameters in the sidebar.

6. Follow the steps in the Streamlit interface (Initialize, Load/Create, Run).

## Docker Configuration Details

-   **Dockerfile:** Sets up a Python 3.12 environment, installs dependencies from `requirements.txt`, and copies the application code. It exposes the default port and sets the default command to run the Streamlit app.
-   **docker-compose.yml:** Defines the `streamlit-app` service based on the `Dockerfile`. It maps the container's default port to the host's default port. Crucially, it should configure `network_mode: host` to allow the container to directly access the host machine's network, enabling connections to a locally running AEDT instance or other services on the local network (like a gRPC server running on the host).

## Connecting to AEDT from Docker

-   **Local AEDT:** When using `network_mode: host` in `docker-compose.yml`, the container shares the host's network stack. You can typically use `localhost` or the machine's IP address within the Streamlit app's gRPC settings if AEDT is running locally with gRPC enabled. For standard local non-gRPC connections, PyAEDT within the container should find the local AEDT installation if environment variables are set correctly or if AEDT is in the default path *from the host's perspective* and if **pyaedt** python module is installed in the program.
-   **Remote AEDT (gRPC):** Configure the gRPC Machine Address and Port in the Streamlit sidebar to point to the machine running AEDT with gRPC enabled. Ensure network connectivity and firewall rules allow the connection from the Docker container (or the host machine if using `network_mode: host`) to the remote AEDT gRPC server.


# Basic Python environment
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Note: Running AEDT itself within Docker requires significant additional setup,
# including licensing, potential GUI forwarding (if not non-graphical),
# and access to the AEDT installation. This Dockerfile primarily sets up
# the Python environment for the script.

EXPOSE 8501
# Command to run the Streamlit app
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0"]

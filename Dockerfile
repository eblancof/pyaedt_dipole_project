# Basic Python environment
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Port will be specified in docker-compose.yml
CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0"]

# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Make our new startup script executable
RUN chmod +x /app/entrypoint.sh

# Set the entrypoint script as the command to run when the container starts
ENTRYPOINT ["/app/entrypoint.sh"]
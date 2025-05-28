FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a directory for SQLite database with proper permissions
RUN mkdir -p instance && chmod 777 instance

# Copy the rest of the application
COPY . . # NOSONAR

# Expose port
EXPOSE 5000

# Command to run the application
CMD ["python", "app.py"] 
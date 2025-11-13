# Use the official Python image
FROM python:3.13-slim

# Install system dependencies for geospatial libraries
RUN apt-get update && apt-get install -y \
    libgeos-dev \
    libproj-dev \
    libspatialindex-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Allow statements and log messages to immediately appear in the logs
ENV PYTHONUNBUFFERED=1

# Copy dependency files first for better caching
COPY pyproject.toml ./

# Install dependencies (without project files)
RUN uv pip install --system -r pyproject.toml

# Copy the rest of the application
COPY . .

EXPOSE $PORT

# Run the FastMCP server with Python directly
CMD ["python", "-u", "server.py"]


# Use the official Python image
FROM python:3.13-slim

# Install system dependencies for geospatial libraries
# This layer is cached unless system dependencies change
RUN apt-get update && apt-get install -y \
    libgeos-dev \
    libproj-dev \
    libspatialindex-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install uv (cached layer)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory to /workspace (matches the path expected by ground_tree_detector)
WORKDIR /workspace

# Allow statements and log messages to immediately appear in the logs
ENV PYTHONUNBUFFERED=1

# Suppress NNPACK warning (harmless - just means CPU optimization unavailable)
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1

# Copy ONLY dependency file first (this layer is cached if pyproject.toml doesn't change)
COPY pyproject.toml ./

# Install dependencies in a separate layer (cached if pyproject.toml unchanged)
# This is the slowest step (~15 min) but will be cached after first build
RUN uv pip install --system -r pyproject.toml

# Copy application code LAST (this changes frequently but is fast to copy)
COPY . .

EXPOSE $PORT

# Run the FastMCP server with Python directly
CMD ["python", "-u", "server.py"]


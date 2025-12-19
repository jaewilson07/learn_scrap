# Stage 1: Builder
FROM python:3.12-slim AS builder

# Install 'uv'
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy dependency definition files
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Stage 2: Final
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv .venv

# Copy application code
COPY src/ ./src/

# Copy project metadata for editable install
COPY pyproject.toml README.md ./

# Install the package in editable mode
RUN . .venv/bin/activate && pip install -e .

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy start script
COPY start.sh .

# Run the app
CMD ["./start.sh"]

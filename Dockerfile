# 1. Start with a Python base image
FROM python:3.12-slim

# 2. Install 'uv' into the container 
# (We copy the executable directly from uv's official image - it's a cool trick!)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 3. Set the working directory
WORKDIR /app

# 4. Copy the project definition files FIRST (for caching)
# You need both pyproject.toml and uv.lock
COPY pyproject.toml uv.lock ./

# 5. Install dependencies using uv
# --frozen: ensures we use exactly the versions in uv.lock
# --no-cache: keeps the image small
RUN uv sync --frozen --no-cache

# 6. Copy the rest of your application code
COPY . .

# 7. IMPORTANT: Add the virtual environment to the PATH
# uv installs into .venv by default, so we need to tell Docker where to find 'uvicorn'
ENV PATH="/app/.venv/bin:$PATH"

# 8. Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
# Use official UV image (includes Python 3.14)
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy dependency definition first (cache layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Copy scripts ONLY (No config, No data)
# Copy application code
COPY scripts/ ./scripts/
COPY config/  ./config/
COPY *.py     ./

# Default Env Var for the container structure
# This points to where we expect the USER to mount their resumes
ENV RESUME_FOLDER="/input_resumes"

# Python path must include site-packages from uv
ENV PATH="/app/.venv/bin:$PATH"

# Default command runs the full pipeline
CMD ["python", "main.py"]

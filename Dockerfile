# Use official UV image (includes Python 3.14)
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy dependency definition first (cache layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Copy application code
COPY scripts/ ./scripts/
COPY hooks/ ./hooks/
COPY simulate/ ./simulate/
COPY main.py ./

# Install git hooks (for privacy validation)
RUN chmod +x hooks/install.sh && ./hooks/install.sh

# Default Env Var for container structure
# This points to where we expect the USER to mount their resumes
ENV RESUME_FOLDER="/input_resumes"
ENV DATA_DIR="/app/data"

# Python path must include site-packages from uv
ENV PATH="/app/.venv/bin:$PATH"

# Default command runs demo mode
CMD ["python", "main.py", "--demo"]

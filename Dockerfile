# ──────────────────────────────────────────────────────────────────────────────
# Stage 1 — builder: install dependencies with build tools
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Build deps for cryptography (cffi) and asyncpg (C extensions)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first (separate layer — rarely invalidated)
RUN pip install --no-cache-dir --upgrade pip

# Install only runtime deps from lock file (layer-cached until requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir \
    --target /deps \
    --no-compile \
    -r requirements.txt


# ──────────────────────────────────────────────────────────────────────────────
# Stage 2 — runtime: lean final image, no build tools
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/deps:/app \
    PATH="/deps/bin:$PATH"

WORKDIR /app

# Non-root user — created before copying files so ownership is set correctly
RUN useradd --uid 1001 --no-create-home --shell /bin/false atlaz

# Packages from builder
COPY --from=builder --chown=atlaz:atlaz /deps /deps

# Application source and Alembic config
COPY --chown=atlaz:atlaz app/        app/
COPY --chown=atlaz:atlaz alembic.ini .

# Entrypoint: runs migrations then starts the server
COPY --chown=atlaz:atlaz docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

EXPOSE 8000

USER atlaz

ENTRYPOINT ["./docker-entrypoint.sh"]

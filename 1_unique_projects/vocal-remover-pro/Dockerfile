# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Builder — compile Python wheels
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Runtime — lean production image
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS final

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_MAX_UPLOAD_SIZE=500 \
    LIBRARY_DIR=/app/library \
    MODEL_DIR=/app/models \
    OMP_NUM_THREADS=4 \
    OPENBLAS_NUM_THREADS=4 \
    MKL_NUM_THREADS=4

WORKDIR /app

# Install runtime system deps (ffmpeg + SSL certs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy compiled venv from builder
COPY --from=builder /opt/venv /opt/venv

# Non-root user for security
RUN useradd -m -u 1000 appuser \
    && mkdir -p /app/library /app/models \
    && chown -R appuser:appuser /app

# Copy application source
COPY --chown=appuser:appuser . /app

USER appuser

EXPOSE 8501

# Streamlit built-in health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

CMD ["streamlit", "run", "app.py"]

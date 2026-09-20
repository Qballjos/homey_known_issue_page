FROM python:3.12-slim

# Install system dependencies & tini for signal handling
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tini \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -m appuser

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app/ ./app/

# Create persistent data directory and set permissions for non-root user
RUN mkdir -p /app/data && chown -R appuser:appgroup /app

# Switch to non-root user for security
USER appuser

# Environment defaults
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

EXPOSE 8000

# Docker healthcheck calling the /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use tini as init process
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start Uvicorn with proxy headers enabled for reverse proxies
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]

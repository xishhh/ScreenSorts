FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python -m venv /app/venv
ENV PATH=/app/venv/bin:$PATH

COPY requirements.txt .

RUN pip install --no-cache-dir torch --extra-index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --gid 1001 appuser

WORKDIR /app

COPY --from=builder /app/venv /app/venv
RUN chmod -R a+r /app/venv && find /app/venv -type d -exec chmod a+x {} +
ENV PATH=/app/venv/bin:$PATH

COPY --chown=appuser:appgroup app/ ./app/

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=5 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

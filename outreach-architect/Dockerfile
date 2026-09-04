# syntax=docker/dockerfile:1
#
# Fixes over the previous revision:
#   * ran as root; now UID 1001
#   * CMD carried --reload, which starts uvicorn's file-watching reloader in
#     production: it spawns a supervisor, doubles memory, and restarts the
#     service whenever a file changes on a mounted volume
#   * HEALTHCHECK probed "/" rather than the liveness endpoint, and curl was
#     installed only incidentally
#   * single stage, so gcc and postgresql-client shipped in the runtime image

FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    ENVIRONMENT=production \
    BIND_HOST=0.0.0.0 \
    PORT=8000 \
    LOG_LEVEL=INFO

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1001 outreach \
    && useradd --system --uid 1001 --gid outreach --create-home outreach

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=outreach:outreach . .

RUN mkdir -p /app/logs /app/data && chown -R outreach:outreach /app/logs /app/data

# /app is created by WORKDIR and owned by root, so the non-root user cannot
# create files directly in it. The SQLite default resolves to the repo
# directory, which meant the container died at startup with
# "sqlite3.OperationalError: unable to open database file". /app/data is the
# writable path, and is where a volume should be mounted.
ENV DATABASE_URL=sqlite:////app/data/outreach.db

USER outreach

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl --fail --silent http://127.0.0.1:8000/health || exit 1

# exec form, no --reload: uvicorn is PID 1 and receives SIGTERM directly.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--timeout-graceful-shutdown", "20", "--no-server-header"]

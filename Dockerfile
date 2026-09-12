# Stage 1: Build React/Vite frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /build/apps/web

COPY apps/web/package*.json ./
RUN npm ci

COPY apps/web ./
RUN npm run build

# Stage 2: Python FastAPI backend
FROM python:3.11-slim AS runtime

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SCHOOLBAG_STATIC_DIR=/app/static \
    PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install backend dependencies
COPY services/school_service/pyproject.toml ./services/school_service/
RUN pip install --no-cache-dir ./services/school_service

# Copy backend code
COPY services/school_service/src ./services/school_service/src
RUN pip install --no-cache-dir -e ./services/school_service

# Copy built frontend from Stage 1
COPY --from=frontend-builder /build/apps/web/dist /app/static

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "schoolbag.interfaces.http.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

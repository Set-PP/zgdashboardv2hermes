# ── Pipeline API (FastAPI) — read-only data server on VPS ─────
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# data/ is mounted as a volume by docker-compose (zawg.db + photos)
EXPOSE 8600
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8600"]

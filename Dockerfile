FROM python:3.12-slim

WORKDIR /app

# libgomp1: xgboost's prebuilt wheel dynamically links against libgomp at runtime --
# without it, "import xgboost" fails with a missing shared library error on slim images.
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# data/ holds the SQLite DBs (predictions.db) -- Fly's persistent volume mounts here
# (see fly.toml), so tracked prediction history survives restarts and redeploys
# instead of resetting every time, unlike a plain ephemeral container filesystem.
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

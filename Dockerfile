FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# レート制限をメモリ上で行うためワーカーは1、並列はスレッドで処理
CMD gunicorn -w 1 --threads 8 -b 0.0.0.0:${PORT:-5000} app:app

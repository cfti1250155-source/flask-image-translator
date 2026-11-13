FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ビルド時にアプリが読み込めることを確認（依存の入れ忘れをデプロイ前に検知）
RUN SECRET_KEY=build python -c "import app"

# 利用制限をメモリ上で行うためワーカーは1、並列はスレッドで処理。
# Gemini の待ち（既定40秒×リトライ）より長く --timeout を取る
CMD gunicorn -w 1 --threads 8 --timeout 120 -b 0.0.0.0:${PORT:-5000} app:app

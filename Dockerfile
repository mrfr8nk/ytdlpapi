FROM python:3.10.13-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p stream

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-1300} --workers 4 --threads 2 app:app"]

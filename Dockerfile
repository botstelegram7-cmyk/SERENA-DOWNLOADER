# Copyright (c) 2026 tusar404
# Licensed under the MIT License.

FROM python:3.12-slim

# ffmpeg provides both ffmpeg and ffprobe, both required by bot/dl/ffmpeg.py
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -U -r requirements.txt

COPY . .

RUN mkdir -p downloads

CMD ["python3", "-m", "bot"]

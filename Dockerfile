# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

RUN python -m venv "${VIRTUAL_ENV}"

WORKDIR /build
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}" \
    PORT=10000

# ffmpeg and ffprobe are required by serena/dl/ffmpeg.py.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin serena

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY . .

# The bot writes temporary media and its runtime data here.
RUN mkdir -p downloads \
    && chown -R serena:serena /app

USER serena

# Render injects PORT at runtime; this documents the local default.
EXPOSE 10000

CMD ["python", "-m", "bot"]

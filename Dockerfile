FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    alsa-utils \
    pulseaudio-utils \
    build-essential \
    gcc \
    libc6-dev \
    portaudio19-dev \
    libasound2-dev \
    libglib2.0-0 \
    libsdl2-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Jarvis.py .
COPY utils.py .

RUN mkdir -p /app/audio

ENV PYTHONUNBUFFERED=1
ENV PYGAME_HIDE_SUPPORT_PROMPT=hide

CMD ["python", "Jarvis.py"]
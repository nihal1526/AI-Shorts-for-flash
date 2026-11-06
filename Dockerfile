# Multi-stage lightweight Python Dockerfile with FFmpeg & fonts for ASS subtitles
FROM python:3.11-slim

# Avoid prompts from debian frontend
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies: FFmpeg, fontconfig, and standard fonts for subtitle burn-in
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fontconfig \
    fonts-dejavu-core \
    fonts-freefont-ttf \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definition and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Ensure storage directories exist with write permissions
RUN mkdir -p storage/downloads storage/rendered storage/temp \
    && chmod -R 777 storage

# Expose standard port (7860 for Hugging Face Spaces, 8000 for standard Docker)
EXPOSE 7860

# Default command: launch FastAPI server
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "7860"]

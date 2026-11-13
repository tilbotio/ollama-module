# syntax=docker/dockerfile:1

# Use a slim Python base image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ARG PORT

# Set working directory
WORKDIR /app

# Install system deps
RUN apt-get -y update && apt-get -y install curl zstd

# Install ollama CLI
RUN curl -fsSL https://ollama.com/install.sh | sh

# Install Python deps.
# We keep layers efficient by copying only requirements first.
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the application source
COPY . .

# Start the app. We use python app.py so it respects APP_HOST/APP_PORT and .env
CMD ollama serve & sleep 5 && ollama pull ${MODEL} & fastapi run --port ${PORT}

# Python slim base
FROM python:3.10-slim

# System deps for opencv/dlib build and runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/matam

# Copy requirements and install
COPY matam/requirements.txt /app/matam/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# Copy source
COPY matam /app/matam

# Ensure necessary directories exist
RUN mkdir -p static/matched static/gallery static/models tmp_frames

ENV PYTHONUNBUFFERED=1 \
    PORT=8080

EXPOSE 8080

# Gunicorn server
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app", "--workers", "2", "--threads", "2", "--timeout", "120"]


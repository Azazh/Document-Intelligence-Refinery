# Dockerfile for RefineryAI Document Intelligence Pipeline
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpoppler-cpp-dev \
        tesseract-ocr \
        libtesseract-dev \
        poppler-utils \
        git \
        && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app/

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install .

# Expose port if running a server (optional)
# EXPOSE 8000

# Default command (can be overridden)
CMD ["make", "run"]

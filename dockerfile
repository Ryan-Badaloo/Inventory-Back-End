FROM python:3.12-alpine

# Prevent Python from writing pyc files & enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (better caching)
COPY requirements.txt .

# Install system dependencies (bash + netcat for DB wait)
RUN apk add --no-cache bash netcat-openbsd

RUN pip3 install --no-cache-dir --upgrade pip \
    && pip3 install --no-cache-dir -r requirements.txt \
    && pip3 install --no-cache-dir "gunicorn" "uvicorn[standard]"

# Copy project files
COPY . .

# Fix Windows CRLF line endings and make script executable
RUN sed -i 's/\r$//' start_backend.sh && chmod +x start_backend.sh

EXPOSE 8000

# Use bash to run script
CMD ["bash", "./start_backend.sh"]
FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN apk add --no-cache netcat-openbsd

RUN pip3 install --no-cache-dir --upgrade pip \
    && pip3 install --no-cache-dir -r requirements.txt \
    && pip3 install --no-cache-dir "gunicorn" "uvicorn[standard]"

COPY . .

# Fix Windows CRLF line endings and make script executable
RUN sed -i 's/\r$//' start_backend.sh && chmod +x start_backend.sh

EXPOSE 8000
CMD ["sh", "start_backend.sh"]
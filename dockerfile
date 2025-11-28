FROM python:3.12-alpine3.22

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
COPY startup.sh .
COPY requirements.txt .

RUN pip3 install --no-cache-dir --upgrade pip \
    && pip3 install --no-cache-dir -r requirements.txt \
    && pip3 install --no-cache-dir "gunicorn" "uvicorn[standard]"

COPY . .

EXPOSE 8000
CMD ["bash","startup.sh"]
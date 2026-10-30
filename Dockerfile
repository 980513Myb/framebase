FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        fonts-dejavu-core \
        libglib2.0-0 \
        libgl1 \
        libjpeg62-turbo \
        libpng16-16 \
        libwebp7 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

RUN mkdir -p config backups fonts templates layouts

EXPOSE 5256

CMD ["python", "main.py"]

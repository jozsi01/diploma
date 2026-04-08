FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libreoffice \
    --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/temp

# Give LibreOffice a writable profile directory
RUN mkdir -p /tmp/libreoffice-profile && chmod 777 /tmp/libreoffice-profile

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
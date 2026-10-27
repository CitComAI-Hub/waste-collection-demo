FROM python:3.12-slim

# git: ds-consumer-auth is installed from its GitHub tag
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .
COPY services/ services/
COPY static/ static/

# gunicorn writes its control socket in the home directory
RUN useradd --uid 10001 --create-home app
USER 10001

EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/healthz')"]

# One process with threads: the data space token is cached per process
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "8", "--timeout", "120", "server:app"]

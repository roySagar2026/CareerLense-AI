# Build from the REPOSITORY ROOT (the root requirements.txt is the single source of
# production dependencies):
#   docker build -f backend/Dockerfile -t careerlens-backend .
#   docker build -f backend/Dockerfile --build-arg INSTALL_OCR=true -t careerlens-backend:ocr .
FROM python:3.12-slim

ARG INSTALL_OCR=false

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Optional Tesseract for scanned-PDF OCR (also set OCR_ENABLED=true at runtime).
RUN if [ "$INSTALL_OCR" = "true" ]; then \
      apt-get update \
      && apt-get install -y --no-install-recommends tesseract-ocr \
      && rm -rf /var/lib/apt/lists/*; \
    fi

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /app --shell /usr/sbin/nologin app

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY --chown=app:app backend/ /app/
COPY --chown=app:app infrastructure/scripts/backend-entrypoint.sh /usr/local/bin/backend-entrypoint.sh
RUN chmod 0755 /usr/local/bin/backend-entrypoint.sh

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).status == 200 else 1)"

ENTRYPOINT ["/usr/local/bin/backend-entrypoint.sh"]

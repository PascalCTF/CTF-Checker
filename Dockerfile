FROM python:3.13-alpine

WORKDIR /app

RUN apk add --no-cache \
      gcc musl-dev linux-headers \
      postgresql-client \
    && rm -rf /var/cache/apk/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/    ./src/
COPY static/ ./static/
COPY templates/ ./templates/
COPY start.sh .

RUN chmod +x start.sh

RUN addgroup -S appuser \
 && adduser  -S -u 1000 -G appuser appuser \
 && chown -R appuser:appuser /app

USER appuser

RUN mkdir -p uploads \
 && chown appuser:appuser uploads

ENV PYTHONPATH=/app/src
EXPOSE 5000

CMD ["./start.sh"]

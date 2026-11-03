FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    TRAIL_SENTINEL_LIVE=1 \
    DAILY_CALL_CAP=200 \
    CALL_COUNTER_FILE=/tmp/.call_counter.json

COPY server.py main.py ./
COPY alerts.py config.py meta_transport.py pipeline.py sam_client.py triage.py vision_router.py ./
COPY webapp ./webapp
COPY fixtures ./fixtures
COPY eval/data/hero_snake_leaves_01.jpg ./eval/data/hero_snake_leaves_01.jpg

EXPOSE 8080

CMD ["python3", "server.py"]

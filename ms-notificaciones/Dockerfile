FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY packages/agm_events /packages/agm_events
COPY contracts/events /contracts/events
ENV EVENT_CONTRACTS_DIR=/contracts/events
RUN pip install --no-cache-dir /packages/agm_events

COPY ms-notificaciones/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY proto /proto
COPY ms-notificaciones /app

RUN pip install --no-cache-dir grpcio-tools \
 && bash /app/generate_proto.sh \
 && pip uninstall -y grpcio-tools || true

RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

EXPOSE 8006 50056
ENTRYPOINT ["./entrypoint.sh"]

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
# Copiar requirements desde el contexto raíz (build context debe ser la raíz del repo)
COPY ms-auth/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar proto y código del servicio
COPY proto /proto
COPY ms-auth /app
COPY ms-auth/scripts/wait_grpc_port.sh /docker/scripts/wait_grpc_port.sh

# Generar stubs gRPC durante el build: instalar grpcio-tools temporalmente
RUN pip install --no-cache-dir grpcio-tools \
 && bash /app/generate_proto.sh \
 && pip uninstall -y grpcio-tools || true

# Windows: entrypoint.sh suele tener CRLF; en Linux rompe el shebang ("no such file or directory")
RUN sed -i 's/\r$//' /app/entrypoint.sh /docker/scripts/wait_grpc_port.sh \
 && chmod +x /app/entrypoint.sh /docker/scripts/wait_grpc_port.sh

WORKDIR /app
EXPOSE 8001 50051

ENTRYPOINT ["./entrypoint.sh"]

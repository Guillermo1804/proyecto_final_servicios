# agm_events

Libreria Python compartida para el bus de eventos AGM (Fase 1+).

## Instalacion local

```bash
cd packages/agm_events
pip install -r requirements.txt
pip install -e .
```

## Smoke test (Fase 1)

Desde la raiz del monorepo, con RabbitMQ levantado:

```bash
docker compose up -d rabbitmq
copy .env.example .env
cd packages/agm_events
pip install -r requirements.txt
pip install -e .
python smoke_test.py
```

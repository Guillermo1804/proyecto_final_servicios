# Generación de stubs gRPC

Requisitos previos:

- Tener Python con `grpcio-tools` instalado. Por ejemplo:

```
pip install grpcio grpcio-tools
```

Uso (por microservicio):

```
cd ms-alumnos
bash generate_proto.sh
# o desde la raíz del repo:
bash scripts/generate_ms_proto.sh ms-alumnos
```

Script maestro (desde la raíz del repo):

```
bash scripts/generate_all_protos.sh
```

Notas:

- Los stubs se generan en `proto_generated/` dentro de cada microservicio.
- Qué `.proto` compila cada MS: `scripts/proto_manifest.sh` (exposición + solo clientes necesarios). Ver `proto/README.md`.
- Decidir si versionar `proto_generated/` o añadirlo a `.gitignore`. Recomendación: añadir a `.gitignore` y generar en CI antes de la build.

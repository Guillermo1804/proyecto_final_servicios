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
```

Script maestro (desde la raíz del repo):

```
bash scripts/generate_all_protos.sh
```

Notas:

- Los stubs se generan en `proto_generated/` dentro de cada microservicio.
- Decidir si versionar `proto_generated/` o añadirlo a `.gitignore`. Recomendación: añadir a `.gitignore` y generar en CI antes de la build.

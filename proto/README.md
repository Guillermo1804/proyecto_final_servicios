# Contratos gRPC AGM (`/proto`)



## Paquetes (namespaces)



Cada archivo define un **package protobuf distinto** para evitar colisiones al generar stubs (Python, C#, Java):



| Archivo | `package` | Ruta gRPC ejemplo |

|---------|-----------|-------------------|

| `agm_common.proto` | `agm.common` | *(sin servicio)* |

| `auth.proto` | `agm.auth` | `/agm.auth.AuthService/ValidateToken` |

| `periodos.proto` | `agm.periodos` | `/agm.periodos.PeriodosService/GetPeriodoActivo` |

| `alumnos.proto` | `agm.alumnos` | `/agm.alumnos.AlumnosService/...` |

| `calificaciones.proto` | `agm.calificaciones` | … |

| `asistencias.proto` | `agm.asistencias` | … |

| `notificaciones.proto` | `agm.notificaciones` | … |

| `reportes.proto` | `agm.reportes` | … |



Los stubs Python siguen nombrándose por archivo (`auth_pb2`, `periodos_pb2`); el **package** define el namespace lógico y la ruta del método gRPC.



## Modelo: base compartida + exposición por MS



| Archivo | Rol |

|---------|-----|

| **`agm_common.proto`** | Tipos **reutilizables** (`UserClaims`, `AccessTokenCredential`, `TokenValidationResult`, eventos). **No** son firma directa de un `rpc`. |

| **`{dominio}.proto`** | `service` del MS + mensajes `*Request` / `*Response` **dedicados** por método RPC. |



### Buena práctica: RPC con mensajes propios del dominio



```protobuf

// agm.common — bloque reutilizable (eventos, anidados)

message AccessTokenCredential { string access_token = 1; }

message TokenValidationResult { bool valid = 1; UserClaims user = 2; ... }



// agm.auth — firma del servicio (extensible sin romper agm.common)

message ValidateTokenRequest {

  agm.common.AccessTokenCredential credential = 1;

}

message ValidateTokenResponse {

  agm.common.TokenValidationResult result = 1;

}

rpc ValidateToken (ValidateTokenRequest) returns (ValidateTokenResponse);

```



Igual criterio en periodos: `GetPeriodoActivo(GetPeriodoActivoRequest)` en lugar de `agm.common.Empty` como parámetro del RPC.



## Seguridad y tokens



| Tema | Dónde vive | Comportamiento |

|------|------------|----------------|

| JWT access (RS256) | `agm.common.AccessTokenCredential` + JWKS MS-1 | MS-2…7 validan offline con `/.well-known/jwks.json` |

| Validación gRPC | `agm.auth.ValidateToken*` (envuelve tipos comunes) | Solo MS-1 implementa `AuthService` |

| Revocación (logout) | `token.revoked.v1` + `agm.common.TokenRevocationPayload` | Workers `run_event_consumer` en MS-2…MS-7 |

| Reset password | `SendResetPasswordRequest.delivery` → `agm.common.PasswordResetDelivery` | Sin JWT suelto en el mensaje |



## Mapa de exposición (servicios gRPC)



| Archivo | MS | Puerto | Servicio |

|---------|-----|--------|----------|

| `auth.proto` | MS-1 | 50051 | `AuthService` |

| `periodos.proto` | MS-2 | 50052 | `PeriodosService` |

| `alumnos.proto` | MS-3 | 50053 | `AlumnosService` |

| `calificaciones.proto` | MS-4 | 50054 | `CalificacionesService` |

| `asistencias.proto` | MS-5 | 50055 | `AsistenciasService` |

| `notificaciones.proto` | MS-6 | 50056 | `NotificacionesService` |

| `reportes.proto` | MS-7 | 50057 | `ReportesService` |



## Generar stubs



```bash
bash scripts/generate_all_protos.sh
```



Manifiesto por MS: `scripts/proto_manifest.sh` (siempre incluye `agm_common.proto` primero).



## Integración asíncrona



Negocio entre dominios: RabbitMQ + `contracts/events/`. gRPC: lecturas puntuales, legacy o administración.



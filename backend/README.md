# Classroom Hub — Backend Distribuido

Ecosistema de **3 microservicios** + **BFF** para aulas en tiempo real con aislamiento por grupos, identidad única por grupo e idempotencia de eventos.

## Arquitectura

```
                    ┌─────────────────────────────────────┐
  App Móvil (Expo)  │         BFF Service :8000           │
  REST + WebSocket  │  • POST /api/v1/sessions            │
        │           │  • GET  /api/v1/groups/{id}/connections
        │           │  • WS   /ws?id_sesion&id_grupo&nombre
        ▼           └──────────┬──────────────┬───────────┘
                               │              │
                    ┌──────────▼───┐   ┌──────▼──────────┐
                    │ Identity :8001│   │ Groups :8002   │
                    │ Nombres únicos  │   │ Idempotencia   │
                    │ por (name,group)│   │ por grupo      │
                    └────────────────┘   └─────────────────┘
```

| Servicio | Puerto | Responsabilidad |
|----------|--------|-----------------|
| **bff-service** | 8000 | Punto de entrada único, WebSocket, broadcast por grupo |
| **identity-service** | 8001 | Sesiones, validación de nombre único **por grupo** |
| **groups-service** | 8002 | Registro idempotente de eventos `(group_id, event_id)` |

## Inicio rápido

```bash
cd backend
docker-compose up --build
```

Health check: `curl http://localhost:8000/health`

## API BFF (contrato para el móvil)

### REST — Sesiones

| Método | Ruta | Body | Respuesta |
|--------|------|------|-----------|
| `POST` | `/api/v1/sessions` | `{ "name": "Ana", "group_id": "grupo-a" }` | `201` + `{ session_id, name, group_id, ... }` |
| `DELETE` | `/api/v1/sessions/{session_id}` | — | `204` |
| `GET` | `/api/v1/groups/{group_id}/connections` | — | `{ names: ["Ana", "Luis"], total: 2 }` |

**409** si el nombre ya existe en ese grupo: `{ "error": "SESION_EXISTE", "mensaje": "..." }`

### WebSocket — `/ws`

Query params (obligatorios): `id_sesion`, `id_grupo`, `nombre`

**Cliente → servidor:**

```json
{ "type": "signal", "event_id": "<uuid-v4>", "timestamp": "2026-05-21T12:00:00.000Z" }
{ "type": "ping" }
```

**Servidor → cliente:**

```json
{ "type": "notification", "data": { "message": "Ana ha enviado una señal!", "sender_name": "Ana", "timestamp": "..." } }
{ "type": "ack", "event_id": "<uuid>", "status": "success|duplicate", "recipients": 3, "latency_ms": 12.5 }
{ "type": "pong" }
```

## Requisitos del proyecto — cobertura

| Requisito | Implementación |
|-----------|----------------|
| Microservicios Identity + Groups | ✅ Servicios independientes con SQLite |
| BFF + WebSocket + broadcast | ✅ `connection_manager`, `handler.py` |
| Identidad exclusiva por grupo | ✅ `UNIQUE(name, group_id)` |
| Aislamiento de grupos | ✅ Broadcast e idempotencia por `group_id` |
| Idempotencia | ✅ Groups service; ACK `duplicate` en BFF |
| Resiliencia / caos | ✅ Degradación si Identity/Groups caen; `/health` agregado |
| Limpieza de sesiones expiradas | ✅ Tarea periódica en Identity (cada 5 min) |

## Pruebas

```bash
# Flujo completo (2 clientes WS + señal + caos Identity)
python scratch/test_flow.py

# Idempotencia entre grupos
python scratch/verify_groups_idempotency.py
```

## Despliegue

Ver [DEPLOYMENT.md](./DEPLOYMENT.md) para EC2, Nginx y demostración de resiliencia.

## Estructura

```
backend/
├── bff_service/          # BFF — entrada única
├── identity_service/     # Identidad
├── groups_service/       # Grupos + idempotencia
├── docker-compose.yml
├── scratch/              # Scripts de prueba
└── DEPLOYMENT.md
```

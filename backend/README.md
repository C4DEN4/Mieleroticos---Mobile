# Classroom Hub Backend

Backend API para Classroom Hub - Sistema de comunicación en tiempo real para entornos educativos con aislamiento estricto de grupos y tolerancia a fallos.

## 📋 Índice

- [Descripción General](#descripción-general)
- [Arquitectura](#arquitectura)
- [Dependencias](#dependencias)
- [Configuración](#configuración)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [API REST](#api-rest)
- [WebSocket](#websocket)
- [Instalación y Ejecución](#instalación-y-ejecución)
- [Requisitos Funcionales Implementados](#requisitos-funcionales-implementados)
- [Monitoreo](#monitoreo)
- [Documentación API Interactiva](#documentación-api-interactiva)

---

## Descripción General

El backend es una API RESTful con soporte WebSocket construida con FastAPI que proporciona:

- **Gestión de sesiones de estudiantes** con validación de identidad única y persistencia en SQLite
- **Comunicación en tiempo real** mediante WebSockets con aislamiento estricto entre grupos
- **Broadcast de señales** con latencia objetivo <500ms
- **Idempotencia** para prevenir procesamiento duplicado de eventos con persistencia en SQLite
- **Tolerancia a fallos** con manejo controlado de errores y persistencia en disco
- **Conexiones concurrentes masivas** (>40 dispositivos simultáneos)
- **Base de datos SQLite embebida** para persistencia de sesiones y eventos procesados

---

## Arquitectura

### Componentes Principales

```
backend/
├── main.py                 # Punto de entrada de la aplicación FastAPI
├── requirements.txt        # Dependencias de Python
├── .env.example           # Plantilla de variables de entorno
├── classroom_hub.db       # Base de datos SQLite (creada automáticamente)
└── app/
    ├── api/               # Endpoints REST
    │   └── sessions.py    # API de gestión de sesiones
    ├── core/              # Configuración y middleware
    │   ├── config.py      # Configuración de la aplicación
    │   ├── database.py    # Gestión de base de datos SQLite
    │   ├── middleware.py  # Middleware de tolerancia a fallos
    │   └── security.py    # Utilidades de seguridad (UUID)
    ├── models/            # Modelos Pydantic
    │   └── session.py     # Modelos de sesión y mensajes
    ├── services/          # Lógica de negocio
    │   ├── session_service.py      # Gestión de sesiones con SQLite
    │   ├── connection_manager.py   # Gestión de conexiones WebSocket
    │   └── idempotency_service.py  # Servicio de idempotencia con SQLite
    └── websocket/         # Manejo de WebSocket
        └── handler.py     # Endpoint WebSocket
```

### Flujo de Datos

1. **Creación de Sesión**: Cliente → API REST → SessionService → SQLite (persistencia) → Respuesta
2. **Conexión WebSocket**: Cliente → WebSocket Handler → Validación contra SQLite → ConnectionManager
3. **Broadcast de Señal**: Cliente → WebSocket → IdempotencyService (SQLite) → ConnectionManager → Grupo

### Persistencia de Datos

El sistema utiliza SQLite para persistencia de datos críticos:

- **Tabla `sessions`**: Almacena sesiones de estudiantes con TTL de 1 hora
- **Tabla `processed_events`**: Almacena IDs de eventos procesados para idempotencia
- **ConnectionManager**: Mantiene conexiones WebSocket activas en memoria (no persistibles)

Esto garantiza que el estado del sistema se mantenga incluso si el proceso se reinicia.

---

## Dependencias

### Paquetes Principales

- **fastapi>=0.104.1**: Framework web moderno y rápido
- **uvicorn[standard]>=0.24.0**: Servidor ASGI para FastAPI
- **websockets>=12.0**: Soporte para WebSocket
- **python-socketio>=5.10.0**: Socket.IO para Python
- **aiohttp>=3.9.1**: Cliente HTTP asíncrono
- **pydantic>=2.5.0**: Validación de datos y settings
- **pydantic-settings>=2.1.0**: Gestión de configuración
- **async-timeout>=4.0.3**: Timeouts para operaciones asíncronas

**Nota**: SQLite es parte de la biblioteca estándar de Python, no requiere instalación adicional.

---

## Configuración

### Variables de Entorno

Copie `.env.example` a `.env` y configure las variables:

```bash
NOMBRE_APLICACION=Classroom Hub BFF
VERSION_APLICACION=1.0.0
HOST=0.0.0.0
PUERTO=8000
DEBUG=True

# WebSocket
WS_MAX_CONEXIONES=100
WS_INTERVALO_PING=20
WS_TIMEOUT_PING=20

# Configuración de sesiones
SESION_TTL=3600  # 1 hora

# Latencia objetivo (ms)
LATENCIA_OBJETIVO_MS=500
```

### Configuración en Código (`app/core/config.py`)

La clase `Configuracion` carga automáticamente las variables desde `.env`:

```python
class Configuracion(BaseSettings):
    nombre_aplicacion: str = "Classroom Hub BFF"
    version_aplicacion: str = "1.0.0"
    host: str = "0.0.0.0"
    puerto: int = 8000
    debug: bool = True

    # Configuración WebSocket
    ws_max_conexiones: int = 100
    ws_intervalo_ping: int = 20
    ws_timeout_ping: int = 20

    # Configuración de sesiones
    sesion_ttl: int = 3600  # 1 hora

    # Latencia objetivo de broadcast (ms)
    latencia_objetivo_ms: int = 500

    class Config:
        env_file = ".env"
        case_sensitive = False


configuracion = Configuracion()
```

---

## Estructura del Proyecto

```
backend/
├── main.py                 # Punto de entrada de la aplicación FastAPI
├── requirements.txt        # Dependencias de Python
├── Dockerfile             # Configuración de Docker
├── .dockerignore          # Archivos ignorados por Docker
├── .env.example           # Plantilla de variables de entorno
├── classroom_hub.db       # Base de datos SQLite (creada automáticamente)
└── app/
    ├── api/               # Endpoints REST
    │   └── sessions.py    # API de gestión de sesiones
    ├── core/              # Configuración y middleware
    │   ├── config.py      # Configuración de la aplicación
    │   ├── database.py    # Gestión de base de datos SQLite
    │   ├── middleware.py  # Middleware de tolerancia a fallos
    │   └── security.py    # Utilidades de seguridad (UUID)
    ├── models/            # Modelos Pydantic
    │   └── session.py     # Modelos de sesión y mensajes
    ├── services/          # Lógica de negocio
    │   ├── session_service.py      # Gestión de sesiones con SQLite
    │   ├── connection_manager.py   # Gestión de conexiones WebSocket
    │   └── idempotency_service.py  # Servicio de idempotencia con SQLite
    └── websocket/         # Manejo de WebSocket
        └── handler.py     # Endpoint WebSocket
```

---

## API REST

### Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Información de la API |
| GET | `/health` | Estado del sistema |
| POST | `/api/v1/sessions/` | Crear sesión |
| GET | `/api/v1/sessions/{session_id}` | Obtener sesión |
| DELETE | `/api/v1/sessions/{session_id}` | Eliminar sesión |

### Crear Sesión

**Request:**
```json
{
  "name": "Juan Pérez",
  "group_id": "grupo-a"
}
```

**Response (201):**
```json
{
  "session_id": "uuid-v4",
  "name": "Juan Pérez",
  "group_id": "grupo-a",
  "created_at": "2024-01-01T00:00:00Z",
  "expires_at": "2024-01-01T01:00:00Z"
}
```

---

## WebSocket

### Conexión

**URL:** `ws://localhost:8000/ws?session_id={session_id}&group_id={group_id}&name={name}`

### Tipos de Mensajes

**signal:** Broadcast una señal al grupo
```json
{
  "type": "signal",
  "event_id": "uuid-v4",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**ack:** Confirmación de recepción
```json
{
  "type": "ack",
  "event_id": "uuid-v4"
}
```

**notification:** Notificación broadcast al grupo
```json
{
  "type": "notification",
  "data": {
    "message": "Juan Pérez ha enviado una señal!",
    "sender_name": "Juan Pérez",
    "timestamp": "2024-01-01T00:00:00Z"
  },
  "event_id": "uuid-v4"
}
```

---

## Instalación y Ejecución

### Prerrequisitos

- Python 3.8+
- SQLite (incluido en la biblioteca estándar de Python)

### Instalación Local

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env
# Editar .env con la configuración deseada
```

### Ejecución Local

**Modo Desarrollo:**
```bash
python main.py
```

**Modo Producción con Uvicorn:**
```bash
uvicorn main:aplicacion --host 0.0.0.0 --port 8000 --workers 4
```

### Docker

**Construir la imagen:**
```bash
cd backend
docker build -t classroom-hub-backend .
```

**Ejecutar el contenedor:**
```bash
docker run -p 8000:8000 classroom-hub-backend
```

**Con variables de entorno:**
```bash
docker run -p 8000:8000 \
  -e PUERTO=8000 \
  -e DEBUG=False \
  classroom-hub-backend
```

### Verificación

```bash
# Health check
curl http://localhost:8000/health

# Documentación API
# Abrir en navegador: http://localhost:8000/docs
```

---

## Requisitos Funcionales Implementados

- **Validación de Identidad Única**: Retorna HTTP 409 si el nombre ya existe, mitiga condiciones de carrera con locks por nombre
- **Asignación de Nodos**: Mapea conexiones de estudiantes con su group_id
- **Aislamiento Estricto de Datos**: Transmisiones enviadas exclusivamente a miembros del mismo grupo
- **Conexión Concurrente Masiva**: Soporta >40 dispositivos simultáneos sin degradación
- **Retransmisión de Señales**: Latencia <500ms para propagación de señales
- **Idempotencia**: Valida UUIDs contra SQLite para prevenir procesamiento duplicado
- **Tolerancia a Fallos**: Intercepta fallos y envía mensajes controlados en lugar de crash

## Monitoreo

### Health Check

```bash
GET /health
```

**Response:**
```json
{
  "estado": "saludable",
  "nombre_aplicacion": "Classroom Hub BFF",
  "version": "1.0.0",
  "conexiones_activas": 10,
  "grupos_activos": 3,
  "sesiones_persistidas": 10,
  "eventos_procesados": 150
}
```

---

## Documentación API Interactiva

FastAPI genera automáticamente documentación interactiva:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

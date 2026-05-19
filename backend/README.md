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
- [Servicios](#servicios)
- [Middleware y Tolerancia a Fallos](#middleware-y-tolerancia-a-fallos)
- [Seguridad](#seguridad)
- [Instalación y Ejecución](#instalación-y-ejecución)
- [Requisitos Funcionales Implementados](#requisitos-funcionales-implementados)

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

### `main.py`

Punto de entrada de la aplicación FastAPI.

**Funcionalidades:**

- **Lifespan Management**: Gestiona el ciclo de vida de la aplicación (startup/shutdown)
- **Middleware Registration**: Registra middleware de CORS y tolerancia a fallos
- **Exception Handlers**: Manejadores de excepciones HTTP, validación y generales
- **Router Inclusion**: Incluye routers de sesiones y WebSocket
- **Health Check**: Endpoint `/health` para monitoreo del estado
- **Root Endpoint**: Endpoint `/` con información básica de la API

**Endpoints:**

- `GET /` - Información de la API
- `GET /health` - Estado del sistema (conexiones activas, grupos, sesiones)

### `app/api/sessions.py`

API REST para gestión de sesiones de estudiantes.

**Endpoints:**

#### POST `/api/v1/sessions/`
Crea una nueva sesión para un estudiante.

**Request Body:**
```json
{
  "name": "Juan Pérez",
  "group_id": "grupo-a"
}
```

**Response (201 Created):**
```json
{
  "session_id": "uuid-v4",
  "name": "Juan Pérez",
  "group_id": "grupo-a",
  "created_at": "2024-01-01T00:00:00Z",
  "expires_at": "2024-01-01T01:00:00Z"
}
```

**Error (409 Conflict):**
```json
{
  "error": "SESSION_EXISTS",
  "message": "Session with name 'Juan Pérez' already exists",
  "status_code": 409
}
```

**Implementa:**
- RQ-001: Validación de Identidad Única (Servidor)
- CA-1.1: Retorna HTTP 409 si el nombre ya existe
- CA-1.2: Mitiga condiciones de carrera para solicitudes concurrentes idénticas

#### GET `/api/v1/sessions/{session_id}`
Recupera una sesión por ID.

**Response (200 OK):**
```json
{
  "session_id": "uuid-v4",
  "name": "Juan Pérez",
  "group_id": "grupo-a",
  "created_at": "2024-01-01T00:00:00Z",
  "expires_at": "2024-01-01T01:00:00Z"
}
```

**Error (404 Not Found):**
```json
{
  "error": "SESSION_NOT_FOUND",
  "message": "Session {session_id} not found or expired",
  "status_code": 404
}
```

#### DELETE `/api/v1/sessions/{session_id}`
Elimina una sesión por ID.

**Response (204 No Content)**

**Error (404 Not Found):**
```json
{
  "error": "SESSION_NOT_FOUND",
  "message": "Session {session_id} not found",
  "status_code": 404
}
```

### `app/models/session.py`

Modelos Pydantic para validación de datos.

**Modelos:**

#### `SessionCreate`
```python
class SessionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    group_id: str = Field(..., min_length=1, max_length=50)
```

#### `SessionResponse`
```python
class SessionResponse(BaseModel):
    session_id: str
    name: str
    group_id: str
    created_at: datetime
    expires_at: datetime
```

#### `SessionError`
```python
class SessionError(BaseModel):
    error: str
    message: str
    status_code: int
```

#### `WebSocketMessage`
```python
class WebSocketMessage(BaseModel):
    type: str
    data: dict
    timestamp: datetime
    event_id: Optional[str] = None
```

### `app/core/config.py`

Gestión de configuración mediante Pydantic Settings.

Carga variables de entorno desde `.env` y proporciona acceso tipado a la configuración.

### `app/core/database.py`

Gestor de base de datos SQLite para persistencia de sesiones y eventos procesados.

**Clase: `BaseDatos`**

**Tablas:**
- `sessions`: Almacena sesiones de estudiantes con TTL de 1 hora
- `processed_events`: Almacena IDs de eventos procesados para idempotencia

**Métodos principales:**
- `crear_sesion()`: Crea una nueva sesión en la base de datos
- `obtener_sesion()`: Recupera una sesión por ID si no está expirada
- `obtener_sesion_por_nombre()`: Recupera una sesión por nombre si no está expirada
- `eliminar_sesion()`: Elimina una sesión por ID
- `limpiar_sesiones_expiradas()`: Elimina todas las sesiones expiradas
- `registrar_evento_procesado()`: Registra un evento como procesado
- `evento_fue_procesado()`: Verifica si un evento ya fue procesado

**Implementa:**
- Tolerancia a fallos mediante persistencia en disco
- Idempotencia persistente para eventos

### `app/core/middleware.py`

Middleware de tolerancia a fallos y manejadores de excepciones.

**Clases:**

#### `MiddlewareToleranciaFallos`
Middleware que intercepta excepciones no manejadas y retorna respuestas controladas en lugar de dejar que la aplicación falle.

**Implementa:**
- RQ-009: Tolerancia a Fallos (Ingeniería del Caos)
- CA-9.1: Intercepta fallos de servicio y envía mensajes controlados
- CA-9.2: Sin fallos inesperados por inyección de latencia o cortes de servicio

**Manejadores de Excepciones:**

- `manejador_excepcion_http`: Maneja excepciones HTTP con respuestas controladas
- `manejador_excepcion_validacion`: Maneja errores de validación con detalles
- `manejador_excepcion_general`: Maneja excepciones generales con degradación graceful

### `app/core/security.py`

Utilidades de seguridad para generación y validación de UUIDs.

**Funciones:**

#### `generar_id_sesion()`
Genera un ID de sesión único usando UUID v4.

#### `generar_id_evento()`
Genera un ID de evento único usando UUID v4 para idempotencia.

#### `validar_uuid(cadena_uuid: str) -> bool`
Valida si un string es un UUID v4 válido.

### `app/services/session_service.py`

Servicio para gestión de sesiones con persistencia en SQLite y mitigación de condiciones de carrera.

**Clase: `ServicioSesion`**

**Atributos:**
- `_bloqueos_nombre: Dict[str, asyncio.Lock]`: Locks por nombre para prevenir condiciones de carrera
- `_bloqueo_global: asyncio.Lock`: Lock global para gestión de locks por nombre

**Métodos:**

#### `crear_sesion(datos_sesion: CrearSesion) -> RespuestaSesion`
Crea una nueva sesión con mitigación de condiciones de carrera y persistencia en SQLite.

**Algoritmo:**
1. Obtiene o crea un lock específico para el nombre
2. Adquiere el lock del nombre
3. Verifica en la base de datos si el nombre ya existe
4. Si existe, lanza ValueError
5. Si no existe, crea la sesión en SQLite con TTL
6. Libera el lock

**Implementa:**
- RQ-001: Validación de Identidad Única
- CA-1.1: Retorna error si el nombre existe
- CA-1.2: Mitiga condiciones de carrera con locks por nombre
- Persistencia en SQLite para tolerancia a fallos

#### `obtener_sesion(id_sesion: str) -> Optional[Dict]`
Recupera una sesión por ID desde SQLite. Retorna None si no existe o está expirada.

#### `eliminar_sesion(id_sesion: str) -> bool`
Elimina una sesión por ID de SQLite. Retorna True si se eliminó, False si no existía.

#### `limpiar_sesiones_expiradas()`
Elimina todas las sesiones expiradas de SQLite.

#### `obtener_cantidad_sesiones_activas() -> int`
Retorna el conteo de sesiones activas (no expiradas) desde SQLite.

#### `obtener_sesiones_por_grupo(id_grupo: str) -> list`
Obtiene todas las sesiones activas de un grupo desde SQLite.

### `app/services/connection_manager.py`

Gestor de conexiones WebSocket con aislamiento estricto de grupos.

**Clase: `GestorConexiones`**

**Atributos:**
- `_conexiones: Dict[str, WebSocket]`: Mapeo id_sesion → WebSocket
- `_miembros_grupo: Dict[str, Set[str]]`: Mapeo id_grupo → set de ids_sesion
- `_grupos_sesion: Dict[str, str]`: Mapeo id_sesion → id_grupo
- `_nombres_sesion: Dict[str, str]`: Mapeo id_sesion → nombre
- `_bloqueo: asyncio.Lock`: Lock para operaciones atómicas

**Métodos:**

#### `conectar(id_sesion, id_grupo, nombre, websocket)`
Conecta un WebSocket y lo asocia con un grupo.

**Implementa:**
- RQ-003: Asignación de Nodos
- CA-3.1: Mapeo en memoria de conexiones de estudiantes a group_ids

#### `desconectar(id_sesion)`
Desconecta un WebSocket y limpia los mapeos.

#### `broadcast_a_grupo(id_grupo, mensaje, excluir_id_sesion)`
Broadcast un mensaje a todos los miembros de un grupo específico.

**Implementa:**
- RQ-004: Aislamiento Estricto de Datos
- CA-4.1: Aislamiento estricto - solo envía a miembros del grupo
- CA-4.2: Sin filtración de datos entre grupos
- RQ-006 CA-6.1: Latencia objetivo <500ms

**Retorna:** Tupla (número de receptores, latencia en ms)

#### `_enviar_mensaje(websocket, mensaje)`
Enviar un mensaje a un WebSocket específico.

#### `obtener_miembros_grupo(id_grupo) -> Set[str]`
Retorna todos los ids_sesion en un grupo.

#### `obtener_grupo_sesion(id_sesion) -> Optional[str]`
Retorna el id_grupo para una sesión.

#### `obtener_nombre_sesion(id_sesion) -> Optional[str]`
Retorna el nombre para una sesión.

#### `obtener_cantidad_conexiones() -> int`
Retorna el número total de conexiones activas.

#### `obtener_cantidad_grupos() -> int`
Retorna el número de grupos activos.

#### `limpiar_conexiones_obsoletas()`
Limpia conexiones obsoletas (cerradas). enviando pings.

### `app/services/idempotency_service.py`

Servicio para gestión de idempotencia y prevención de procesamiento duplicado con persistencia en SQLite.

**Clase: `ServicioIdempotencia`**

**Atributos:**
- `_bloqueo: asyncio.Lock`: Lock para operaciones atómicas

**Métodos:**

#### `es_evento_duplicado(id_evento: str) -> bool`
Verificar si un evento con el ID dado ya ha sido procesado en SQLite.

**Algoritmo:**
1. Valida el UUID (invalid UUIDs son tratados como duplicados)
2. Verifica en la base de datos si ya fue procesado
3. Si no fue procesado, lo registra en SQLite
4. Retorna True si es duplicado, False si es nuevo

**Implementa:**
- RQ-008: Idempotencia y Sincronización Post-Conexión
- CA-8.2: Valida UUIDs contra SQLite. Si existe, descarta broadcast pero confirma recepción
- Persistencia en SQLite para tolerancia a fallos

#### `reconocer_evento(id_evento: str) -> bool`
Reconocer que un evento ha sido procesado y puede ser removido de SQLite.

#### `obtener_tamano_caché() -> int`
Obtener el tamaño actual de la caché de eventos procesados en SQLite.

#### `limpiar_eventos_antiguos(horas: int = 24) -> int`
Limpiar eventos procesados más antiguos que el número de horas especificado.

### `app/websocket/handler.py`

Manejador del endpoint WebSocket para comunicación en tiempo real.

**Endpoint:**

#### WebSocket `/ws`
Endpoint WebSocket para comunicación en tiempo real.

**Query Parameters:**
- `session_id`: ID de sesión (requerido)
- `group_id`: ID de grupo (requerido)
- `name`: Nombre del estudiante (requerido)

**Flujo de Conexión:**

1. **Validación de Sesión**: Verifica en SQLite que la sesión exista y no esté expirada
2. **Verificación de Parámetros**: Confirma que id_grupo y nombre coinciden con la sesión
3. **Límite de Conexiones**: Verifica que no se exceda el máximo de conexiones
4. **Aceptación**: Acepta la conexión WebSocket
5. **Registro**: Registra la conexión en GestorConexiones
6. **Loop de Mensajes**: Recibe y procesa mensajes continuamente
7. **Limpieza**: Al desconectar, limpia la conexión

**Implementa:**
- RQ-005: Conexión Concurrente Masiva
- CA-5.1: Soporta conexión simultánea de >40 dispositivos sin degradación
- RQ-006: Retransmisión de Señales (Broadcast)
- CA-6.1: Latencia <500ms para propagación de señales
- CA-6.2: Renderizado dinámico de texto de notificación

**Tipos de Mensajes:**

##### `signal`
Broadcast una señal a todos los miembros del grupo (excepto el remitente).

**Request:**
```json
{
  "type": "signal",
  "event_id": "uuid-v4",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Validación de Idempotencia:**
- Verifica en SQLite si el event_id ya fue procesado
- Si es duplicado, retorna ACK con status "duplicate"
- Si es nuevo, registra en SQLite y procede con broadcast

**Response (ACK):**
```json
{
  "type": "ack",
  "event_id": "uuid-v4",
  "status": "success",
  "recipients": 5,
  "latency_ms": 123.45
}
```

**Broadcast a Grupo:**
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

##### `ack`
Confirmación de recepción de un evento desde el cliente.

**Request:**
```json
{
  "type": "ack",
  "event_id": "uuid-v4"
}
```

##### `ping`
Ping para mantener la conexión viva.

**Response:**
```json
{
  "type": "pong"
}
```

##### Mensajes Desconocidos
Retorna error para tipos de mensaje no reconocidos.

**Response:**
```json
{
  "type": "error",
  "message": "Unknown message type: {type}"
}
```

---

## API REST

### Endpoints Disponibles

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/` | Información de la API | No |
| GET | `/health` | Estado del sistema | No |
| POST | `/api/v1/sessions/` | Crear sesión | No |
| GET | `/api/v1/sessions/{session_id}` | Obtener sesión | No |
| DELETE | `/api/v1/sessions/{session_id}` | Eliminar sesión | No |

### Códigos de Error

| Código | Error | Descripción |
|--------|-------|-------------|
| 200 | OK | Solicitud exitosa |
| 201 | Created | Recurso creado exitosamente |
| 204 | No Content | Recurso eliminado exitosamente |
| 400 | Bad Request | Solicitud inválida |
| 404 | Not Found | Recurso no encontrado |
| 409 | Conflict | Recurso ya existe (sesión duplicada) |
| 422 | Unprocessable Entity | Error de validación |
| 500 | Internal Server Error | Error interno del servidor |
| 503 | Service Unavailable | Servicio temporalmente no disponible |

---

## WebSocket

### Conexión

**URL:** `ws://localhost:8000/ws`

**Query Parameters:**
- `session_id`: ID de sesión válido
- `group_id`: ID del grupo de la sesión
- `name`: Nombre del estudiante

### Códigos de Cierre WebSocket

| Código | Razón | Descripción |
|--------|-------|-------------|
| 4001 | Invalid or expired session | Sesión inválida o expirada |
| 4002 | Session parameters mismatch | Parámetros de sesión no coinciden |
| 4003 | Maximum connections reached | Límite de conexiones alcanzado |
| 1000 | Normal Closure | Cierre normal |
| 1001 | Going Away | Cliente desconectado |

### Flujo de Mensajes

```
Cliente → WebSocket → Handler → ServicioIdempotencia (SQLite) → GestorConexiones → Grupo
         ← ACK ← Handler ← GestorConexiones
```

---

## Servicios

### ServicioSesion
Gestiona el ciclo de vida de las sesiones de estudiantes con:
- **Persistencia en SQLite**: Las sesiones se almacenan en base de datos
- **Prevención de condiciones de carrera**: Locks por nombre para solicitudes concurrentes
- **Validación de identidad única**: Restricción UNIQUE en base de datos

### GestorConexiones
Gestiona conexiones WebSocket con aislamiento estricto entre grupos. Cada conexión está asociada a un id_grupo y solo recibe mensajes de su grupo. Las conexiones se mantienen en memoria (no persistibles).

### ServicioIdempotencia
Previene el procesamiento duplicado de eventos mediante:
- **Persistencia en SQLite**: IDs de eventos procesados se almacenan en base de datos
- **Validación de UUID**: Solo acepta UUID v4 válidos
- **Limpieza automática**: Método para limpiar eventos antiguos

---

## Middleware y Tolerancia a Fallos

### MiddlewareToleranciaFallos
Middleware global que captura excepciones no manejadas y retorna respuestas HTTP 503 controladas en lugar de dejar que la aplicación falle.

### Exception Handlers
- **manejador_excepcion_http**: Maneja excepciones HTTP con respuestas estandarizadas
- **manejador_excepcion_validacion**: Maneja errores de validación con detalles de los campos
- **manejador_excepcion_general**: Maneja excepciones generales con mensajes genéricos para no exponer detalles internos

---

## Seguridad

### Generación de UUID
Todos los IDs (sesiones, eventos) son UUID v4 generados criptográficamente para garantizar unicidad.

### Validación de UUID
Se valida que todos los UUIDs recibidos sean UUID v4 válidos antes de procesarlos.

### Validación de Sesión
Las conexiones WebSocket validan contra SQLite que el id_sesion exista, no esté expirado, y coincida con los parámetros proporcionados.

### Aislamiento de Grupos
El GestorConexiones garantiza que los mensajes solo se envían a miembros del mismo grupo, previniendo filtración de datos entre grupos.

---

## Instalación y Ejecución

### Prerrequisitos

- Python 3.8+
- SQLite (incluido en la biblioteca estándar de Python)

### Instalación

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Configuración

```bash
cp .env.example .env
# Editar .env con la configuración deseada
```

### Ejecución

**Modo Desarrollo:**
```bash
python main.py
```

**Modo Producción con Uvicorn:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
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

### RQ-001: Validación de Identidad Única (Servidor)
- **CA-1.1**: Retorna HTTP 409 Conflict si el nombre ya existe
- **CA-1.2**: Mitiga condiciones de carrera para solicitudes concurrentes idénticas usando locks por nombre
- **Persistencia**: Las sesiones se almacenan en SQLite con restricción UNIQUE en nombre

### RQ-003: Asignación de Nodos
- **CA-3.1**: Mapea y asocia en memoria cada conexión de estudiante con su group_id

### RQ-004: Aislamiento Estricto de Datos
- **CA-4.1**: Transmisiones del Grupo A enviadas exclusivamente a WebSockets del Grupo A
- **CA-4.2**: Prohíbe filtración de datos entre canales de diferentes grupos

### RQ-005: Conexión Concurrente Masiva
- **CA-5.1**: Soporta conexión simultánea de >40 dispositivos sin degradación

### RQ-006: Retransmisión de Señales (Broadcast)
- **CA-6.1**: Latencia <500ms para propagación de señales
- **CA-6.2**: Renderizado dinámico de texto de notificación con nombre del estudiante

### RQ-008: Idempotencia y Sincronización Post-Conexión
- **CA-8.2**: Valida UUIDs contra SQLite. Si existe, descarta broadcast pero confirma recepción
- **Persistencia**: Los IDs de eventos procesados se almacenan en SQLite para tolerancia a fallos

### RQ-009: Tolerancia a Fallos (Ingeniería del Caos)
- **CA-9.1**: Intercepta fallos de servicio y envía mensajes controlados en lugar de crash
- **CA-9.2**: Sin fallos inesperados por inyección de latencia o cortes de servicio

## Monitoreo

### Health Check Endpoint

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

### Logs

La aplicación utiliza logging de Python con nivel INFO por defecto. Los logs incluyen:
- Conexiones/desconexiones WebSocket
- Errores de validación
- Broadcast de señales con métricas de latencia
- Excepciones no manejadas

---

## Documentación API Interactiva

FastAPI genera automáticamente documentación interactiva:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Licencia

[Agregar licencia según corresponda]

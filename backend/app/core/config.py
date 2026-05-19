from pydantic_settings import BaseSettings
from typing import Optional


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

    # Configuración Redis para locks distribuidos y caché
    redis_host: str = "localhost"
    redis_puerto: int = 6379
    redis_bd: int = 0
    redis_contrasena: Optional[str] = None

    # Configuración de sesiones
    sesion_ttl: int = 3600  # 1 hora

    # Latencia objetivo de broadcast (ms)
    latencia_objetivo_ms: int = 500

    class Config:
        env_file = ".env"
        case_sensitive = False


configuracion = Configuracion()

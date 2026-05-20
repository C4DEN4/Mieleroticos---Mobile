from pydantic_settings import BaseSettings

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

    # Latencia objetivo de broadcast (ms)
    latencia_objetivo_ms: int = 500

    # URLs de microservicios (nombres de servicios en docker-compose)
    identity_service_url: str = "http://identity-service:8001"
    groups_service_url: str = "http://groups-service:8002"

    class Config:
        env_file = ".env"
        case_sensitive = False

configuracion = Configuracion()

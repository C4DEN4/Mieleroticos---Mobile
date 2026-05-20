from pydantic_settings import BaseSettings

class Configuracion(BaseSettings):
    nombre_aplicacion: str = "Identity Microservice"
    host: str = "0.0.0.0"
    puerto: int = 8001
    debug: bool = True
    db_path: str = "identity.db"
    sesion_ttl: int = 3600  # 1 hora

    class Config:
        env_file = ".env"
        case_sensitive = False

configuracion = Configuracion()

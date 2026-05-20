from pydantic_settings import BaseSettings

class Configuracion(BaseSettings):
    nombre_aplicacion: str = "Groups Microservice"
    host: str = "0.0.0.0"
    puerto: int = 8002
    debug: bool = True
    db_path: str = "groups.db"

    class Config:
        env_file = ".env"
        case_sensitive = False

configuracion = Configuracion()

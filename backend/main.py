from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import logging
from app.core.config import configuracion as settings
from app.core.database import base_datos
from app.api.sessions import router as router_sesiones
from app.websocket.handler import router as router_websocket
from app.services.session_service import servicio_sesion
from app.services.connection_manager import gestor_conexiones
from app.core.middleware import (
    MiddlewareToleranciaFallos,
    manejador_excepcion_http,
    manejador_excepcion_validacion,
    manejador_excepcion_general
)

logging.basicConfig(level=logging.INFO)
registrador = logging.getLogger(__name__)


@asynccontextmanager
async def ciclo_vida(aplicacion: FastAPI):
    """Gestor del ciclo de vida de la aplicación."""
    registrador.info("Iniciando Classroom Hub BFF")
    registrador.info(f"Máximo de conexiones WebSocket: {settings.ws_max_conexiones}")
    registrador.info(f"Latencia objetivo de broadcast: {settings.latencia_objetivo_ms}ms")

    yield

    registrador.info("Cerrando Classroom Hub BFF")
    registrador.info(f"Conexiones activas al cierre: {gestor_conexiones.obtener_cantidad_conexiones()}")


aplicacion = FastAPI(
    title=settings.nombre_aplicacion,
    version=settings.version_aplicacion,
    lifespan=ciclo_vida
)

# Middleware de tolerancia a fallos
aplicacion.add_middleware(MiddlewareToleranciaFallos)

# Middleware CORS
aplicacion.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Manejadores de excepciones para tolerancia a fallos
aplicacion.add_exception_handler(StarletteHTTPException, manejador_excepcion_http)
aplicacion.add_exception_handler(RequestValidationError, manejador_excepcion_validacion)
aplicacion.add_exception_handler(Exception, manejador_excepcion_general)

# Incluir routers
aplicacion.include_router(router_sesiones)
aplicacion.include_router(router_websocket)


@aplicacion.get("/health")
async def verificar_salud():
    """Endpoint de verificación de salud con consulta a base de datos."""
    return {
        "estado": "saludable",
        "nombre_aplicacion": settings.nombre_aplicacion,
        "version": settings.version_aplicacion,
        "conexiones_activas": gestor_conexiones.obtener_cantidad_conexiones(),
        "grupos_activos": gestor_conexiones.obtener_cantidad_grupos(),
        "sesiones_persistidas": servicio_sesion.obtener_cantidad_sesiones_activas(),
        "eventos_procesados": base_datos.obtener_cantidad_eventos_procesados()
    }


@aplicacion.get("/")
async def raiz():
    """Endpoint raíz."""
    return {
        "mensaje": "API Classroom Hub BFF",
        "version": settings.version_aplicacion,
        "documentacion": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:aplicacion",
        host=settings.host,
        port=settings.puerto,
        reload=settings.debug,
        log_level="info"
    )

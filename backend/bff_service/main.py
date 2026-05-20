from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import logging
import uvicorn
from app.core.config import configuracion as settings
from app.api.sessions import router as router_sesiones
from app.api.sessions import router_es as router_sesiones_es
from app.api.connections import router as router_conexiones
from app.websocket.handler import router as router_websocket
from app.services.connection_manager import gestor_conexiones
from app.services.client_http import cliente_http
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
    registrador.info("Iniciando Classroom Hub BFF Distribuido")
    registrador.info(f"Identity Service URL: {settings.identity_service_url}")
    registrador.info(f"Groups Service URL: {settings.groups_service_url}")
    yield
    await cliente_http.cerrar()
    registrador.info("Cerrando Classroom Hub BFF Distribuido")

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
aplicacion.include_router(router_sesiones_es)
aplicacion.include_router(router_conexiones)
aplicacion.include_router(router_websocket)

@aplicacion.get("/health")
async def verificar_salud():
    """Endpoint de verificación de salud que verifica los microservicios centrales."""
    estado_identidad = "desconocido"
    estado_grupos = "desconocido"
    
    try:
        session = await cliente_http.obtener_sesion()
        async with session.get(f"{settings.identity_service_url}/health") as resp:
            if resp.status == 200:
                estado_identidad = "saludable"
            else:
                estado_identidad = f"error ({resp.status})"
    except Exception:
        estado_identidad = "caído / no disponible"

    try:
        session = await cliente_http.obtener_sesion()
        async with session.get(f"{settings.groups_service_url}/health") as resp:
            if resp.status == 200:
                estado_grupos = "saludable"
            else:
                estado_grupos = f"error ({resp.status})"
    except Exception:
        estado_grupos = "caído / no disponible"

    return {
        "estado": "saludable" if estado_identidad == "saludable" and estado_grupos == "saludable" else "degradado",
        "nombre_aplicacion": settings.nombre_aplicacion,
        "version": settings.version_aplicacion,
        "conexiones_activas": gestor_conexiones.obtener_cantidad_conexiones(),
        "grupos_activos": gestor_conexiones.obtener_cantidad_grupos(),
        "servicios_internos": {
            "identity_service": estado_identidad,
            "groups_service": estado_grupos
        }
    }

@aplicacion.get("/")
async def raiz():
    return {
        "mensaje": "API Classroom Hub BFF Distribuido",
        "version": settings.version_aplicacion,
        "documentacion": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:aplicacion",
        host=settings.host,
        port=settings.puerto,
        reload=settings.debug
    )

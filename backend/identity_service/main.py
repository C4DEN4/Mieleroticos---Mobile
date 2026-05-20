from fastapi import FastAPI
import uvicorn
from app.core.config import configuracion as settings
from app.api.sessions import router as router_sesiones
from app.services.session_service import servicio_sesion

aplicacion = FastAPI(
    title=settings.nombre_aplicacion,
    version="1.0.0"
)

aplicacion.include_router(router_sesiones)

@aplicacion.get("/health")
async def health():
    return {
        "estado": "saludable",
        "servicio": settings.nombre_aplicacion,
        "sesiones_activas": servicio_sesion.obtener_cantidad_sesiones_activas()
    }

@aplicacion.get("/")
async def root():
    return {"mensaje": "Identity Microservice is running", "puerto": settings.puerto}

if __name__ == "__main__":
    uvicorn.run(
        "main:aplicacion",
        host=settings.host,
        port=settings.puerto,
        reload=settings.debug
    )

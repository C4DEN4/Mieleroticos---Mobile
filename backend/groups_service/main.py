from fastapi import FastAPI
import uvicorn
from app.core.config import configuracion as settings
from app.api.events import router as router_eventos
from app.services.idempotency_service import servicio_idempotencia

aplicacion = FastAPI(
    title=settings.nombre_aplicacion,
    version="1.0.0"
)

aplicacion.include_router(router_eventos)

@aplicacion.get("/health")
async def health():
    return {
        "estado": "saludable",
        "servicio": settings.nombre_aplicacion,
        "eventos_procesados": servicio_idempotencia.obtener_tamano_cache()
    }

@aplicacion.get("/")
async def root():
    return {"mensaje": "Groups Microservice is running", "puerto": settings.puerto}

if __name__ == "__main__":
    uvicorn.run(
        "main:aplicacion",
        host=settings.host,
        port=settings.puerto,
        reload=settings.debug
    )

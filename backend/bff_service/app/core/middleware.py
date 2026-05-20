from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

registrador = logging.getLogger(__name__)

class MiddlewareToleranciaFallos:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            try:
                await self.app(scope, receive, send)
            except Exception as exc:
                registrador.error(f"Excepción no manejada: {str(exc)}", exc_info=True)
                respuesta = JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    content={
                        "error": "SERVICIO_NO_DISPONIBLE",
                        "mensaje": "El servicio está experimentando dificultades. Por favor intente más tarde.",
                        "codigo_estado": status.HTTP_503_SERVICE_UNAVAILABLE
                    }
                )
                await respuesta(scope, receive, send)
        else:
            await self.app(scope, receive, send)

async def manejador_excepcion_http(solicitud: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "ERROR_HTTP",
            "mensaje": str(exc.detail),
            "codigo_estado": exc.status_code
        }
    )

async def manejador_excepcion_validacion(solicitud: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ERROR_VALIDACION",
            "mensaje": "Datos de solicitud inválidos",
            "detalles": exc.errors(),
            "codigo_estado": status.HTTP_422_UNPROCESSABLE_ENTITY
        }
    )

async def manejador_excepcion_general(solicitud: Request, exc: Exception):
    registrador.error(f"Excepción general: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "ERROR_INTERNO",
            "mensaje": "Ocurrió un error inesperado en la pasarela BFF",
            "codigo_estado": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
    )

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

registrador = logging.getLogger(__name__)


class MiddlewareToleranciaFallos:
    """
    Middleware para tolerancia a fallos y manejo graceful de errores.

    Implementa RQ-009: Tolerancia a Fallos (Ingeniería del Caos)
    CA-9.1: Intercepta fallos de servicio y envía mensajes controlados en lugar de crash
    CA-9.2: Sin crashes inesperados por inyección de latencia o cortes de servicio
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            solicitud = Request(scope, receive)

            try:
                await self.app(scope, receive, send)
            except Exception as exc:
                registrador.error(f"Excepción no manejada: {str(exc)}", exc_info=True)

                # Enviar respuesta de error controlada en lugar de crash
                respuesta = JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    content={
                        "error": "SERVICIO_NO_DISPONIBLE",
                        "mensaje": "El servicio está temporalmente no disponible. Por favor intente más tarde.",
                        "codigo_estado": status.HTTP_503_SERVICE_UNAVAILABLE
                    }
                )

                await respuesta(scope, receive, send)
        else:
            await self.app(scope, receive, send)


async def manejador_excepcion_http(solicitud: Request, exc: StarletteHTTPException):
    """Maneja excepciones HTTP con respuestas controladas."""
    registrador.warning(f"Excepción HTTP: {exc.status_code} - {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "ERROR_HTTP",
            "mensaje": str(exc.detail),
            "codigo_estado": exc.status_code
        }
    )


async def manejador_excepcion_validacion(solicitud: Request, exc: RequestValidationError):
    """Maneja errores de validación con respuestas controladas."""
    registrador.warning(f"Error de validación: {exc.errors()}")

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
    """
    Maneja excepciones generales con degradación graceful.

    Implementa CA-9.1: Mensajes de error controlados en lugar de crashes
    """
    registrador.error(f"Excepción general: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "ERROR_INTERNO",
            "mensaje": "Ocurrió un error inesperado. El servicio está trabajando para resolverlo.",
            "codigo_estado": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
    )
